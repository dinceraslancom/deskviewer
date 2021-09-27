import asyncio
import pickle
import sys
from threading import Thread

import cv2
import numpy as np
import websockets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel

from . import constant

key_translate = {}
for i in dir(Qt):
    data = i.split('_')
    if len(data) == 2:
        key_translate[getattr(Qt, i)] = data[1]

key_translate[16777249] = constant.CTRL
key_translate[16777248] = constant.SHIFT
key_translate[16777251] = constant.ALT


class EventList(list):
    def append(self, __object) -> None:
        if __object not in self:
            super().append(__object)


event_list = EventList()


async def connect(host, port, username, password, quality):
    global event_list

    async with websockets.connect(f"ws://{username}:{password}@{host}:{port}",
                                  max_size=None) as websocket:
        await websocket.send(quality)
        while True:
            events, event_list = event_list, EventList()

            await websocket.send(str(events))

            box = await websocket.recv()
            frame = await websocket.recv()
            w.update_frame(frame, box)


def start_client(app, host, port, username, password, quality):
    try:
        if sys.version_info >= (3, 7):
            import uvloop
            uvloop.install()

        asyncio.run(connect(host, port, username, password, quality))

    except Exception as e:
        print(e)
        app.exit()


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.title = "DeskView"
        self.setMouseTracking(True)

        self.setWindowTitle(self.title)
        self.label = QLabel(self)
        self.current_frame = None
        self.current_width = None
        self.current_height = None
        self.setMouseTracking(True)

    @staticmethod
    def get_button(e):
        if e.button() == Qt.LeftButton:
            return constant.LEFT
        elif e.button() == Qt.RightButton:
            return constant.RIGHT
        elif e.button() == Qt.MiddleButton:
            return constant.MIDDLE

    # Mouse Events

    def mousePressEvent(self, e) -> None:
        event_list.append((
            constant.MOUSE_DOWN, (
                e.x() / self.current_width, e.y() / self.current_height,
                self.get_button(e))))

    def mouseReleaseEvent(self, e) -> None:
        event_list.append((
            constant.MOUSE_UP, (
                e.x() / self.current_width, e.y() / self.current_height,
                self.get_button(e))))

    def mouseDoubleClickEvent(self, e) -> None:
        event_list.append((
            constant.MOUSE_DOUBLE_CLICK, (
                e.x() / self.current_width, e.y() / self.current_height,
                self.get_button(e))))

    def wheelEvent(self, e):
        if e.angleDelta().y() > 0:
            event = constant.SCROLL_UP
        else:
            event = constant.SCROLL_DOWN

        event_list.append((event, constant.SCROLL_STEP))

    # Key Events

    def keyPressEvent(self, e):
        try:
            key = chr(e.key())
        except:
            key = key_translate.get(e.key())
        finally:
            event_list.append((constant.KEY_PRESS, key))

    def update_label_size(self) -> None:
        width, height = int(w.width()), int(w.height())
        if (self.current_width, self.current_height) != (width, height):
            self.current_width, self.current_height = width, height
            self.label.setFixedHeight(self.current_height)
            self.label.setFixedWidth(self.current_width)

    def update_frame(self, frame, box):
        self.update_label_size()

        if not (box and frame):
            return

        frame_cv2 = cv2.cvtColor(
            np.array(pickle.loads(frame)),
            cv2.COLOR_BGRA2BGR
        )

        if self.current_frame is not None:
            x_min, y_min, x_max, y_max = eval(box)
            self.current_frame[y_min: y_max, x_min: x_max] = frame_cv2
        else:
            self.current_frame = frame_cv2

        height, width = self.current_frame.shape[:2]

        self.label.setPixmap(
            QPixmap(
                QImage(self.current_frame, width, height,
                       QImage.Format_RGB888).rgbSwapped()
            ).scaled(self.current_width, self.current_height))


def main():
    global w
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-H', '--host', metavar='ADDRESS', default='0.0.0.0',
                        help='Specify alternate connection address')

    parser.add_argument('--port', action='store',
                        default=8765, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8765]')

    parser.add_argument('--username', '-u', default='username')
    parser.add_argument('--password', '-p', default='password')

    parser.add_argument('--quality', '-q', default='high',
                        help="""high, low""")

    args = parser.parse_args()

    print(f'Connecting Server {args.host}:{args.port}')

    app = QApplication(sys.argv)
    w = MainWindow()
    w.setGeometry(640, 100, 800, 500)

    Thread(target=start_client, daemon=True, args=(app,
                                                   args.host,
                                                   args.port,
                                                   args.username,
                                                   args.password,
                                                   args.quality,
                                                   )).start()
    w.show()
    app.exit(app.exec_())


if __name__ == '__main__':
    main()
