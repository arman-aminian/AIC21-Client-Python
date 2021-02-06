ANT_TYPES = ["SARBAAZ", "KARGAR"]
CELL_TYPES = ["EMPTY", "WALL", "BASE"]
RESOURCE_TYPES = ["BREAD", "GRASS"]
DIRECTIORN = ["RIGHT", "LEFT", "UP", "DOWN", "CENTER"]


class Ant:
    def __init__(self, type, health, locationCell):
        # ANT_TYPES
        self.type = type
        # Current Cell
        self.locationCell = locationCell
        self.health = health

    # returns a DIRECTION
    def move(self):
        pass

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
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        # CELL_TYPES
        self.type = type
		# current ants in this cell
        self.ants = []


class Resource:
    def __init__(self, type, amount):
        # RESOURCE_TYPES
        self.type = type
        self.amount = amount

    def get_type(self):
        return self.type

    def get_amount(self):
        return self.amount

class GameConfig:
    def __init__(self):
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
        
# CurrentState: each turn before AI.py is called
# GameConfig: getting from server at startup

# def AI(self, currentState):
# 	#
# 	#
# 	#

# 	return {
# 		Message,
# 		Direction,
# 	}
