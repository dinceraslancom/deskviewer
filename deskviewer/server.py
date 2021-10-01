import asyncio
import base64
import http
import os
import pickle
import sys
from queue import Queue
from threading import Thread
from time import sleep

import cv2
import mss
import numpy
import numpy as np
import pyautogui
import websockets

from . import constant

pyautogui.FAILSAFE = False

WIDTH, HEIGHT = pyautogui.size()

AUTHORIZATION = None

sys.stderr = open(os.devnull, 'a')


class EventsQueue(Queue):
    """ Created for handle with same command stack """

    def __contains__(self, item):
        with self.mutex:
            return item in self.queue


events_queue = EventsQueue()


class FrameService:
    def __init__(self, quality):
        self.scale = getattr(constant, quality.upper() + '_SCALE')
        self.last_frame_gray = None
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[0]

    def screenshot(self):
        """ Handle with screenshot """
        return self.sct.grab(self.monitor)

    def resize(self, img):
        height, width = img.shape[:2]
        return cv2.resize(img,
                          (int(width / self.scale), int(height / self.scale)))

    @staticmethod
    def convert_to_cv2(sct_img):
        return cv2.cvtColor(numpy.array(sct_img), cv2.COLOR_BGRA2BGR)

    @staticmethod
    def convert_to_gray(cv2_img):
        return cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def get_bounding_box(gray_frame_1, gray_frame_2):
        es = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 4))
        diff = cv2.absdiff(gray_frame_1, gray_frame_2)
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY)[1]
        diff = cv2.dilate(thresh, es, iterations=2)

        contours, hierarchy = cv2.findContours(
            diff.copy(),
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_NONE
        )

        if not contours:
            return None

        boundings_x = []
        boundings_y = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            boundings_x.append(x)
            boundings_x.append(x + w)
            boundings_y.append(y)
            boundings_y.append(y + h)

        x_min = min(boundings_x)
        y_min = min(boundings_y)
        x_max = max(boundings_x)
        y_max = max(boundings_y)
        return x_min, y_min, x_max, y_max

    @staticmethod
    def crop(frame, box):
        x_min, y_min, x_max, y_max = box
        return frame[y_min: y_max, x_min: x_max]

    def get(self):
        if self.last_frame_gray is None:
            ss = self.screenshot()
            frame = self.convert_to_cv2(ss)
            frame = self.resize(frame)
            self.last_frame_gray = self.convert_to_gray(frame)
            height, width = frame.shape[:2]
            return frame, (0, width, 0, height)

        ss = self.screenshot()
        frame = self.convert_to_cv2(ss)
        frame = self.resize(frame)
        frame_gray = self.convert_to_gray(frame)

        box = self.get_bounding_box(self.last_frame_gray, frame_gray)

        if not box:
            return None, None

        self.last_frame_gray = frame_gray
        frame_cropped = self.crop(frame, box)

        return frame_cropped, box


def delay_press(key):
    pyautogui.keyDown(key)
    sleep(constant.MODIFIER_KEYS_PRESS_DELAY)
    pyautogui.keyUp(key)


def events_handler():
    while True:
        sleep(constant.EVENTS_DELAY)

        while not events_queue.empty():

            e, c = events_queue.get()

            # Mouse

            if constant.MOUSE_DOWN == e:
                pyautogui.mouseDown(x=c[0] * WIDTH,
                                    y=c[1] * HEIGHT,
                                    button=c[2])

            elif constant.MOUSE_UP == e:
                pyautogui.mouseUp(x=c[0] * WIDTH,
                                  y=c[1] * HEIGHT,
                                  button=c[2])

            elif constant.MOUSE_DOUBLE_CLICK == e:
                pyautogui.doubleClick(x=c[0] * WIDTH,
                                      y=c[1] * HEIGHT,
                                      button=c[2])

            elif constant.MOUSE_MOVE == e:
                pyautogui.moveTo(x=c[0] * WIDTH,
                                 y=c[1] * HEIGHT,
                                 button=c[2])

            elif constant.SCROLL_DOWN == e:
                pyautogui.scroll(-c)

            elif constant.SCROLL_UP == e:
                pyautogui.scroll(c)

            # Keyboard

            elif constant.KEY_PRESS == e and c in constant.MODIFIER_KEYS:
                Thread(target=delay_press, args=(c,), daemon=True).start()

            elif constant.KEY_PRESS == e:
                pyautogui.press(c)


Thread(target=events_handler, daemon=True).start()


def get_basic_auth(username, password):
    user_pass = f'{username}:{password}'
    basic_credentials = base64.b64encode(user_pass.encode()).decode()
    return f'Basic {basic_credentials}'


async def screen_handler(websocket, path, *args, **kwargs):
    remote_ip = websocket.remote_address[0]
    print(f'Connected: {remote_ip}')

    quality = await websocket.recv()
    frame_service = FrameService(quality)

    while True:
        events = eval(await websocket.recv())

        for event in events:

            if event in events_queue:
                continue

            events_queue.put(event)

        frame_cropped, box = frame_service.get()

        if box:
            await websocket.send(bytes(str(box).encode()))
            await websocket.send(pickle.dumps(np.array(frame_cropped)))
        else:
            await websocket.send('')
            await websocket.send('')


class BasicAuthServerProtocol(websockets.WebSocketServerProtocol):

    async def process_request(self, path, request_headers):
        try:
            authorization = request_headers['Authorization']
        except KeyError:
            return http.HTTPStatus.UNAUTHORIZED, [], b'Missing credentials\n'
        if authorization != AUTHORIZATION:
            return http.HTTPStatus.FORBIDDEN, [], b'Incorrect credentials\n'


async def serve(bind="0.0.0.0", port=8765):
    async with websockets.serve(
            screen_handler,
            bind,
            port,
            max_size=None,
            create_protocol=BasicAuthServerProtocol):
        await asyncio.Future()


def main():
    global AUTHORIZATION
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--bind', '-b', metavar='ADDRESS', default='0.0.0.0',
                        help='Specify alternate bind address '
                             '[default: all interfaces]')

    parser.add_argument('--port', action='store',
                        default=8765, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8765]')

    parser.add_argument('--username', '-u', default='username')
    parser.add_argument('--password', '-p', default='password')

    args = parser.parse_args()

    bind, port = args.bind, args.port

    AUTHORIZATION = get_basic_auth(args.username, args.password)

    print(f'Server Starting {bind}:{port}')

    if sys.version_info >= (3, 7):
        import uvloop

        uvloop.install()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(serve(bind, port))
    else:
        asyncio.run(serve(bind, port))


if __name__ == '__main__':
    main()
