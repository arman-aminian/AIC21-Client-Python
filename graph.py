class Node:
    def __init__(self, wall=True, bread=0, grass=0):
        self.wall = wall
        self.bread = bread
        self.grass = grass
        
    def __repr__(self):
        return f"{self.wall} {self.bread} {self.grass}"


class Graph:
    def __init__(self, dim, base_pos):
        self.dim = dim  # width, height
        self.adj = {}
        self.nodes = {}
        for i in range(dim[0]):
            for j in range(dim[1]):
                self.adj[(i, j)] = []
                if (i, j) == base_pos:
                    self.nodes[(i, j)] = Node(False)
                else:
                    self.nodes[(i, j)] = Node()
    
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
