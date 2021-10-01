from setuptools import setup, find_packages

requires = [
    'numpy==1.20.3; python_version >= "3"',
    'mss==6.1.0; python_version >= "3"',
    'websockets==10.0; python_version >= "3"',
    'asyncio==3.4.3; python_version >= "3.3"',
    'uvloop==0.16.0; python_version >= "3.7"',
    'PyQt5==5.15.4; python_version > "3"',
    'pyautogui==0.9.53; python_version >= "3"',
    'opencv-python-headless==4.5.3.56; python_version >= "3"',

]

with open("README.rst", "r", encoding="utf8") as f:
    readme = f.read()

setup(
    name='deskviewer',
    version='0.0.3',
    package_dir={'deskviewer': 'deskviewer'},
    author="Dincer Aslan",
    author_email="dinceraslan.com@gmail.com",
    description="A tool that allows remote computer control.",
    long_description=readme,
    long_description_content_type='text/x-rst',
    url="https://github.com/dinceraslancom/deskviewer",
    project_urls={
        'Source': 'https://github.com/dinceraslancom/deskviewer',
    },
    install_requires=requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.3",
    entry_points={
        "console_scripts": [
            "deskviewer.publish = deskviewer.server:main",
            "deskviewer.connect = deskviewer.client:main",
            "deskviewer = deskviewer.main:main",
        ]
    },
)
