import json
import math
import random


class Node:
    GRASS_WEIGHT = 1
    BREAD_WEIGHT = 1
    DISTANCE_WEIGH = 2

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
    def grass_value(self, src, dest, shortest_path_info):
        distance = Graph.get_shortest_distance(self, src, shortest_path_info, default=math.inf)
        return -distance * self.DISTANCE_WEIGH + self.grass * self.GRASS_WEIGHT + src.grass * src.GRASS_WEIGHT

    def bread_value(self, src, dest, shortest_path_info):
        distance = Graph.get_shortest_distance(self, src, shortest_path_info, default=math.inf)
        return -distance * self.DISTANCE_WEIGH + self.bread * self.BREAD_WEIGHT + src.bread * src.BREAD_WEIGHT


class Graph:
    def __init__(self, dim, base_pos):
        self.dim = dim  # width, height
        self.base_founded = False
        self.nodes = {}
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
        path = self.shortest_path(src, dest)
        if path is not None:
            next_pos = path[1]
            if next_pos[0] - src[0] in [1, -(self.dim[0] - 1)]:
                return "RIGHT"
            if next_pos[0] - src[0] in [-1, self.dim[0] - 1]:
                return "LEFT"
            if next_pos[1] - src[1] in [-1, self.dim[1] - 1]:
                return "UP"
            if next_pos[1] - src[1] in [1, -(self.dim[1] - 1)]:
                return "DOWN"
        else:
            return "NONE"

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
        if self.nodes[pos].wall:
            return []
        neighbors = [self.up(pos), self.right(pos), self.down(pos),
                     self.left(pos)]
        neighbors = [n for n in neighbors if not self.nodes[n].wall]
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
        return Node(pos=node.pos, discovered=False, wall=random.choice([True, False, False, False]))

    def get_node(self, pos):
        return self.nodes[pos] if self.nodes[pos].discovered else self.guess_node(self.nodes[pos])

    def get_weight(self, src, dest):
        # todo: make it better on guessing nodes
        weight = src.get_distance(dest)
        return weight

    def get_shortest_path(self, src, nodes):
        q = [src]
        in_queue = {src.pos: True}
        dist = {src.pos: 0}
        parent = {src.pos: src.pos}

        if src.wall:
            return {
                'dist': dist,
                'parent': parent,
            }

        while q:
            current_node = q.pop(0)
            neighbors = self.get_neighbors(current_node.pos)
            in_queue[current_node.pos] = False

            for neighbor in neighbors:
                next_node = nodes[neighbor]
                if next_node.wall:
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

    def get_random_nodes(self):
        return {pos: self.get_node(pos) for pos in self.nodes.keys()}

    def find_all_shortest_path(self):
        shortest_path_info = {}
        nodes = self.get_random_nodes()

        for pos in self.nodes.keys():
            shortest_path_info[pos] = self.get_shortest_path(nodes[pos], nodes)
        return shortest_path_info

    @staticmethod
    def get_nearest_grass_nodes(src, dest, nodes, shortest_path_info):
        grass_nodes = []
        for node in nodes.values():
            if node.grass > 0:
                grass_nodes.append(node)
        return sorted(grass_nodes, key=lambda n: n.grass_value(src, dest, shortest_path_info), reverse=True)[:20]

    @staticmethod
    def get_nearest_bread_nodes(src, dest, nodes, shortest_path_info):
        bread_nodes = []
        for node in nodes.values():
            if node.grass > 0:
                bread_nodes.append(node)
        return sorted(bread_nodes, key=lambda n: n.bread_value(src, dest, shortest_path_info), reverse=True)[:20]

    @staticmethod
    def get_shortest_distance(src, dest, shortest_path_info, default=None):
        return shortest_path_info[src.pos]['dist'].get(dest.pos, default)
