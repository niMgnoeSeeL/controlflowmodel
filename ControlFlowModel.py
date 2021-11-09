import operator
import sys
from itertools import starmap
from random import choice, randint, random
from typing import Dict, List, Set, Tuple

from sklearn import tree

from Coverage import FunctionCoverageRunner, population_coverage
from example.python.crash import crashme
from example.python.triangle import triangle
from FormulaGenerator import FormulaGenerator
from Fuzzer import FunctionRunner
from GreyboxFuzzer import GreyboxFuzzerRecorder
from MutationFuzzer import MutationFuzzer, Mutator, PowerSchedule


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


class CoverageGraph:
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

    def __iter__(self):
        return iter(self.nodes)




class ControlFlowModel:
    def __init__(
        self,
        cov_graph: CoverageGraph,
        record: Dict[Tuple[Tuple[str, int]], Set[str]],
    ) -> None:
        self._cov_tree = cov_graph
        self._record = record
        self._formula_generator = FormulaGenerator()

    def identify_branch(self) -> None:
        self._bnodes = []
        for node in self._cov_tree:
            if node.num_child() > 1:
                self._bnodes.append(node)
        print(self._bnodes)

    def get_covering_inputs(self, node: Node):
        covering_inputs = set()
        for cov, inputs in self._record.items():
            if node.label in cov:
                covering_inputs = covering_inputs.union(inputs)
        return covering_inputs

    def calc_fitness(self, formula, accepts, rejects):
        fitness = 0
        for inp in accepts:
            fitness += int(formula(inp)) * 2 - 1
        for inp in rejects:
            fitness += int(not formula(inp)) * 2 - 1
        return fitness

    def estimate_predicate(
        self, accepts: List, rejects: List, max_trial=100000
    ):
        input_size = len(accepts + rejects)
        gb_fitness, gb_formula, gb_formula_str = -sys.maxsize, None, None
        trial = 0
        while trial < max_trial:
            try:
                if random() >= 0.5:
                    sample = choice(accepts)
                    formula, formula_str = self._formula_generator.generate(
                        sample, True
                    )
                else:
                    sample = choice(rejects)
                    formula, formula_str = self._formula_generator.generate(
                        sample, False
                    )
            except IndexError as _:
                continue

            fitness = self.calc_fitness(formula, accepts, rejects)
            if fitness > gb_fitness:
                gb_formula, gb_formula_str, gb_fitness = (
                    formula,
                    formula_str,
                    fitness,
                )
            if fitness == input_size:
                break
            trial += 1
        return gb_formula, gb_formula_str, gb_fitness / input_size

    def model(self) -> None:
        self.identify_branch()
        self._edge_condition = {}
        for bnode in self._bnodes:
            pool = self.get_covering_inputs(bnode)
            for branch in bnode:
                accepts = self.get_covering_inputs(branch).intersection(pool)
                rejects = pool - accepts
                if len(accepts) and len(rejects):
                    formula, formula_str, conf = self.estimate_predicate(
                        list(accepts), list(rejects)
                    )
                    self._edge_condition[Edge(bnode, branch)] = (
                        formula_str,
                        conf,
                    )
                else:
                    self._edge_condition[Edge(bnode, branch)] = None, None

    def __str__(self) -> str:
        ret = ""
        for edge, pred in self._edge_condition.items():
            formula_str, conf = pred
            ret += f"{edge} := {formula_str} ({conf=})\n"
        return ret

    __repr__ = __str__


if __name__ == "__main__":
    n = 30000
    seed_input = "good"

    program_str = sys.argv[1]
    if program_str == "crash":
        program = crashme
    elif program_str == "triangle":
        program = triangle

    greybox_recorder = GreyboxFuzzerRecorder(
        [seed_input], Mutator(), PowerSchedule()
    )
    greybox_recorder.runs(FunctionCoverageRunner(program), trials=n)
    record = greybox_recorder.get_record()

    coverage_graph = CoverageGraph()
    for cov, inputs in record.items():
        print(f"[Coverage]: {cov}, [Input]: {inputs}")
        coverage_graph.accept(cov)
    coverage_graph.print_tree()

    cfm = ControlFlowModel(cov_graph=coverage_graph, record=record)
    cfm.model()
    print(cfm)
