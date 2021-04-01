import json
import math
import random


def pos_str(pos):
    return f"{pos[0]},{pos[1]}"


def str_pos(s: str):
    return int(s.split(',')[0]), int(s.split(',')[1])


class Node:
    GRASS_WEIGHT = 1
    BREAD_WEIGHT = 1
    DISTANCE_WEIGH = 2

    def __init__(self, pos, discovered, wall=True, bread=0, grass=0):
        self.pos = pos
        self.discovered = discovered
        self.wall = wall
        self.bread = bread
        self.grass = grass

    def __repr__(self):
        return f"{self.__dict__}"

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
        self.adj = {}
        self.nodes = {}
        for i in range(dim[0]):
            for j in range(dim[1]):
                self.adj[(i, j)] = []
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

    def init_from_graph(self, adj_json, nodes_json):
        # adj part
        adj_dict = json.loads(adj_json)
        self.adj.clear()
        for k, v in adj_dict.items():
            self.adj[str_pos(k)] = [str_pos(s) for s in v]
        # nodes part
        nodes_dict = json.loads(nodes_json)
        self.nodes.clear()
        for k, v in nodes_dict.items():
            d, w, b, g = list(v.values())
            self.nodes[str_pos(k)] = Node(k, d, w, b, g)

    def get_nodes(self):
        new_dict = {}
        for k, v in self.nodes.items():
            new_dict[pos_str(k)] = v.__dict__
        return json.dumps(new_dict)

    def get_adj(self):
        new_dict = {}
        for k, v in self.adj.items():
            new_dict[pos_str(k)] = [pos_str(p) for p in v]
        return json.dumps(new_dict)

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
                neighbors = self.adj[node]
                for u in neighbors:
                    path = list(prev_path)
                    path.append(u)
                    q.append(path)
                    if u == dest:
                        return path
                visited.append(node)

        return None

    def set_bread_grass(self, pos, b, g):
        self.nodes[pos].bread = b
        self.nodes[pos].grass = g

    def change_type(self, pos):
        self.nodes[pos].wall = False
        self.nodes[pos].discovered = True
        neighbors = self.get_neighbors(pos)
        for n in neighbors:
            if not self.is_wall(n):
                self.adj[pos].append(n)
                self.adj[n].append(pos)

    def is_wall(self, pos):
        return self.nodes[pos].wall

    def get_neighbors(self, pos):
        return [self.up(pos), self.right(pos), self.down(pos), self.left(pos)]

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
