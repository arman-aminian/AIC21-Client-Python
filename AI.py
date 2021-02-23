from Model import *
import random


class AI:
    def __init__(self):
        self.message = None  # type: str
        self.value = 0 #type: int
        self.direction = None  # type: DIRECTION
        self.currentState = None  # type: CurrentState
        self.gameConfig = None  # type: GameConfig

    # this will be called in controller
    def set_current_state(self, currentState):
        self.currentState = currentState

    # this will be called in controller
    def set_game_config(self, gameConfig):
        self.gameConfig = gameConfig

    # this will be called each turn and it should return message and direction
    def turn(self):
        self.message = ""
        self.value = random.randint(1,10)
        self.direction = random.choice(list(Direction)).value
        return (self.message, self.value , self.direction)
