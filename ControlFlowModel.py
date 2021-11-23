import operator
import string
import sys
from functools import reduce
from itertools import starmap
from random import choice, randint, random
from typing import Dict, List, Set, Tuple

import numpy as np
from sklearn import tree

from FormulaGenerator import PredicateGenerator
from MutationFuzzer import Mutator
from graph import Edge, Node


class ControlFlowModel:
    def __init__(self, record, contcov_graph, coverage_graph, runner):
        self._record = record
        self._contcov_graph = contcov_graph
        self._coverage_graph = coverage_graph
        self._runner = runner
        self._edge_condition = {}
        self._bnodes = None
        self._mutator = Mutator()
        self._formula_generator = PredicateGenerator()

    def set_context_map(self, context_map):
        self._context_map = context_map

    def identify_branch(self) -> None:
        self._bnodes = []
        for node in self._coverage_graph:
            if node.num_child() > 1:
                self._bnodes.append(node)
        print("branches:", self._bnodes)

    def identify_call_context(self) -> None:
        self._call_contexts = set()
        for path, _ in self._record.items():
            for cont_cov in path:
                call_stack, _ = cont_cov
                for call_context in call_stack.split("-"):
                    if call_context != "":
                        self._call_contexts.add(call_context)
        print("call contexts:", self._call_contexts)

    def mutate_input(self, inp, idx) -> str:
        # sourcery skip: use-assigned-variable
        random_chr = inp[idx]
        while random_chr == inp[idx]:
            random_chr = self._mutator.generate_random_character()
        return inp[:idx] + random_chr + inp[idx + 1 :]

    def get_path(self, inp):
        self._runner.run(inp)
        return self._runner.trace()

    def get_contcov_bnode_coverage(self, path, context_bnode_labels):
        contcov_bnodes = {
            contcov: set()
            for contcov in path
            if contcov in context_bnode_labels
        }
        for idx, contcov in enumerate(path):
            if contcov in context_bnode_labels:
                contcov_bnodes[contcov].add(path[idx + 1])
        return contcov_bnodes

    def get_context_nodes(self, coverage_node) -> Set[Node]:
        return {
            context_node
            for context_node in self._contcov_graph
            if coverage_node.label == context_node.label[1]
        }

    def get_context_bnode_labels(self):
        context_bnodes = reduce(
            set.union, [self.get_context_nodes(bnode) for bnode in self._bnodes]
        )
        return {bnode.label for bnode in context_bnodes}

    def model_context(self, inp_sample_size=1, mut_trial=1) -> None:
        self._context_map = {}
        # set difference로 차이를 보면, 서로 다른 context에서 cover가 되었을 때, 영향을 미치는 것이 맞지만, 이를 파악하지 못 할 수 있다.
        # 처음 바뀐 부분으로 차이를 보면, mutate 된 부분이 여러 곳에 영향을 미치는 것을 파악하지 못 할 수 있다.
        # 우선은 set difference로 가자.
        context_bnode_labels = self.get_context_bnode_labels()
        context_bnode_essential_idx = {
            bnode_label: set() for bnode_label in context_bnode_labels
        }
        for path, inputs in self._record.items():
            print(f"[D] Analyze {path=}")
            contcov_bnodes = self.get_contcov_bnode_coverage(
                path, context_bnode_labels
            )
            inp_samples = np.random.choice(
                list(inputs), min(inp_sample_size, len(inputs)), replace=False
            )
            for inp in inp_samples:
                print(f"[D] Sample input: {inp}")
                for idx in range(len(inp)):
                    for _ in range(mut_trial):
                        new_inp = self.mutate_input(inp, idx)
                        print(f"[D]    New input: {new_inp}")
                        new_path = self.get_path(new_inp)
                        new_contcov_bnodes = self.get_contcov_bnode_coverage(
                            new_path, context_bnode_labels
                        )
                        for (
                            bnode_label,
                            child_label_set,
                        ) in contcov_bnodes.items():
                            if bnode_label not in new_contcov_bnodes:
                                continue
                            elif (
                                child_label_set
                                != new_contcov_bnodes[bnode_label]
                            ):
                                context_bnode_essential_idx[bnode_label].add(
                                    idx
                                )
        callstack_essential_idx = {}
        for k, v in context_bnode_essential_idx.items():
            if k[0] == "":
                continue
            callstack = tuple(k[0].split("-"))
            if callstack not in callstack_essential_idx:
                callstack_essential_idx[callstack] = set()
            callstack_essential_idx[callstack] = callstack_essential_idx[
                callstack
            ].union(v)
        for k, v in callstack_essential_idx.items():
            print(f"[D, callstack_essential_idx] {k=} {v=}")
        # todo: 그래서, 여기서 어떻게 context_map을 만들 수 있나? 아래는 임시 방편.
        for k, v in callstack_essential_idx.items():
            self._context_map[k[0]] = range(min(v), max(v) + 1)
            print(f"[context_map] {k=} {v=}")
        

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
