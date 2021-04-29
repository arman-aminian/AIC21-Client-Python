import math
import random
from itertools import chain

import Utils
from Model import Direction


class Node:
    GRASS_WEIGHT = 1
    BREAD_WEIGHT = 1
    DISTANCE_WEIGH = 10
    GRASS_LIMIT = 10
    BREAD_LIMIT = 10

    def __init__(self, pos, discovered, wall=False, swamp=False, trap=False,
                 bread=0, grass=0,
                 ally_workers=0, ally_soldiers=0, enemy_workers=0,
                 enemy_soldiers=0):
        # REMEMBER to change the encode/decode function after adding attrs
        self.pos = pos
        self.discovered = discovered
        self.wall = wall
        self.swamp = swamp
        self.trap = trap
        self.bread = bread
        self.grass = grass
        self.ally_workers = ally_workers
        self.ally_soldiers = ally_soldiers
        self.enemy_workers = enemy_workers
        self.enemy_soldiers = enemy_soldiers

    def __repr__(self):
        return f"{self.__dict__}"

    def __eq__(self, other):
        if type(self) is type(other):
            return self.__dict__ == other.__dict__
        return False

    def get_distance(self, node):
        return abs(self.pos[0] - node.pos[0]) + abs(self.pos[1] - node.pos[1])

    # todo: make get value better(use dest)
    # todo: make default dist better
    def grass_value(self, src, dest, graph, number=0):
        distance = graph.get_shortest_distance(src, self, 'grass', default=math.inf) \
                   + graph.get_shortest_distance(dest, self, 'grass', default=math.inf)
        return -distance * self.DISTANCE_WEIGH + self.grass + number * self.GRASS_WEIGHT

    def bread_value(self, src, dest, graph, number=0):
        distance = graph.get_shortest_distance(src, self, 'bread', default=math.inf) \
                   + graph.get_shortest_distance(dest, self, 'bread', default=math.inf)
        return -distance * self.DISTANCE_WEIGH + self.bread + number * self.BREAD_WEIGHT


