from enum import Enum

class Ant:
    def __init__(self, type, health, locationCell):
        # ANT_TYPES
        self.type = type
        # Current Cell
        self.locationCell = locationCell
        self.health = health

    # get current location
    def get_location(self):
        return self.locationCell

    # get cells in this ants view
    def get_neighbours_cell(self):
        return currentState.around_cells

    def get_health(self):
        return self.health


class Map:
    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width
        self.cells = []


class Cell:
    def __init__(self, x, y, type, resource_value, resource_type):
        self.x = x
        self.y = y
        # CELL_TYPES
        self.type = type
        # current ants in this cell
        self.ants = []
        self.resource_value = resource_value
        self.resource_type = resource_type


class Resource:
    def __init__(self, type, amount):
        # RESOURCE_TYPES
        self.type = type
        self.amount = amount

    def get_type(self):
        return self.type

    def get_amount(self):
        return self.amount


class Message:
    def __init__(self, text: str, turn: int):
        self.text = text
        self.turn = turn


class GameConfig:
    map_width = 0 # int
    map_height = 0 # int
    ant_type = None
    base_x = -1 #int
    base_y = -1 # int
    health_kargar = 0 # int
    health_sarbaz = 0 # int
    attack_distance = 0 # int
    generate_sarbaz = 0 # int
    rate_death_resource = 0 # float

    def __init__(self, message):
        self.__dict__ = message

    def get_base_cell(self):
        return Cell(x, y, CellType.BASE, None, None)


class CurrentState:
    around_cells = [] #List["Cell"]
    chat_box = [] #List["Message"]
    current_x: int
    current_y: int
    current_resource_type = None #ResourceTypes
    current_resource_value: int
    health: int

    # This will keep the current state of the game
    def __init__(self, around_cells, chat_box, current_x, current_y,
                 current_resource_value, current_resource_type, health):
        self.around_cells = around_cells
        self.chat_box = chat_box
        self.current_x = current_x
        self.current_y = current_y
        self.current_resource_value = current_resource_value
        self.current_resource_type = current_resource_type
        self.health = health



class AntType(Enum):
    SARBAAZ = 0
    KARGAR = 1

    @staticmethod
    def get_value(string: str):
        if string == "SARBAAZ":
            return AntTypes.SARBAAZ
        if string == "KARGAR":
            return AntTypes.KARGAR
        return None


class Direction(Enum):
    CENTER = 0
    RIGHT = 1
    UP = 2
    LEFT = 3
    DOWN = 4

    @staticmethod
    def get_value(string: str):
        if string == "CENTER":
            return Direction.CENTER
        if string == "right":
            return Direction.RIGHT
        if string == "UP":
            return Direction.UP
        if string == "LEFT":
            return Direction.LEFT
        if string == "DOWN":
            return Direction.DOWN
        return None


class CellType(Enum):
    BASE = 0
    EMPTY = 1
    WALL = 2

    @staticmethod
    def get_value(string: str):
        if string == "BASE":
            return CellTypes.BASE
        if string == "EMPTY":
            return CellTypes.EMPTY
        if string == "WALL":
            return CellTypes.WALL
        return None


class ResourceType(Enum):
    BREAD = 0
    GRASS = 1

    @staticmethod
    def get_value(string: str):
        if string == "BREAD":
            return ResourceTypes.BREAD
        if string == "GRASS":
            return ResourceTypes.GRASS
        return None


class ServerConstants:
    KEY_INFO = "info"
    KEY_TURN = "turn"
    KEY_TYPE = "type"

    CONFIG_KEY_IP = "ip"
    CONFIG_KEY_PORT = "port"
    CONFIG_KEY_TOKEN = "token"

    MESSAGE_TYPE_EVENT = "event"
    MESSAGE_TYPE_INIT = "init"
    MESSAGE_TYPE_PICK = "pick"
    MESSAGE_TYPE_SHUTDOWN = "shutdown"
    MESSAGE_TYPE_TURN = "turn"
    MESSAGE_TYPE_END_TURN = "endTurn"

    CHANGE_TYPE_ADD = "a"
    CHANGE_TYPE_DEL = "d"
    CHANGE_TYPE_MOV = "m"
    CHANGE_TYPE_ALT = "c"


class ServerMessage:
    def __init__(self, type, turn, info):
        self.type = type
        self.info = info
        self.turn = turn

# CurrentState: each turn before AI.py is called
