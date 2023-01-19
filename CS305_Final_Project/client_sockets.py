from CONSTANTS import *
from controlled import controlled
from controller import controller
from encryption import *
from socket import *
import pickle
from PIL import ImageGrab
from PIL import Image, ImageTk
from cv2 import cv2
import time
import threading
import sys
import numpy as np
import pyautogui as ag
import mouse
from _keyboard import getKeycodeMapping
import tkinter.messagebox
import tkinter
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import zlib
import pyaudio
import struct


class controlMessageSocket:

    def __init__(self, client, address, version):
        # server address
        self.serverAddress = address

        # The registered client
        self.client = client

        # Create socket
        if version == 4:
            self.sock = socket(AF_INET, SOCK_STREAM)
        else:
            self.sock = socket(AF_INET6, SOCK_STREAM)

        # self.sock.bind(('', self.serverAddress[1]))
        self.connectToServer()

        # Create a receive_server_data threading
        self.receiverThread = threading.Thread(target=self.receiver)
        self.receiverThread.start()

    def connectToServer(self):
        timeTry = 0
        while timeTry < 9:
            try:
                self.sock.connect(self.serverAddress)
                print("\n CLIENT: Meeting, Connect to server successfully.")
                break
            except:
                timeTry += 1
                time.sleep(1)
                print('\n CLIENT: Meeting, NO.' + str(timeTry) + ' try, ' + 'could not connect to the server ' + str(
                    self.serverAddress))
        if timeTry >= 9: sys.exit()

    def sender(self, data, sendingAESPassword=False):
        print('\n CLIENT: sender: ' + str(data))
        if sendingAESPassword:
            # only use for sending AES
            self.sock.send(data)
        else:
            # General
            # return a string
            # aesPass type = str
            self.sock.send(aesEncrypt(self.client.aesPass, data.encode()))

    def receiver(self):
        AES_whether_send = 0
        while True:
            try:
                message = self.sock.recv(81920).decode()
                print('\n SERVER: ' + message)
                message = message.split('&', 1)
                if message[0].strip().lower() == 'password':
                    message = message[1].split('$', 1)
                    if message[0].strip().lower() == 'message':
                        # key_pub type=str
                        key_pub = message[1].strip()
                        pub_key = RSA.importKey(key_pub)
                        cipher = PKCS1_cipher.new(pub_key)
                        # rsa_text type=bytes
                        rsa_text = base64.b64encode(cipher.encrypt(bytes(self.client.aesPass.encode("utf8"))))
                        self.sender(rsa_text, True)
                        AES_whether_send = 1
                        self.client.SocketConnector()
                        break
            except:
                break

        while AES_whether_send:
            ecdata = self.sock.recv(81920)
            aesPass = self.client.aesPass
            # aesPass type=str
            try:
                message = aesDecrypt(aesPass, ecdata).decode()
            except:
                print(ecdata)
            print('\n SERVER: ' + str(message))
            self.analyzer(message)

    def analyzer(self, message):
        # Meeting ########################################
        message = message.split('&', 1)
        if message[0].strip().lower() == 'create meeting':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'eval':
                meetingParameter = eval(message[1])
                self.client.meetingNumber = meetingParameter['MeetingNum']
                self.client.meetingMember = meetingParameter['Member']
                self.client.state = MEETING
                self.client.admin = ON
                # print('The number of meeting you created is ' + str(meetingParameter['MeetingNum']))
            elif message[0].strip() == 'error':
                pass
                # print("You are failed to create meeting")
        elif message[0].strip().lower() == 'leave meeting':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'destroy':
                meetingParameter = eval(message[1])
                if not meetingParameter['MeetingNum'] == self.client.meetingNumber:
                    pass
                    # print('Leave Meeting, server give wrong feedback')
                self.client.meetingNumber = "number is null"
                self.client.state = MAIN
                self.client.videoHandler.close()
                self.client.video = OFF
                self.client.audioHandler.close()
                self.client.audio = OFF
                self.client.screenSharingHandler.close()
                self.client.screenSharing = OFF

                # print('You leave the meeting ' + str(meetingParameter['MeetingNum']))
            elif message[0].strip().lower() == 'error':
                pass
                # print("You are failed to leave meeting")
        elif message[0].strip().lower() == 'join meeting':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'eval':
                meetingParameter = eval(message[1])
                self.client.meetingNumber = meetingParameter['MeetingNum']
                self.client.meetingMember = meetingParameter['Member']
                self.client.state = MEETING
                # print('The number of meeting you joined is ' + str(meetingParameter['MeetingNum']))
            elif message[0].strip().lower() == 'error':
                pass
                # print(message[1])
        elif message[0].strip().lower() == 'close meeting':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'destroy':
                meetingParameter = eval(message[1])
                if self.client.meetingNumber == meetingParameter['MeetingNum']:
                    self.client.meetingNumber = "Number is null"
                    self.client.state = MAIN
                    self.client.videoHandler.close()
                    self.client.video = OFF
                    self.client.audioHandler.close()
                    self.client.audio = OFF
                    self.client.screenSharingHandler.close()
                    self.client.screenSharing = OFF

                    # print('You close the meeting ' + str(meetingParameter['MeetingNum']))
            elif message[0].strip().lower() == 'error':
                pass
                # print(message[1])
        elif message[0].strip().lower() == 'transfer host':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'eval':
                self.client.admin = OFF

            elif message[0].strip().lower() == 'error':
                pass
                # print(message[1])
        elif message[0].strip().lower() == 'forbid audio':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'eval':
                self.client.audioHandler.close()
                self.client.audio = OFF
            elif message[0].strip().lower() == 'error':
                pass
        elif message[0].strip().lower() == 'forbid video':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'eval':
                self.client.videoHandler.close()
                self.client.video = OFF
                # print(message[1])
            elif message[0].strip().lower() == 'error':
                pass
                # print(message[1])
        elif message[0].strip().lower() == 'forbid screen':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'eval':
                self.client.screenSharingHandler.close()
                self.client.screenSharing = OFF
                # print(message[1])
            elif message[0].strip().lower() == 'error':
                pass
                # print(message[1])
        # Video ###########################################
        elif message[0].strip().lower() == 'start video sharing':
            print('*******************')
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'message':
                print('*******************')
                if message[1].strip().lower() == 'video sharing permitted':
                    print('*******************')
                    self.client.videoHandler.run()
                    self.client.video = ON
                # print('server reply'+message[1])
            elif message[0].strip().lower() == 'error':
                pass
                # print(message[1])
        elif message[0].strip().lower() == 'end video sharing':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'message':
                if message[1].strip().lower() == 'video sharing closed':
                    self.client.videoHandler.close()
                    self.client.video = OFF
                    # print(message[1])
            elif message[0].strip().lower() == 'error':
                pass
                # print(message[1])

        # Audio ###########################################
        elif message[0].strip().lower() == 'start audio sharing':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'message':
                if message[1].strip().lower() == 'audio sharing permitted':
                    self.client.audioHandler.run()
                    self.client.audio = ON
            elif message[0].strip().lower() == 'error':
                pass
                # print(message[1])
        elif message[0].strip().lower() == 'end audio sharing':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'message':
                if message[1].strip().lower() == 'audio sharing closed':
                    self.client.audioHandler.close()
                    self.client.audio = OFF
                    # print(message[1])
            elif message[0].strip().lower() == 'error':
                pass

        # Screen Sharing ######################################
        elif message[0].strip().lower() == 'start screen sharing':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'message':
                if message[1].strip().lower() == 'screen sharing permitted':
                    self.client.screenSharingHandler.run()
                    self.client.screenSharing = ON
            elif message[0].strip().lower() == 'error':
                pass
        elif message[0].strip().lower() == 'end screen sharing':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'message':
                if message[1].strip().lower() == 'screen sharing closed':
                    self.client.screenSharingHandler.close()
                    self.client.screenSharing = OFF
            elif message[0].strip().lower() == 'error':
                pass

        # Screen Control ######################################
        elif message[0].strip().lower() == 'start control':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'message':
                if message[1].strip().lower() == 'waiting for permission':
                    pass
            elif message[0].strip().lower() == 'error':
                pass
            elif message[0].strip().lower() == 'eval':
                self.client.screenControllerIp = str(message[1])
        elif message[0].strip().lower() == 'permit control':
            message = message[1].split('$', 1)
            if message[0].strip().lower() == 'eval':
                if self.client.screenControllerIp == None:
                    # I am controller
                    self.client.screenControlHandler.runController()
                    self.client.screenController = ON
                else:
                    # I am controlled
                    self.client.screenControlHandler.runControlled()
                    self.client.screenControlled = ON
        elif message[0].strip().lower() == 'reject control':
            if message[0].strip().lower() == 'message':
                self.client.screenControllerIp = None
        elif message[0].strip().lower() == 'end control':
            if message[0].strip().lower() == 'message':
                if message[1].strip().lower() == 'controller disconnect':
                    # I am controlled
                    self.client.screenControlHandler.closeControlled()
                    self.client.screenControlled = OFF
                elif message[1].strip().lower() == 'controlled disconnect':
                    # I am controller
                    self.client.screenControlHandler.closeController()
                    self.client.screenController = OFF

    def create(self):
        request = "Create Meeting"
        self.sender(request)

    def leave(self):
        request = "Leave Meeting"
        self.sender(request)

    def join(self, sid):
        request = "Join Meeting:" + str(sid)
        self.sender(request)

    def close(self):
        request = "Close Meeting"
        self.sender(request)

    def transferHost(self, ipOfNewHost):
        request = "Transfer Host:" + str(ipOfNewHost)
        self.sender(request)

    def forbidVideo(self):
        request = "Forbid Video"
        self.sender(request)

    def forbidAudio(self):
        request = "Forbid Audio"
        self.sender(request)

    def forbidScreen(self):
        request = "Forbid Screen"
        self.sender(request)

    def permitVideo(self):
        request = "Permit Video"
        self.sender(request)

    def permitAudio(self):
        request = "Permit Audio"
        self.sender(request)

    def permitScreen(self):
        request = "Permit Screen"
        self.sender(request)

    def enableVideo(self):
        request = "Start Video Sharing"
        self.sender(request)

    def disableVideo(self):
        request = "End Video Sharing"
        self.sender(request)

    def enableAudio(self):
        request = "Start Audio Sharing"
        self.sender(request)

    def disableAudio(self):
        request = "End Audio Sharing"
        self.sender(request)

    def enableScreenSharing(self):
        request = "Start Screen Sharing"
        self.sender(request)

    def disableScreenSharing(self):
        request = "End Screen Sharing"
        self.sender(request)

    def enableScreenControl(self, ipControlled):
        request = "Start Control :" + str(ipControlled)
        self.sender(request)

    def disableScreenControl(self):
        request = "End Control"
        self.sender(request)

    def agreeScreenControl(self, ipController):
        request = "Permit Control :" + str(ipController)
        self.sender(request)

    def disagreeScreenControl(self, ipController):
        request = "Reject Control :" + str(ipController)
        self.sender(request)