class Graph:
    TSP_NODE_LIMIT = 5

    def __init__(self, dim, base_pos):
        self.base_pos = base_pos
        self.dim = dim  # width, height
        self.enemy_base_pos = None
        self.nodes = {}
        self.bfs_info = {}
        self.edge_nodes = []
        self.shortest_path_info = {'bread': {}, 'grass': {}}
        for i in range(dim[0]):
            for j in range(dim[1]):
                if (i, j) == base_pos:
                    self.nodes[(i, j)] = Node(
                        pos=(i, j),
                        discovered=True,
                        wall=False
                    )
                else:
                    self.nodes[(i, j)] = Node(
                        pos=(i, j),
                        discovered=False
                    )

    def step(self, src, dest):
        if dest[0] - src[0] in [1, -(self.dim[0] - 1)]:
            return "RIGHT"
        if dest[0] - src[0] in [-1, self.dim[0] - 1]:
            return "LEFT"
        if dest[1] - src[1] in [-1, self.dim[1] - 1]:
            return "UP"
        if dest[1] - src[1] in [1, -(self.dim[1] - 1)]:
            return "DOWN"

    # @Utils.time_measure
    def total_grass_number(self):
        res = 0
        for pos in self.nodes.keys():
            if not self.nodes[pos].wall:
                if self.nodes[pos].grass > 0:
                    if self.get_path(self.nodes[pos], self.nodes[self.base_pos]) is not None:
                        #     print(pos)
                        res = res + self.nodes[pos].grass
        return res

    # @Utils.time_measure
    def total_bread_number(self):
        res = 0
        # print("###########")
        # print("total_bread_number:")
        for pos in self.nodes.keys():
            if not self.nodes[pos].wall:
                if self.nodes[pos].bread > 0:
                    if self.get_path(self.nodes[pos], self.nodes[self.base_pos]) is not None:
                        #     print(pos)
                        res = res + self.nodes[pos].bread
        return res

    # @Utils.time_measure
    def shortest_path(self, src, dest):
        q = [[src]]
        visited = []

        while q:
            prev_path = q.pop(0)
            node = prev_path[-1]
            if node not in visited:
                neighbors = self.get_neighbors(node)
                for u in neighbors:
                    path = list(prev_path)
                    path.append(u)
                    q.append(path)
                    if u == dest:
                        return path
                visited.append(node)

        return None

    def set_bread(self, pos, b):
        self.nodes[pos].bread = b

    def set_grass(self, pos, g):
        self.nodes[pos].grass = g

    def set_ally_workers(self, pos, aw):
        self.nodes[pos].ally_workers = aw

    def set_ally_soldiers(self, pos, a_s):
        self.nodes[pos].ally_soldiers = a_s

    def set_enemy_workers(self, pos, ew):
        self.nodes[pos].enemy_workers = ew

    def set_enemy_soldiers(self, pos, es):
        self.nodes[pos].enemy_soldiers = es

    def discover(self, pos, is_wall):
        self.nodes[pos].wall = is_wall
        self.nodes[pos].discovered = True

    def get_neighbors(self, pos):
        if self.nodes[pos].wall or not self.nodes[pos].discovered:
            return []
        neighbors = [self.up(pos), self.right(pos), self.down(pos),
                     self.left(pos)]
        neighbors = [n for n in neighbors if not self.nodes[n].wall and
                     self.nodes[pos].discovered]
        return neighbors

    def get_neighbors_with_not_discovered_nodes(self, pos):
        if self.nodes[pos].wall and self.nodes[pos].discovered:
            return []
        neighbors = [self.up(pos), self.right(pos), self.down(pos), self.left(pos)]
        neighbors = [n for n in neighbors if not self.nodes[n].wall or not self.nodes[n].discovered]
        return neighbors

    def right(self, pos):
        if pos[0] == self.dim[0] - 1:
            return 0, pos[1]
        return pos[0] + 1, pos[1]

    def left(self, pos):
        if pos[0] == 0:
            return self.dim[0] - 1, pos[1]
        return pos[0] - 1, pos[1]

    def up(self, pos):
        if pos[1] == 0:
            return pos[0], self.dim[1] - 1
        return pos[0], pos[1] - 1

    def down(self, pos):
        if pos[1] == self.dim[1] - 1:
            return pos[0], 0
        return pos[0], pos[1] + 1

    def guess_node(self, node):
        # todo: make guessing better
        return Node(pos=node.pos, discovered=False, wall=True)
        # opposite_node_pos = (self.dim[0] - 1 - node.pos[0], self.dim[1] - 1 - node.pos[1])
        # opposite_node = self.nodes[opposite_node_pos]
        # if not opposite_node.discovered or random.randint(1, 5) != 1:
        #     return Node(pos=node.pos, discovered=False, wall=random.choice([True, False, False, False]))
        # return Node(
        #     pos=node.pos,
        #     discovered=False,
        #     wall=opposite_node.wall,
        #     bread=opposite_node.bread,
        #     grass=opposite_node.grass
        # )

    def get_node(self, pos):
        return self.nodes[pos] if self.nodes[pos].discovered else self.guess_node(self.nodes[pos])

    def get_worker_weight(self, src, dest):
        return int(src.swamp) * Utils.SWAMP_TURNS + 1

    # @Utils.time_measure
    def get_shortest_path(self, src, name_of_other_object, number_of_object):
        q = [src]
        in_queue = {src.pos: True}
        dist = {src.pos: 0}
        parent = {src.pos: src.pos}

        if (src.discovered and src.wall) or (getattr(src, name_of_other_object) > 0 and number_of_object == 0):
            return {
                'dist': dist,
                'parent': parent,
            }

        while q:
            current_node = q.pop(0)
            neighbors = self.get_neighbors_with_not_discovered_nodes(current_node.pos)
            in_queue[current_node.pos] = False

            for neighbor in neighbors:
                next_node = self.nodes[neighbor]
                if getattr(next_node, name_of_other_object) > 0 and number_of_object == 0:
                    continue
                if number_of_object * int(next_node.trap):
                    continue
                weight = self.get_worker_weight(current_node, next_node)
                if dist.get(next_node.pos) is None or weight + dist[current_node.pos] < dist.get(next_node.pos):
                    dist[next_node.pos] = weight + dist[current_node.pos]
                    parent[next_node.pos] = current_node.pos
                    if not in_queue.get(next_node.pos):
                        in_queue[next_node.pos] = True
                        q.append(next_node)
        return {
            'dist': dist,
            'parent': parent,
        }

    # @Utils.time_measure
    def get_path(self, src, dest):
        q = [src]
        parent = {src.pos: src.pos}

        if src.wall:
            return None

        while q:
            current_node = q.pop(0)
            neighbors = self.get_neighbors(current_node.pos)

            for neighbor in neighbors:
                next_node = self.nodes[neighbor]
                if parent.get(next_node.pos) is None:
                    parent[next_node.pos] = current_node.pos
                    q.append(next_node)
                    if next_node.pos == dest.pos:
                        path = []
                        last_node_pos = next_node.pos
                        while last_node_pos != src.pos:
                            path.append(self.nodes[last_node_pos])
                            last_node_pos = parent[last_node_pos]
                        return list(reversed(path))
        return None

    # @Utils.time_measure
    def get_path_with_non_discovered(self, src, dest, unsafe_cells=None, name='soldier'):
        if src == dest:
            print('IM IN TARGET')
            raise
        unsafe_pos = {}
        for pos in (unsafe_cells or []):
            unsafe_pos.update(
                set(
                    Utils.get_view_distance_neighbors(
                        pos, self.dim[0], self.dim[1], Utils.BASE_RANGE, exact=False, sort=False
                    )
                )
            )

        q = [src]
        in_queue = {src.pos: True}
        dist = {src.pos: 0}
        parent = {src.pos: src.pos}

        if src.wall:
            return None

        while q:
            current_node = q.pop(0)
            in_queue[current_node.pos] = False
            neighbors = self.get_neighbors_with_not_discovered_nodes(current_node.pos)

            for neighbor in neighbors:
                next_node = self.nodes[neighbor]
                if next_node.pos in unsafe_pos:
                    continue
                if parent.get(next_node.pos) is None:
                    parent[next_node.pos] = current_node.pos
                    q.append(next_node)
                    weight = getattr(self, f'get_{name}_weight')(current_node, next_node)
                    if dist.get(next_node.pos) is None or weight + dist[current_node.pos] < dist.get(next_node.pos):
                        dist[next_node.pos] = weight + dist[current_node.pos]
                        parent[next_node.pos] = current_node.pos
                        if not in_queue.get(next_node.pos):
                            in_queue[next_node.pos] = True
                            q.append(next_node)

        return self.get_first_move_from_parent(parent, src.pos, dest.pos) if dist.get(dest.pos) else None

    # @Utils.time_measure
    def get_path_with_max_length(self, src, dest, max_len):
        q = [src]
        parent = {src.pos: src.pos}

        if src.wall:
            return None

        while q:
            current_node = q.pop(0)
            neighbors = self.get_neighbors_with_not_discovered_nodes(current_node.pos)

            for neighbor in neighbors:
                next_node = self.nodes[neighbor]
                if parent.get(next_node.pos) is None:
                    parent[next_node.pos] = current_node.pos

                    path = []
                    last_node_pos = next_node.pos
                    while last_node_pos != src.pos:
                        path.append(self.nodes[last_node_pos])
                        last_node_pos = parent[last_node_pos]
                    if len(path) > max_len:
                        return None

                    q.append(next_node)
                    if next_node.pos == dest.pos:
                        path = []
                        last_node_pos = next_node.pos

                        while last_node_pos != src.pos:
                            path.append(self.nodes[last_node_pos])
                            last_node_pos = parent[last_node_pos]
                        return list(reversed(path))
        return None

    def get_random_nodes(self):
        return {pos: self.get_node(pos) for pos in self.nodes.keys()}

    # @Utils.time_measure
    def find_all_shortest_path(self, number_of_object, name_of_object, nodes):
        for node in nodes:
            pos = node.pos
            default = Utils.WORKER_MAX_CARRYING_RESOURCE_AMOUNT if pos == self.base_pos else 0
            self.shortest_path_info[name_of_object][pos] = self.get_shortest_path(
                self.nodes[pos], 'bread' if name_of_object == 'grass' else 'grass',
                number_of_object.get(name_of_object, default)
            )

    # @Utils.time_measure
    def get_nearest_grass_nodes(self, src, dest, number_of_object):
        number = number_of_object.get('grass', 0)
        grass_nodes_temp = []
        for node in self.nodes.values():
            if node.grass > 0 and node.pos != src.pos and node.pos != dest.pos:
                grass_nodes_temp.append(node)

        self.find_all_shortest_path(
            number_of_object, 'grass', [src, dest]
        )

        # print(grass_nodes_temp)
        grass_nodes = []
        for node in grass_nodes_temp:
            if self.get_shortest_distance(
                    dest, node, 'grass'
            ) is not None and self.get_shortest_distance(
                src, node, 'grass'
            ) is not None:
                grass_nodes.append(node)

        return sorted(grass_nodes, key=lambda n: n.grass_value(src, dest, self, number), reverse=True)[
               :self.TSP_NODE_LIMIT]

    # @Utils.time_measure
    def get_nearest_bread_nodes(self, src, dest, number_of_object):
        number = number_of_object.get('bread', 0)
        bread_nodes_temp = []
        for node in self.nodes.values():
            if node.bread > 0 and node.pos != src.pos and node.pos != dest.pos:
                bread_nodes_temp.append(node)

        self.find_all_shortest_path(
            number_of_object, 'bread', [src, dest]
        )
        # print(bread_nodes_temp)
        bread_nodes = []
        for node in bread_nodes_temp:
            if self.get_shortest_distance(
                    dest, node, 'bread'
            ) is not None and self.get_shortest_distance(
                src, node, 'bread'
            ) is not None:
                bread_nodes.append(node)

        return sorted(bread_nodes, key=lambda n: n.bread_value(src, dest, self, number), reverse=True)[
               :self.TSP_NODE_LIMIT]

    # @Utils.time_measure
    def get_shortest_distance(self, src, dest, name_of_object, default=None):
        return self.shortest_path_info[name_of_object].get(src.pos, {}).get('dist', {}).get(dest.pos, default)

    # @Utils.time_measure
    def get_shortest_path_from_shortest_path_info(self, src_pos, dest_pos, name_of_object):
        parent = self.shortest_path_info[name_of_object][src_pos].get('parent', [])
        pos = dest_pos
        path = []
        while parent[pos] != pos:
            path.append(pos)
            pos = parent[pos]
        return list(reversed(path))

    # @Utils.time_measure
    def get_first_move_to_enemy_base(self, src_pos):
        our_base = self.base_pos
        their_base = self.enemy_base_pos or (self.dim[0] - 1 - our_base[0], self.dim[1] - 1 - our_base[1])
        path = self.get_path(self.nodes[src_pos], self.nodes[their_base])
        return self.step(src_pos, path[0].pos) if path else "None"

    # @Utils.time_measure
    def get_first_move_to_opposite_node(self, src_pos):
        opposite_node_pos = (self.dim[0] - 1 - src_pos[0], self.dim[1] - 1 - src_pos[1])
        path = self.get_path(self.nodes[src_pos], self.nodes[opposite_node_pos])
        return self.step(src_pos, path[0].pos) if path else "None"

    # @Utils.time_measure
    def get_edge_nodes(self, src):
        q = [src]
        parent = {src.pos: src.pos}
        dist = {src.pos: 0}
        edge_nodes = set()

        if src.wall:
            return None

        while q:
            current_node = q.pop(0)
            neighbors = self.get_neighbors_with_not_discovered_nodes(current_node.pos)

            for neighbor in neighbors:
                next_node = self.nodes[neighbor]
                if not next_node.discovered:
                    edge_nodes.add(current_node.pos)
                    continue
                if parent.get(next_node.pos) is None:
                    parent[next_node.pos] = current_node.pos
                    dist[next_node.pos] = dist[current_node.pos] + 1
                    q.append(next_node)

        return {
            'edge_nodes': sorted(list(edge_nodes)),
            'distance': dist,
            'parent': parent,
        }

    # @Utils.time_measure
    def get_best_list(self, src, each_list_max_size):
        if not self.edge_nodes:
            self.bfs(src)
        edge_nodes = self.edge_nodes
        distance = self.bfs_info.get('dist')
        parent = self.bfs_info.get('parent')
        # print("BEST LIST EDGE NODES", edge_nodes)

        while len(edge_nodes) > each_list_max_size and len(
                edge_nodes) % each_list_max_size != 0:
            edge_nodes.pop(0)

        all_list = []
        for i in range(len(edge_nodes)):
            if all_list and edge_nodes[i] in all_list[0]:
                break
            all_list.append([])
            for j in range(i, len(edge_nodes), math.ceil(len(edge_nodes) / each_list_max_size)):
                all_list[-1].append(edge_nodes[j])

        # print("ALL LIST", all_list)
        mn_value = math.inf
        mn_idx = 0
        for i in range(len(all_list)):
            value = self.get_value_of_list(all_list[i], distance)
            if value < mn_value:
                mn_idx = i
                mn_value = value

        return all_list[mn_idx], parent

    @staticmethod
    def get_value_of_list(list_of_candidate, dist):
        value = 0
        for pos in list_of_candidate:
            value += dist.get(pos)
        return value / len(list_of_candidate)

    # @Utils.time_measure
    def get_first_move_to_discover(self, curr_pos, src_pos, each_list_max_size, my_id, all_ids):
        src = self.nodes[src_pos]
        # print("FIRST MOVE EDGE NODES", self.edge_nodes)
        best_list, parent = self.get_best_list(src, each_list_max_size)
        # print(best_list)
        idx = random.randint(0, len(best_list) - 1)
        ids = all_ids[-each_list_max_size:]

        for i in range(len(ids)):
            if ids[-i] == my_id:
                idx = i
                break

        # print("MY GOAL IS TO REACH", best_list[idx % len(best_list)])
        # print("1", parent, src_pos, best_list[idx % len(best_list)])
        # print("HAHAAHHAHAHAH", self.step(curr_pos.pos, self.get_first_move_from_parent(parent, src_pos, best_list[idx % len(best_list)])), best_list[idx % len(best_list)])

        return self.step(
            curr_pos.pos, self.get_first_move_from_parent(
                parent, src_pos, best_list[idx % len(best_list)])
        ), best_list[idx % len(best_list)]

    @staticmethod
    def get_first_move_from_parent(parent, src, dest):
        last = dest
        while parent[last] != src:
            last = parent[last]
        return last

    # @Utils.time_measure
    def bfs(self, src):
        self.edge_nodes = []
        q = [src]
        in_queue = {src.pos: True}
        dist = {src.pos: 0}
        parent = {src.pos: src.pos}

        while q:
            current_node = q.pop(0)
            neighbors = self.get_neighbors_with_not_discovered_nodes(current_node.pos)
            in_queue[current_node.pos] = False

            for neighbor in neighbors:
                next_node = self.nodes[neighbor]
                if not next_node.discovered:
                    self.edge_nodes.append(current_node.pos)
                    continue
                weight = self.get_soldier_weight(current_node, next_node)
                if dist.get(next_node.pos) is None or weight + dist[current_node.pos] < dist.get(next_node.pos):
                    dist[next_node.pos] = weight + dist[current_node.pos]
                    parent[next_node.pos] = current_node.pos
                    if not in_queue.get(next_node.pos):
                        in_queue[next_node.pos] = True
                        q.append(next_node)

        # print("EDGE NODES", self.edge_nodes)
        self.edge_nodes = list(set(self.edge_nodes))
        self.edge_nodes.sort()
        self.bfs_info = {
            'dist': dist,
            'parent': parent,
        }
        return self.bfs_info

    def get_soldier_weight(self, src, dest):
        return int(src.swamp) * Utils.SWAMP_TURNS + 1

    # @Utils.time_measure
    def get_best_node_to_support(self, src_pos, grass_weight=1, bread_weight=1, distance_weight=1):
        src = self.nodes[src_pos]
        best_value = -math.inf
        best_pos = None

        dist = self.bfs_info.get('dist')
        parent = self.bfs_info.get('parent')

        for node in self.nodes.values():
            poses = Utils.get_view_distance_neighbors(node.pos, self.dim[0], self.dim[1], 3, sort=False)
            bread_number = 0
            grass_number = 0
            distance = dist.get(node.pos, 0)
            for pos in poses:
                bread_number += self.nodes[pos].bread
                grass_number += self.nodes[pos].grass

            value = grass_number * grass_weight + bread_number * bread_weight - distance * distance_weight
            if distance and value > best_value:
                best_value = value
                best_pos = node.pos

        return self.get_first_move_from_parent(parent, src.pos, best_pos)

    # @Utils.time_measure
    def get_resource_best_move(self, src_pos, dest_pos, name_of_object, limit, number_of_object):
        best_nodes = getattr(
            self, f'get_nearest_{name_of_object}_nodes'
        )(self.nodes[src_pos], self.nodes[dest_pos], number_of_object)
        number_of_bread_need = max(0, limit[name_of_object]['min'] - number_of_object.get(name_of_object, 0))
        if number_of_bread_need == 0:
            return Direction.get_value(self.step(
                src_pos, self.get_shortest_path_from_shortest_path_info(src_pos, self.base_pos, name_of_object)[0])
            ), name_of_object, self.get_shortest_distance(
                self.nodes[src_pos], self.nodes[self.base_pos], name_of_object
            )
        if not best_nodes:
            return None, None, math.inf

        return Direction.get_value(self.step(
            src_pos, self.get_shortest_path_from_shortest_path_info(src_pos, best_nodes[0].pos, name_of_object)[0])
        ), name_of_object, self.get_shortest_distance(
            self.nodes[src_pos], self.nodes[best_nodes[0].pos], name_of_object, default=math.inf
        )

    # @Utils.time_measure
    def convert_grass_cells_to_wall(self):
        converted_map = Graph((self.dim[0], self.dim[1]), self.base_pos)
        for pos in self.nodes.keys():
            if self.nodes[pos].grass > 0:
                converted_map.nodes[pos] = Node(
                    pos=pos,
                    discovered=True,
                    wall=True
                )
            else:
                converted_map.nodes[pos] = self.nodes[pos]
        return converted_map

    # @Utils.time_measure
    def convert_bread_cells_to_wall(self):
        converted_map = Graph((self.dim[0], self.dim[1]), self.base_pos)
        for pos in self.nodes.keys():
            if self.nodes[pos].bread > 0:
                converted_map.nodes[pos] = Node(
                    pos=pos,
                    discovered=True,
                    wall=True
                )
            else:
                converted_map.nodes[pos] = self.nodes[pos]
        return converted_map

    def convert_base_possible_cells_to_wall(self, base_possible_cells):
        converted_map = Graph((self.dim[0], self.dim[1]), self.base_pos)
        for pos in self.nodes.keys():
            if pos in [p[1] for p in base_possible_cells]:
                converted_map.nodes[pos] = Node(
                    pos=pos,
                    discovered=True,
                    wall=True
                )
            else:
                converted_map.nodes[pos] = self.nodes[pos]
        return converted_map

    def get_first_move_to_base(self, src, number_of_object):
        dest = self.nodes[self.base_pos]
        resource_number = number_of_object.get('bread', 0) + number_of_object.get('grass', 0)
        if src.pos == dest.pos:
            print('IM IN base')
            return None

        q = [src]
        in_queue = {src.pos: True}
        dist = {src.pos: 0}
        parent = {src.pos: src.pos}

        if src.wall:
            return None

        while q:
            current_node = q.pop(0)
            in_queue[current_node.pos] = False
            neighbors = self.get_neighbors(current_node.pos)

            for neighbor in neighbors:
                next_node = self.nodes[neighbor]
                if int(next_node.trap) * resource_number:
                    continue
                if parent.get(next_node.pos) is None:
                    parent[next_node.pos] = current_node.pos
                    q.append(next_node)
                    weight = self.get_worker_weight(current_node, next_node)
                    if dist.get(next_node.pos) is None or weight + dist[current_node.pos] < dist.get(next_node.pos):
                        dist[next_node.pos] = weight + dist[current_node.pos]
                        parent[next_node.pos] = current_node.pos
                        if not in_queue.get(next_node.pos):
                            in_queue[next_node.pos] = True
                            q.append(next_node)

        return Direction.get_value(
            self.step(src.pos, self.get_first_move_from_parent(parent, src.pos, dest.pos))
        ) if dist.get(dest.pos) else None

    def get_reachable_resource_from_base(self):
        reachable_resource = set()
        q = [self.nodes[self.base_pos]]
        parent = {self.base_pos: self.base_pos}

        while q:
            current_node = q.pop(0)
            if current_node.bread + current_node.grass > 0:
                reachable_resource.add(current_node.pos)
            neighbors = self.get_neighbors(current_node.pos)

            for neighbor in neighbors:
                next_node = self.nodes[neighbor]
                if not next_node.trap and parent.get(next_node.pos) is None:
                    parent[next_node.pos] = current_node.pos
                    q.append(next_node)

        return reachable_resource
