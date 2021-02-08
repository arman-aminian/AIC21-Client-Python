from enum import Enum

class Ant:
    def __init__(self, type, health, locationCell):
        # ANT_TYPES
        self.type = type
        # Current Cell
        self.locationCell = locationCell
        self.health = health

    def send_message(self, text):
        pass

    # get current location
    def get_location(self):
        return self.locationCell

    # get cells in this ants view
    def get_neighbours_cell(self):
        pass

    def get_health(self):
        return self.health


class Map:
    def __init__(self, length, width):
        self.length = length
        self.width = width
        self.cells = None


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
    def __init__(self, text, turn):
        self.text = text
        self.turn = turn


class GameConfig:
    map_width: int
    map_height: int
    ant_type: AntType
    base_x: int
    base_y: int
    health_kargar: int
    health_sarbaz: int
    attack_distance: int
    generate_sarbaz: int
    rate_death_resource: float

    # This will initiate game constants at the beginning of the game.
    def __init__(self, map_width, map_height, ant_type, base_x, base_y,
    health_kargar, health_sarbaz, attack_distance, generate_sarbaz,
    rate_death_resource):
        self.map_width = map_width
        self.map_height = map_height
        self.ant_type = ant_type
        self.base_x = base_x
        self.base_y = base_y
        self.health_kargar = health_kargar
        self.health_sarbaz = health_sarbaz
        self.attack_distance = attack_distance
        self.generate_sarbaz = generate_sarbaz
        self.rate_death_resource = rate_death_resource


class CurrentState:
    around_cells: List["Cell"]
    chat_box: List["Message"]
    current_x: int
    current_y: int
    current_resource_type: ResourceTypes
    current_resource_value: int
    health: int

    # This will keep the current state of the game
    def __init__(self,around_cells, chat_box, current_x, current_y,
    current_resource_value, current_resource_type, health):
        self.around_cells = around_cells
        self.chat_box = chat_box
        self.current_x = current_x
        self.current_y = current_y
        self.current_resource_value = current_resource_value
        self.current_resource_type = current_resource_type
        self.health = health

class AntTypes(Enum):
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
    def get_value(string:str):
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


class CellTypes(Enum):
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


class ResourceTypes(Enum):
    BREAD = 0
    GRASS = 1

    @staticmethod
    def get_value(string: str):
        if string == "BREAD":
            return ResourceTypes.BREAD
        if string == "GRASS":
            return ResourceTypes.GRASS
        return None

# CurrentState: each turn before AI.py is called