class videoSocket:
    def __init__(self, client, address, version):
        # The registered client
        self.client = client
        self.serverAddress = address
        self.videoReceiverEnable = 1
        self.videoSenderEnable = 0
        self.interval = RESOLUTION_LEVEL
        self.fx = 1 / (self.interval + 1)
        if self.fx < 0.3:
            self.fx = 0.3

        if version == 4:
            self.sock = socket(AF_INET, SOCK_STREAM)
        else:
            self.sock = socket(AF_INET6, SOCK_STREAM)

        self.connectToServer()
        # Create a receive_server_data threading
        self.receiverThread = threading.Thread(target=self.videoReceiver)
        self.receiverThread.start()
        self.senderThread = threading.Thread(target=self.videoSender)
        self.senderThread.start()

    def run(self):
        self.cap = cv2.VideoCapture(0)
        # self.cap = cv2.VideoCapture(0)
        self.videoSenderEnable = 1
        # self.videoReceiverEnable = 1
        print("\n CLIENT: client video run")

    def close(self):
        # self.receiveStop = 0
        # print('1')
        try:
            self.cap.release()
        except:
            pass
        self.videoSenderEnable = 0
        # self.cap.release()
        # print('2')
        # # self.sock.close()
        # print('3')
        # self.cap.release()

        # cv2.destroyAllWindows()

    def connectToServer(self):
        timeTry = 0
        while timeTry < 9:
            try:
                self.sock.connect(self.serverAddress)
                print("\n CLIENT: Video, Connect to server successfully.")
                break
            except:
                timeTry += 1
                time.sleep(1)
                print('\n CLIENT: Video, NO.' + str(timeTry) + ' try, ' + 'could not connect to the server ' + str(
                    self.serverAddress))
        if timeTry >= 9: sys.exit()

    def videoReceiver(self):
        data = "".encode("utf-8")
        payload_size = struct.calcsize("L")
        sign = 1
        defaultImage = cv2.imread('.\\default_img.jpg')
        print('\n CLIENT: video receiver start')
        while True:
            while len(data) < payload_size:
                data += self.sock.recv(81920)
            packed_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("L", packed_size)[0]
            # print(2)
            while len(data) < msg_size:
                data += self.sock.recv(81920)
            dataEncry = data[:msg_size]
            data = data[msg_size:]
            try:
                if self.videoReceiverEnable:
                    ip_type_frame = pickle.loads(zlib.decompress(aesDecrypt(self.client.aesPass, dataEncry)))
                    # cv2.imwrite('.\\'+sourceIP+str(sign)+'.jpg',frame)
                    # sign+=1
                    # sList[0]: send type, 1:img, 0:diff
                    sourceIP = ip_type_frame[0]
                    if ip_type_frame[1]:
                        frame = ip_type_frame[2]
                        preFrame = frame
                    else:
                        frame = preFrame ^ ip_type_frame[2]

                    cv2.imshow(sourceIP, frame)
                    cv2.waitKey(1)
            except:
                pass

    def videoSender(self):
        print('\n CLIENT: videosenderworks')
        preFrame = None
        # send type, 1:img, 0:diff
        # if diffTurn == 0 we should send full image, if not, send min[diff,full image]
        diffTurn = 0
        while True:
            try:
                if self.videoSenderEnable:
                    ret, frame = self.cap.read()
                    # sframe = frame
                    sframe = cv2.resize(frame, (0, 0), fx=self.fx, fy=self.fx)
                    # send type, 1:img, 0:diff
                    type_frame = [1, sframe]
                    data = pickle.dumps(type_frame)
                    zdata = zlib.compress(data, zlib.Z_BEST_COMPRESSION)
                    if diffTurn % 10 != 0:
                        diffTurn += 1
                        sdiff = sframe ^ preFrame
                        # send type, 1:img, 0:diff
                        sList_diff = [0, sdiff]
                        data_diff = pickle.dumps(sList_diff)
                        zdata_diff = zlib.compress(data_diff, zlib.Z_BEST_COMPRESSION)
                        if len(zdata_diff) < len(zdata):
                            zdata = zdata_diff

                    dataEncry = aesEncrypt(self.client.aesPass, zdata)
                    self.sock.sendall(struct.pack("L", len(dataEncry)) + dataEncry)
                    # sampling rate adjustment
                    for i in range(self.interval):
                        ret, frame = self.cap.read()
                    preFrame = cv2.resize(frame, (0, 0), fx=self.fx, fy=self.fx)
            except:
                pass
        print('\n CLIENT: videosenderfailed')


