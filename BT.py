import time

from Model import Direction
from Utils import get_view_distance_neighbors, time_measure


class BT:
    def __init__(self, graph, cur, max_distance=10, start=None):
        self.start = start or time.time()
        self.graph = graph
        self.best_path = None
        self.max_distance = max_distance
        self.path = max_distance * [-1]
        self.best = None
        self.visited = set(get_view_distance_neighbors(cur, self.graph.dim[0],
                                                       self.graph.dim[1], 4))

        for pos, node in graph.nodes.items():
            if node.discovered:
                self.visited.add(pos)

    def bt(self, cur, dist):
        delay = time.time() - self.start
        if delay > 0.08:
            return
        now = len(self.visited)
        # print(cur, dist, now)
        if not self.best or now > self.best:
            # print(self.path)
            self.best_path = self.path.copy()
            self.best = now
        if dist == self.max_distance:
            return

        neighbors = self.graph.get_neighbors_with_not_discovered_nodes(cur)
        # print(neighbors)
        for next_node in neighbors:
            vis = set(get_view_distance_neighbors(next_node, self.graph.dim[0],
                                                  self.graph.dim[1], 4))
            not_changed = self.visited.copy()
            self.visited |= vis
            self.path[dist] = next_node
            self.bt(next_node, dist + 1)
            self.visited = not_changed


def solve_bt(graph, pos, max_distance=10, start=None):
    self = BT(graph, pos, max_distance, start)
    self.bt(pos, 0)
    # print("best", self.best_path)
    self.best_path = [p for p in self.best_path if p != -1]
    if not self.best_path:
        # print("FUCKED UP")
        return 0
    # print(self.best_path)
    return Direction.get_value(self.graph.step(pos, self.best_path[0]))
