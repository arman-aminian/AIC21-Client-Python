import copy
from Model import *
from Utils import *
from graph import *
from message.map_message import *
from tsp_generator import get_tsp_first_move, get_limit


class AI:
    game_round = -1
    life_cycle = 1
    map = None
    w, h = -1, -1
    id = 0
    ids = {}
    latest_pos = {}
    found_history = {}
    state = None

    def __init__(self):
        # Current Game State
        self.game: Game = None

        # Answer
        self.message: str = None
        self.direction: int = None
        self.value: int = None

        # mine
        self.pos = (-1, -1)
        self.new_neighbors = {}
        self.encoded_neighbors = ""

    def search_neighbors(self):
        # TODO improve by creating the list of indices instead of all the cells
        ant = self.game.ant
        cells = ant.visibleMap.cells
        neighbor_cells = [j for sub in cells for j in sub if j is not None]
        neighbor_nodes = []
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
                              AI.map.nodes[n.pos] != n}
        AI.found_history.update(set(self.new_neighbors.keys()))

    def update_map_from_neighbors(self):
        if not self.new_neighbors:
            return
        # just in case. not really needed
        for pos, n in self.new_neighbors.items():
            AI.map.nodes[pos] = copy.deepcopy(n)

    def update_map_from_chat_box(self):
        maps = [msg for msg in
                self.game.chatBox.allChats[-MAX_MESSAGES_PER_TURN:] if '!' in
                msg.text and msg.turn == AI.game_round - 1]
        if AI.life_cycle == 1:
            maps = [msg for msg in self.game.chatBox.allChats if '!' in
                    msg.text]

        for m in maps:
            ant_id, ant_pos, nodes = decode_nodes(m.text, AI.w, AI.h,
                                                  self.game.ant.viewDistance)
            AI.latest_pos[ant_id] = (ant_pos, m.turn)
            for pos, n in nodes.items():
                if n != AI.map.nodes[pos]:
                    AI.map.nodes[pos] = copy.deepcopy(n)

    def update_ids_from_chat_box(self):
        id_msgs = [msg.text for msg in
                   self.game.chatBox.allChats[-MAX_MESSAGES_PER_TURN:] if
                   msg.text.startswith("id") and msg.turn == AI.game_round - 1]
        if AI.life_cycle == 1:
            id_msgs = [msg.text for msg in self.game.chatBox.allChats if
                       msg.text.startswith("id")]

        for m in id_msgs:
            msg_type = int(m[2])
            msg_id = int(m[3:])
            if msg_id not in AI.ids[0] and msg_id not in AI.ids[1]:
                AI.ids[msg_type].append(msg_id)

        if AI.game_round == 2:
            AI.id = sorted(AI.ids[self.game.ant.antType]).index(AI.id) + 1
            AI.ids[0] = [x for x in range(1, len(AI.ids[0]) + 1)]
            AI.ids[1] = [x for x in range(1, len(AI.ids[1]) + 1)]

    def send_id(self):
        self.message = "id" + str(self.game.ant.antType) + str(AI.id)
        self.value = MESSAGE_VALUE["id"]

    def make_id(self, min_id=1, max_id=220):
        all_ids = AI.ids[0] + AI.ids[1] if AI.ids else []
        iid = random.randint(min_id, max_id)
        while iid in all_ids:
            iid = random.randint(min_id, max_id)
        AI.id = iid

    def get_next_pos(self, cur_pos, move):
        if move == 1:
            next_pos = (cur_pos[0] + 1, cur_pos[1])
        elif move == 2:
            next_pos = (cur_pos[0], cur_pos[1] - 1)
        elif move == 3:
            next_pos = (cur_pos[0] - 1, cur_pos[1])
        elif move == 4:
            next_pos = (cur_pos[0], cur_pos[1] + 1)
        else:
            return (-1, -1)

        next_pos = ((next_pos[0] + self.game.mapWidth) % self.game.mapWidth,
                    (next_pos[1] + self.game.mapHeight) % self.game.mapHeight)
        return next_pos

    def get_init_ants_next_move(self, preferred_moves) -> int:
        for m in preferred_moves:
            next_node = AI.map.nodes[self.get_next_pos(self.pos, m)]
            if (not next_node.wall) and (self.get_next_pos(self.pos, m) != AI.latest_pos[AI.id]):
                return m
        print("error on get_init_ants_next_move")
        return Direction.get_random_direction()

    def get_init_ant_final_move(self):
        if self.game.baseX < (self.game.mapWidth / 2):
            if self.game.baseY < (self.game.mapHeight / 2):
                # left-up region
                if AI.id == 1 or AI.id == 4:
                    m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
                elif AI.id == 2:
                    if self.pos[0] < self.pos[1]:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[1])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[2])
                else:
                    if self.game_round % 2 == 1:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[0])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[0])
                print("left-up region : ", m)
            else:
                # left-down region
                if AI.id == 1 or AI.id == 2:
                    m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
                elif AI.id == 3:
                    if self.pos[0] < self.h - self.pos[1]:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[3])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[2])
                else:
                    if self.game_round % 2 == 1:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[1])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[1])
                print("left-down region : ", m)
        else:
            if self.game.baseY < (self.game.mapHeight / 2):
                # right-up region
                if AI.id == 3 or AI.id == 4:
                    m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
                elif AI.id == 2:
                    if self.w - self.pos[0] < self.pos[1]:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[1])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[0])
                else:
                    if self.game_round % 2 == 1:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[2])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[2])
                print("right-up region : ", m)
            else:
                # right-down region
                if AI.id == 2 or AI.id == 3:
                    m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
                elif AI.id == 1:
                    if self.w - self.pos[0] < self.h - self.pos[1]:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[3])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[0])
                else:
                    if self.game_round % 2 == 1:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[3])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[3])
                print("right-down region : ", m)
        if m < 5:
            return m
        else:
            print("something went wrong, init ants move :", m, "from id:", AI.id)
            return Direction.get_random_direction()

    def turn(self) -> (str, int, int):
        self.update_ids_from_chat_box()

        if AI.life_cycle > 1 and AI.id not in AI.ids[0] and \
                AI.id not in AI.ids[1]:
            self.send_id()

        if AI.game_round == -1:
            if not self.game.chatBox.allChats:
                AI.game_round = 1
            else:
                AI.game_round = self.game.chatBox.allChats[-1].turn + 1

        if AI.life_cycle == 1:
            AI.w, AI.h = self.game.mapWidth, self.game.mapHeight
            AI.map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
            AI.ids[AntType.SARBAAZ.value] = []
            AI.ids[AntType.KARGAR.value] = []
            if AI.game_round > 2:
                self.make_id(min_id=INIT_ANTS_NUM + 1)
            elif AI.game_round == 1:
                self.make_id()
            self.send_id()

        self.pos = (self.game.ant.currentX, self.game.ant.currentY)
        AI.latest_pos[AI.id] = (self.pos, AI.game_round)
        self.search_neighbors()
        self.update_map_from_neighbors()
        self.update_map_from_chat_box()

        if AI.life_cycle > 1:
            self.encoded_neighbors = encode_graph_nodes(self.pos,
                                                        self.new_neighbors,
                                                        AI.w, AI.h,
                                                        self.game.viewDistance,
                                                        AI.id)
            # TODO not discovered = guess node
            self.message = self.encoded_neighbors
            self.value = MESSAGE_VALUE["map"]

        if self.game.ant.antType == AntType.KARGAR.value:
            if AI.game_round != 1:
                if AI.id <= Utils.INIT_ANTS_NUM:
                    self.direction = self.get_init_ant_final_move()
                else:
                    # other ants
                    self.direction = Direction.get_random_direction()
                # todo: Delete this, this is test
                name_of_object = random.choice(['bread', 'grass'])
                print(name_of_object)

                if self.game_round > 5:
                    x = get_tsp_first_move(
                        src_pos=self.pos,
                        dest_pos=AI.map.base_pos,
                        name_of_object=name_of_object,
                        graph=AI.map,
                        limit=get_limit(name_of_object, min=2)
                    )
                    self.direction = x
                    print("pos:", self.pos, "move:", x)
            else:
                # first move
                self.direction = Direction.get_random_direction()
        else:
            # todo sarbaz move

            if AI.id <= Utils.INIT_ANTS_NUM:
                self.direction = Direction.get_random_direction()

            self.value = 5
            self.direction = Direction.RIGHT.value

        AI.game_round += 1
        AI.life_cycle += 1
        return self.message, self.value, self.direction