class audioSocket:
    def __init__(self, client, address, version):
        self.client = client
        self.audioReceiverEnable = 1
        self.audioSenderEnable = 0
        self.serverAddress = address
        if version == 4:
            self.sock = socket(AF_INET, SOCK_STREAM)
        else:
            self.sock = socket(AF_INET6, SOCK_STREAM)
        self.connectToServer()

        # initialise microphone recording
        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True,
                                          frames_per_buffer=CHUNK)
        self.recording_stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                                            frames_per_buffer=CHUNK)

        # start threads
        self.receiverThread = threading.Thread(target=self.audioReceiver)
        self.receiverThread.start()
        self.senderThread = threading.Thread(target=self.audioSender)
        self.senderThread.start()

    def run(self):
        # self.audioReceiverEnable = 1
        self.audioSenderEnable = 1

    def close(self):
        # self.receiveStop = 0
        self.audioSenderEnable = 0
        # self.sock.close()

    def connectToServer(self):
        timeTry = 0
        while timeTry < 9:
            try:
                self.sock.connect(self.serverAddress)
                print("\n CLIENT: Audio, Connect to server successfully.")
                break
            except:
                timeTry += 1
                time.sleep(1)
                print('\n CLIENT: Audio, NO.' + str(timeTry) + ' try, ' + 'could not connect to the server ' + str(
                    self.serverAddress))
        if timeTry >= 9: sys.exit()

    def audioReceiver(self):
        data = "".encode("utf-8")
        payload_size = struct.calcsize("L")
        while True:
            while len(data) < payload_size:
                data += self.sock.recv(81920)
            packed_size = data[:payload_size]
            msg_size = struct.unpack("L", packed_size)[0]
            data = data[payload_size:]
            while len(data) < msg_size:
                data += self.sock.recv(81920)
            dataEncry = data[:msg_size]
            data = data[msg_size:]
            if self.audioReceiverEnable:
                try:
                    frames = pickle.loads(zlib.decompress(aesDecrypt(self.client.aesPass, dataEncry)))
                    for frame in frames:
                        self.playing_stream.write(frame, CHUNK)
                except:
                    pass
            else:
                pass

    def audioSender(self):
        while True:
            if self.audioSenderEnable:
                try:
                    frames = []
                    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                        data = self.recording_stream.read(CHUNK)
                        frames.append(data)
                    audio_raw = pickle.dumps(frames)
                    dataEncry = aesEncrypt(self.client.aesPass, zlib.compress(audio_raw, zlib.Z_BEST_COMPRESSION))
                    self.sock.sendall(struct.pack("L", len(dataEncry)) + dataEncry)
                except:
                    pass
            else:
                pass
        print('\n CLIENT: audiosenderfailed')


