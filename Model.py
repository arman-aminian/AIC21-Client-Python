from enum import Enum
from typing import *


class Ant:
    antType: int
    antTeam: int
    currentResource: "Resource"
    currentX: int
    currentY: int
    health: int
    visibleMap: "Map"
    attackDistance: int
    viewDistance: int

    def __init__(
        self,
        ant_type: int,
        ant_team: int,
        currentResource: "Resource",
        currentX: int,
        currentY: int,
        health: int,
        visibleMap: "Map",
        attackDistance: int,
        viewDistance: int
    ):
        self.antType = ant_type
        self.antTeam = ant_team
        self.currentX = currentX
        self.currentY = currentY
        self.currentResource = currentResource
        self.visibleMap = visibleMap
        self.health = health
        self.attackDistance = attackDistance
        self.viewDistance = viewDistance

    @classmethod
    def createAntXY(cls, ant_type: int, ant_team: int, currentX: int, currentY: int):
        return cls(ant_type, ant_team, None, currentX, currentY, -1, None, -1, -1)

    @classmethod
    def createCurrentAnt(
        cls,
        ant_type: int,
        ant_team: int,
        currentState: "CurrentState",
        visibleMap: "Map",
        attackDistance: int,
        viewDistance: int,
    ):
        return cls(
            ant_type,
            ant_team,
            Resource(
                currentState.current_resource_type, currentState.current_resource_value
            ),
            currentState.current_x,
            currentState.current_y,
            currentState.health,
            visibleMap,
            attackDistance,
            viewDistance
        )


class Map:
    cells: List["Cell"]
    antCurrentX: int
    antCurrentY: int

    def __init__(
        self,
        cells: List["Cell"],
        currentX: int,
        currentY: int,
    ):
        super().__init__()
        self.cells = cells
        self.antCurrentX = currentX
        self.antCurrentY = currentY


class Cell:
    x = 0
    y = 0
    type = 0
    resource_value = 0
    resource_type = 0
    ants = List["Ant"]

    def __init__(self, x, y, type, resource_value, resource_type):
        self.x = x
        self.y = y
        self.type = type
        self.ants = []
        self.resource_value = resource_value
        self.resource_type = resource_type


class Resource:
    type: int
    value: int

    def __init__(self, type: int, value: int):
        super().__init__()
        self.value = value
        self.type = type


class Message:
    def __init__(self, text: str, turn: int):
        self.text = text
        self.turn = turn


class GameConfig:
    ant_type: int = 0
    base_x: int = -1
    base_y: int = -1
    health_kargar: int = 0
    health_sarbaaz: int = 0
    attack_distance: int = 0
    view_distance: int = 0
    generate_kargar: int = 0
    generate_sarbaz: int = 0
    generate_sarbaaz: int = 0
    rate_death_resource: int = 0

    def __init__(self, message):
        self.__dict__ = message


class CurrentState:
    around_cells: List["Cell"] = []
    chat_box: List["Message"] = []
    current_x: int = -1
    current_y: int = -1
    current_resource_type: int = None
    current_resource_value: int = 0
    health: int = 0

    def __init__(self, message):
        self.__dict__ = message
        cells = []
        for cel in self.around_cells:
            this_cell = Cell(
                cel["cell_x"],
                cel["cell_y"],
                cel["cell_type"],
                cel["resource_value"],
                cel["resource_type"],
            )
            cells.append(this_cell)
            for clientAnt in cel["ants"]:
                this_cell.ants.append(
                    Ant.createAntXY(
                        clientAnt["ant_type"],
                        clientAnt["ant_team"],
                        cel["cell_x"],
                        cel["cell_y"],
                    )
                )
        self.around_cells = cells


class Game:
    ant: "Ant"
    chatBox: "ChatBox"
    antType: int
    baseX: int
    baseY: int
    healthKargar: int
    healthSarbaaz: int
    attackDistance: int
    viewDistance: int
    generateKargar: int
    rateDeathResource: int
    generateSarbaaz: int

    def __init__(self):
        super().__init__()
        self.ant = None
        self.chatBox = None
        self.baseX = None
        self.baseY = None
        self.healthKargar = None
        self.healthSarbaaz = None
        self.attackDistance = None
        self.viewDistance = None
        self.generateKargar = None
        self.generateSarbaaz = None
        self.rateDeathResource = None

    def initGameConfig(self, gameConfig: "GameConfig"):
        self.antType = gameConfig.ant_type
        self.baseX = gameConfig.base_x
        self.baseY = gameConfig.base_y
        self.healthKargar = gameConfig.health_kargar
        self.healthSarbaaz = gameConfig.health_sarbaaz
        self.attackDistance = gameConfig.attack_distance
        self.viewDistance = gameConfig.view_distance
        self.generateKargar = gameConfig.generate_kargar
        self.generateSarbaaz = gameConfig.generate_sarbaaz
        self.rateDeathResource = gameConfig.rate_death_resource

    def setCurrentState(self, currentState: "CurrentState"):
        self.chatBox = ChatBox(currentState.chat_box)
        self.ant = self.initialAntState(currentState)

    def initialAntState(self, currentState: "CurrentState"):
        my_map = Map(
            currentState.around_cells,
            currentState.current_x,
            currentState.current_y,
        )
        return Ant.createCurrentAnt(
            self.antType,
            AntTeam.ALLIED.value,
            currentState,
            my_map,
            self.attackDistance,
            self.viewDistance,
        )


class ChatBox:
    allChats: List["Chat"]

    def __init__(self, allChats):
        super().__init__()
        self.allChats = allChats


class Chat:
    text: str
    turn: int

    def __init__(self, text, turn):
        super().__init__()
        self.text = text
        self.turn = turn


class AntType(Enum):
    SARBAAZ = 0
    KARGAR = 1

    @staticmethod
    def get_value(string: str):
        if string == "SARBAAZ":
            return AntType.SARBAAZ
        if string == "KARGAR":
            return AntType.KARGAR
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
            return CellType.BASE
        if string == "EMPTY":
            return CellType.EMPTY
        if string == "WALL":
            return CellType.WALL
        return None


class ResourceType(Enum):
    BREAD = 0
    GRASS = 1

    @staticmethod
    def get_value(string: str):
        if string == "BREAD":
            return ResourceType.BREAD
        if string == "GRASS":
            return ResourceType.GRASS
        return None


class ServerConstants:
    KEY_INFO = "info"
    KEY_TURN = "turn"
    KEY_TYPE = "type"

    # CONFIG_KEY_IP = "ip"
    # CONFIG_KEY_PORT = "port"
    CONFIG_KEY_TOKEN = "token"

    MESSAGE_TYPE_INIT = "3"
    MESSAGE_TYPE_TURN = "4"
    MESSAGE_TYPE_KILL = "7"


class AntTeam(Enum):
    ENEMY = 1
    ALLIED = 0


class ServerMessage:
    def __init__(self, type, turn, info):
        self.type = type
        self.info = info
        self.turn = turn
