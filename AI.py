import copy
from Model import *
from Utils import *
from graph import *
from message.map_message import *
from message.possible_base_message import *
from tsp_generator import get_limit, get_number_of_object
from state import *
from BT import *


class AI:
    game_round = -1
    life_cycle = 1
    map = None
    w, h = -1, -1
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
    soldier_path_neighbors_history = []
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
    shot_once = False
    # NEW SHIT
    chosen_near_base_cell_BK = None
    chosen_near_base_cell_BU = None
    near_base_safe_cells = []
    shot_default_dir = None
    first_id = -1
    exploration_target = None

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
        self.visible_bread = []
        self.visible_grass = []

    # @time_measure
    def search_neighbors(self):
        # TODO improve by creating the list of indices instead of all the cells
        ant = self.game.ant
        cells = ant.visibleMap.cells
        neighbor_cells = [j for sub in cells for j in sub if j is not None]
        neighbor_nodes = []
        for n in neighbor_cells:
            w = n.type == CellType.WALL.value
            s = n.type == CellType.SWAMP.value
            t = n.type == CellType.TRAP.value
            if w:
                neighbor_nodes.append(Node((n.x, n.y), True, True))
            elif s:
                neighbor_nodes.append(Node((n.x, n.y), True, False, swamp=True))
            elif t:
                neighbor_nodes.append(Node((n.x, n.y), True, False, trap=True))
            else:
                b = n.resource_value if \
                    n.resource_type == ResourceType.BREAD.value else 0
                g = n.resource_value if \
                    n.resource_type == ResourceType.GRASS.value else 0

                if b > 0 and manhattan_dist(self.pos, (n.x, n.y), *AI.map.dim) <= 3:
                    self.visible_bread.append({'number': b, 'pos': (n.x, n.y)})

                if g > 0 and manhattan_dist(self.pos, (n.x, n.y), *AI.map.dim) <= 3:
                    self.visible_grass.append({'number': g, 'pos': (n.x, n.y)})

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
                neighbor_nodes.append(Node((n.x, n.y), True, False,
                                           bread=b,
                                           grass=g,
                                           ally_workers=aw,
                                           ally_soldiers=ally_s,
                                           enemy_workers=ew,
                                           enemy_soldiers=es))

        self.new_neighbors = {n.pos: n for n in neighbor_nodes if
                              AI.map.nodes[n.pos] != n}
        if AI.life_cycle > 1:
            self.value = self.determine_value(neighbor_cells, neighbor_nodes)
        AI.found_history.update(set(self.new_neighbors.keys()))

    # @time_measure
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

    # @time_measure
    def update_map_from_neighbors(self):
        if not self.new_neighbors:
            return
        # just in case. not really needed
        for pos, n in self.new_neighbors.items():
            AI.map.nodes[pos] = copy.deepcopy(n)

    # @time_measure
    def update_map_from_chat_box(self):
        maps = [msg for msg in
                self.game.chatBox.allChats[-MAX_MESSAGES_PER_TURN:] if '!' in
                msg.text and msg.turn == AI.game_round - 1]
        if AI.life_cycle == 1:
            if AI.born_game_round > MAX_MESSAGES_INIT:
                maps = [msg for msg in self.game.chatBox.allChats[-MAX_MESSAGES_INIT * MAX_MESSAGES_PER_TURN:] if '!' in
                        msg.text]
            else:
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

    # @time_measure
    def update_ids_from_chat_box(self):
        id_msgs = [msg.text for msg in
                   self.game.chatBox.allChats[-MAX_MESSAGES_PER_TURN:] if
                   msg.text.startswith("id") and msg.turn == AI.game_round - 1]
        if AI.life_cycle <= 3:
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

    # @time_measure
    def get_init_ants_next_move(self, preferred_moves, map) -> int:
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
                    path = map.get_path_with_max_length(map.nodes[self.pos], map.nodes[self.fix_pos(p)], 2)
                    if path is not None:
                        return Direction.get_value(map.step(self.pos, path[0].pos))

        print_with_debug("error on get_init_ants_next_move", f=AI.out_file)
        return Direction.get_random_direction()

    def get_init_ant_explore_move(self):
        AI.worker_state = WorkerState.InitCollecting
        if AI.id <= Utils.INIT_ANTS_NUM:
            if AI.id == Utils.GRASS_ONLY_ID:
                m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1],
                                                 AI.map.convert_bread_cells_to_wall())
            else:
                m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id - 1], AI.map)
        else:
            m = self.get_init_ants_next_move(Utils.INIT_STRAIGHT_ANTS_MOVES[AI.id % 4], AI.map)

        if m < 5:
            return m
        else:
            print_with_debug("something went wrong, init ants move :", m, "from id:", AI.id, f=AI.out_file)
            return Direction.get_random_direction()

    # @time_measure
    def get_new_ant_collect_move(self, own_discovered_search=False):
        if own_discovered_search:
            search_map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
            for p in self.found_history:
                search_map.nodes[p] = AI.map.nodes[p]
        else:
            search_map = AI.map
        if self.has_resource_in_map(2, 1) is None:
            m = self.get_init_ant_explore_move()
        elif self.game.ant.currentResource.type == ResourceType.BREAD.value:
            print_with_debug("ANT is holding bread", f=AI.out_file)
            if self.has_resource_in_map(ResourceType.BREAD.value,
                                        WORKER_MAX_CARRYING_RESOURCE_AMOUNT - self.game.ant.currentResource.value) \
                    == ResourceType.BREAD.value:
                print_with_debug("state has bread res to find", f=AI.out_file)
                m, AI.last_name_of_object, d = search_map.get_resource_best_move(
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
                m = Direction.get_value(AI.map.step(self.pos, path[0].pos))
        elif self.game.ant.currentResource.type == ResourceType.GRASS.value:
            print_with_debug("ANT is holding grass", f=AI.out_file)
            if self.has_resource_in_map(ResourceType.GRASS.value,
                                        WORKER_MAX_CARRYING_RESOURCE_AMOUNT - self.game.ant.currentResource.value) \
                    == ResourceType.GRASS.value:
                print_with_debug("state has grass res to find", f=AI.out_file)
                m, AI.last_name_of_object, d = search_map.get_resource_best_move(
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
                m = Direction.get_value(AI.map.step(self.pos, path[0].pos))
        else:
            print_with_debug("ANT isn't hold anything", f=AI.out_file)
            grass_dir = None
            grass_dis = math.inf
            bread_dir = None
            bread_dis = math.inf
            print_with_debug("ANT isn't hold anything")
            if self.has_resource_in_map(ResourceType.GRASS.value,
                                        1,
                                        own_discovered_search) \
                    == ResourceType.GRASS.value:
                grass_dir, AI.last_name_of_object, grass_dis = search_map.get_resource_best_move(
                    src_pos=self.pos,
                    dest_pos=AI.map.base_pos,
                    name_of_object='grass',
                    limit=get_limit(
                        bread_min=math.inf,
                        grass_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT
                    ),
                    number_of_object=get_number_of_object(self.game.ant.currentResource),
                )
            if self.has_resource_in_map(ResourceType.BREAD.value,
                                        1,
                                        own_discovered_search) \
                    == ResourceType.BREAD.value:
                bread_dir, AI.last_name_of_object, bread_dis = search_map.get_resource_best_move(
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
            if (grass_dis <= bread_dis
                or ((AI.id % Utils.NEW_GRASS_PRIORITY_PER_ROUND) == 0) and grass_dis - Utils.PRIORITY_GAP <= bread_dis) \
                    and grass_dis != math.inf:
                m = grass_dir
            elif bread_dir is not None:
                m = bread_dir
            else:
                m = self.get_init_ant_explore_move()
        return m

    # @time_measure
    def get_init_ant_collect_move(self, own_discovered_search=False):
        if own_discovered_search:
            search_map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
            for p in self.found_history:
                search_map.nodes[p] = AI.map.nodes[p]
        else:
            search_map = AI.map

        if self.game.ant.currentResource.type == ResourceType.BREAD.value:
            if self.has_resource_in_map(ResourceType.BREAD.value,
                                        WORKER_MAX_CARRYING_RESOURCE_AMOUNT - self.game.ant.currentResource.value,
                                        own_discovered_search) \
                    == ResourceType.BREAD.value:
                print_with_debug("state has res to find", f=AI.out_file)
                m, AI.last_name_of_object, d = search_map.get_resource_best_move(
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
                                        WORKER_MAX_CARRYING_RESOURCE_AMOUNT - self.game.ant.currentResource.value,
                                        own_discovered_search) \
                    == ResourceType.GRASS.value:
                print_with_debug("state has res to find", f=AI.out_file)
                m, AI.last_name_of_object, d = search_map.get_resource_best_move(
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
            grass_dir = None
            grass_dis = math.inf
            bread_dir = None
            bread_dis = math.inf
            print_with_debug("ANT isn't hold anything")
            if self.has_resource_in_map(ResourceType.GRASS.value,
                                        1,
                                        own_discovered_search) \
                    == ResourceType.GRASS.value:
                grass_dir, AI.last_name_of_object, grass_dis = search_map.get_resource_best_move(
                    src_pos=self.pos,
                    dest_pos=AI.map.base_pos,
                    name_of_object='grass',
                    limit=get_limit(
                        bread_min=math.inf,
                        grass_min=WORKER_MAX_CARRYING_RESOURCE_AMOUNT
                    ),
                    number_of_object=get_number_of_object(self.game.ant.currentResource),
                )
            if self.has_resource_in_map(ResourceType.BREAD.value,
                                        1,
                                        own_discovered_search) \
                    == ResourceType.BREAD.value \
                    and AI.id != Utils.GRASS_ONLY_ID:
                bread_dir, AI.last_name_of_object, bread_dis = search_map.get_resource_best_move(
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
            if ((grass_dis <= bread_dis and AI.id != BREAD_PRIORITY_ID)
                or ((
                            AI.id == GRASS_PRIORITY_ID1 or AI.id == GRASS_PRIORITY_ID2) and grass_dis - PRIORITY_GAP <= bread_dis)
                or (AI.id == BREAD_PRIORITY_ID and grass_dis + PRIORITY_GAP < bread_dis)) \
                    and grass_dis != math.inf:
                m = grass_dir
            elif bread_dir is not None:
                m = bread_dir
            else:
                m = self.get_init_ant_explore_move()
        return m

    def has_resource_in_map(self, res_type: int, res_num=10, own_discovered_search=False):
        if own_discovered_search:
            own_map = Graph((AI.w, AI.h), (self.game.baseX, self.game.baseY))
            for p in self.found_history:
                own_map.nodes[p] = AI.map
        else:
            own_map = AI.map

        print_with_debug("total bread num:", own_map.total_bread_number(), f=AI.out_file)
        print_with_debug("total grass num:", own_map.total_grass_number(), f=AI.out_file)
        if res_type == ResourceType.BREAD.value:
            if AI.map.total_bread_number() >= res_num:
                return res_type
        elif res_type == ResourceType.GRASS.value:
            if AI.map.total_grass_number() >= res_num:
                return res_type
        elif AI.map.total_grass_number() >= res_num:
            return ResourceType.BREAD.value
        elif AI.map.total_bread_number() >= res_num:
            return ResourceType.GRASS.value
        else:
            return None

    #     # @time_measure
    #     @handle_exception
    def turn(self) -> (str, int, int):
        if AI.debug and AI.life_cycle > 2 and (AI.ids and (AI.id in AI.ids[0] or AI.id in AI.ids[1])):
            t = "soldier" if self.game.ant.antType == AntType.SARBAAZ.value else "worker"
            AI.out_file = open(AI.output_path + t + '_' + str(AI.born_game_round) + '_' + str(AI.first_id) + ".txt",
                               "a+")

        self.round_initialization()

        if AI.game_round == 1:
            AI.worker_state = WorkerState.InitExploring if self.game.ant.antType == AntType.KARGAR.value else WorkerState.Null
            self.direction = self.random_valid_dir()


        # *************************************************************************************************************************
        # ########################################################KAARGAAAR########################################################
        # *************************************************************************************************************************
        elif self.game.ant.antType == AntType.KARGAR.value:
            print_map(AI.map, self.pos)
            if self.game.ant.currentResource.value is not None \
                    and self.game.ant.currentResource.value >= (WORKER_MAX_CARRYING_RESOURCE_AMOUNT / 2):
                print_with_debug("worker has >= (max carrying resources amount / 2) => back to base with bfs",
                                 f=AI.out_file)

                dir = AI.map.get_first_move_to_base(AI.map.nodes[self.pos],
                                                    get_number_of_object(self.game.ant.currentResource))
                if dir is None:
                    self.direction = Direction.CENTER.value
                else:
                    self.direction = dir
                print_with_debug("bfs dir:", self.direction)
            elif self.game_round > MAX_TURN_COUNT - 10:
                print_with_debug("last rounds => back to base with bfs",
                                 f=AI.out_file)
                if self.pos == AI.map.base_pos:
                    self.direction = Direction.CENTER.value
                else:
                    dir = AI.map.get_first_move_to_base(AI.map.nodes[self.pos],
                                                        get_number_of_object(self.game.ant.currentResource))
                    if dir is None:
                        self.direction = Direction.CENTER.value
                    else:
                        self.direction = dir
                print_with_debug("bfs dir:", self.direction)
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

                    self.direction = self.get_new_ant_collect_move()
                    if self.direction == 0 or self.direction is None:
                        print_with_debug("new ants at the end:", self.direction, f=AI.out_file)
                        print_with_debug("=> move like init ant explore", f=AI.out_file)
                        self.direction = self.get_init_ant_explore_move()

        # *************************************************************************************************************************
        # ########################################################SAARBAAAZ########################################################
        # *************************************************************************************************************************
        elif self.game.ant.antType == AntType.SARBAAZ.value:
            print_map(AI.map, self.pos, f=AI.out_file)
            if AI.life_cycle == 1:
                self.direction = self.random_valid_dir()
            else:
                if AI.born_game_round < 50:
                    AI.soldier_state = SoldierState.Explorer_Supporter

                self.handle_base()
                self.handle_shot()

                if AI.soldier_state == SoldierState.Explorer_Supporter:
                    # TODO fill this
                    self.direction = self.get_first_move_to_go()

                # ####################################### DEFAULT SECTION
                if AI.soldier_state == SoldierState.Null:
                    # print("exp target", AI.game_round, self.pos, AI.exploration_target)
                    if AI.exploration_target is None:
                        self.direction = self.get_soldier_first_move_to_discover()
                        print_with_debug(f'in soldier discover: pos = {self.pos}, direction = {self.direction}',
                                         f=AI.out_file)
                    else:
                        if self.pos == AI.exploration_target:
                            # print("NONE TARGET", self.pos, AI.exploration_target)
                            AI.exploration_target = None
                            self.direction = self.get_soldier_first_move_to_discover()
                        else:
                            self.direction = self.get_first_move_to_target(self.pos, AI.exploration_target)

        self.send_msg()
        self.end_round()

        print_with_debug("turn", AI.game_round, "id", AI.id, "pos", self.pos,
                         "worker state", AI.worker_state,
                         "soldier state", AI.soldier_state,
                         "dir", Direction.get_string(self.direction),
                         "map value", self.value, f=AI.out_file, debug=False)

        if self.message is not None and len(self.message) > 32:
            self.message = ""
            self.value = -100000

        if self.direction is None:
            self.direction = self.random_valid_dir()
            if self.direction is None or self.direction == Direction.CENTER.value:
                self.direction = Direction.get_random_direction()

        return self.message, self.value, self.direction

    def random_valid_dir(self):
        d = [(1, 0), (0, -1), (-1, 0), (0, 1)]
        nears = []
        for i, dd in enumerate(d):
            pos = tuple(map(sum, zip(self.pos, dd)))
            pos = fix(pos, AI.w, AI.h)
            if not AI.map.nodes[pos].swamp and not AI.map.nodes[pos].wall:
                nears.append(pos)
        t = random.choice(nears)
        return Direction.get_value(AI.map.step(self.pos, t))

    # @time_measure
    def round_initialization(self):
        print_with_debug("************************************************************************", f=AI.out_file)
        print_with_debug("************************************************************************", f=AI.out_file)
        print_with_debug("************************************************************************", f=AI.out_file)
        print_with_debug("ROUND START!", f=AI.out_file)
        if AI.id == Utils.GRASS_ONLY_ID:
            print_with_debug("Grass only ant", f=AI.out_file)

        print_with_debug(AI.found_history, f=AI.out_file)
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
            AI.latest_map.nodes[k].swamp = v.swamp
            AI.latest_map.nodes[k].trap = v.trap
            AI.latest_map.nodes[k].grass = v.grass
            AI.latest_map.nodes[k].enemy_soldiers = v.enemy_soldiers

        self.pos = (self.game.ant.currentX, self.game.ant.currentY)
        print_with_debug("ROUND:", self.game_round, f=AI.out_file)
        print_with_debug("POS:", self.pos, f=AI.out_file)
        self.search_neighbors()
        self.update_map_from_chat_box()
        self.update_map_from_neighbors()

        if AI.game_round > 5 and not AI.shot_once:
            self.check_for_base()
        if self.game.ant.antType == AntType.SARBAAZ.value:
            self.soldier_update_history()
            print_with_debug("soldier history", AI.soldier_path_neighbors_history, f=AI.out_file)

        self.check_for_possible_base_cells()
        AI.own_cells_history.append(self.pos)

        print_with_debug("known cells", [k for k, v in AI.map.nodes.items() if v.discovered], f=AI.out_file)
        print_with_debug("found history", AI.found_history, f=AI.out_file)

    # @time_measure
    def end_round(self):
        AI.latest_pos[AI.id] = (self.pos, AI.game_round)
        AI.game_round += 1
        AI.life_cycle += 1
        AI.prev_round_resource = self.game.ant.currentResource.value
        AI.prev_hp = self.game.ant.health
        AI.prev_es = sum([AI.map.nodes[v].enemy_soldiers for v in
                          get_view_distance_neighbors(self.pos, AI.w, AI.h, self.game.ant.viewDistance)])
        if not AI.shot_once and self.shot:
            AI.shot_once = True

    # @time_measure
    def send_msg(self):
        now = time.time()

        if AI.life_cycle > 1 and (not self.shot or self.value == VALUES["enemy_base"]):
            if self.direction is None:
                print_with_debug("turn", AI.game_round, "id", AI.id, "pos", self.pos,
                                 "worker state", AI.worker_state,
                                 "soldier state", AI.soldier_state,
                                 "map value", self.value,
                                 "enemy base pos", AI.map.enemy_base_pos, f=AI.out_file)
            if AI.map is not None:
                dis_list = get_view_distance_neighbors(self.pos, AI.w, AI.h, 4)
                neighbors = {pos: n for pos, n in AI.map.nodes.items() if
                             pos in dis_list}
                self.encoded_neighbors = encode_graph_nodes(self.pos,
                                                            neighbors,
                                                            AI.w, AI.h,
                                                            self.game.viewDistance,
                                                            AI.id, self.direction,
                                                            self.shot,
                                                            AI.map.enemy_base_pos)
                self.message = self.encoded_neighbors
        elif AI.life_cycle > 1 and self.shot and AI.soldier_state == SoldierState.Null:
            possible_cells = get_view_distance_neighbors(AI.latest_pos[AI.id][0], AI.w,
                                                         AI.h, 6, exact=True)
            possible_cells = [p for p in possible_cells if
                              p not in AI.soldier_path_neighbors_history]
            AI.possible_base_cells = list(set(AI.possible_base_cells).
                                          intersection(possible_cells))
            print_with_debug("tell them", AI.latest_pos[AI.id][0], possible_cells, AI.own_cells_history[-3],
                             f=AI.out_file)
            self.message = encode_possible_cells(AI.id, AI.latest_pos[AI.id][0],
                                                 AI.own_cells_history[-3],
                                                 AI.w, AI.h, possible_cells)
            print_with_debug(self.message, f=AI.out_file)
            self.direction = solve_bt(AI.map, self.pos, max_distance=5)
            AI.soldier_state = SoldierState.HasBeenShot
            self.value = VALUES["shot"]

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

    # @time_measure
    def check_for_base(self):
        hp = self.game.ant.health
        neighbors = get_view_distance_neighbors(AI.latest_pos[AI.id][0], AI.w, AI.h,
                                                self.game.ant.viewDistance)
        cond = (hp == AI.prev_hp - BASE_DMG and AI.prev_es == 0) or \
               (hp == AI.prev_hp - BASE_DMG - SOLDIER_DMG and AI.prev_es == 1) or \
               (hp == AI.prev_hp - BASE_DMG - 2 * SOLDIER_DMG and AI.prev_es == 2)
        print_with_debug("HERE IS ES", [AI.map.nodes[v] for v in neighbors if AI.map.nodes[v].enemy_soldiers > 0],
                         f=AI.out_file)
        if cond:
            print_with_debug("YESSSSS I GOT SHOTTTTTTTTTT", f=AI.out_file)
            self.shot = True
            AI.soldier_state = SoldierState.HasBeenShot

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

    # @time_measure
    def soldier_update_history(self):
        if not self.shot:
            neighbors = get_view_distance_neighbors(AI.latest_pos[AI.id][0], AI.w, AI.h, 6)
            new_neighbors = [p for p in neighbors if p not in AI.soldier_path_neighbors_history]
            AI.soldier_path_neighbors_history += new_neighbors.copy()

    # @time_measure
    def check_for_possible_base_cells(self):
        possible_msgs = [msg.text for msg in
                         self.game.chatBox.allChats[-MAX_MESSAGES_PER_TURN:] if
                         msg.text.startswith("s") and
                         msg.turn == AI.game_round - 1]
        if AI.life_cycle == 1:
            possible_msgs = [msg.text for msg in self.game.chatBox.allChats if
                             msg.text.startswith("s")]

        # if possible_msgs:
        #     print_with_debug("I HAVE S MESSAGE HAHAHAHHAA", f=AI.out_file)
        #     if AI.life_cycle > 1:
        #         AI.soldier_state = SoldierState.PreparingForAttack
        #     elif AI.life_cycle == 1:
        #         AI.soldier_state = SoldierState.WaitingForComrades
        #     AI.cell_target = None

        for m in possible_msgs:
            print_with_debug("possible msg:", m)
            ant_id, pos, prev_pos, possible_cells = decode_possible_cells(m, AI.w, AI.h)
            AI.possible_base_cells = list(set(AI.possible_base_cells).
                                          intersection(possible_cells))
            if (prev_pos, pos) not in AI.near_base_safe_cells:
                AI.near_base_safe_cells.append((prev_pos, pos))

        # if AI.near_base_targets:
        #     AI.near_base_targets.sort()
        #     distances = [manhattan_dist(AI.map.base_pos, t[0], AI.w, AI.h) for t in AI.near_base_targets]
        #     min_i = distances.index(min(distances))
        #     print_with_debug("HAHAHAHA i had shot msgs", AI.near_base_targets, distances, f=AI.out_file)
        #     AI.cell_target = AI.near_base_targets[min_i][0] if AI.cell_target is None else AI.cell_target
        #     if AI.near_base_targets[min_i][0] != AI.near_base_targets[min_i][1]:
        #         AI.attack_dir = self.get_first_move_to_target(AI.near_base_targets[min_i][0], AI.near_base_targets[min_i][1])
        #     else:
        #         AI.attack_dir = Direction.get_random_direction()

    def get_soldier_first_move_to_discover(self, init=True):
        if init:
            # print("GOT IN INIT.")
            AI.latest_map.bfs(AI.map.nodes[self.pos])
            # print("INIT EDGE NODES", AI.latest_map.edge_nodes)
        # print("IDS", AI.ids)
        move, AI.exploration_target = AI.latest_map.get_first_move_to_discover(
            AI.map.nodes[self.pos], self.pos, len(AI.ids[self.game.ant.antType]), AI.id, AI.ids[self.game.ant.antType]
        )
        return Direction.get_value(move)

    def get_soldier_first_node_to_support(self):
        return Direction.get_value(
            AI.map.step(self.pos, AI.map.get_best_node_to_support(self.pos))
        )

    def get_first_move_to_target(self, src, dest, unsafe_cells=None, name='soldier'):
        print_with_debug(src, dest, f=AI.out_file)
        print_with_debug(AI.map.get_path_with_non_discovered(AI.map.nodes[src], AI.map.nodes[dest], unsafe_cells),
                         f=AI.out_file)
        return Direction.get_value(
            AI.map.step(
                src, AI.map.get_path_with_non_discovered(AI.map.nodes[src], AI.map.nodes[dest], unsafe_cells, name)
            )
        )

    # @time_measure
    def handle_base(self):
        if AI.map.enemy_base_pos is not None and \
                AI.soldier_state == SoldierState.Null:
            AI.soldier_state = SoldierState.BK_GoingNearEnemyBase
            near_base_cells = get_view_distance_neighbors(
                AI.map.enemy_base_pos, AI.w, AI.h, BASE_RANGE + 1, exact=True)
            # TODO manhattan dist or bfs?
            distances = [manhattan_dist(self.pos, p, AI.w, AI.h) for p in
                         near_base_cells]
            candidates_idx = sorted(enumerate(distances), key=lambda x: x[1])[:4]
            AI.chosen_near_base_cell_BK = near_base_cells[
                random.choice(candidates_idx)[0]]
            print_with_debug("BASE WAS FOUND STATE",
                             "pos", self.pos,
                             "near base cells", near_base_cells,
                             "distances", distances,
                             "chosen near cell BK", AI.chosen_near_base_cell_BK,
                             f=AI.out_file)

        # going to the chosen cell near enemy base
        if AI.soldier_state == SoldierState.BK_GoingNearEnemyBase:
            if self.pos == AI.chosen_near_base_cell_BK:
                AI.soldier_state = SoldierState.BK_StayingNearBase
                AI.chosen_near_base_cell_BK = None
                print_with_debug("BK GOING NEAR ENEMY BASE STATE",
                                 "REACHED DEST",
                                 "pos", self.pos,
                                 "chosen near cell BK",
                                 AI.chosen_near_base_cell_BK,
                                 f=AI.out_file)
            else:
                self.direction = self.get_first_move_to_target(self.pos,
                                                               AI.chosen_near_base_cell_BK)
                print_with_debug("BK GOING NEAR ENEMY BASE STATE",
                                 "pos", self.pos,
                                 "chosen near cell BK",
                                 AI.chosen_near_base_cell_BK,
                                 f=AI.out_file)

        if AI.soldier_state == SoldierState.BK_StayingNearBase:
            # TODO decide to either stay or attack
            # ATTACK
            self.direction = Direction.CENTER.value
            ally_s = len(
                [a for a in self.game.ant.getMapRelativeCell(0, 0).ants if
                 a.antType == AntType.SARBAAZ.value and a.antTeam == AntTeam.ALLIED.value])
            print_with_debug("BK STAYING NEAR BASE STATE",
                             "pos", self.pos,
                             "allies", ally_s,
                             f=AI.out_file)
            # TODO add other attacking conditions
            if ally_s >= ALLIES_REQUIRED_TO_ATTACK:
                AI.soldier_state = SoldierState.AttackingBase

    # @time_measure
    def handle_shot(self):
        if AI.soldier_state == SoldierState.HasBeenShot:
            # GOING FORWARD ONE CELL WHEN SHOT
            self.direction = Direction.get_value(
                AI.map.step(AI.latest_pos[AI.id][0], self.pos))
            if AI.latest_pos[AI.id][0] == self.pos:
                self.direction = Direction.get_random_direction()
            print_with_debug("GOT SHOT STATE",
                             "prev pos", AI.latest_pos[AI.id][0],
                             "pos", self.pos,
                             "dir", self.direction,
                             f=AI.out_file)

        if AI.soldier_state == SoldierState.Null and AI.near_base_safe_cells:
            AI.soldier_state = SoldierState.BU_GoingNearEnemyBase
            # TODO manhattan dist or bfs?
            distances = [manhattan_dist(self.pos, p[0], AI.w, AI.h) for p in
                         AI.near_base_safe_cells]
            candidates_idx = sorted(enumerate(distances), key=lambda x: x[1])[
                             :4]
            AI.chosen_near_base_cell_BU = AI.near_base_safe_cells[
                random.choice(candidates_idx)[0]]
            print_with_debug("FOUND SHOT MSG STATE",
                             "pos", self.pos,
                             "near base cells", AI.near_base_safe_cells,
                             "distances", distances,
                             "chosen cell BU",
                             AI.chosen_near_base_cell_BU,
                             f=AI.out_file)

        if AI.soldier_state == SoldierState.BU_GoingNearEnemyBase:
            if self.pos == AI.chosen_near_base_cell_BU[0]:
                AI.soldier_state = SoldierState.BU_StayingNearBase
                print_with_debug("BU GOING NEAR ENEMY BASE STATE",
                                 "REACHED DEST",
                                 "pos", self.pos,
                                 "chosen cell BU",
                                 AI.chosen_near_base_cell_BU,
                                 f=AI.out_file)
            else:
                self.direction = self.get_first_move_to_target(self.pos,
                                                               AI.chosen_near_base_cell_BU[
                                                                   0])
                print_with_debug("BU GOING NEAR ENEMY BASE STATE",
                                 "pos", self.pos,
                                 "dir", self.direction,
                                 "chosen cell BU",
                                 AI.chosen_near_base_cell_BU,
                                 f=AI.out_file)

        if AI.soldier_state == SoldierState.BU_StayingNearBase:
            # TODO decide to either stay or attack
            # ATTACK
            self.direction = Direction.CENTER.value
            ally_s = len(
                [a for a in self.game.ant.getMapRelativeCell(0, 0).ants if
                 a.antType == AntType.SARBAAZ.value and a.antTeam == AntTeam.ALLIED.value])
            print_with_debug("BU STAYING NEAR BASE STATE",
                             "pos", self.pos,
                             "allies", ally_s,
                             f=AI.out_file)
            # TODO add other attacking conditions
            if ally_s >= ALLIES_REQUIRED_TO_ATTACK:
                AI.soldier_state = SoldierState.AttackingBase

        if AI.soldier_state == SoldierState.AttackingBase:
            if AI.map.enemy_base_pos is not None:
                if self.pos == AI.map.enemy_base_pos:
                    self.direction = Direction.CENTER.value
                else:
                    self.direction = self.get_first_move_to_target(self.pos,
                                                                   AI.map.enemy_base_pos)
                print_with_debug("ATT BASE FOUND",
                                 "pos", self.pos,
                                 "target", AI.map.enemy_base_pos,
                                 "dir", self.direction,
                                 f=AI.out_file)
            else:
                self.direction = solve_bt(AI.map, self.pos, max_distance=7)
                print_with_debug("ATT BASE NOT FOUND",
                                 "dir from bt",
                                 "pos", self.pos,
                                 "dir", self.direction,
                                 f=AI.out_file)
                if self.direction == Direction.CENTER.value:
                    print_with_debug("CENTER VALUE FROM BT", f=AI.out_file)
                    # TODO go in the dir of prev -> pos
                    if self.pos == AI.chosen_near_base_cell_BU[0]:
                        AI.shot_default_dir = Direction.get_value(
                            AI.map.step(self.pos,
                                        AI.chosen_near_base_cell_BU[1]))
                    self.direction = AI.shot_default_dir
                    print_with_debug("ATT BASE NOT FOUND",
                                     "dir from logic",
                                     "pos", self.pos,
                                     "dir", self.direction,
                                     "default dir", AI.shot_default_dir,
                                     f=AI.out_file)

    def get_first_move_to_go(self):
        bread_number = 0
        grass_number = 0
        AI.map.bfs(AI.map.nodes[self.pos])
        distance_to_base = AI.map.bfs_info['dist'][AI.map.base_pos]
        for d in self.visible_bread:
            num, pos = d["number"], d["pos"]
            if AI.map.bfs_info['dist'].get(pos) is not None:
                bread_number += num

        for d in self.visible_grass:
            num, pos = d["number"], d["pos"]
            if AI.map.bfs_info['dist'].get(pos) is not None:
                grass_number += num

        if self.get_value(bread_number, grass_number, distance_to_base) > VALUE_TO_SUPPORT:
            AI.exploration_target = None
            return Direction.CENTER.value

        return self.get_soldier_first_move_to_discover()

    def get_value(self, bread_number, grass_number, distance_to_base):
        return bread_number + grass_number + distance_to_base
