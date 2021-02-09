import os
import sys
import threading
import traceback
from queue import Queue
from threading import Thread

from AI import AI
from network import Network
from world import World

class Controller:

    def __init__(self):
        self.sending_flag = True
        self.conf = GameConfig()
        self.network = None
        self.queue = Queue()
        self.world = World(queue=self.queue)
        self.client = AI()
        self.argNames = ["AICHostIP", "AICHostPort", "AICToken", "AICRetryDelay"]
        self.argDefaults = ["127.0.0.1", 7099, "00000000000000000000000000000000", "1000"]
        self.turn_num = 0

    def start():
        self.network = Network(ip=self.conf[self.argNames[0]],
                               port=self.conf[self.argNames[1]],
                               token=self.conf[self.argNames[2]],
                               message_handler=self.handle_message)
        self.network.connect()

    def terminate(self):
        print("finished!")
        self.network.close()
        self.sending_flag = False

    def run():
            while self.sending_flag:
                event = self.queue.get()
                self.queue.task_done()
                message = {
                    # feel this out
                }
                self.network.send(message)

    def turn(gameConfig, massage):
        self.client.set_currrent_state()
        
        
    def handle_shutdown_massage(massage):
        pass

    def handle_turn_massage(massage):
        pass

    def handle_init_massage(massage):
        pass

    def handle_map_massage(massage):
        pass

    def handle_message(self, message):
       pass






c = Controller()
c.start()
