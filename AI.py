from Model import *
from graph import *
from message import *


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
        self.w, self.h = -1, -1
        self.pos = (-1, -1)
        self.map = None
        self.new_neighbors = {}
        self.encoded_neighbors = ""
        self.map_value = 10

    """
    Return a tuple with this form:
        (message: str, message_value: int, message_dirction: int)
    check example
    """

    def search_neighbors(self):
        # TODO improve by creating the list of indices instead of all the cells
        ant = self.game.ant
        cells = ant.visibleMap.cells
        neighbor_cells = [j for sub in cells for j in sub if j is not None]
        neighbor_nodes = []
        print("i am in", self.pos)
        for n in neighbor_cells:
            w = n.type == CellType.WALL.value
            if w:
                neighbor_nodes.append(Node((n.x, n.y), True, True))
            else:
                b = n.resource_value if \
                    n.resource_type == ResourceType.BREAD.value else 0
                g = n.resource_value if \
                    n.resource_type == ResourceType.GRASS.value else 0
                aw, ally_s, ew, es = [0] * 4
                for a in n.ants:
                    if a.antTeam == self.game.ant.antTeam:
                        if a.antType == AntType.KARGAR.value:
                            aw += 1
                        elif a.antType == AntType.SARBAAZ.value:
                            ally_s += 1
                    else:
                        if a.antType == AntType.KARGAR.value:
                            ew += 1
                        elif a.antType == AntType.SARBAAZ.value:
                            es += 1
                neighbor_nodes.append(Node((n.x, n.y), True, False, b, g, aw,
                                           ally_s, ew, es))
        
        self.new_neighbors = {n.pos: n for n in neighbor_nodes if
                              self.map.nodes[n.pos] != n}
        
    def update_map_from_neighbors(self):
        if not self.new_neighbors:
            return
        # just in case. not really needed
        for pos, n in self.new_neighbors.items():
            self.map.nodes[pos].__dict__ = n.__dict__
            
    def update_map_from_chat_box(self):
        # TODO add map value if so that we won't search through messages
        # that are not maps
        maps = [msg.text for msg in self.game.chatBox.allChats]
        for m in maps:
            nodes = decode_nodes(self.pos, m, self.w, self.h,
                                 self.game.ant.viewDistance)
            for n in nodes:
                if n != self.map.nodes[n.pos]:
                    self.map.nodes[n.pos].__dict__ = n.__dict__

    def turn(self) -> (str, int, int):
        AI.round += 1
        self.direction = Direction.LEFT.value
    
        # MAP RELATED #################################################
        self.pos = (self.game.ant.currentX, self.game.ant.currentY)
        self.w, self.h = self.game.mapWidth, self.game.mapHeight
        self.map = Graph((self.w, self.h), (self.game.baseX, self.game.baseY))
        # should always create map based on chat box
        self.update_map_from_chat_box()
        if AI.round == 2:
            print(self.map.nodes)
        # should always update what you see
        self.search_neighbors()
        self.update_map_from_neighbors()
        self.encoded_neighbors = encode_graph_nodes(self.pos,
                                                    self.new_neighbors,
                                                    self.w, self.h,
                                                    self.game.viewDistance)
        print(self.encoded_neighbors)
        return self.encoded_neighbors, self.map_value, self.direction
        # END OF MAP RELATED ##########################################
    
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
