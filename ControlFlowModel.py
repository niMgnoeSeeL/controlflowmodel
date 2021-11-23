import operator
import sys
from functools import reduce
from itertools import starmap
from random import choice, randint, random
from typing import Dict, List, Set, Tuple

from sklearn import tree

from Coverage import FunctionCoverageRunner, population_coverage
from example.python.crash import crashme
from example.python.triangle import triangle
from FormulaGenerator import PredicateGenerator
from Fuzzer import FunctionRunner
from graph import Edge, Node
from GreyboxFuzzer import GreyboxFuzzerRecorder
from MutationFuzzer import MutationFuzzer, Mutator, PowerSchedule


class ControlFlowModel:
    def __init__(self, record, contcov_graph, coverage_graph, context_map=None):
        self._record = record
        self._contcov_graph = contcov_graph
        self._coverage_graph = coverage_graph
        self._context_map = context_map or {}
        self._edge_condition = {}
        self._bnodes = None
        self._formula_generator = PredicateGenerator()

    def set_context_map(self, context_map):
        self._context_map = context_map

    def identify_branch(self) -> None:
        self._bnodes = []
        for node in self._coverage_graph:
            if node.num_child() > 1:
                self._bnodes.append(node)
        print(self._bnodes)

    def get_context_nodes(self, coverage_node) -> Set[Node]:
        return {
            context_node
            for context_node in self._contcov_graph
            if coverage_node.label == context_node.label[1]
        }

    def get_input(self, contcov_node) -> Set[str]:
        covering_inputs = set()
        for path, inputs in self._record.items():
            if contcov_node.label in path:
                covering_inputs = covering_inputs.union(inputs)
        return covering_inputs

    def get_input_in_context(self, contcov_node) -> Set[str]:
        covering_inputs = self.get_input(contcov_node)
        call_stack = contcov_node.label[0].split("-")
        inputs_in_context = set()
        for inp in covering_inputs:
            inp_in_context = inp[:]
            for call_context in call_stack:
                map_func = (
                    self._context_map[call_context]
                    if call_context in self._context_map
                    else range(len(inp_in_context))
                )
                inp_in_context = "".join([inp_in_context[i] for i in map_func])
            inputs_in_context.add(inp_in_context)
        return inputs_in_context

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

    def model_condition(self) -> None:
        if self._bnodes is None:
            self.identify_branch()
        for node in self._bnodes:
            context_nodes = self.get_context_nodes(node)
            pool = reduce(
                set.union,
                [self.get_input_in_context(node) for node in context_nodes],
            )
            for child in node:
                print(f"Modeling {node} -> {child}...", end=" ")
                context_child = self.get_context_nodes(child)
                accepts = reduce(
                    set.union,
                    [self.get_input_in_context(node) for node in context_child],
                ).intersection(pool)
                rejects = pool - accepts
                if len(accepts) and len(rejects):
                    formula, formula_str, conf = self.estimate_predicate(
                        list(accepts), list(rejects)
                    )
                    self._edge_condition[Edge(node, child)] = (
                        formula_str,
                        conf,
                    )
                    print(f"formula: <{formula_str}> (conf: {conf})")
                else:
                    self._edge_condition[Edge(node, child)] = (None, None)
                    print("No accepts or rejects; skip.")

    
    def get_edge_cond(self):
        return self._edge_condition
    
    def get_context_map(self):
        return self._context_map