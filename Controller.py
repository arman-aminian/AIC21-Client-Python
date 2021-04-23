import os
import sys
import threading
import traceback
from queue import Queue
from threading import Thread
from AI import AI
from Model import CurrentState, Direction, Game, GameConfig, ServerConstants
from Network import Network
import json
import time


class Controller:
    def __init__(self):
        self.sending_flag = True
        self.gameConfig = None
        self.conf = {}
        self.network = None
        self.queue = Queue()
        self.client = AI()
        self.argNames = ["AICHostIP", "AICHostPort", "AICToken", "AICRetryDelay"]
        self.argDefaults = [
            "127.0.0.1",
            7099,
            "00000000000000000000000000000000",
            "1000",
        ]
        self.turn_num = 0

    def handle_message(self, message):
        if message[ServerConstants.KEY_TYPE] == ServerConstants.MESSAGE_TYPE_INIT:
            self.handle_init_message(message[ServerConstants.KEY_INFO])

        elif message[ServerConstants.KEY_TYPE] == ServerConstants.MESSAGE_TYPE_TURN:
            gameStatus = CurrentState(message[ServerConstants.KEY_INFO])
            threading.Thread(target=self.launch_on_thread, args=([gameStatus])).start()

        elif message[ServerConstants.KEY_TYPE] == ServerConstants.MESSAGE_TYPE_KILL:
            exit(4)

        elif message[ServerConstants.KEY_TYPE] == ServerConstants.MESSAGE_TYPE_DUMMY:
            pass

    def launch_on_thread(self, world):
        # try:
        self.handle_turn_message(world)

    # except Exception as e:
    #     print("Error in client:")
    #     print(e)

    def send_direction_message(self, direction):
        self.network.send({"type": 1, "info": {"direction": direction}})

    def send_chat_message(self, chat, value):
        self.network.send({"type": 2, "info": {"message": chat, "value": value}})

    def send_end_message(self):
        self.network.send({"type": 6, "info": {}})

    def handle_turn_message(self, currentState):
        self.client = AI()
        game = Game()
        game.initGameConfig(self.gameConfig)
        game.setCurrentState(currentState)
        self.client.game = game
        start = time.time() * 1000
        (message, value, direction) = self.client.turn()
        diff = time.time() * 1000 - start
        if diff > 2000:
            pass
        elif diff > 1000:
            self.send_direction_message(Direction.CENTER.value)
        else:
            if direction is not None:
                self.send_direction_message(direction)
            if message is not None and value is not None:
                self.send_chat_message(message, value)
        self.send_end_message()

    def handle_init_message(self, message):
        self.gameConfig = GameConfig(message)

    def start(self):
        self.read_settings()
        self.network = Network(
            ip=self.conf[self.argNames[0]],
            port=int(self.conf[self.argNames[1]]),
            token=self.conf[self.argNames[2]],
            message_handler=self.handle_message,
        )
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


if __name__ == "__main__":
    c = Controller()
    # if len(sys.argv) > 1 and sys.argv[1] == '--verbose':
    #     DEBUGGING_MODE = True
    c.start()
