from Model import *
import random
import json
from typing import *


class AI:
    def __init__(self):
        # Current Game State
        self.game: Game = None

        # Answer
        self.message: str = None
        self.direction: int = None
        self.value: int = None

    """
    Return a tuple with this form:
        (message: str, message_value: int, message_dirction: int)
    check example
    """

    def turn(self) -> (str, int, int):
        """ self.message = "hello python"
        self.value = random.randint(1,10)
        self.direction = random.choice(list(Direction)).value """

        # todo update map
        # mh

        if self.game.ant.antType == AntType.KARGAR.value:
            # todo kargar move
            # mehdi
            self.direction = Direction.LEFT.value
        else:
            # todo sarbaz move
            # arman
            self.direction = Direction.RIGHT.value

        self.message = (str(AntType.KARGAR.value))
        self.value = random.randint(1, 10)

        return (self.message, self.value, self.direction)
