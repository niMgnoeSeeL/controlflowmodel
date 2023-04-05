from graphviz import Digraph
from typing import List


class Node:
    def __init__(self, label) -> None:
        self.label = label
        self._childs = []

    def add_child(self, child_node) -> None:
        self._childs.append(child_node)

    def get_child(self, label):
        for child in self._childs:
            if child.label == label:
                return child
        return None

    def num_child(self):
        return len(self._childs)

    def __iter__(self):
        return iter(self._childs)

    def __str__(self) -> str:
        return f"<{self.label}>"

    __repr__ = __str__


class Edge:
    def __init__(self, src: Node, dest: Node) -> None:
        self.src = src.label
        self.dest = dest.label

    def __hash__(self) -> int:
        return hash((self.src, self.dest))

    def __str__(self) -> str:
        return f"E<{self.src} -> {self.dest}>"


class Graph:
    def __init__(self) -> None:
        self.root = Node("ENTRY")
        self.nodes: List[Node] = [self.root]

    def find_node(self, label) -> Node:
        node_of_label = [node for node in self.nodes if node.label == label]
        if len(node_of_label):
            return node_of_label[0]
        else:
            return None

    def add_node(self, label, parent: Node) -> Node:
        node_of_label = [node for node in self.nodes if node.label == label]
        if len(node_of_label):
            print(f"Node of label {label} already exists. PASS.")
            return None
        else:
            new_node = Node(label)
            self.nodes.append(new_node)
            parent.add_child(new_node)
            return new_node

    def accept(self, path) -> None:
        curr_node = self.root
        for elem in path:
            if next_node := curr_node.get_child(elem):
                curr_node = next_node
            elif node := self.find_node(elem):
                curr_node.add_child(node)
                curr_node = node
            else:
                curr_node = self.add_node(elem, curr_node)

    def get_tree(self):
        return self.root

    def print_tree(self):
        traversed_nodes = set()
        queue = [self.root]
        while len(traversed_nodes) != len(self.nodes):
            if not len(queue):
                print("Not all nodes are connected.")
                print(f"Traversed nodes: {traversed_nodes}")
                print(f"Remaining nodes: {set(self.nodes) - traversed_nodes}")
                raise Exception()
            curr_node = queue.pop(0)
            print(f"{curr_node}")
            for child in curr_node:
                print(f"|   {child}")
                queue.append(child)
            traversed_nodes.add(curr_node)

    def print_graph(self, title: str):
        dot = Digraph()
        node_dict = {}
        for idx, node in enumerate(self.nodes):
            node_dict[node] = f"N{idx}"
            dot.node(f"N{idx}", str(node))
        dot.node("N-1", "<EXIT>")
        for node in self:
            if node.num_child() == 0:
                dot.edge(node_dict[node], "N-1")
            for child in node:
                dot.edge(node_dict[node], node_dict[child])
        # add title
        dot.attr(label=title)
        # dot.render(view=True, filename=outfile)
        return dot

    def __iter__(self):
        return iter(self.nodes)