class screenSharingSocket:
    def __init__(self, client, address, version):
        self.client = client
        self.serverAddress = address
        if version == 4:
            self.sock = socket(AF_INET, SOCK_STREAM)
        else:
            self.sock = socket(AF_INET6, SOCK_STREAM)
        self.connectToServer()

        self.screenSharingReceiverEnable = 1
        self.screenSharingSenderEnable = 0
        self.quality = 25
        self.encodeParam = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
        self.samplingRate = SAMPLING_RATE
        self.receiverThread = threading.Thread(target=self.screenSharingReceiver)
        self.receiverThread.start()
        self.senderThread = threading.Thread(target=self.screenSharingSender)
        self.senderThread.start()

    def close(self):
        # self.screenSharingReceiverEnable = 1
        self.screenSharingSenderEnable = 0

    def run(self):
        # self.screenSharingReceiverEnable = 1
        self.screenSharingSenderEnable = 1

        #

    def connectToServer(self):
        timeTry = 0
        while timeTry < 9:
            try:
                self.sock.connect(self.serverAddress)
                print("\n CLIENT: ScreenSharing, Connect to server successfully.")
                break
            except:
                timeTry += 1
                time.sleep(1)
                print('\n CLIENT: ScreenSharing, NO.' + str(
                    timeTry) + ' try, ' + 'could not connect to the server ' + str(
                    self.serverAddress))
        if timeTry >= 9: sys.exit()

    def screenSharingSender(self):
        preImm = None
        diffTurn = 0
        while True:
            if self.screenSharingSenderEnable:
                # print("\n CLIENT: screenSharingSender starts...")
                im = ImageGrab.grab()
                imm = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)  # 转为opencv的BGR格式
                imm = cv2.resize(imm, (960, 540))
                # send type, 1:img, 0:diff
                sList_imm = [1, imm]
                data_imm = pickle.dumps(sList_imm)
                zdata_imm = zlib.compress(data_imm, zlib.Z_BEST_COMPRESSION)
                if diffTurn % 10 != 0:
                    diffTurn += 1
                    diffImm = imm ^ preImm
                    # send type, 1:img, 0:diff
                    sList_diff = [0, diffImm]
                    data_diff = pickle.dumps(sList_diff)
                    zdata_diff = zlib.compress(data_diff, zlib.Z_BEST_COMPRESSION)
                    if len(zdata_diff) < len(zdata_imm):
                        zdata_imm = zdata_diff

                dataEncry = aesEncrypt(self.client.aesPass, zdata_imm)
                self.sock.sendall(struct.pack("L", len(dataEncry)) + dataEncry)

                for i in range(self.samplingRate):
                    preImm = ImageGrab.grab()

    def screenSharingReceiver(self):
        # print("\n CLIENT: screenSharingReceiver starts...")
        data = "".encode("utf-8")
        payload_size = struct.calcsize("L")
        while True:
            # 接受客户端消息,设置一次最多接受10240字节的数据
            while len(data) < payload_size:
                data += self.sock.recv(81920)
            packed_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("L", packed_size)[0]
            while len(data) < msg_size:
                data += self.sock.recv(81920)
            dataEncry = data[:msg_size]
            data = data[msg_size:]
            try:
                sList = pickle.loads(zlib.decompress(aesDecrypt(self.client.aesPass, dataEncry)))
                if sList[0]:
                    imm = sList[1]
                    preimm = imm
                else:
                    imm = sList[1] + preimm
                cv2.imshow('ScreenSharing', imm)
                cv2.waitKey(100)
            except:
                pass


