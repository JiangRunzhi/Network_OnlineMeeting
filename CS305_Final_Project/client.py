from client_sockets import *
from CONSTANTS import *
import random


class Client:
    def __init__(self):
        # get AES
        self.aesPass = ''.join(random.sample(
            ['z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g', 'f',
             'e', 'd', 'c', 'b', 'a'], 16))
        # Attribution of client
        self.meetingNumber = "\n CLIENT: Number is null"
        self.state = MAIN
        self.meetingMember = {}
        self.changed = True
        self.admin = OFF
        self.video = OFF
        self.audio = OFF
        self.screenSharing = OFF
        self.screenController = OFF
        self.screenControlled = OFF
        # Request, controller ip
        self.screenControllerIp = None
        # initial
        self.videoHandler = None
        self.audioHandler = None
        self.screenSharingHandler = None
        self.screenControlHandler = None
        # Socket for meeting control message
        self.meetingHandler = controlMessageSocket(self, (SERVERIP, MEETINGPORT), VERSION)
        self.videoHandler = videoSocket(self, (SERVERIP, VIDEOPORT), VERSION)


    # Connect after AES_sent
    def SocketConnector(self):
        # Socket for video sharing
        self.videoHandler = videoSocket(self, (SERVERIP, VIDEOPORT), VERSION)

        # Socket for audio sharing
        self.audioHandler = audioSocket(self, (SERVERIP, AUDIOPORT), VERSION)

        # Socket for screen sharing
        self.screenSharingHandler = screenSharingSocket(self, (SERVERIP, SCREENSHARINGPORT), VERSION)

        # Socket for screen control
        self.screenControlHandler = screenControlSocket(self, (SERVERIP, SCREENCONTROLPORT), VERSION)

    # An action function to change the CIL menu based on different actions
    def action(self, actionNumber):
        self.changed = True
        if self.state == MAIN:

            # Create a meeting
            if actionNumber == '1':
                self.createMeeting()

            # Join a meeting
            elif actionNumber == '2':
                selection = input("\n CLIENT: Please input the meeting id:")
                while not str.isdigit(selection):
                    selection = input("\n CLIENT: Please input the meeting id:")
                selection = int(selection)
                self.joinMeeting(selection)

        elif self.state == MEETING:
            # "1. (Stop) Share screen"
            if actionNumber == '1':
                if self.screenSharing == OFF:
                    self.screenSharingEnable()
                else:
                    self.screenSharingDisable()

            # "2. (Stop) Control other's screen"
            elif actionNumber == '2':
                if self.screenController == OFF:
                    ipControlled = input("\n CLIENT: Please input the ip you want to control:")
                    self.screenControlEnable(ipControlled)
                else:
                    self.screenControlDisable()


            # "3. (Reject,0) or (Permit,1) control my screen"
            elif actionNumber == '3':
                if self.screenControllerIp == None:
                    print("No control request.")
                else:
                    while True:
                        selection = input("\n CLIENT: (Reject,0) or (Permit,1):")
                        if str(selection) == str(0):
                            self.screenControlDisagree(self.screenControllerIp)
                            break
                        elif str(selection) == str(1):
                            self.screenControlAgree(self.screenControllerIp)
                            break
            # "5. (Stop) Share video"
            elif actionNumber == '5':
                if self.video == OFF:
                    self.videoEnable()
                else:
                    self.videoDisable()

            # "6. (Stop) Share audio"
            elif actionNumber == '6':
                if self.audio == OFF:
                    self.audioEnable()
                else:
                    self.audioDisable()

            # "7. Leave a meeting"
            elif actionNumber == '7':
                if self.state == MEETING:
                    self.leaveMeeting()
                else:
                    print("\n CLIENT: You are not in a meeting")

            # "8. Show current meeting members"
            elif actionNumber == '8':
                print(self.meetingMember)
            # "9. Close a meeting"
            elif actionNumber == '9':
                if self.admin:
                    self.closeMeeting()
                else:
                    print("\n CLIENT: You are not an admin")

            elif actionNumber == '10':
                newHost = input('input new host ip')
                self.hostTransfer(newHost)

            elif actionNumber == '11':
                self.videoForbid()

            elif actionNumber == '12':
                self.audioForbid()

            elif actionNumber == '13':
                self.screenForbid()

            elif actionNumber == '14':
                self.videoPermit()

            elif actionNumber == '15':
                self.audioPermit()

            elif actionNumber == '16':
                self.screenPermit()

    # All the functions defined bellow are not a must
    def createMeeting(self):
        self.meetingHandler.create()

    def joinMeeting(self, sid):
        self.meetingHandler.join(sid)

    def leaveMeeting(self):
        self.meetingHandler.leave()

    # admin use only
    def closeMeeting(self):
        self.meetingHandler.close()

    def hostTransfer(self, ipOfNewHost):
        self.meetingHandler.transferHost(ipOfNewHost)

    def videoForbid(self):
        self.meetingHandler.forbidVideo()

    def audioForbid(self):
        self.meetingHandler.forbidAudio()

    def screenForbid(self):
        self.meetingHandler.forbidScreen()

    def videoPermit(self):
        self.meetingHandler.permitVideo()

    def audioPermit(self):
        self.meetingHandler.permitAudio()

    def screenPermit(self):
        self.meetingHandler.permitScreen()

    # admin use only
    def videoEnable(self):
        self.meetingHandler.enableVideo()

    def videoDisable(self):
        self.meetingHandler.disableVideo()

    def audioEnable(self):
        self.meetingHandler.enableAudio()

    def audioDisable(self):
        self.meetingHandler.disableAudio()

    def screenSharingEnable(self):
        self.meetingHandler.enableScreenSharing()

    def screenSharingDisable(self):
        self.meetingHandler.disableScreenSharing()

    def screenControlEnable(self, ipControlled):
        self.meetingHandler.enableScreenControl(ipControlled)

    def screenControlDisable(self):
        self.meetingHandler.disableScreenControl()

    def screenControlAgree(self, ipController):
        self.meetingHandler.agreeScreenControl(ipController)

    def screenControlDisagree(self, ipController):
        self.meetingHandler.disagreeScreenControl(ipController)






