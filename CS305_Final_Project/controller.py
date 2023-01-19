import re
import struct
import socket
import threading
import tkinter
import numpy as np
from cv2 import cv2
from os import startfile
import tkinter.messagebox
from threading import Thread
from PIL import Image, ImageTk


class controller(threading.Thread):
    def __init__(self, conn):
        super(controller, self).__init__()
        self.sock = conn
        # 基础常量设置
        self.BUF_SIZE = 10240
        self.main_togoEnable = 1
        # 基础变量设置
        self.socks5 = None  # socket5
        self.scale = 1  # 放缩大小
        self.is_scale = False  # 放缩标志
        self.show_canvas = None  # 屏幕显示画布
        self.fix_width, self.fix_height = 0, 0  # 原传输画面尺寸

    def run(self):

        # 开启主窗口
        self.root = tkinter.Tk()

        # 设置标题，图标
        self.root.resizable(False, False)
        self.root.title("远程控制")

        # 设置tkinter组件
        menu = tkinter.Menu(self.root)
        self.root['menu'] = menu

        sca_lab = tkinter.Label(self.root, text=" 缩放大小:")
        sca = tkinter.Scale(self.root, from_=10, to=100, orient=tkinter.HORIZONTAL, length=100,
                            showvalue=100, resolution=0.1, tickinterval=50, command=self.set_scale)

        sca_lab.grid(row=1, column=0, padx=10, pady=10, ipadx=0, ipady=0)
        sca.grid(row=1, column=1, padx=0, pady=0, ipadx=100, ipady=0)
        sca.set(60)
        self.show_screen
        # 开启窗口循环
        self.root.mainloop()

    def close(self):
        self.main_togoEnable = 0

    def set_scale(self, x):
        """设置缩放大小"""

        self.scale = float(x) / 100
        self.is_scale = True

    def show_screen(self):
        """显示远程窗口"""

        if self.show_canvas is None:
            self.is_scale = True
            self.show_canvas = tkinter.Toplevel(self.root)
            Thread(target=self.main_togo).start()
        else:
            self.show_canvas.destroy()

    def bind_events(self, canvas, soc):
        """处理事件"""
        scale = self.scale
        soc = self.sock

        def event_do(data):
            soc.sendall(data)

        # 鼠标左键
        def left_down(e):
            return event_do(struct.pack('>BBHH', 1, 100, int(e.x / scale), int(e.y / scale)))

        def left_up(e):
            return event_do(struct.pack('>BBHH', 1, 117, int(e.x / scale), int(e.y / scale)))

        canvas.bind(sequence="<1>", func=left_down)
        canvas.bind(sequence="<ButtonRelease-1>", func=left_up)

        # 鼠标右键
        def right_down(e):
            return event_do(struct.pack('>BBHH', 3, 100, int(e.x / scale), int(e.y / scale)))

        def right_up(e):
            return event_do(struct.pack('>BBHH', 3, 117, int(e.x / scale), int(e.y / scale)))

        canvas.bind(sequence="<3>", func=right_down)
        canvas.bind(sequence="<ButtonRelease-3>", func=right_up)

        # 鼠标滚轮
        def Wheel(e):
            if e.delta < 0:
                return event_do(struct.pack('>BBHH', 2, 0, int(e.x / scale), int(e.y / scale)))
            else:
                return event_do(struct.pack('>BBHH', 2, 1, int(e.x / scale), int(e.y / scale)))

        canvas.bind(sequence="<MouseWheel>", func=Wheel)

        # 键盘
        def key_down(e):
            return event_do(struct.pack('>BBHH', e.keycode, 100, int(e.x / scale), int(e.y / scale)))

        def keyup(e):
            return event_do(struct.pack('>BBHH', e.keycode, 117, int(e.x / scale), int(e.y / scale)))

        canvas.bind(sequence="<KeyPress>", func=key_down)
        canvas.bind(sequence="<KeyRelease>", func=keyup)

    def main_togo(self):

        lenb = self.sock.recv(5)
        imtype, le = struct.unpack(">BI", lenb)
        imb = b''

        while le > self.BUF_SIZE:
            t = self.sock.recv(self.BUF_SIZE)
            imb += t
            le -= len(t)
        while le > 0:
            t = self.sock.recv(le)
            imb += t
            le -= len(t)

        data = np.frombuffer(imb, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        h, w, _ = img.shape
        self.fix_height, self.fix_width = h, w
        imsh = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        imi = Image.fromarray(imsh)
        imgTK = ImageTk.PhotoImage(image=imi)
        cv = tkinter.Canvas(self.show_canvas, width=w, height=h, bg="white")
        cv.focus_set()
        self.bind_events(cv, self.sock)
        cv.pack()
        cv.create_image(0, 0, anchor=tkinter.NW, image=imgTK)
        h = int(h * self.scale)
        w = int(w * self.scale)
        while self.main_togoEnable:
            if self.is_scale:
                h = int(self.fix_height * self.scale)
                w = int(self.fix_width * self.scale)
                cv.config(width=w, height=h)
                self.is_scale = False
            try:
                lenb = self.soc.recv(5)
                imtype, le = struct.unpack(">BI", lenb)
                imb = b''
                while le > self.BUF_SIZE:
                    t = self.soc.recv(self.BUF_SIZE)
                    imb += t
                    le -= len(t)
                while le > 0:
                    t = self.soc.recv(le)
                    imb += t
                    le -= len(t)
                data = np.frombuffer(imb, dtype=np.uint8)
                ims = cv2.imdecode(data, cv2.IMREAD_COLOR)
                if imtype == 1:
                    # 全传
                    img = ims
                else:
                    # 差异传
                    img = img + ims
                imt = cv2.resize(img, (w, h))
                imsh = cv2.cvtColor(imt, cv2.COLOR_RGB2RGBA)
                imi = Image.fromarray(imsh)
                imgTK.paste(imi)
            except:
                self.show_canvas = None
                self.show_screen()
                return

# if __name__ == '__main__':
#     soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     soc.connect(('127.0.0.1',1111))
#     new_thread = controller(soc)
#     new_thread.start()
