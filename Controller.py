import os
import sys
import threading
import traceback
from queue import Queue
from threading import Thread
from AI import AI
from Model import CurrentState, GameConfig, ServerConstants
from Network import Network


class Controller:

    def __init__(self):
        self.sending_flag = True
        self.gameConfig = None
        self.conf = {}
        self.network = None
        self.queue = Queue()
        self.client = AI()
        self.argNames = ["AICHostIP", "AICHostPort",
                         "AICToken", "AICRetryDelay"]
        self.argDefaults = ["127.0.0.1", 7099,
                            "00000000000000000000000000000000", "1000"]
        self.turn_num = 0

    def handle_message(self, message):
        if message[ServerConstants.KEY_TYPE] == ServerConstants.MESSAGE_TYPE_INIT:
            self.handle_init_message(message[ServerConstants.KEY_INFO])
            threading.Thread().start()

        elif message[ServerConstants.KEY_TYPE] == ServerConstants.MESSAGE_TYPE_TURN:
            self.handle_turn_message(message[ServerConstants.KEY_INFO])
            threading.Thread().start()

    def send_direction_message(self, direction):
        self.network.send({
            "type": 1,
            "info": {"direction": direction}
        })

    def send_chat_message(self, chat, value):
        self.network.send({
            "type": 2,
            "info": {"message": chat,
                     "value": value
                     }
        })

    def send_end_message(self):
        self.network.send({
            "type": 6,
            "info": {}
        })

    def handle_turn_message(self, message):
        currentState = CurrentState(message)
        self.client.set_current_state(currentState)
        self.client.set_game_config(self.gameConfig)
        (message, value, direction) = self.client.turn()
        self.send_direction_message(direction)
        self.send_chat_message(message,value)

    def handle_init_message(self, message):
        self.gameConfig = GameConfig(message)

    def start(self):
        self.read_settings()
        self.network = Network(ip=self.conf[self.argNames[0]],
                               port=int(self.conf[self.argNames[1]]),
                               token=self.conf[self.argNames[2]],
                               message_handler=self.handle_message)
        self.network.connect()
        Thread().start()

    def read_settings(self):
        if os.environ.get(self.argNames[0]) is None:
            for i in range(len(self.argNames)):
                self.conf[self.argNames[i]] = self.argDefaults[i]
        else:
            for i in range(len(self.argNames)):
                self.conf[self.argNames[i]] = os.environ.get(self.argNames[i])

    def terminate(self):
        print("finished!")
        self.network.close()
        self.sending_flag = False

if __name__ == '__main__':
    c = Controller()
    # if len(sys.argv) > 1 and sys.argv[1] == '--verbose':
    #     DEBUGGING_MODE = True
    c.start()
