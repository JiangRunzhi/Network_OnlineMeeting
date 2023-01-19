from CONSTANTS import *
from encryption import *
import pickle
import struct
import zlib
from random import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import random

Connection_MEETINGPORT = {}  # store all the connection from MEETINGPORT format should be {ip: conn}
Connection_VIDEOPORT = {}
Connection_AUDIOPORT = {}
Connection_SCREENSHARINGPORT = {}
Connection_SCREENCONTROLPORT = {}
Connect_set = [Connection_MEETINGPORT,
               Connection_VIDEOPORT,
               Connection_AUDIOPORT,
               Connection_SCREENSHARINGPORT,
               Connection_SCREENCONTROLPORT]

Meeting_Record = {}  # format should be {Meeting_num : dict(Meeting)}
Video_Permitted = []  # format should be [ip]
Audio_Permitted = []  # format should be [ip]
Control_Pair = {}  # format should be {ip_A: ip_B}
ScreenSharing_Permitted = {}  # screen sharing ip, format should be {Meeting_num : $ip$}
Client_AES = {}


def clear_ip_info(addr_ip, Permission=None):
    if Permission is None:
        Permission = ['ScreenSharing_ip', 'Meeting_Record', 'Video_Permitted', 'Audio_Permitted', 'Control_Pair',
                      'Client_AES']
    if 'Client_AES' in Permission:
        try:
            Client_AES.pop(str(addr_ip))
            print(str(addr_ip) + ' Client_AES pop successfully')
        except:
            pass
    global ScreenSharing_Permitted
    if 'ScreenSharing_ip' in Permission:
        for meeting_num in list(ScreenSharing_Permitted.keys()):
            if addr_ip == ScreenSharing_Permitted[meeting_num]:
                del ScreenSharing_Permitted[meeting_num]
    if 'Meeting_Record' in Permission:
        for meeting_num in list(Meeting_Record.keys()):
            if (addr_ip in Meeting_Record[meeting_num]['Member']):
                Meeting_Record[meeting_num]['Member'].remove(addr_ip)
                # try:
                #     message = 'Leave Meeting& Destroy$ ' + str({'MeetingNum': meeting_num})
                #     send_message(addr_ip, MEETINGPORT, message)
                # except:
                #     print('already drop connection')
                # print('---------------')
                # print(Meeting_Record[meeting_num])
                if len(Meeting_Record[meeting_num]['Member']) == 0:  # No one in this room
                    del Meeting_Record[meeting_num]
                else:  # notice everyone in the room the new member list
                    if addr_ip == Meeting_Record[meeting_num]['Host']:
                        Meeting_Record[meeting_num]['Host'] = Meeting_Record[meeting_num]['Member'][
                            0]  # transfer host to the first guy
                    message = 'Leave Meeting& Eval$ ' + str(Meeting_Record[meeting_num])
                    broadcast(meeting_num, MEETINGPORT, message)
    if 'Video_Permitted' in Permission:
        if addr_ip in Video_Permitted:  # kick addr_ip out from Video_Permitted
            Video_Permitted.remove(addr_ip)
    if 'Audio_Permitted' in Permission:  # kick addr_ip out from Audio_Permitted
        if addr_ip in Audio_Permitted:
            Audio_Permitted.remove(addr_ip)
    if 'Control_Pair' in Permission:
        for control_ip in list(Control_Pair.keys()):
            if (addr_ip == control_ip):  # addr_ip is controller
                message = 'End Control& Message$ control disconnect'
                send_message(Control_Pair[control_ip], MEETINGPORT, message)
                del Control_Pair[control_ip]
            if (addr_ip == Control_Pair[control_ip]):  # addr_ip is controller
                message = 'End Control& Message$ control disconnect'
                send_message(control_ip, MEETINGPORT, message)
                del Control_Pair[control_ip]


def disconnect_ip(addr_ip):
    print('start disconnect connect_set')
    for Connections in Connect_set:  # search all connection records
        for ip in list(Connections.keys()):
            if (ip == addr_ip):  # this connection is already disconnected, close and delete it
                Connections[ip].close()
                del Connections[ip]
    print('start clear info')
    clear_ip_info(addr_ip)