class screenControlSocket:
    def __init__(self, client, address, version):
        # self.windows = tkinter.Tk()
        # self.screenImageSenderThread = None
        # self.screenImageReceiverThread = None
        # self.screenControlReceiverThread = None
        # self.screenControlSenderThread = None
        self.client = client
        self.serverAddress = address
        if version == 4:
            self.sock = socket(AF_INET, SOCK_STREAM)
        else:
            self.sock = socket(AF_INET6, SOCK_STREAM)
        self.connectToServer()
        #
        # self.operationReceiverEnable = 0
        # self.operationSenderEnable = 0
        # self.screenImageSenderEnable = 0
        # self.screenImageReceiverEnable = 0
        # platform type checking to obtain correct keyboard & mouse input
        # PLATFORM_TYPE = b'win'
        # if sys.platform == "win32":
        #     PLATFORM_TYPE = b'win'
        # elif sys.platform == "darwin":
        #     PLATFORM_TYPE = b'osx'
        # elif sys.platform.system() == "Linux":
        #     PLATFORM_TYPE = b'x11'
        # self.platformType = PLATFORM_TYPE
        #
        # self.quality = 25
        # self.encodeParam = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
        # self.samplingRate = SAMPLING_RATE
        # self.receiverThread = threading.Thread(target=self.operationSender)
        # self.receiverThread.start()
        # self.senderThread = threading.Thread(target=self.operationReceiver)
        # self.senderThread.start()
        self.classOfControlled = controlled(self.sock)
        self.classOfController = controller(self.sock)

    def runController(self):
        self.classOfController.start()
        # self.operationSenderEnable = 1
        # self.screenImageReceiverEnable = 1
        # # self.screenControlSenderThread = threading.Thread(target=self.operationSender)
        # # self.screenControlSenderThread.start()
        # self.screenImageReceiverThread = threading.Thread(target=self.screenImageReceiver, args=self.windows)
        # self.screenImageReceiverThread.start()

    def runControlled(self):
        self.classOfControlled.start()
        # self.operationReceiverEnable = 1
        # self.screenImageSenderEnable = 1
        # self.screenControlReceiverThread = threading.Thread(target=self.operationReceiver)
        # self.screenControlReceiverThread.start()
        # self.screenImageSenderThread = threading.Thread(target=self.screenImageSender)
        # self.screenImageSenderThread.start()

    def closeControlled(self):
        self.classOfControlled.close()
        # self.operationReceiverEnable = 0
        # self.screenImageSenderEnable = 0

    def closeController(self):
        self.classOfController.close()
        # self.operationSenderEnable = 0
        # self.screenImageReceiverEnable = 0

    def connectToServer(self):
        timeTry = 0
        while timeTry < 9:
            try:
                self.sock.connect(self.serverAddress)
                print("\n CLIENT: ScreenControl, Connect to server successfully.")
                break
            except:
                timeTry += 1
                time.sleep(1)
                print('\n CLIENT: ScreenSharing, NO.' + str(
                    timeTry) + ' try, ' + 'could not connect to the server ' + str(
                    self.serverAddress))
        if timeTry >= 9: sys.exit()

    # def screenImageSender(self):
    #     preImm = None
    #     diffTurn = 0
    #     while self.screenImageSenderEnable:
    #         # print("\n CLIENT: screenSharingSender starts...")
    #         im = ImageGrab.grab()
    #         imm = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)  # 转为opencv的BGR格式
    #         imm = cv2.resize(imm, (960, 540))
    #         # send type, 1:img, 0:diff
    #         sList_imm = [1, imm]
    #         data_imm = pickle.dumps(sList_imm)
    #         zdata_imm = zlib.compress(data_imm, zlib.Z_BEST_COMPRESSION)
    #         if diffTurn % 10 != 0:
    #             diffTurn += 1
    #             diffImm = imm ^ preImm
    #             # send type, 1:img, 0:diff
    #             sList_diff = [0, diffImm]
    #             data_diff = pickle.dumps(sList_diff)
    #             zdata_diff = zlib.compress(data_diff, zlib.Z_BEST_COMPRESSION)
    #             if len(zdata_diff) < len(zdata_imm):
    #                 zdata_imm = zdata_diff
    #
    #         dataEncry = aesEncrypt(self.client.aesPass, zdata_imm)
    #         self.sock.sendall(struct.pack("L", len(dataEncry)) + dataEncry)
    #         print("screenImageSender")
    #         for i in range(self.samplingRate):
    #             preImm = ImageGrab.grab()
    #
    # def operationReceiver(self):
    #     conn = self.sock
    #     keycodeMapping = {}
    #
    #     def Op(key, op, ox, oy):
    #         # print(key, op, ox, oy)
    #         if key == 4:
    #             # 鼠标移动
    #             mouse.move(ox, oy)
    #         elif key == 1:
    #             if op == 100:
    #                 # 左键按下
    #                 ag.mouseDown(button=ag.LEFT)
    #             elif op == 117:
    #                 # 左键弹起
    #                 ag.mouseUp(button=ag.LEFT)
    #         elif key == 2:
    #             # 滚轮事件
    #             if op == 0:
    #                 # 向上
    #                 ag.scroll(-SCROLL_SENSITIVITY)
    #             else:
    #                 # 向下
    #                 ag.scroll(SCROLL_SENSITIVITY)
    #         elif key == 3:
    #             # 鼠标右键
    #             if op == 100:
    #                 # 右键按下
    #                 ag.mouseDown(button=ag.RIGHT)
    #             elif op == 117:
    #                 # 右键弹起
    #                 ag.mouseUp(button=ag.RIGHT)
    #         else:
    #             k = keycodeMapping.get(key)
    #             if k is not None:
    #                 if op == 100:
    #                     ag.keyDown(k)
    #                 elif op == 117:
    #                     ag.keyUp(k)
    #
    #     try:
    #         plat = b'win'
    #         # while True:
    #         #     plat += conn.recv(3 - len(plat))
    #         #     if len(plat) == 3:
    #         #         break
    #         # print("Plat:", plat.decode())
    #         keycodeMapping = getKeycodeMapping(plat)
    #         # base_len = 6
    #         data = "".encode("utf-8")
    #         payload_size = struct.calcsize("L")
    #         while self.operationReceiverEnable:
    #             print("operationReceiverEnable")
    #             while len(data) < payload_size:
    #                 data += conn.recv(81920)
    #             packed_size = data[:payload_size]
    #             msg_size = struct.unpack("L", packed_size)[0]
    #             data = data[payload_size:]
    #             while len(data) < msg_size:
    #                 data += conn.recv(81920)
    #             dataEncry = data[:msg_size]
    #             data = data[msg_size:]
    #
    #             cmd = pickle.loads(aesDecrypt(self.client.aesPass, dataEncry))
    #             key = cmd[0]
    #             op = cmd[1]
    #             x = cmd[2]
    #             y = cmd[3]
    #             Op(key, op, x, y)
    #     except:
    #         return
    #
    # def screenImageReceiver(self, window):
    #     global WHETHER_SCALE, ORIGINAL_HEIGHT, ORIGINAL_WIDTH
    #     data = "".encode("utf-8")
    #     payload_size = struct.calcsize("L")
    #     WHETHER_SCALE = None
    #     window.title('Controlling')
    #     imsh = cv2.imread(".\\default_img.jpg")
    #     h, w, _ = imsh.shape
    #     ORIGINAL_HEIGHT, ORIGINAL_WIDTH = h, w
    #     imi = Image.fromarray(imsh)
    #     cv = tkinter.Canvas(window, width=w, height=h, bg="white")
    #     cv.focus_set()
    #     th = threading.Thread(target=self.operationSender, args=cv).start()
    #     th.daemon = True
    #     cv.pack()
    #     imgTK = ImageTk.PhotoImage(image=imi)
    #     cv.create_image(0, 0, anchor=tkinter.NW, image=imgTK)
    #     h = int(h * SCALE)
    #     w = int(w * SCALE)
    #     while self.screenImageReceiverEnable:
    #         print("screenImageReceiver")
    #         if WHETHER_SCALE:
    #             h = int(ORIGINAL_HEIGHT * SCALE)
    #             w = int(ORIGINAL_WIDTH * SCALE)
    #             cv.config(width=w, height=h)
    #             WHETHER_SCALE = False
    #         # 接受客户端消息,设置一次最多接受10240字节的数据
    #         while len(data) < payload_size:
    #             data += self.sock.recv(81920)
    #         packed_size = data[:payload_size]
    #         data = data[payload_size:]
    #         msg_size = struct.unpack("L", packed_size)[0]
    #         while len(data) < msg_size:
    #             data += self.sock.recv(81920)
    #         dataEncry = data[:msg_size]
    #         data = data[msg_size:]
    #         try:
    #             sList = pickle.loads(zlib.decompress(aesDecrypt(self.client.aesPass, dataEncry)))
    #             if sList[0]:
    #                 imm = sList[1]
    #                 preimm = imm
    #             else:
    #                 imm = sList[1] + preimm
    #             # cv2.imshow('ScreenSharing', imm )
    #             # cv2.waitKey(100)
    #             imsh = cv2.resize(imm, (w, h))
    #             imi = Image.fromarray(imsh)
    #             imgTK.paste(imi)
    #         except:
    #             window = None
    #             pass
    #
    # def operationSender(self, canvas):
    #     global root, last_send
    #
    #     def SetScale(x):
    #         global SCALE, WHETHER_SCALE
    #         SCALE = float(x) / 100
    #         WHETHER_SCALE = True
    #
    #     PLATFORM_TYPE = self.platformType
    #     val = tkinter.StringVar()
    #
    #     host_lab = tkinter.Label(root, text="Host:")
    #     host_en = tkinter.Entry(root, show=None, font=('Arial', 14), textvariable=val)
    #     sca_lab = tkinter.Label(root, text="Scale:")
    #     sca = tkinter.Scale(root, from_=10, to=100, orient=tkinter.HORIZONTAL, length=100,
    #                         showvalue=100, resolution=0.1, tickinterval=50, command=SetScale)
    #
    #     host_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
    #     host_en.grid(row=0, column=1, padx=0, pady=0, ipadx=40, ipady=0)
    #     sca_lab.grid(row=1, column=0, padx=10, pady=10, ipadx=0, ipady=0)
    #     sca.grid(row=1, column=1, padx=0, pady=0, ipadx=100, ipady=0)
    #
    #     sca.set(100)
    #
    #     last_send = time.time()
    #
    #     def EventDo(cmd):
    #         dataEncry = aesEncrypt(self.client.aesPass, pickle.dumps(cmd))
    #         self.sock.sendall(struct.pack("L", len(dataEncry)) + dataEncry)
    #
    #     # 鼠标左键
    #
    #     def LeftDown(e):
    #         return EventDo([1, 100, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #     def LeftUp(e):
    #         return EventDo([1, 117, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #     canvas.bind(sequence="<1>", func=LeftDown)
    #     canvas.bind(sequence="<ButtonRelease-1>", func=LeftUp)
    #
    #     # 鼠标右键
    #     def RightDown(e):
    #         return EventDo([3, 100, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #     def RightUp(e):
    #         return EventDo([3, 117, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #     canvas.bind(sequence="<3>", func=RightDown)
    #     canvas.bind(sequence="<ButtonRelease-3>", func=RightUp)
    #
    #     # 鼠标滚轮
    #     if PLATFORM_TYPE == b'win' or PLATFORM_TYPE == 'osx':
    #         # windows/mac
    #         def Wheel(e):
    #             if e.delta < 0:
    #                 return EventDo([2, 0, int(e.x / SCALE), int(e.y / SCALE)])
    #             else:
    #                 return EventDo([2, 1, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #         canvas.bind(sequence="<MouseWheel>", func=Wheel)
    #     elif PLATFORM_TYPE == b'x11':
    #         def WheelDown(e):
    #             return EventDo([2, 0, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #         def WheelUp(e):
    #             return EventDo([2, 1, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #         canvas.bind(sequence="<Button-4>", func=WheelUp)
    #         canvas.bind(sequence="<Button-5>", func=WheelDown)
    #
    #     # 鼠标滑动
    #     # 100ms发送一次
    #     def Move(e):
    #         global last_send
    #         cu = time.time()
    #         if cu - last_send > IDLE:
    #             last_send = cu
    #             sx, sy = int(e.x / SCALE), int(e.y / SCALE)
    #             return EventDo([4, 0, sx, sy])
    #
    #     canvas.bind(sequence="<Motion>", func=Move)
    #
    #     # 键盘
    #     def KeyDown(e):
    #         return EventDo([e.keycode, 100, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #     def KeyUp(e):
    #         return EventDo([e.keycode, 117, int(e.x / SCALE), int(e.y / SCALE)])
    #
    #     canvas.bind(sequence="<KeyPress>", func=KeyDown)
    #     canvas.bind(sequence="<KeyRelease>", func=KeyUp)
