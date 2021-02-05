class Ant:
	def __init__(self, type, health, locationCell)
		self.type = type
		self.locationCell = locationCell
		self.health = health

	def move(self):
		pass

	def send_message(self, text):
		pass

	def get_location(self):
		return self.locationCell

	def get_neighbours(self):
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
		self.type = type


class Resource:
	def __init__(self, type, amount)
		self.type = type
		self.amount = amount

	def get_type(self)
		return self.type

	def get_amount(self)
		return self.amount


class Player:
	def __init__(self):
		pass
