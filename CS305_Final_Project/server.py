from server_sockets import *
from CONSTANTS import *
import socket
import threading


def socket_listen(port_listen):
    # Start a threading function to listen a port
    # Create a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the address
    sock.bind(('', port_listen))
    # Socket listen
    sock.listen(5)

    while True:
        # Wait to client to connect
        conn, addr = sock.accept()

        addr_ip, addr_port = addr
        add_conn(addr_ip, port_listen, conn)

        if port_listen == MEETINGPORT:
            # print(Connection_MEETINGPORT)
            threading.Thread(target=Meeting, args=(conn, addr_ip)).start()

        if (port_listen == VIDEOPORT):
            # this port is used for video transmission
            threading.Thread(target=Video, args=(conn, addr_ip)).start()

        if (port_listen == AUDIOPORT):
            # this port is used for audio transmission
            threading.Thread(target=Audio, args=(conn, addr_ip)).start()

        if (port_listen == SCREENSHARINGPORT):
            # this port is used for screen sharing transmission
            threading.Thread(target=Screen, args=(conn, addr_ip)).start()

        if (port_listen == SCREENCONTROLPORT):
            # this port is used for screen sharing transmission
            threading.Thread(target=Control, args=(conn, addr_ip)).start()


if __name__ == "__main__":

    # Threading lists
    ths = []

    # Ports which need to listen
    '''Modify here'''
    ports = [MEETINGPORT, VIDEOPORT, AUDIOPORT, SCREENSHARINGPORT, SCREENCONTROLPORT]

    # Add threadings
    for port_listen in ports:
        ths.append(threading.Thread(target=socket_listen, args=(port_listen,)))

    # Start threading
    try:
        for th in ths:
            th.start()
    except Exception as e:
        print(e)
