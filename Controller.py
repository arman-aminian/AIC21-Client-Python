import os
import sys
import threading
import traceback
from queue import Queue
from threading import Thread
from models import Map
from AI import AI
from network import Network
from world import World

class Controller:

    def __init__(self):
        self.sending_flag = True
        self.conf = GameConfig()
        self.network = None
        self.queue = Queue()
        self.map = Map()
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
                message = handle_map_massage()
                self.network.send(message)

    def turn(gameConfig, massage):
        self.client.set_currrent_state()
        
        
    def handle_chat(massage):
        pass

    def handle_direction(massage):
        self.client.set_direction(massage.direction)

    def handle_init_massage(massage):
      self.client.set_current_state(massage)
        

    def handle_map_massage():
     return {
                    "map_width": self.conf.map_width,
                    "map_heigth": self.conf.map_height,
                    "ant_type": self.conf.ant_type, 
                    "base_x": self.conf.base_x,  
                    "base_y": self.conf.base_y,
                    "health_kargar": self.conf.health_kargar,
                    "health_sarbaaz": self.conf.health_sarbaz,
                    "attack_distance":self.conf.attack_distance,
                    "generate_kargar": self.conf.generate_kargar,
                    "generate_sarbaaz": self.conf.generate_sabaz,
                    "rate_death_resource": self.conf.rate_death_resource
                }
      

    def handle_message(self, massage):
      # this need changes
      if (massage.type == 0) :
         self.handle_init_massage()
      elif (massage.type == 1) :
          self.handle_direction(massage)
      elif (massage.type == 2) :
          self.handle_chat(massage)
      pass






c = Controller()
c.start()
