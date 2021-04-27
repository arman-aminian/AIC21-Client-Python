import copy
from Model import *
from Utils import *
from graph import *
from message.map_message import *
from message.possible_base_message import *
from tsp_generator import get_limit, get_number_of_object
from state import *
from BT import *


def print_with_debug(*args, f, debug=False):
    if debug and f is not None:
        print(*args, file=f)


class AI:
    game_round = -1
    life_cycle = 1
    map = None
    w, h = -1, -1
    first_id = 0
    id = 0
    ids = {}
    latest_pos = {}
    found_history = set()
    worker_state = WorkerState.Null
    soldier_state = SoldierState.Null
    soldier_init_random_dir = None
    last_name_of_object = None
    possible_base_cells = []
    soldier_targets = []
    prev_round_resource = 0
    path_neighbors_history = []
    own_cells_history = []
    latest_map = None
    cell_target = None
    attack_dir = None
    out_file = None
    output_path = "/media/mh/New Volume/AIC21-Client-Python/output/"
    debug = False
    born_game_round = -1
    prev_hp = 0
    prev_es = 0

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
        self.shot = False

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
                    if a.antTeam == AntTeam.ALLIED.value:
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
        if AI.life_cycle > 1:
            self.value = self.determine_value(neighbor_cells, neighbor_nodes)
        AI.found_history.update(set(self.new_neighbors.keys()))

    def determine_value(self, neighbor_cells, neighbor_nodes):
        for n in neighbor_cells:
            if n.type == CellType.BASE.value and (n.x, n.y) != AI.map.base_pos and \
                    AI.map.enemy_base_pos is None:
                AI.map.enemy_base_pos = (n.x, n.y)
                return VALUES["enemy_base"]

        sum_bg = 0
        for n in neighbor_nodes:
            if not AI.map.nodes[n.pos].discovered and \
                    (n.bread > 0 or n.grass > 0):
                sum_bg += n.bread
                sum_bg += n.grass
        if sum_bg > 0:
            return VALUES["bg"] + sum_bg

        total_disc = 0
        for n in neighbor_nodes:
            if not AI.map.nodes[n.pos].discovered:
                total_disc += 1
        if total_disc >= 5:
            return VALUES["disc_gt_5"] + total_disc

        total_soldiers = 0
        for n in neighbor_nodes:
            if AI.map.nodes[n.pos].enemy_soldiers < n.enemy_soldiers:
                total_soldiers += 1
        if total_soldiers > 0:
            return VALUES["es"] + total_soldiers

        if 0 < total_disc < 5:
            return VALUES["disc_lt_5"] + total_disc

        if self.pos in self.new_neighbors.keys():
            if self.new_neighbors[self.pos].bread > AI.map.nodes[self.pos].bread \
                    or self.new_neighbors[self.pos].grass > AI.map.nodes[self.pos].grass:
                return VALUES["bg_add"] + abs(self.new_neighbors[self.pos].bread - AI.map.nodes[self.pos].bread) + \
                       abs(self.new_neighbors[self.pos].grass - AI.map.nodes[self.pos].grass)

        if self.game.ant.antType == AntType.KARGAR.value and self.pos in self.new_neighbors.keys():
            if self.new_neighbors[self.pos].bread < AI.map.nodes[self.pos].bread \
                    or self.new_neighbors[self.pos].grass < AI.map.nodes[self.pos].grass:
                if self.game.ant.currentResource.value > AI.prev_round_resource:
                    return VALUES["bg_sub"] + abs(self.new_neighbors[self.pos].bread - AI.map.nodes[self.pos].bread) + \
                       abs(self.new_neighbors[self.pos].grass - AI.map.nodes[self.pos].grass)

        return VALUES["none"]

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
            ant_id, ant_pos, ant_dir, \
            ant_shot, nodes, enemy_base_pos = decode_nodes(m.text,
                                                           AI.w, AI.h,
                                                           self.game.ant.viewDistance)
            AI.latest_pos[ant_id] = (ant_pos, m.turn)
            for pos, n in nodes.items():
                if n != AI.map.nodes[pos]:
                    AI.map.nodes[pos] = copy.deepcopy(n)

            if enemy_base_pos is not None:
                AI.map.enemy_base_pos = enemy_base_pos

            if ant_shot:
                target = add_pos_dir(ant_pos, ant_dir, AI.w, AI.h)
                AI.soldier_targets.append(target)

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
        self.value = VALUES["id"]

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

    def fix_pos(self, pos):
        return ((pos[0] + self.game.mapWidth) % self.game.mapWidth,
                (pos[1] + self.game.mapHeight) % self.game.mapHeight)

    def is_road_to_wall(self, move: int):
        for i in [1, 2]:
            tf = True
            for j in [-1, 0, 1]:
                if move == 1:
                    p = (self.pos[0] + i, self.pos[1] + j)
                elif move == 2:
                    p = (self.pos[0] + j, self.pos[1] - i)
                elif move == 3:
                    p = (self.pos[0] - i, self.pos[1] + j)
                else:
                    p = (self.pos[0] + j, self.pos[1] + i)
                node = AI.map.nodes[self.fix_pos(pos=p)]
                if not node.wall:
                    tf = False
            if tf:
                return True
        return False

    def get_init_ants_next_move(self, preferred_moves) -> int:
        for m in preferred_moves:
            if (not self.is_road_to_wall(m)) and (self.get_next_pos(self.pos, m) != AI.latest_pos[AI.id][0]):
                for j in [0, 1, -1]:
                    if m == 1:
                        p = (self.pos[0] + 2, self.pos[1] + j)
                    elif m == 2:
                        p = (self.pos[0] + j, self.pos[1] - 2)
                    elif m == 3:
                        p = (self.pos[0] - 2, self.pos[1] + j)
                    else:
                        p = (self.pos[0] + j, self.pos[1] + 2)
                    # own_map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
                    # for p in self.found_history:
                    #     own_map.nodes[p] = AI.map.nodes[p]
                    path = AI.map.get_path_with_max_length(AI.map.nodes[self.pos], AI.map.nodes[self.fix_pos(p)], 2)
                    if path is not None:
                        return Direction.get_value(AI.map.step(self.pos, path[0].pos))

        print_with_debug("error on get_init_ants_next_move", f=AI.out_file)
        return Direction.get_random_direction()

    def get_init_ant_explore_move(self):
        AI.worker_state = WorkerState.InitCollecting
        if AI.id <= Utils.INIT_ANTS_NUM:
            m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
        else:
            m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id % 4])

        if m < 5:
            return m
        else:
            print_with_debug("something went wrong, init ants move :", m, "from id:", AI.id, f=AI.out_file)
            return Direction.get_random_direction()

    # @time_measure
    def get_init_ant_collect_move(self):
        # own_map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
        # for p in self.found_history:
        #     own_map.nodes[p] = AI.map.nodes[p]
        if self.game.ant.currentResource.type == ResourceType.BREAD.value:
            if self.has_resource_in_map(ResourceType.BREAD.value,
                                        WORKER_MAX_CARRYING_RESOURCE_AMOUNT - self.game.ant.currentResource.value) \
                    == ResourceType.BREAD.value:
                print_with_debug("state has res to find", f=AI.out_file)
                m, AI.last_name_of_object, d = AI.map.get_resource_best_move(
                    src_pos=self.pos,
                    dest_pos=AI.map.base_pos,
                    name_of_object='bread',
                    limit=get_limit(
                        bread_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT,
                        grass_min=math.inf
                    ),
                    number_of_object=get_number_of_object(self.game.ant.currentResource),
                )
            else:
                print_with_debug("state has not other res", f=AI.out_file)
                path = AI.map.get_path(AI.map.nodes[self.pos], AI.map.nodes[AI.map.base_pos])
                return Direction.get_value(AI.map.step(self.pos, path[0].pos))
        elif self.game.ant.currentResource.type == ResourceType.GRASS.value:
            if self.game.ant.currentResource.value == WORKER_MAX_CARRYING_RESOURCE_AMOUNT:
                path = AI.map.get_path(AI.map.nodes[self.pos], AI.map.nodes[AI.map.base_pos])
                return Direction.get_value(AI.map.step(self.pos, path[0].pos))
            if self.has_resource_in_map(ResourceType.GRASS.value,
                                        WORKER_MAX_CARRYING_RESOURCE_AMOUNT - self.game.ant.currentResource.value) \
                    == ResourceType.GRASS.value:
                print_with_debug("state has res to find", f=AI.out_file)
                m, AI.last_name_of_object, d = AI.map.get_resource_best_move(
                    src_pos=self.pos,
                    dest_pos=AI.map.base_pos,
                    name_of_object='grass',
                    limit=get_limit(
                        bread_min=math.inf,
                        grass_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT
                    ),
                    number_of_object=get_number_of_object(self.game.ant.currentResource),
                )
            else:
                print_with_debug("state has not to find", f=AI.out_file)
                path = AI.map.get_path(AI.map.nodes[self.pos], AI.map.nodes[AI.map.base_pos])
                return Direction.get_value(AI.map.step(self.pos, path[0].pos))
        else:
            print_with_debug("ANT isn't hold anything", f=AI.out_file)
            grass_dir, AI.last_name_of_object, grass_dis = AI.map.get_resource_best_move(
                src_pos=self.pos,
                dest_pos=AI.map.base_pos,
                name_of_object='grass',
                limit=get_limit(
                    bread_min=math.inf,
                    grass_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT
                ),
                number_of_object=get_number_of_object(self.game.ant.currentResource),
            )
            bread_dir, AI.last_name_of_object, bread_dis = AI.map.get_resource_best_move(
                src_pos=self.pos,
                dest_pos=AI.map.base_pos,
                name_of_object='bread',
                limit=get_limit(
                    bread_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT,
                    grass_min=math.inf
                ),
                number_of_object=get_number_of_object(
                    self.game.ant.currentResource),
            )
            print_with_debug("grass_dir:", grass_dir, f=AI.out_file)
            print_with_debug("grass_dis:", grass_dis, f=AI.out_file)
            print_with_debug("bread_dir:", bread_dir, f=AI.out_file)
            print_with_debug("bread_dis:", bread_dis, f=AI.out_file)
            if grass_dis <= bread_dis and grass_dis != math.inf:
                m = grass_dir
            elif bread_dir is not None:
                m = bread_dir
            else:
                m = self.get_init_ant_explore_move()
        return m

    def has_resource_in_map(self, res_type: int, res_num=10):
        own_map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
        for p in self.found_history:
            own_map.nodes[p] = AI.map.nodes[p]
        print_with_debug("total bread num:", own_map.total_bread_number(), f=AI.out_file)
        print_with_debug("total grass num:", own_map.total_grass_number(), f=AI.out_file)
        if res_type == ResourceType.BREAD.value:
            if AI.map.total_bread_number() >= res_num:
                return res_type
        elif res_type == ResourceType.GRASS.value:
            if AI.map.total_grass_number() >= res_num:
                return res_type
        elif AI.map.total_bread_number() >= res_num:
            return ResourceType.BREAD.value
        elif AI.map.total_grass_number() >= res_num:
            return ResourceType.GRASS.value
        else:
            return None

    # @time_measure
    @handle_exception
    def turn(self) -> (str, int, int):
        if AI.debug and AI.life_cycle > 2 and (AI.id in AI.ids[0] or AI.id in AI.ids[1]):
            t = "soldier" if self.game.ant.antType == AntType.SARBAAZ.value else "worker"
            if AI.id in range(1, INIT_ANTS_NUM + 1, 1):
                AI.out_file = open(AI.output_path + t + '_' + str(AI.first_id) + '_' + str(AI.born_game_round) + ".txt", "a+")
            else:
                AI.out_file = open(AI.output_path + t + '_' + str(AI.id) + '_' + str(AI.born_game_round) + ".txt", "a+")
        
        print_with_debug("*************************************************", f=AI.out_file)
        print_with_debug("ROUND START!", f=AI.out_file)
        print_with_debug("ROUND START!", f=AI.out_file)
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
            AI.latest_map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
            if AI.game_round > 2:
                self.make_id(min_id=INIT_ANTS_NUM + 1)
            elif AI.game_round == 1:
                self.make_id()
                AI.first_id = AI.id
            self.send_id()
            AI.latest_pos[AI.id] = ((-1, -1), -1)
            AI.born_game_round = AI.game_round - 1

        for k, v in AI.map.nodes.items():
            AI.latest_map.nodes[k].wall = v.wall
            AI.latest_map.nodes[k].bread = v.bread
            AI.latest_map.nodes[k].discovered = v.discovered

        self.pos = (self.game.ant.currentX, self.game.ant.currentY)
        print_with_debug("ROUND:", self.game_round, f=AI.out_file)
        print_with_debug("POS:", self.pos, f=AI.out_file)
        AI.own_cells_history.append(self.pos)
        self.search_neighbors()
        self.update_map_from_chat_box()
        self.update_map_from_neighbors()
        if self.game.ant.antType == AntType.SARBAAZ.value:
            self.soldier_update_history()
            print_with_debug("soldier history", AI.path_neighbors_history, f=AI.out_file)
        
        if AI.game_round > 5:
            self.check_for_base()

        if AI.life_cycle > 1 and AI.map.enemy_base_pos is not None and self.game.ant.antType == AntType.SARBAAZ.value:
            AI.soldier_state = SoldierState.PreparingForAttack
            if AI.cell_target is None:
                AI.cell_target = AI.map.enemy_base_pos
        self.check_for_possible_base_cells()

        print_with_debug("known cells", [k for k, v in AI.map.nodes.items() if v.discovered], f=AI.out_file)
        print_with_debug("found history", AI.found_history, f=AI.out_file)

        if AI.game_round == 1:
            AI.worker_state = WorkerState.InitExploring if self.game.ant.antType == AntType.KARGAR.value else WorkerState.Null
            self.direction = Direction.get_random_direction()

        elif self.game.ant.antType == AntType.KARGAR.value:
            if self.game.ant.currentResource.value is not None and self.game.ant.currentResource.value >= (WORKER_MAX_CARRYING_RESOURCE_AMOUNT / 2):
                print_with_debug("worker has max carrying resources amount => back to base with bfs", f=AI.out_file)
                path = AI.map.get_path(AI.map.nodes[self.pos], AI.map.nodes[AI.map.base_pos])
                self.direction = Direction.get_value(AI.map.step(self.pos, path[0].pos))
            else:
                if AI.id <= Utils.INIT_ANTS_NUM:
                    print_with_debug("INIT ANT", f=AI.out_file)
                    if AI.worker_state == WorkerState.InitExploring:
                        self.direction = self.get_init_ant_explore_move()
                    elif AI.worker_state == WorkerState.Null or AI.worker_state == WorkerState.InitCollecting:
                        self.direction = self.get_init_ant_collect_move()
                else:
                    print_with_debug("NEW ANT", f=AI.out_file)
                    if AI.worker_state == WorkerState.Null:
                        self.determine_worker_state()

                    # todo delete
                    # if AI.worker_state == WorkerState.Exploring:
                    #     self.direction = self.worker_explore()
                    # else:
                    if self.has_resource_in_map(2, 1) is None:
                        self.direction = self.get_init_ant_explore_move()
                    elif self.game.ant.currentResource.type == ResourceType.BREAD.value:
                        print_with_debug("ANT is holding bread", f=AI.out_file)
                        if self.has_resource_in_map(ResourceType.BREAD.value,
                                                    WORKER_MAX_CARRYING_RESOURCE_AMOUNT - self.game.ant.currentResource.value) \
                                == ResourceType.BREAD.value:
                            print_with_debug("state has bread res to find", f=AI.out_file)
                            self.direction, AI.last_name_of_object, d = AI.map.get_resource_best_move(
                                src_pos=self.pos,
                                dest_pos=AI.map.base_pos,
                                name_of_object='bread',
                                limit=get_limit(
                                    bread_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT,
                                    grass_min=math.inf
                                ),
                                number_of_object=get_number_of_object(self.game.ant.currentResource),
                            )
                        else:
                            print_with_debug("state has not other res", f=AI.out_file)
                            path = AI.map.get_path(AI.map.nodes[self.pos], AI.map.nodes[AI.map.base_pos])
                            self.direction = Direction.get_value(AI.map.step(self.pos, path[0].pos))
                    elif self.game.ant.currentResource.type == ResourceType.GRASS.value:
                        print_with_debug("ANT is holding grass", f=AI.out_file)
                        if self.has_resource_in_map(ResourceType.GRASS.value,
                                                    WORKER_MAX_CARRYING_RESOURCE_AMOUNT - self.game.ant.currentResource.value) \
                                == ResourceType.GRASS.value:
                            print_with_debug("state has grass res to find", f=AI.out_file)
                            self.direction, AI.last_name_of_object, d = AI.map.get_resource_best_move(
                                src_pos=self.pos,
                                dest_pos=AI.map.base_pos,
                                name_of_object='grass',
                                limit=get_limit(
                                    bread_min=math.inf,
                                    grass_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT
                                ),
                                number_of_object=get_number_of_object(self.game.ant.currentResource),
                            )
                        else:
                            print_with_debug("state has not to find", f=AI.out_file)
                            path = AI.map.get_path(AI.map.nodes[self.pos], AI.map.nodes[AI.map.base_pos])
                            self.direction = Direction.get_value(AI.map.step(self.pos, path[0].pos))
                    else:
                        print_with_debug("ANT isn't hold anything", f=AI.out_file)
                        grass_dir, AI.last_name_of_object, grass_dis = AI.map.get_resource_best_move(
                            src_pos=self.pos,
                            dest_pos=AI.map.base_pos,
                            name_of_object='grass',
                            limit=get_limit(
                                bread_min=math.inf,
                                grass_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT
                            ),
                            number_of_object=get_number_of_object(self.game.ant.currentResource),
                        )
                        bread_dir, AI.last_name_of_object, bread_dis = AI.map.get_resource_best_move(
                            src_pos=self.pos,
                            dest_pos=AI.map.base_pos,
                            name_of_object='bread',
                            limit=get_limit(
                                bread_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT,
                                grass_min=math.inf
                            ),
                            number_of_object=get_number_of_object(
                                self.game.ant.currentResource),
                        )
                        print_with_debug("grass_dir:", grass_dir, f=AI.out_file)
                        print_with_debug("grass_dis:", grass_dis, f=AI.out_file)
                        print_with_debug("bread_dir:", bread_dir, f=AI.out_file)
                        print_with_debug("bread_dis:", bread_dis, f=AI.out_file)
                        if (grass_dir is not None and bread_dir is None) or grass_dis <= bread_dis:
                            self.direction = grass_dir
                        elif grass_dir is None and bread_dir is not None:
                            self.direction = bread_dir
                        else:
                            self.direction = self.get_init_ant_explore_move()

                    if self.direction == 0 or self.direction is None:
                        print_with_debug("new ants at the end:", self.direction, f=AI.out_file)
                        print_with_debug("=> move like init ant explore", f=AI.out_file)
                        self.direction = self.get_init_ant_explore_move()

        elif self.game.ant.antType == AntType.SARBAAZ.value:
            # self.direction = Direction.get_random_direction()
            # if AI.soldier_state == SoldierState.Null:
            #     self.determine_soldier_state()

            # if AI.soldier_state == SoldierState.FirstFewRounds:
            #     self.direction = AI.soldier_init_random_dir

            if AI.life_cycle == 1:
                self.direction = Direction.get_random_direction()
            else:
                if AI.soldier_state == SoldierState.WaitingForComrades:
                    ally_s = len(
                        [a for a in self.game.ant.getMapRelativeCell(0, 0).ants
                         if a.antType == AntType.SARBAAZ.value and a.antTeam == self.game.ant.antTeam])
                    if ally_s > 2 or abs(MAX_TURN_COUNT - AI.game_round) <= 30:
                        AI.soldier_state = SoldierState.PreparingForAttack
                    else:
                        self.direction = Direction.CENTER.value

                if AI.soldier_state == SoldierState.PreparingForAttack:
                    ally_s = len(
                        [a for a in self.game.ant.getMapRelativeCell(0, 0).ants if a.antType == AntType.SARBAAZ.value and a.antTeam == self.game.ant.antTeam])
                    if self.pos == AI.cell_target and (ally_s > 2 or abs(MAX_TURN_COUNT - AI.game_round) <= 10):
                        AI.soldier_state = SoldierState.Attacking
                    elif AI.cell_target is not None and self.pos != AI.cell_target:
                        self.direction = self.get_first_move_to_target(self.pos, AI.cell_target)
                    elif self.pos == AI.cell_target and ally_s <= 2:
                        self.direction = Direction.CENTER.value
                    elif AI.cell_target is None and AI.map.enemy_base_pos is not None:
                        self.direction = Direction.get_random_direction()

                if AI.soldier_state == SoldierState.HasBeenShot:
                    self.direction = Direction.CENTER.value
                    ally_s = len(
                        [a for a in self.game.ant.getMapRelativeCell(0, 0).ants
                         if a.antType == AntType.SARBAAZ.value and a.antTeam == self.game.ant.antTeam])
                    if ally_s > 2:
                        self.soldier_state = SoldierState.Attacking

                if AI.soldier_state == SoldierState.Attacking:
                    # TODO COMPLETE THIS
                    if AI.map.enemy_base_pos is not None:
                        self.direction = self.get_first_move_to_target(self.pos, AI.map.enemy_base_pos)
                    else:
                        self.direction = solve_bt(AI.map, self.pos, max_distance=7)
                        if self.direction == Direction.CENTER.value:
                            print_with_debug("CENTER VALUE FROM BT", f=AI.out_file)
                            self.direction = AI.attack_dir

                if AI.soldier_state == SoldierState.CellTargetFound:
                    if self.pos == AI.cell_target:
                        AI.soldier_state = SoldierState.Null
                    elif AI.cell_target is not None:
                        self.direction = self.get_first_move_to_target(self.pos, AI.cell_target)
                    else:
                        AI.soldier_state = SoldierState.Null

                if AI.game_round < 175 and AI.soldier_state == SoldierState.Null:
                    self.direction = self.get_soldier_first_move_to_discover()
                    if AI.cell_target is not None:
                        AI.soldier_state = SoldierState.CellTargetFound
                    print_with_debug(f'in soldier discover: pos = {self.pos}, direction = {self.direction}', f=AI.out_file)

                elif AI.game_round >= 175 and AI.soldier_state == SoldierState.Null:
                    self.direction = self.get_soldier_first_node_to_support()
                    print_with_debug(f'in soldier support: pos = {self.pos}, direction = {self.direction}', f=AI.out_file)

        if AI.life_cycle > 1 and (not self.shot or self.value == VALUES["enemy_base"]):
            if self.direction is None:
                print_with_debug("turn", AI.game_round, "id", AI.id, "pos", self.pos,
                                 "worker state", AI.worker_state,
                                 "soldier state", AI.soldier_state,
                                 "map value", self.value,
                                 "enemy base pos", AI.map.enemy_base_pos,
                                 "soldier target cell", AI.cell_target, f=AI.out_file)
            self.encoded_neighbors = encode_graph_nodes(self.pos,
                                                        self.new_neighbors,
                                                        AI.w, AI.h,
                                                        self.game.viewDistance,
                                                        AI.id, self.direction,
                                                        self.shot,
                                                        AI.map.enemy_base_pos)
            self.message = self.encoded_neighbors
        elif AI.life_cycle > 1 and self.shot and (AI.soldier_state == SoldierState.Null or AI.soldier_state == SoldierState.CellTargetFound):
            possible_cells = Utils.get_view_distance_neighbors(self.pos, AI.w,
                                                               AI.h, 6, True)
            possible_cells = [p for p in possible_cells if
                              p not in AI.path_neighbors_history]
            AI.possible_base_cells = list(set(AI.possible_base_cells).
                                          intersection(possible_cells))
            print_with_debug("tell them", AI.latest_pos[AI.id][0], possible_cells, f=AI.out_file)
            self.message = encode_possible_cells(AI.id, self.pos,
                                                 AI.own_cells_history[-3],
                                                 AI.w, AI.h, possible_cells)
            print_with_debug(self.message, f=AI.out_file)
            self.direction = solve_bt(AI.map, self.pos, max_distance=5)
            AI.soldier_state = SoldierState.HasBeenShot
            self.value = VALUES["shot"]

        print_with_debug("turn", AI.game_round, "id", AI.id, "pos", self.pos,
                         "worker state", AI.worker_state,
                         "soldier state", AI.soldier_state,
                         "dir", Direction.get_string(self.direction),
                         "map value", self.value,
                         "enemy base pos", AI.map.enemy_base_pos,
                         "soldier target cell", AI.cell_target, f=AI.out_file)

        AI.latest_pos[AI.id] = (self.pos, AI.game_round)
        AI.game_round += 1
        AI.life_cycle += 1
        AI.prev_round_resource = self.game.ant.currentResource.value
        AI.prev_hp = self.game.ant.health
        AI.prev_es = sum([AI.map.nodes[v].enemy_soldiers for v in get_view_distance_neighbors(self.pos, AI.w, AI.h, self.game.ant.viewDistance)])
        
        if self.game.ant.currentX in range(10, 25):
            self.direction = Direction.RIGHT.value
        
        return self.message, self.value, self.direction

    def determine_worker_state(self):
        # TODO discuss the logic and improve
        # AI.worker_state = WorkerState.Exploring
        total_grass = sum([v.grass for k, v in AI.map.nodes.items()])
        total_bread = sum([v.bread for k, v in AI.map.nodes.items()])
        diff = total_grass - total_bread
        if -20 <= diff <= 20 or diff > 20 or total_bread == 0:
            AI.worker_state = WorkerState.GrassOnly
        elif diff < -20 or total_grass == 0:
            AI.worker_state = WorkerState.BreadOnly
        else:
            AI.worker_state = WorkerState.Exploring

    def worker_explore(self):
        # third version (BT)
        d = solve_bt(AI.map, self.pos)
        return d

        # second version
        # size = 4
        # while self.is_radius_fully_discovered(size):
        #     size += 1
        #
        # # right, up, left, down
        # scores = self.calculate_score(size)
        # print_with_debug("scores, right up left down", scores, f=AI.out_file)
        # # TODO add the extra step when two sides have the same scores
        # d = [(1, 0), (0, -1), (-1, 0), (0, 1)]
        # possible_pos = [fix(tuple(map(sum, zip(self.pos, dd))), AI.w, AI.h)
        #                 for dd in d]
        # same_score_indices = [i + 1 for i, s in enumerate(scores)
        #                       if s == max(scores) and
        #                       possible_pos[i] != AI.latest_pos[AI.id][0]]
        # return random.choice(same_score_indices) if same_score_indices else \
        #     scores.index(max(scores)) + 1

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
                print_with_debug("HUGE MOTHERFUCKING ERROR!", f=AI.out_file)

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

    def determine_soldier_state(self):
        if AI.life_cycle < 5:
            AI.soldier_state = SoldierState.FirstFewRounds
            AI.soldier_init_random_dir = Direction.get_random_direction()

    def check_for_base(self):
        hp = self.game.ant.health
        neighbors = get_view_distance_neighbors(AI.latest_pos[AI.id][0], AI.w, AI.h,
                                                self.game.ant.viewDistance)
        es = sum([AI.map.nodes[v].enemy_soldiers for v in neighbors])
        cond = (hp == AI.prev_hp - BASE_DMG and AI.prev_es == 0) or \
               (hp == AI.prev_hp - BASE_DMG - SOLDIER_DMG and AI.prev_es == 1) or \
               (hp == AI.prev_hp - BASE_DMG - 2 * SOLDIER_DMG and AI.prev_es == 2)
        print_with_debug("HERE IS ES", [AI.map.nodes[v] for v in neighbors if AI.map.nodes[v].enemy_soldiers > 0], f=AI.out_file)
        if cond:
            print_with_debug("YESSSSS I GOT SHOTTTTTTTTTT", f=AI.out_file)
            self.shot = True

    def find_possible_base_cells(self):
        for target in AI.soldier_targets:
            possible_cells = Utils.get_view_distance_neighbors(target, AI.w,
                                                               AI.h, 6, True)
            possible_cells = [p for p in possible_cells if
                              not AI.map.nodes[p].discovered and
                              not AI.map.nodes[p].wall]
            AI.possible_base_cells = list(set(AI.possible_base_cells)
                                          .intersection(possible_cells))
            if not AI.possible_base_cells:
                print_with_debug("HUGE MOTHERFUCKING ERROR!", f=AI.out_file)

    def chosse_best_target(self):
        if len(AI.soldier_targets) == 1:
            return AI.soldier_targets[0]

        if AI.soldier_targets:
            costs = []
            for target in AI.soldier_targets:
                costs.append(len(AI.map.get_path(AI.map.nodes[AI.map.base_pos], AI.map.nodes[target])))
            min_i = AI.soldier_targets.index(min(costs))
            return AI.soldier_targets[min_i]

    def soldier_update_history(self):
        neighbors = get_view_distance_neighbors(self.pos, AI.w, AI.h,
                                                5 if self.shot else 6)
        new_neighbors = [p for p in neighbors if p not in AI.path_neighbors_history]
        AI.path_neighbors_history += new_neighbors

    def check_for_possible_base_cells(self):
        possible_msgs = [msg.text for msg in
                         self.game.chatBox.allChats[-MAX_MESSAGES_PER_TURN:] if
                         msg.text.startswith("s") and
                         msg.turn == AI.game_round - 1]
        if AI.life_cycle == 1:
            possible_msgs = [msg.text for msg in self.game.chatBox.allChats if
                             msg.text.startswith("s")]

        if possible_msgs:
            print_with_debug("I HAVE S MESSAGE HAHAHAHHAA", f=AI.out_file)
            if AI.life_cycle > 1:
                AI.soldier_state = SoldierState.PreparingForAttack
            elif AI.life_cycle == 1:
                AI.soldier_state = SoldierState.WaitingForComrades
            AI.cell_target = None

        targets = []
        for m in possible_msgs:
            # TODO use this info
            ant_id, pos, prev_pos, possible_cells = decode_possible_cells(m, AI.w, AI.h)
            AI.possible_base_cells = list(set(AI.possible_base_cells).
                                          intersection(possible_cells))
            targets.append((prev_pos, pos))

        if targets:
            targets.sort()
            distances = [Utils.manhattan_dist(AI.map.base_pos, t[0], AI.w, AI.h) for t in targets]
            min_i = distances.index(min(distances))
            print_with_debug("HAHAHAHA i had shot msgs", targets, distances, f=AI.out_file)
            AI.cell_target = targets[min_i][0] if AI.cell_target is None else AI.cell_target
            if targets[min_i][0] != targets[min_i][1]:
                AI.attack_dir = self.get_first_move_to_target(targets[min_i][0], targets[min_i][1])
            else:
                AI.attack_dir = Direction.get_random_direction()

    def get_soldier_first_move_to_discover(self):
        move, _ = AI.latest_map.get_first_move_to_discover(AI.map.nodes[self.pos], self.pos, len(AI.ids[self.game.ant.antType]), AI.id, AI.ids[self.game.ant.antType])
        return Direction.get_value(move)

    def get_soldier_first_node_to_support(self):
        return Direction.get_value(
            AI.map.step(self.pos, AI.map.get_best_node_to_support(self.pos))
        )

    # def get_init_ant_explore_move(self):
    #     AI.worker_state = WorkerState.InitCollecting
    #     if self.game.baseX < (self.game.mapWidth / 2):
    #         if self.game.baseY < (self.game.mapHeight / 2):
    #             # left-up region
    #             if AI.id == 1 or AI.id == 4:
    #                 m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
    #             elif AI.id == 2:
    #                 if self.pos[0] < self.pos[1]:
    #                     m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[1])
    #                 else:
    #                     m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[2])
    #             else:
    #                 if self.game_round % 2 == 1:
    #                     m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[0])
    #                 else:
    #                     m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[0])
    #             print_with_debug("left-up region : ", m, f=AI.out_file)
    #         else:
    #             # left-down region
    #             if AI.id == 1 or AI.id == 2:
    #                 m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
    #             elif AI.id == 3:
    #                 if self.pos[0] < self.h - self.pos[1]:
    #                     m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[3])
    #                 else:
    #                     m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[2])
    #             else:
    #                 if self.game_round % 2 == 1:
    #                     m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[1])
    #                 else:
    #                     m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[1])
    #             print_with_debug("left-down region : ", m, f=AI.out_file)
    #     else:
    #         if self.game.baseY < (self.game.mapHeight / 2):
    #             # right-up region
    #             if AI.id == 3 or AI.id == 4:
    #                 m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
    #             elif AI.id == 2:
    #                 if self.w - self.pos[0] < self.pos[1]:
    #                     m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[1])
    #                 else:
    #                     m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[0])
    #             else:
    #                 if self.game_round % 2 == 1:
    #                     m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[2])
    #                 else:
    #                     m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[2])
    #             print_with_debug("right-up region : ", m, f=AI.out_file)
    #         else:
    #             # right-down region
    #             if AI.id == 2 or AI.id == 3:
    #                 m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1])
    #             elif AI.id == 1:
    #                 if self.w - self.pos[0] < self.h - self.pos[1]:
    #                     m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[3])
    #                 else:
    #                     m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[0])
    #             else:
    #                 if self.game_round % 2 == 1:
    #                     m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES1[3])
    #                 else:
    #                     m = self.get_init_ants_next_move(Utils.INIT_CENTER_ANTS_MOVES2[3])
    #             print_with_debug("right-down region : ", m, f=AI.out_file)
    #     if m < 5:
    #         return m
    #     else:
    #         print_with_debug("something went wrong, init ants move :", m, "from id:", AI.id, f=AI.out_file)
    #         return Direction.get_random_direction()

    def get_first_move_to_target(self, src, dest):
        print_with_debug(src, dest, f=AI.out_file)
        print_with_debug(AI.map.get_path(AI.map.nodes[src], AI.map.nodes[dest]), f=AI.out_file)
        return Direction.get_value(
            AI.map.step(src, AI.map.get_path_with_non_discovered(AI.map.nodes[src], AI.map.nodes[dest])[0].pos))