def send_message(dst_ip, PORT, message, types='message'):
    # send message to target address (ip, port)
    # print(Connection_MEETINGPORT)
    conn = None
    if (PORT == MEETINGPORT):
        conn = Connection_MEETINGPORT[dst_ip]
    elif (PORT == VIDEOPORT):
        conn = Connection_VIDEOPORT[dst_ip]
    elif (PORT == AUDIOPORT):
        conn = Connection_AUDIOPORT[dst_ip]
    elif (PORT == SCREENSHARINGPORT):
        conn = Connection_SCREENSHARINGPORT[dst_ip]
    elif (PORT == SCREENCONTROLPORT):
        conn = Connection_SCREENCONTROLPORT[dst_ip]
    try:
        if types == 'message':
            # aesPass type = str
            conn.send(aesEncrypt(Client_AES[str(dst_ip)], message.encode()))
        elif types == 'public_key':
            # only for public_key sending
            conn.send(message)
        elif types == 'video':
            # only for video sending
            dataEncry = aesEncrypt(Client_AES[str(dst_ip)], message)
            conn.sendall(struct.pack("L", len(dataEncry)) + dataEncry)
        elif types == 'audio':
            # only for video sending
            dataEncry = aesEncrypt(Client_AES[str(dst_ip)], message)
            conn.send(struct.pack("L", len(dataEncry)) + dataEncry)
        elif types == 'screensharing':
            # only for video sending
            dataEncry = aesEncrypt(Client_AES[str(dst_ip)], message)
            conn.sendall(struct.pack("L", len(dataEncry)) + dataEncry)
        elif types == 'screencontrol':
            # only for video sending
            # dataEncry = aesEncrypt(Client_AES[str(dst_ip)], message)
            # conn.sendall(struct.pack("L", len(dataEncry)) + dataEncry)
            conn.sendall(message)
    except ConnectionResetError:
        print(dst_ip, ' disconnect!')
        print('start disconnect')
        disconnect_ip(dst_ip)


def broadcast(meeting_num, port, message, types='message', Except=None):
    for member_ip in Meeting_Record[meeting_num]['Member']:
        if member_ip != Except:
            send_message(member_ip, port, message, types)


def add_conn(ip, port, conn):
    print('ip: ', ip, ' port: ', port, ' connect')

    if (port == MEETINGPORT):
        if (ip not in Connection_MEETINGPORT.keys()):  # new connection
            Connection_MEETINGPORT[ip] = conn
        elif (getattr(Connection_MEETINGPORT[ip], '_closed')):  # connection closed
            print('ip: ', ip, ' port: ', port, ' re-connect')
            Connection_MEETINGPORT[ip] = conn
    if (port == VIDEOPORT):
        if (ip not in Connection_VIDEOPORT.keys()):  # new connection
            Connection_VIDEOPORT[ip] = conn
        elif (getattr(Connection_VIDEOPORT[ip], '_closed')):  # connection closed
            print('ip: ', ip, ' port: ', port, ' re-connect')
            Connection_VIDEOPORT[ip] = conn
    if (port == AUDIOPORT):
        if (ip not in Connection_AUDIOPORT.keys()):  # new connection
            Connection_AUDIOPORT[ip] = conn
        elif (getattr(Connection_AUDIOPORT[ip], '_closed')):  # connection closed
            print('ip: ', ip, ' port: ', port, ' re-connect')
            Connection_AUDIOPORT[ip] = conn
    if (port == SCREENSHARINGPORT):
        if (ip not in Connection_SCREENSHARINGPORT.keys()):  # new connection
            Connection_SCREENSHARINGPORT[ip] = conn
        elif (getattr(Connection_SCREENSHARINGPORT[ip], '_closed')):  # connection closed
            print('ip: ', ip, ' port: ', port, ' re-connect')
            Connection_SCREENSHARINGPORT[ip] = conn
    if (port == SCREENCONTROLPORT):
        if (ip not in Connection_SCREENCONTROLPORT.keys()):  # new connection
            Connection_SCREENCONTROLPORT[ip] = conn
        elif (getattr(Connection_SCREENCONTROLPORT[ip], '_closed')):  # connection closed
            print('ip: ', ip, ' port: ', port, ' re-connect')
            Connection_SCREENCONTROLPORT[ip] = conn


def get_Meeting_number(addr_ip):
    # get meeting number according to addr (ip, port)
    # return meeting number
    for meeting_num in Meeting_Record:
        if (addr_ip in Meeting_Record[meeting_num]['Member']):
            return meeting_num
    return -1


