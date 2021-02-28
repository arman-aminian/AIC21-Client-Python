import socket
import json
import time

from Model import *


class Network():
    def __init__(self, ip, port, token, message_handler):
        self.receive_flag = True
        self.ip = ip
        self.port = port
        self.token = token
        self.message_handler = message_handler
        self.result = b''
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        connect_attempt = 1
        connected = False
        error = None
        while connected is False and connect_attempt < 11:
            try:
                print("Trying to connect #{}".format(connect_attempt))
                connect_attempt += 1
                self.s.connect((self.ip, self.port))
                connected = True
                self.send({"type": ServerConstants.CONFIG_KEY_TOKEN,
                                        "turn": 0,
                                        "info": {ServerConstants.CONFIG_KEY_TOKEN: self.token}
                                        })
                init = self.receive()
                if init[ServerConstants.KEY_TYPE] == "wrong token":
                    raise ConnectionRefusedError("wrong token")
                elif not init[ServerConstants.KEY_TYPE] == ServerConstants.MESSAGE_TYPE_INIT:
                    self.close()
                    raise IOError("first message was not init")
            except Exception as e:
                print("error while connecting to server", e)
                error = e
                time.sleep(2)
                continue
            print("connected to server!")
            self.message_handler(init)
            self.start_receiving()
        if connected is False:
            print('Cant connect to server, ERROR: {}'.format(error))

    def send(self, message):
        j_obj = json.dumps(message, default = str)
        self.s.send(j_obj.encode('UTF-8'))
        self.s.send(b'\x00')

    def receive(self):
        while self.receive_flag:
            self.result += self.s.recv(1024)
            if b'\x00' in self.result:
                ans = json.loads(self.result[:self.result.index(b'\x00')].decode('UTF-8'))
                self.result = self.result[self.result.index(b'\x00') + 1:]
                return ans

    def start_receiving(self):
        import threading

        def run():
            while self.receive_flag:
                try:
                    self.message_handler(self.receive())
                except ConnectionError:
                    print("disconnected from server!")
                    self.close()
                    break

        tr = threading.Thread(target=run, daemon=False)
        tr.start()

    def terminate(self):
        self.receive_flag = False

    def close(self):
        self.terminate()
        self.s.close()
