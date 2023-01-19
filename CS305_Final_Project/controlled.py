import os
import struct
import socket
import threading
from keyboard import wait
from PIL import ImageGrab
from cv2 import cv2
from config import *
import numpy as np
from threading import Lock
from threading import Thread
import keyboard
import mouse

# from win32gui import GetDC
# from win32api import GetSystemMetrics
# from win32print import GetDeviceCaps
from win32.lib.win32con import DESKTOPHORZRES, DESKTOPVERTRES


class controlled(threading.Thread):
    def __init__(self, conn):
        super(controlled, self).__init__()
        self.sock = conn
        self.lock = threading.Lock()
        self.handleEnable=1
        self.ctrlEnable=1
    def run(self):
        self.img = None  # 压缩后np图像
        self.imbyt = None  # 编码后的图像
        self.scaling = 1  # 屏幕的缩放比例
        self.main_togo()
    def close(self):
        self.handleEnable = 0
        self.ctrlEnable=0
    def main_togo(self):
        conn = self.sock
        Thread(target=lambda: self.handle(conn)).start()
        Thread(target=lambda: self.ctrl(conn)).start()

    def ctrl(self, conn):
        """读取控制命令，并在本机还原操作"""

        def Op(key, op, ox, oy):
            # 缩放后的点击的坐标值
            ox /= self.scaling
            oy /= self.scaling

            if key == 1:
                if op == 100:
                    # 左键按下
                    mouse.move(ox, oy)
                    mouse.press(button=mouse.LEFT)
                elif op == 117:
                    # 左键弹起
                    x, y = mouse.get_position()
                    if ox != x or oy != y:
                        if not mouse.is_pressed():
                            mouse.press(button=mouse.LEFT)
                        mouse.move(ox, oy)
                    mouse.release(button=mouse.LEFT)
            elif key == 2:
                # 滚轮事件
                if op == 0:
                    # 向上
                    mouse.move(ox, oy)
                    mouse.wheel(delta=-1)
                else:
                    # 向下
                    mouse.move(ox, oy)
                    mouse.wheel(delta=1)
            elif key == 3:
                # 鼠标右键
                if op == 100:
                    # 右键按下
                    mouse.move(ox, oy)
                    mouse.press(button=mouse.RIGHT)
                elif op == 117:
                    # 右键弹起
                    mouse.move(ox, oy)
                    mouse.release(button=mouse.RIGHT)
            else:
                k = OFFICIAL_VIRTUAL_KEYS.get(key)
                if k is not None:
                    if op == 100:
                        keyboard.press(k)
                    elif op == 117:
                        keyboard.release(k)

        try:
            base_len = 6
            while self.ctrlEnable:
                cmd = b''
                rest = base_len - 0
                while rest > 0:
                    cmd += conn.recv(rest)
                    rest -= len(cmd)
                key = cmd[0]
                op = cmd[1]
                x = struct.unpack('>H', cmd[2:4])[0]
                y = struct.unpack('>H', cmd[4:6])[0]
                Op(key, op, x, y)
        except:
            return

    def handle(self, conn):

        self.lock.acquire()
        if self.imbyt is None:
            imorg = np.asarray(ImageGrab.grab())
            _, self.imbyt = cv2.imencode(".jpg", imorg, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
            imnp = np.asarray(self.imbyt, np.uint8)
            self.img = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
        self.lock.release()
        lenb = struct.pack(">BI", 1, len(self.imbyt))
        conn.sendall(lenb)
        conn.sendall(self.imbyt)

        while self.handleEnable:
            cv2.waitKey(70)
            gb = ImageGrab.grab()
            imgnpn = np.asarray(gb)
            _, timbyt = cv2.imencode(".jpg", imgnpn, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
            imnp = np.asarray(timbyt, np.uint8)
            imgnew = cv2.imdecode(imnp, cv2.IMREAD_COLOR)
            # 计算图像差值
            imgs = imgnew - self.img
            if (imgs != 0).any():
                # 画质改变
                pass
            else:
                continue
            self.imbyt = timbyt
            self.img = imgnew
            # 无损压缩
            _, imb = cv2.imencode(".png", imgs)
            l1 = len(self.imbyt)  # 原图像大小
            l2 = len(imb)  # 差异图像大小
            try:
                if l1 > l2:
                    # 传差异化图像
                    lenb = struct.pack(">BI", 0, l2)
                    conn.sendall(lenb)
                    conn.sendall(imb)
                else:
                    # 传原编码图像
                    lenb = struct.pack(">BI", 1, l1)
                    conn.sendall(lenb)
                    conn.sendall(self.imbyt)
            except ConnectionResetError or ConnectionAbortedError:
                break


# if __name__ == '__main__':
#     soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     soc.bind(('', 1111))
#     soc.listen(1)
#     conn, addrr = soc.accept()
#     new_thread = controlled(conn)
#     new_thread.start()
#     print(new_thread.number)
