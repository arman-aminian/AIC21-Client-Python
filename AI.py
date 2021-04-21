import copy
from Model import *
from Utils import *
from graph import *
from message.map_message import *
from tsp_generator import get_tsp_first_move, get_limit, get_number_of_object
from state import *


class AI:
    game_round = -1
    life_cycle = 1
    map = None
    w, h = -1, -1
    id = 0
    ids = {}
    latest_pos = {}
    found_history = set()
    state = WorkerState.Null
    last_name_of_object = None

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
            AI.ids[AntType.SARBAAZ.value] = []
            AI.ids[AntType.KARGAR.value] = []
            id_msgs = [msg.text for msg in self.game.chatBox.allChats if
                       msg.text.startswith("id")]

        for m in id_msgs:
            msg_type = int(m[2])
            msg_id = int(m[3:])
            if msg_id not in AI.ids[0] and msg_id not in AI.ids[1]:
                AI.ids[msg_type].append(msg_id)

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
            return -1, -1

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
                    AI.state = WorkerState.InitCollecting
                    m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
                elif AI.id == 2:
                    AI.state = WorkerState.InitCollecting
                    if self.pos[0] < self.pos[1]:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[1])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[2])
                else:
                    AI.state = WorkerState.InitExploring
                    if self.game_round % 2 == 1:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[0])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[0])
                print("left-up region : ", m)
            else:
                # left-down region
                if AI.id == 1 or AI.id == 2:
                    AI.state = WorkerState.InitCollecting
                    m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
                elif AI.id == 3:
                    AI.state = WorkerState.InitExploring
                    if self.pos[0] < self.h - self.pos[1]:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[3])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[2])
                else:
                    AI.state = WorkerState.InitExploring
                    if self.game_round % 2 == 1:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[1])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[1])
                print("left-down region : ", m)
        else:
            if self.game.baseY < (self.game.mapHeight / 2):
                # right-up region
                if AI.id == 3 or AI.id == 4:
                    AI.state = WorkerState.InitCollecting
                    m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
                elif AI.id == 2:
                    AI.state = WorkerState.InitCollecting
                    if self.w - self.pos[0] < self.pos[1]:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[1])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[0])
                else:
                    AI.state = WorkerState.InitExploring
                    if self.game_round % 2 == 1:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[2])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[2])
                print("right-up region : ", m)
            else:
                # right-down region
                if AI.id == 2 or AI.id == 3:
                    AI.state = WorkerState.InitCollecting
                    m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
                elif AI.id == 1:
                    AI.state = WorkerState.InitCollecting
                    if self.w - self.pos[0] < self.h - self.pos[1]:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[3])
                    else:
                        m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[0])
                else:
                    AI.state = WorkerState.InitExploring
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

    def has_resource_in_own_map(self, res_type: int, res_num=10):
        own_map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
        for p in self.found_history:
            own_map.nodes[p] = AI.map.nodes[p]
        if res_type == ResourceType.BREAD:
            if own_map.total_bread_number() >= res_num:
                return res_type
        elif res_type == ResourceType.GRASS.value:
            if own_map.total_grass_number() >= res_num:
                return res_type
        elif own_map.total_bread_number() >= res_num:
            return ResourceType.BREAD.value
        elif own_map.total_grass_number() >= res_num:
            return ResourceType.GRASS.value
        else:
            return None

    def turn(self) -> (str, int, int):
        print("ROUND START!")
        self.update_ids_from_chat_box()

        if AI.game_round == 2:
            prev_id = AI.id
            AI.id = sorted(AI.ids[self.game.ant.antType]).index(AI.id) + 1
            AI.ids[0] = [x for x in range(1, len(AI.ids[0]) + 1)]
            AI.ids[1] = [x for x in range(1, len(AI.ids[1]) + 1)]
            AI.latest_pos[AI.id] = AI.latest_pos[prev_id]

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
            if AI.game_round > 2:
                self.make_id(min_id=INIT_ANTS_NUM + 1)
            elif AI.game_round == 1:
                self.make_id()
            self.send_id()
            AI.latest_pos[AI.id] = ((-1, -1), -1)

        self.pos = (self.game.ant.currentX, self.game.ant.currentY)
        self.search_neighbors()
        self.update_map_from_neighbors()
        self.update_map_from_chat_box()

        print("known cells", [k for k, v in AI.map.nodes.items() if v.discovered])
        print("history", AI.found_history)

        if AI.life_cycle > 1:
            self.encoded_neighbors = encode_graph_nodes(self.pos,
                                                        self.new_neighbors,
                                                        AI.w, AI.h,
                                                        self.game.viewDistance,
                                                        AI.id)
            # TODO not discovered = guess node
            self.message = self.encoded_neighbors
            self.value = MESSAGE_VALUE["map"]

        if AI.game_round == 1:
            self.direction = Direction.get_random_direction()

        elif self.game.ant.antType == AntType.KARGAR.value:
            print("res:", self.game.ant.currentResource.type)
            if AI.id <= Utils.INIT_ANTS_NUM:
                if AI.state == WorkerState.InitExploring:
                    self.direction = self.get_init_ant_final_move()
                elif AI.state == WorkerState.Null or AI.state == WorkerState.InitCollecting:
                    if self.game.ant.currentResource.type == ResourceType.BREAD:
                        if self.has_resource_in_own_map(ResourceType.BREAD.value, self.game.ant.currentResource.value)\
                                == ResourceType.BREAD:
                            self.direction, AI.last_name_of_object = get_tsp_first_move(
                                src_pos=self.pos,
                                dest_pos=AI.map.base_pos,
                                name_of_object=AI.last_name_of_object,
                                graph=AI.map,
                                limit=get_limit(
                                    bread_min=GameConfig.generate_kargar,
                                    grass_min=math.inf
                                ),
                                number_of_object=get_number_of_object(self.game.ant.currentResource),
                            )
                        else:
                            self.direction = self.get_init_ant_final_move()
                    elif self.game.ant.currentResource.type == ResourceType.GRASS:
                        if self.has_resource_in_own_map(ResourceType.GRASS.value, self.game.ant.currentResource.value)\
                                == ResourceType.GRASS:
                            self.direction, AI.last_name_of_object = get_tsp_first_move(
                                src_pos=self.pos,
                                dest_pos=AI.map.base_pos,
                                name_of_object=AI.last_name_of_object,
                                graph=AI.map,
                                limit=get_limit(
                                    bread_min=math.inf,
                                    grass_min=GameConfig.generate_sarbaaz
                                ),
                                number_of_object=get_number_of_object(self.game.ant.currentResource),
                            )
                        else:
                            self.direction = self.get_init_ant_final_move()
                    elif self.has_resource_in_own_map(2, self.game.ant.currentResource.value)\
                            == ResourceType.BREAD:
                        self.direction, AI.last_name_of_object = get_tsp_first_move(
                            src_pos=self.pos,
                            dest_pos=AI.map.base_pos,
                            name_of_object=AI.last_name_of_object,
                            graph=AI.map,
                            limit=get_limit(
                                bread_min=GameConfig.generate_kargar,
                                grass_min=0
                            ),
                            number_of_object=get_number_of_object(self.game.ant.currentResource),
                        )
                    elif self.has_resource_in_own_map(2, self.game.ant.currentResource.value)\
                            == ResourceType.GRASS:
                        self.direction, AI.last_name_of_object = get_tsp_first_move(
                            src_pos=self.pos,
                            dest_pos=AI.map.base_pos,
                            name_of_object=AI.last_name_of_object,
                            graph=AI.map,
                            limit=get_limit(
                                bread_min=0,
                                grass_min=GameConfig.generate_sarbaaz
                            ),
                            number_of_object=get_number_of_object(self.game.ant.currentResource),
                        )
                    else:
                        self.direction = self.get_init_ant_final_move()

            else:
                if AI.state == WorkerState.Null:
                    self.determine_state()

                if AI.state == WorkerState.Exploring:
                    self.direction = self.explore()
                elif AI.state == WorkerState.BreadOnly:
                    # TODO based on tsp
                    pass
                elif AI.state == WorkerState.GrassOnly:
                    # TODO based on tsp
                    pass
                else:
                    # first move
                    self.direction = Direction.get_random_direction()

            # todo: Delete this, this is test
            AI.last_name_of_object = AI.last_name_of_object or random.choice(['bread', 'grass'])

            if self.game_round > 5:
                x, AI.last_name_of_object = get_tsp_first_move(
                    src_pos=self.pos,
                    dest_pos=AI.map.base_pos,
                    name_of_object=AI.last_name_of_object,
                    graph=AI.map,
                    limit=get_limit(bread_min=2, grass_min=2),
                    number_of_object=get_number_of_object(self.game.ant.currentResource),
                )
                self.direction = x
        elif self.game.ant.antType == AntType.SARBAAZ.value:
            # todo sarbaz move
            self.value = 5
            self.direction = Direction.get_random_direction()

        print("turn", AI.game_round, "id", AI.id, "pos", self.pos,
              "state", AI.state, "dir", Direction.get_string(self.direction))

        AI.latest_pos[AI.id] = (self.pos, AI.game_round)
        AI.game_round += 1
        AI.life_cycle += 1
        return self.message, self.value, self.direction

    def determine_state(self):
        # TODO discuss the logic and improve
        AI.state = WorkerState.Exploring
        # total_grass = sum([v.grass for k, v in AI.map.items()])
        # total_bread = sum([v.bread for k, v in AI.map.items()])
        # diff = total_grass - total_bread
        # if -20 <= diff <= 20 or diff >= 30:
        #     AI.state = WorkerState.GrassOnly
        # elif diff <= -30:
        #     AI.state = WorkerState.BreadOnly
        # else:
        #     AI.state = WorkerState.Exploring

    def explore(self):
        # second version
        size = 4
        while self.is_radius_fully_discovered(size):
            size += 1

        # right, up, left, down
        scores = self.calculate_score(size)
        print("scores, right up left down", scores)
        # TODO add the extra step when two sides have the same scores
        d = [(1, 0), (0, -1), (-1, 0), (0, 1)]
        possible_pos = [fix(tuple(map(sum, zip(self.pos, dd))), AI.w, AI.h)
                        for dd in d]
        same_score_indices = [i + 1 for i, s in enumerate(scores)
                              if s == max(scores) and
                              possible_pos[i] != AI.latest_pos[AI.id][0]]
        return random.choice(same_score_indices) if same_score_indices else \
            scores.index(max(scores)) + 1

        # first version
        # # right -> up -> left -> down
        # points = [fix((self.pos[0] + 1, self.pos[1]), AI.w, AI.h),
        #           fix((self.pos[0], self.pos[1] + 1), AI.w, AI.h),
        #           fix((self.pos[0] - 1, self.pos[1]), AI.w, AI.h),
        #           fix((self.pos[0], self.pos[1] - 1), AI.w, AI.h)]
        # num_non_discovered = []
        # for p in points:
        #     new_positions = get_view_distance_neighbors(p, AI.w, AI.h, self.game.ant.viewDistance)
        #     n = sum([pos for pos in new_positions if
        #              not AI.map.nodes[pos].discovered])
        #     num_non_discovered.append(n)
        #
        # if num_non_discovered.count(max(num_non_discovered)) == 1:
        #     return num_non_discovered.index(max(num_non_discovered)) + 1
        #
        # # do it for all the points in the radius
        # self.total_non_discovered_points()

    def is_radius_fully_discovered(self, size):
        for i in range(self.pos[0] - size, self.pos[0] + size + 1):
            for j in range(self.pos[1] - size, self.pos[1] + size + 1):
                pos = tuple(map(sum, zip(self.pos, (i, j))))
                pos = fix(pos, AI.w, AI.h)
                if not AI.map.nodes[pos].discovered:
                    return False
        return True

    def calculate_score(self, size):
        # right -> up -> left -> down
        d = [[(0, -size), (size, size)],
             [(-size, -size), (size, 0)],
             [(-size, -size), (0, size)],
             [(-size, 0), (size, size)]]
        scores = [0, 0, 0, 0]
        # calculate the base scores based on number of non-discovered cells
        for k, dd in enumerate(d):
            start = tuple(map(sum, zip(self.pos, dd[0])))
            finish = tuple(map(sum, zip(self.pos, dd[1])))
            for i in range(start[0], finish[0] + 1):
                for j in range(start[1], finish[1] + 1):
                    pos = fix((i, j), AI.w, AI.h)
                    if not AI.map.nodes[pos].discovered:
                        scores[k] += 1
                    if AI.map.nodes[pos].discovered and pos != self.pos:
                        scores[k] -= 1
                        scores[k] -= int(AI.map.nodes[pos].ally_workers > 0)

        # remove a direction's score if we are facing a wall
        # based on path existence (check 3 neighbor walls)
        # right -> up -> left -> down
        d = [(1, 0), (0, -1), (-1, 0), (0, 1)]
        for i, dd in enumerate(d):
            pos = tuple(map(sum, zip(self.pos, dd)))
            pos = fix(pos, AI.w, AI.h)
            if AI.map.nodes[pos].discovered and AI.map.nodes[pos].wall:
                scores[(i + 1) % 4] = scores[i] if scores[(i + 1) % 4] != -500 else -500
                scores[(i + 3) % 4] = scores[i] if scores[(i + 3) % 4] != -500 else -500
                scores[i] = -500
            elif not AI.map.nodes[pos].discovered and AI.map.nodes[pos].wall:
                print("HUGE MOTHERFUCKING ERROR!")

        return scores

    # first version
    # def total_non_discovered_points(self, src, dest):
    #     paths = shortest_path(src, dest, AI.w, AI.h)
    #     num_discovered = [0] * len(paths)
    #     for i, path in enumerate(paths):
    #         temp_map = copy.deepcopy(AI.map)
    #         for pos in path:
    #             new_positions = get_view_distance_neighbors(pos, AI.w, AI.h, self.game.ant.viewDistance)
    #             n = sum([p for p in new_positions if not temp_map[p].discovered])
    #             num_discovered[i] += n
    #             for p in new_positions:
    #                 temp_map[p].discovered = True