def Video(conn, addr_ip):
    # lock = threading.RLock()
    # default_message = 'DEFAULT'
    data = "".encode("utf-8")
    payload_size = struct.calcsize("L")
    while (True):
        while len(data) < payload_size:
            data += conn.recv(81920)
            # print('waiting')
        packed_size = data[:payload_size]
        msg_size = struct.unpack("L", packed_size)[0]
        data = data[payload_size:]
        while len(data) < msg_size:
            data += conn.recv(81920)
        dataEncry = data[:msg_size]
        data = data[msg_size:]

        if addr_ip not in Video_Permitted:  # not permitted
            # print(addr_ip,' deny')
            continue

        aesPass = Client_AES[str(addr_ip)]
        type_frame = pickle.loads(zlib.decompress(aesDecrypt(aesPass, dataEncry)))

        meeting_num = get_Meeting_number(addr_ip)
        ip_type_frame = [addr_ip] + type_frame
        video = zlib.compress(pickle.dumps(ip_type_frame), zlib.Z_BEST_COMPRESSION)
        broadcast(meeting_num, VIDEOPORT, video, 'video')


def Audio(conn, addr_ip):  # this audio does not close echo
    data = "".encode("utf-8")
    payload_size = struct.calcsize("L")
    while (True):
        while len(data) < payload_size:
            data += conn.recv(81920)
        packed_size = data[:payload_size]
        packed_size = data[:payload_size]
        msg_size = struct.unpack("L", packed_size)[0]
        data = data[payload_size:]
        while len(data) < msg_size:
            data += conn.recv(81920)
        dataEncry = data[:msg_size]
        data = data[msg_size:]

        if addr_ip not in Audio_Permitted:  # not permitted
            continue
        aesPass = Client_AES[str(addr_ip)]
        message = aesDecrypt(aesPass, dataEncry)
        print(addr_ip)
        meeting_num = get_Meeting_number(addr_ip)
        # message = str({addr_ip: message})
        # broadcast(meeting_num, AUDIOPORT, message, Except=addr_ip)  # broadcast to everyone
        # print(message)
        broadcast(meeting_num, AUDIOPORT, message, 'audio', addr_ip)


def Screen(conn, addr_ip):
    data = "".encode("utf-8")
    payload_size = struct.calcsize("L")
    while (True):
        while len(data) < payload_size:
            data += conn.recv(81920)
        packed_size = data[:payload_size]
        msg_size = struct.unpack("L", packed_size)[0]
        data = data[payload_size:]
        while len(data) < msg_size:
            data += conn.recv(81920)
        dataEncry = data[:msg_size]
        data = data[msg_size:]

        if addr_ip not in ScreenSharing_Permitted.values():  # this ip is not allowed to share
            continue

        aesPass = Client_AES[str(addr_ip)]
        message = aesDecrypt(aesPass, dataEncry)

        meeting_num = get_Meeting_number(addr_ip)
        broadcast(meeting_num, SCREENSHARINGPORT, message, 'screensharing', addr_ip)  # broadcast to everyone


