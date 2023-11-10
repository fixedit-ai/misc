"""
Simple http forwarding to another client for testing forwarding of RTP over RTSP over HTTP.

Based on code from: https://medium.com/@gdieu/build-a-tcp-proxy-in-python-part-1-3-7552cd5afdfe
"""

import sys
import socket
import select

ADDRESS = "0.0.0.0"
PORT = 8080

TARGET_ADDRESS = "192.168.0.90"
TARGET_PORT = 443


class Proxy:
    def __init__(self, target_addr, target_port):
        self.socket_list = []
        self.msg_queue = {}
        self.target_addr = target_addr
        self.target_port = target_port

    def serve(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setblocking(0)
            sock.bind((ADDRESS, PORT))
            sock.listen(3)
            self.socket_list.append(sock)
            print('[*] Listening on {0} {1}'.format(ADDRESS, PORT))
            while True:
                readable, writable, exceptional = select.select(self.socket_list, [], [])
                for s in readable:
                    if s == sock:
                        rserver = self.remote_conn()
                        if rserver:
                            client, addr = sock.accept()
                            print('Accepted connection {0} {1}'.format(addr[0], addr[1]))
                            self.store_sock(client, addr, rserver)
                            break
                        else:
                            print(
                                    "the connection with the remote server (%s:%d) can't be established" %
                                    (self.target_addr, self.target_port)
                            )
                            client.close()
                    data = self.received_from(s, 3)
                    self.msg_queue[s].send(data)
                    if len(data) == 0:
                        self.close_sock(s)
                        break
        except KeyboardInterrupt:
            print('Ending server')        

    def remote_conn(self):
        try:
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.connect((self.target_addr, self.target_port))
            return remote_sock
        except Exception as e:
            print(e)
            return False

    def store_sock(self, client, addr, rserver):
        self.socket_list.append(client)
        self.socket_list.append(rserver)
        self.msg_queue[client] =  rserver
        self.msg_queue[rserver] =  client

    def received_from(self, sock, timeout):
        data = b""
        sock.settimeout(timeout)
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                data =+ data
        except:
            pass
        return data

    def close_sock(self, sock):
        print ('End of connection with client')
        self.socket_list.remove(self.msg_queue[sock])
        self.socket_list.remove(self.msg_queue[self.msg_queue[sock]])
        serv = self.msg_queue[sock]
        self.msg_queue[serv].close()
        self.msg_queue[sock].close()
        del self.msg_queue[sock]
        del self.msg_queue[serv]


if __name__ == "__main__":
    target_addr = TARGET_ADDRESS
    target_port = TARGET_PORT
    if len(sys.argv) >= 2:
        target_addr = sys.argv[1]
    if len(sys.argv) >= 3:
        target_port = int(sys.argv[2])

    proxy = Proxy(target_addr, target_port)
    proxy.serve()
    print("OK, all done")
