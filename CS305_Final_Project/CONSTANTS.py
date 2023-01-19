import pyaudio
# The constants for Client
MAIN = 1
MEETING = 2
OFF = False
ON = True

# Server ip
SERVERIP = '127.0.0.1'
# TCP/IP version
VERSION = 4
# Receiving port of client and server
# for control message
MEETINGPORT = 2222
# for video message
VIDEOPORT = 2223
# for audio message
AUDIOPORT = 2224
# for screen-sharing message
SCREENSHARINGPORT = 2225
# for screen-control message
SCREENCONTROLPORT = 2226
# collect above ports together
PORTS = [MEETINGPORT, VIDEOPORT, AUDIOPORT, SCREENSHARINGPORT, SCREENCONTROLPORT]

# Video
RESOLUTION_LEVEL = 1

# Audio
CHUNK = 1024
FORMAT = pyaudio.paInt16  # 格式
CHANNELS = 1  # 输入/输出通道数
RATE = 20000  # 音频数据的采样频率
RECORD_SECONDS = 0.5  # 记录秒
# Screen Sharing
SAMPLING_RATE = 5

# Screen-controlling
# Controlled
# 画面周期
PERIOD_IMAGE = 0.05
# 鼠标滚轮灵敏度
SCROLL_SENSITIVITY = 5
# socket缓冲区大小 controlled
BUFFER_SIZE_CONTROLLED = 1024
# Controller
# 画面周期
IDLE = 0.05
# 放缩大小
SCALE = 1
# 原传输画面尺寸
ORIGINAL_WIDTH, ORIGINAL_HEIGHT = 0, 0
# 放缩标志
WHETHER_SCALE = False
# 屏幕显示画布
CANSHOW = None
# socket缓冲区大小 controller
BUFFER_SIZE_CONTROLLER = 10240
# 线程
THREAD = None
# 压缩比 1-100 数值越小，压缩比越高，图片质量损失越严重
IMAGE_QUALITY = 50



'''
client command send to MEETINGPORT:
1. create a meeting
    request: 'Create Meeting'
    response: (1) success: 'Eval$ {'MeetingNum': meeting_num, 'Host': addr_ip, 'Member': [addr_ip], 'Forbid_Video': False, 'Forbid_Audio': False}'
              (2) fail: 'Error$ You\'re already in a room'

2. leave meeting
    request: 'Leave Meeting' 
    response: (1) success: 'Destroy$ ' + str({'MeetingNum': meeting_num})
              (2) fail: 'Error$ You are not in any meeting'

3.'Join Meeting : $meeting_num$' : join meeting $meeting_num$
    return : (1) success : 'Message$ You join meeting '+ str(meeting_num) +' successfully'
            (2) 'Error$ You\'re already in a room'
            (3) 'Error$ Room ' + str(meeting_num) + ' not exit'

4."Close Meeting" : close meeting
    return : (1) success : 'Destroy$ {'MeetingNum':meeting_num}'
            (2) 'Error$ You are not in any meeting'
            (3) 'Error$ You are not the host'

5."Start Video Sharing" : start video sharing
    return : (1) success : 'Message$ video sharing permitted'  this means you can transfer video through VIDEOPORT
            (2) 'Error$ You are already permitted'
            (3) 'Start Video Sharing& Error$ This meeting forbid video'

6."End Video Sharing" : end video sharing
    return : (1) success : 'Message$ video sharing closed'  this means you can not transfer video through VIDEOPORT
            (2) 'Error$ You are not video permitted'

7."Start Audio Sharing" : start Audio sharing
    return : (1) success : 'Start Audio Sharing& Message$ audio sharing permitted'  this means you can transfer video through AUDIOPORT
            (2) 'Start Audio Sharing& Error$ You are already permitted'
            (3) 'Start Audio Sharing& Error$ This meeting forbid audio'

8."End Audio Sharing" : end video sharing
    return : (1) success : 'End Audio Sharing& Message$ audio sharing closed'  this means you can not transfer video through AUDIOPORT
            (2) 'End Audio Sharing& Error$ You are not audio permitted'

9."Start Screen Sharing" : start Screen sharing
    return : (1) success : 'Start Screen Sharing& Message$ screen sharing permitted'  this means you can transfer video through AUDIOPORT
            (2) 'Start Screen Sharing& Error$ Only one screen sharing'
            (3) 'Start Video Sharing& Error$ This meeting forbid screen'

10."End Screen Sharing" : end Screen sharing
    return : (1) success : 'End Screen Sharing& Message$ screen sharing closed'  this means you can not transfer video through AUDIOPORT

11."Start Control : $ip$" : ask permit to control target $ip$
    return : (1) success : 'Start Control& Message$ Waiting for permission' this means server is asking permission from target ip
             (2) 'Start Control& Error$ You are controlling others'
             (3) 'Start Control& Error$ dst_ip has already been controlled'

12."End Control" : disconnect control
    return : (1) success : 'End Control& Message$ control disconnect'
             (2) 'End Control& Error$ Your are not controlling or being controlled'

13."Permit Control : $ip$" : permit $ip$ to control your pc
    return : (1) success : 'Permit Control& Eval$ ' + str({control_ip:addr_ip}) # tell both of PCs {control_ip:addr_ip}
             (2) 'Permit Control& Error$ Your are being controlled'
             (3) 'Permit Control& Error$ Your are controlling others'
             (4) 'Permit Control& Error$ dst_ip is controlling others or not willing to control'

14."Transfer Host : $ip$" : means transfer host to target $ip$
    return : (1) success : 'Transfer Host& Eval$ ' + str(room)          # room['Host'] has been changed to $ip$
             (2) 'Transfer Host& Error$ Your are not in any meeting'
             (3) 'Transfer Host& Error$ Your are not host'
             (4) 'Transfer Host& Error$ New host not exist'

15."Forbid Video" : host set video forbidden
    return : (1) success : 'Forbid Video& Eval$ ' + str({'MeetingNum': meeting_num, 'Host': addr_ip, 'Member': [addr_ip],......})  
             (2) 'Forbid Video& Error$ Your are not host'

16."Forbid Audio" : host set audio forbidden
    return : (1) success : 'Forbid Audio& Eval$ '+ str({'MeetingNum': meeting_num, 'Host': addr_ip, 'Member': [addr_ip],......})  
             (2) 'Forbid Audio& Error$ Your are not host'

17."Forbid Screen" : host set screen forbidden
    return : (1) success : 'Forbid Screen& Eval$ '+ str({'MeetingNum': meeting_num, 'Host': addr_ip, 'Member': [addr_ip],......})  
             (2) 'Forbid Screen& Error$ Your are not host'
'''