def Meeting(conn, addr_ip):
    # handshake to get AES password ############################
    rsa = RSA.generate(2048)
    # key, type=str
    private_key = rsa.exportKey().decode('utf-8')
    public_key = rsa.publickey().exportKey().decode('utf-8')
    message = 'Password & message$ ' + public_key
    send_message(addr_ip, MEETINGPORT, message.encode(), 'public_key')
    AES_whether_got = 0
    while True:
        try:
            # type=bytes
            tmp_bytes_message = conn.recv(4096)
            pri_key = RSA.importKey(private_key)
            cipher = PKCS1_cipher.new(pri_key)
            # aesPass type=str
            aesPass = cipher.decrypt(base64.b64decode(tmp_bytes_message), 0).decode('utf-8')
            Client_AES[str(addr_ip)] = aesPass
            print('****************')
            print(addr_ip)
            print('AES_KEY: ' + str(aesPass))
            print('****************')
            AES_whether_got = 1
            break
        except ConnectionResetError:
            print(addr_ip, ' disconnect!')
            print('start meeting disconnect')
            disconnect_ip(addr_ip)
            break
    ############################################################
    while AES_whether_got:
        try:
            ecdata = conn.recv(4096)
            aesPass = Client_AES[str(addr_ip)]
            # ecdata type=str, aesPass type=str
            message = aesDecrypt(aesPass, ecdata).decode()
        except ConnectionResetError:
            print(addr_ip, ' disconnect!')
            print('start meeting disconnect')
            disconnect_ip(addr_ip)
            break
        print(addr_ip, ' command ', message)

        if 'Create Meeting' in message:
            # the format should be just 'Create Meeting' server will generate a meeting
            # number randomly. return a dict {
            # 'MeetingNum': meeting_num,
            # 'Host': addr_ip,
            # 'Member': [addr_ip],
            # 'Forbid_Video': True/False,
            # 'Forbid_Audio': True/False,
            # 'Forbid_Screen': True/False}

            # a client can only in one meeting
            print('before: ', Meeting_Record)
            meeting_num = get_Meeting_number(addr_ip)

            if meeting_num != -1:  # already in a room
                message = 'Create Meeting& Error$ Your in already in a room'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                meeting_num = random.randint(100, 999)
                while meeting_num in Meeting_Record.keys():  # this meeting number is occupied
                    meeting_num = random.randint(100, 999)
                message = {'MeetingNum': meeting_num,
                           'Host': addr_ip,
                           'Member': [addr_ip],
                           'Forbid_Video': False,
                           'Forbid_Audio': False,
                           'Forbid_Screen': False}
                Meeting_Record[meeting_num] = message
                message = 'Create Meeting& Eval$ ' + str(message)
                send_message(addr_ip, MEETINGPORT, message)
                # conn.send(message.encode())
                print('after: ', Meeting_Record)

        if 'Leave Meeting' in message:
            # not implement host transfer
            # format should just be 'Leave Meeting'
            print('before: ', Meeting_Record)
            meeting_num = get_Meeting_number(addr_ip)
            if meeting_num == -1:  # client is not in any meeting
                message = 'Leave Meeting& Error$ Your are not in any meeting'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                message = 'Leave Meeting& Destroy$ ' + str({'MeetingNum': meeting_num})
                send_message(addr_ip, MEETINGPORT, message)
                clear_ip_info(addr_ip, Permission=['ScreenSharing_ip',
                                                   'Meeting_Record',
                                                   'Video_Permitted',
                                                   'Audio_Permitted',
                                                   'Control_Pair'])
            print('after: ', Meeting_Record)

        if 'Join Meeting' in message:
            # format should be 'Join Meeting : $Meeting_number$'
            meeting_num = get_Meeting_number(addr_ip)
            print('before: ', Meeting_Record)
            if meeting_num != -1:  # already in a room
                message = 'Join Meeting& Error$ You\'re already in a room'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                meeting_num = int(message.split(':')[1].strip())
                if meeting_num not in Meeting_Record.keys():  # no target room
                    message = 'Join Meeting& Error$ Room ' + str(meeting_num) + ' not exit'
                    send_message(addr_ip, MEETINGPORT, message)
                else:
                    # success
                    Meeting_Record[meeting_num]['Member'].append(addr_ip)
                    # message = 'Join Meeting& Message$ Your join meeting '+ str(meeting_num) +' successfully'
                    # send_message((addr_ip,MEETINGPORT),message)
                    # notice everyone in the room the new member list
                    message = 'Join Meeting& Eval$ ' + str(Meeting_Record[meeting_num])
                    broadcast(meeting_num, MEETINGPORT, message)
            print('after: ', Meeting_Record)

        if "Close Meeting" in message:
            print('before: ', Meeting_Record)
            meeting_num = get_Meeting_number(addr_ip)
            if meeting_num == -1:  # client is not in any meeting
                message = 'Close Meeting& Error$ Your are not in any meeting'
                send_message(addr_ip, MEETINGPORT, message)
            elif (Meeting_Record[meeting_num]['Host'] == addr_ip):  # client is the host
                # notice everyone else in the room closed
                message = 'Close Meeting& Destroy$ ' + str({'MeetingNum': meeting_num})
                broadcast(meeting_num, MEETINGPORT, message)
                for ip in list(Meeting_Record[meeting_num]['Member']):  # clear all information of members
                    clear_ip_info(ip, Permission=['ScreenSharing_ip',
                                                  'Meeting_Record',
                                                  'Video_Permitted',
                                                  'Audio_Permitted',
                                                  'Control_Pair'])
                # del Meeting_Record[meeting_num]

            else:  # client is not the host
                message = 'Close Meeting& Error$ Your are not the host'
                send_message(addr_ip, MEETINGPORT, message)
            print('after: ', Meeting_Record)

        if "Start Video Sharing" in message:  # apply for video sharing
            print('before ', Video_Permitted)
            meeting_num = get_Meeting_number(addr_ip)
            print(meeting_num)
            print(type(meeting_num))
            if (addr_ip in Video_Permitted):  # already permitted
                message = 'Start Video Sharing& Message$ video sharing permitted'
                send_message(addr_ip, MEETINGPORT, message)
            elif Meeting_Record[meeting_num]['Forbid_Video']:  # video forbid
                message = 'Start Video Sharing& Error$ This meeting forbid video'
                send_message(addr_ip, MEETINGPORT, message)
            else:  # success
                Video_Permitted.append(addr_ip)
                message = 'Start Video Sharing& Message$ video sharing permitted'
                send_message(addr_ip, MEETINGPORT, message)
                print('after ', Video_Permitted)

        if "End Video Sharing" in message:  # shut down video sharing
            if addr_ip in Video_Permitted:  # success
                Video_Permitted.remove(addr_ip)
                message = 'End Video Sharing& Message$ video sharing closed'
                send_message(addr_ip, MEETINGPORT, message)
            else:  # already shut down
                message = 'End Video Sharing& Message$ video sharing closed'
                send_message(addr_ip, MEETINGPORT, message)

        if "Start Audio Sharing" in message:  # apply for video sharing
            print('before ', Audio_Permitted)
            meeting_num = get_Meeting_number(addr_ip)
            if (addr_ip in Audio_Permitted):  # already permitted
                print('fail')
                message = 'Start Audio Sharing& Message$ audio sharing permitted'
                send_message(addr_ip, MEETINGPORT, message)
            elif Meeting_Record[meeting_num]['Forbid_Audio']:  # audio forbid
                message = 'Start Audio Sharing& Error$ This meeting forbid audio'
                send_message(addr_ip, MEETINGPORT, message)
            else:  # success
                Audio_Permitted.append(addr_ip)
                message = 'Start Audio Sharing& Message$ audio sharing permitted'
                send_message(addr_ip, MEETINGPORT, message)
                print('after ', Audio_Permitted)

        if "End Audio Sharing" in message:  # shut down video sharing
            if (addr_ip in Audio_Permitted):  # success
                Audio_Permitted.remove(addr_ip)
                message = 'End Audio Sharing& Message$ audio sharing closed'
                send_message(addr_ip, MEETINGPORT, message)
            else:  # already shut down
                message = 'End Audio Sharing& Error$ You are not audio permitted'
                send_message(addr_ip, MEETINGPORT, message)

        if "Start Screen Sharing" in message:
            print('before ', ScreenSharing_Permitted)
            meeting_num = get_Meeting_number(addr_ip)
            if (addr_ip in ScreenSharing_Permitted.values()):  # already permitted
                message = 'Start Screen Sharing& Message$ screen sharing permitted'
                send_message(addr_ip, MEETINGPORT, message)
            elif Meeting_Record[meeting_num]['Forbid_Screen']:  # screen forbid
                message = 'Start Screen Sharing& Error$ This meeting forbid screen'
                send_message(addr_ip, MEETINGPORT, message)
            elif meeting_num in ScreenSharing_Permitted.keys():  # only 1 client share screen in a meeting
                message = 'Start Screen Sharing& Error$ Only one screen sharing'
                send_message(addr_ip, MEETINGPORT, message)
            else:  # success
                ScreenSharing_Permitted[meeting_num] = addr_ip
                message = 'Start Screen Sharing& Message$ screen sharing permitted'
                send_message(addr_ip, MEETINGPORT, message)
                print('after ', ScreenSharing_Permitted)

        if "End Screen Sharing" in message:  # shut down video sharing
            print('before ', ScreenSharing_Permitted)
            meeting_num = get_Meeting_number(addr_ip)
            if (addr_ip in ScreenSharing_Permitted.values()):  # success
                del ScreenSharing_Permitted[meeting_num]
                message = 'End Screen Sharing& Message$ screen sharing closed'
                send_message(addr_ip, MEETINGPORT, message)
            else:  # already shut down
                message = 'End Screen Sharing& Message$ screen sharing closed'
                send_message(addr_ip, MEETINGPORT, message)
            print('after ', ScreenSharing_Permitted)

        if "Start Control" in message:  # start control pc_A, format should be "Start Control : $ip$"
            dst_ip = message.split(':')[1].strip()
            meeting_num = get_Meeting_number(addr_ip)
            if (dst_ip in Meeting_Record[meeting_num]['Member']):
                if (addr_ip in Control_Pair.keys()):  # already controlling others
                    message = 'Start Control& Error$ You are controlling others'
                    send_message(addr_ip, MEETINGPORT, message)
                elif (dst_ip in Control_Pair.values()):  # dst has been controlled
                    message = 'Start Control& Error$ dst_ip has already been controlled'
                    send_message(addr_ip, MEETINGPORT, message)

                else:
                    Control_Pair[addr_ip] = '?'
                    message = 'Start Control& Message$ Waiting for permission'
                    send_message(addr_ip, MEETINGPORT, message)
                    # pc being controlled X should deliver "Permit Control: $pc_Y_ip$" back
                    message = 'Start Control& Eval$ ' + addr_ip
                    send_message(dst_ip, MEETINGPORT, message)
            else:
                message = 'Start Control& Error$ No such people'
                send_message(addr_ip, MEETINGPORT, message)

        if "Permit Control" in message:  # permit pc_A control. format should be "Permit Control : $ip$"
            control_ip = message.split(':')[1].strip()
            if (addr_ip in Control_Pair.values()):  # being controlled
                message = 'Permit Control& Error$ Your are being controlled'
                send_message(addr_ip, MEETINGPORT, message)
            elif (addr_ip in Control_Pair.keys()):  # Controlling others
                message = 'Permit Control& Error$ Your are controlling others'
                send_message(addr_ip, MEETINGPORT, message)
            elif (control_ip in Control_Pair.keys() and Control_Pair[
                control_ip] != '?'):  # control_ip Controlling others
                message = 'Permit Control& Error$ dst_ip is controlling others or not willing to control'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                Control_Pair[control_ip] = addr_ip
                message = 'Permit Control& Eval$ ' + str(
                    [control_ip, addr_ip])  # tell both of them {control_ip:addr_ip}
                send_message(control_ip, MEETINGPORT, message)
                send_message(addr_ip, MEETINGPORT, message)

        if "Reject Control" in message:  # Reject pc_A control. format should be "Reject Control : $ip$"
            control_ip = message.split(':')[1].strip()
            if (addr_ip in Control_Pair.values()):  # being controlled
                message = 'Reject Control& Error$ Your are being controlled'
                send_message(addr_ip, MEETINGPORT, message)
            elif (addr_ip in Control_Pair.keys()):  # Controlling others
                message = 'Reject Control& Error$ Your are controlling others'
                send_message(addr_ip, MEETINGPORT, message)
            elif (control_ip in Control_Pair.keys() and Control_Pair[
                control_ip] != '?'):  # control_ip Controlling others
                message = 'Reject Control& Error$ dst_ip is controlling others or not willing to control'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                del Control_Pair[control_ip]
                message = 'Reject Control& message $ ' + str(
                    {control_ip: addr_ip})  # tell both of them {control_ip:addr_ip}
                send_message(control_ip, MEETINGPORT, message)

        if "End Control" in message:  # end been controlled. format should be 'End Control'
            if (addr_ip in Control_Pair.keys()):  # addr_ip is controller
                message = 'End Control& Message$ controller disconnect'
                send_message(addr_ip, MEETINGPORT, message)
                send_message(Control_Pair[addr_ip], MEETINGPORT, message)
                del Control_Pair[addr_ip]
            elif (addr_ip in Control_Pair.values()):  # addr_ip is being controlled
                control_ip = ''
                for k, v in Control_Pair.items():
                    if (v == addr_ip):
                        control_ip = k
                message = 'End Control& Message$ controlled disconnect'
                send_message(addr_ip, MEETINGPORT, message)
                send_message(Control_Pair[addr_ip], MEETINGPORT, message)
                del Control_Pair[control_ip]
            else:  # not controlling or being controlled
                message = 'End Control& Error$ Your are not controlling or being controlled'
                send_message(addr_ip, MEETINGPORT, message)

        if "Transfer Host" in message:  # format should be "Transfer Host : $ip$" means transfer host to target $ip$
            new_host = message.split(':')[1].strip()
            meeting_num = get_Meeting_number(addr_ip)
            if meeting_num == -1:  # not in any meeting
                message = 'Transfer Host& Error$ Your are not in any meeting'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                room = Meeting_Record[meeting_num]
                if room['Host'] != addr_ip:  # not meeting host
                    message = 'Transfer Host& Error$ Your are not host'
                    send_message(addr_ip, MEETINGPORT, message)
                elif new_host not in room['Member']:
                    message = 'Transfer Host& Error$ New host not exist'
                    send_message(addr_ip, MEETINGPORT, message)
                else:
                    room['Host'] = new_host
                    message = 'Transfer Host& Eval$ ' + str(room)
                    broadcast(meeting_num, MEETINGPORT, message)

        if "Forbid Video" in message:
            meeting_num = get_Meeting_number(addr_ip)
            room = Meeting_Record[meeting_num]
            if room['Host'] != addr_ip:
                message = 'Forbid Video& Error$ Your are not host'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                room['Forbid_Video'] = True
                message = 'Forbid Video& Eval$ ' + str(room)
                broadcast(meeting_num, MEETINGPORT, message)
                for ip in list(room['Member']):
                    clear_ip_info(ip, Permission=['Video_Permitted'])

        if "Forbid Audio" in message:
            meeting_num = get_Meeting_number(addr_ip)
            room = Meeting_Record[meeting_num]
            if room['Host'] != addr_ip:
                message = 'Forbid Audio& Error$ Your are not host'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                room['Forbid_Audio'] = True
                message = 'Forbid Audio& Eval$ ' + str(room)
                broadcast(meeting_num, MEETINGPORT, message)
                for ip in list(room['Member']):
                    clear_ip_info(ip, Permission=['Audio_Permitted'])

        if "Forbid Screen" in message:
            meeting_num = get_Meeting_number(addr_ip)
            room = Meeting_Record[meeting_num]
            if room['Host'] != addr_ip:
                message = 'Forbid Screen& Error$ Your are not host'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                room['Forbid_Screen'] = True
                message = 'Forbid Screen& Eval$ ' + str(room)
                broadcast(meeting_num, MEETINGPORT, message)
                for ip in list(room['Member']):
                    clear_ip_info(ip, Permission=['Screen_Permitted'])

        if "Permit Video" in message:
            meeting_num = get_Meeting_number(addr_ip)
            room = Meeting_Record[meeting_num]
            if room['Host'] != addr_ip:
                message = 'Permit Video& Error$ Your are not host'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                room['Forbid_Video'] = False
                message = 'Permit Video& Eval$ ' + str(room)
                broadcast(meeting_num, MEETINGPORT, message)

        if "Permit Audio" in message:
            meeting_num = get_Meeting_number(addr_ip)
            room = Meeting_Record[meeting_num]
            if room['Host'] != addr_ip:
                message = 'Permit Audio& Error$ Your are not host'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                room['Forbid_Audio'] = False
                message = 'Permit Audio& Eval$ ' + str(room)
                broadcast(meeting_num, MEETINGPORT, message)

        if "Permit Screen" in message:
            meeting_num = get_Meeting_number(addr_ip)
            room = Meeting_Record[meeting_num]
            if room['Host'] != addr_ip:
                message = 'Permit Screen& Error$ Your are not host'
                send_message(addr_ip, MEETINGPORT, message)
            else:
                room['Forbid_Screen'] = False
                message = 'Permit Screen& Eval$ ' + str(room)
                broadcast(meeting_num, MEETINGPORT, message)


def Control(conn, addr_ip):
    data = "".encode("utf-8")
    payload_size = struct.calcsize("L")
    while (True):
        # while len(data) < payload_size:
        #     data += conn.recv(81920)
        # packed_size = data[:payload_size]
        # msg_size = struct.unpack("L", packed_size)[0]
        # data = data[payload_size:]
        # while len(data) < msg_size:
        #     data += conn.recv(81920)
        # dataEncry = data[:msg_size]
        # data = data[msg_size:]

        data = conn.recv(81920)
        if addr_ip in Control_Pair.values():
            for k, v in Control_Pair.items():
                if (v == addr_ip):
                    control_ip = k
            # aesPass = Client_AES[str(addr_ip)]
            # message = aesDecrypt(aesPass, dataEncry)
            message = data
            send_message(control_ip, SCREENCONTROLPORT, message, 'screencontrol')
            print("Control")
            continue
        if addr_ip in Control_Pair.keys():
            # aesPass = Client_AES[str(addr_ip)]
            # message = aesDecrypt(aesPass, dataEncry)
            message = data
            send_message(Control_Pair[addr_ip], SCREENCONTROLPORT, message, 'screencontrol')
            continue
