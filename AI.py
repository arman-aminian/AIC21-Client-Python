from Model import *
from graph import *
import random
import json
from typing import *


class AI:
    round = 0

    def __init__(self):
        # Current Game State
        self.game: Game = None

        # Answer
        self.message: str = None
        self.direction: int = None
        self.value: int = None

        # mine
        self.g = None

    """
    Return a tuple with this form:
        (message: str, message_value: int, message_dirction: int)
    check example
    """

    def turn(self) -> (str, int, int):
        AI.round += 1

        # self.message = str(AI.round)
        # self.value = random.randint(1, 10)
        # at the beginning, create the map graph
        if AI.round == 1:
            self.g = Graph((self.game.mapWidth, self.game.mapHeight),
                           (self.game.baseX, self.game.baseY))
            self.message = "made map"
            self.direction = Direction.RIGHT.value
            return self.message, self.value, self.direction

        # todo update map
        # mh

        if self.game.ant.antType == AntType.KARGAR.value:
            # todo kargar move
            # mehdi

            # todo delete
            l = len(self.game.chatBox.allChats)
            if l > 0:
                # self.message = "hichi " + str(l)
                self.message = "hichi " + self.game.chatBox.allChats[l-1].text
                self.value = 4
            self.direction = Direction.LEFT.value
        else:
            # todo sarbaz move
            # self.message = str(len(self.game.chatBox.allChats))
            l = len(self.game.chatBox.allChats)
            if l > 0:
                self.message = str(self.game.chatBox.allChats[0].turn)
            else:
                self.message = "nothing"
            self.value = 5
            self.direction = Direction.RIGHT.value

        return self.message, self.value, self.direction
