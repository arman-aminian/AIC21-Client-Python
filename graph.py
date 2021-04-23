import math
import random
from itertools import chain

import Utils


class Node:
    GRASS_WEIGHT = 1
    BREAD_WEIGHT = 1
    DISTANCE_WEIGH = 2
    GRASS_LIMIT = 10
    BREAD_LIMIT = 10

    def __init__(self, pos, discovered, wall=False, bread=0, grass=0,
                 ally_workers=0, ally_soldiers=0, enemy_workers=0,
                 enemy_soldiers=0):
        # REMEMBER to change the encode/decode function after adding attrs
        self.pos = pos
        self.discovered = discovered
        self.wall = wall
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
        distance = graph.get_shortest_distance(self, src, 'grass', default=math.inf)
        return -distance * self.DISTANCE_WEIGH + min(self.GRASS_LIMIT, self.grass + src.grass) * self.GRASS_WEIGHT

    def bread_value(self, src, dest, graph, number=0):
        distance = graph.get_shortest_distance(self, src, 'bread', default=math.inf)
        return -distance * self.DISTANCE_WEIGH + min(self.BREAD_LIMIT,
                                                     src.bread + self.bread + number) * self.BREAD_WEIGHT


class Graph:
    TSP_NODE_LIMIT = 5

    def __init__(self, dim, base_pos):
        self.base_pos = base_pos
        self.dim = dim  # width, height
        self.enemy_base_pos = None
        self.nodes = {}
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
        next_pos = dest
        if next_pos[0] - src[0] in [1, -(self.dim[0] - 1)]:
            return "RIGHT"
        if next_pos[0] - src[0] in [-1, self.dim[0] - 1]:
            return "LEFT"
        if next_pos[1] - src[1] in [-1, self.dim[1] - 1]:
            return "UP"
        if next_pos[1] - src[1] in [1, -(self.dim[1] - 1)]:
            return "DOWN"

    def total_grass_number(self):
        res = 0
        for pos in self.nodes.keys():
            res = res + self.nodes[pos].grass
        return res

    def total_bread_number(self):
        res = 0
        for pos in self.nodes.keys():
            res = res + self.nodes[pos].bread
        return res

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
        if self.nodes[pos].wall:
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

    def get_weight(self, src, dest):
        # todo: make it better on guessing nodes
        weight = src.get_distance(dest)
        return weight

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
                weight = self.get_weight(current_node, next_node)
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

    def get_random_nodes(self):
        return {pos: self.get_node(pos) for pos in self.nodes.keys()}

    def find_all_shortest_path(self, number_of_object, name_of_object, nodes):
        for node in nodes:
            pos = node.pos
            self.shortest_path_info[name_of_object][pos] = self.get_shortest_path(
                self.nodes[pos], 'bread' if name_of_object == 'grass' else 'grass',
                number_of_object.get(name_of_object, 0)
            )

    def get_nearest_grass_nodes(self, src, dest, number_of_object):
        number = number_of_object.get('grass', 0)
        grass_nodes_temp = []
        for node in self.nodes.values():
            if node.grass > 0 and node.pos != src.pos and node.pos != dest.pos:
                grass_nodes_temp.append(node)

        self.find_all_shortest_path(
            number_of_object, 'grass', list(chain([src], grass_nodes_temp, [dest]))
        )
        print(grass_nodes_temp)
        grass_nodes = []
        for node in grass_nodes_temp:
            if self.get_shortest_distance(
                    node, dest, 'grass'
            ) is not None and self.get_shortest_distance(
                src, node, 'grass'
            ) is not None:
                grass_nodes.append(node)

        return sorted(grass_nodes, key=lambda n: n.grass_value(src, dest, self, number), reverse=True)[
               :self.TSP_NODE_LIMIT]

    def get_nearest_bread_nodes(self, src, dest, number_of_object):
        number = number_of_object.get('bread', 0)
        bread_nodes_temp = []
        for node in self.nodes.values():
            if node.bread > 0 and node.pos != src.pos and node.pos != dest.pos:
                bread_nodes_temp.append(node)

        self.find_all_shortest_path(
            number_of_object, 'bread', list(chain([src], bread_nodes_temp, [dest]))
        )
        print(bread_nodes_temp)
        bread_nodes = []
        for node in bread_nodes_temp:
            if self.get_shortest_distance(
                    node, dest, 'bread'
            ) is not None and self.get_shortest_distance(
                src, node, 'bread'
            ) is not None:
                bread_nodes.append(node)

        return sorted(bread_nodes, key=lambda n: n.bread_value(src, dest, self, number), reverse=True)[
               :self.TSP_NODE_LIMIT]

    def get_shortest_distance(self, src, dest, name_of_object, default=None):
        return self.shortest_path_info[name_of_object].get(src.pos, {}).get('dist', {}).get(dest.pos, default)

    def get_shortest_path_from_shortest_path_info(self, src, dest, name_of_object):
        parent = self.shortest_path_info[name_of_object][src.pos].get('parent', [])
        path = []
        pos = dest.pos
        while parent[pos] != pos:
            path.append(self.nodes[pos])
            pos = parent[pos]
        return list(reversed(path))

    def get_first_move_to_enemy_base(self, src_pos):
        our_base = self.base_pos
        their_base = self.enemy_base_pos or (self.dim[0] - 1 - our_base[0], self.dim[1] - 1 - our_base[1])
        path = self.get_path(self.nodes[src_pos], self.nodes[their_base])
        return self.step(src_pos, path[0].pos) if path else "None"

    def get_first_move_to_opposite_node(self, src_pos):
        opposite_node_pos = (self.dim[0] - 1 - src_pos[0], self.dim[1] - 1 - src_pos[1])
        path = self.get_path(self.nodes[src_pos], self.nodes[opposite_node_pos])
        return self.step(src_pos, path[0].pos) if path else "None"
