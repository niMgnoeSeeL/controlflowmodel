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



class ControlFlowModel:
    def __init__(
        self,
        cov_graph: CoverageGraph,
        record: Dict[Tuple[Tuple[str, int]], Set[str]],
    ) -> None:
        self._cov_tree = cov_graph
        self._record = record
        self._edge_condition = {}
        self._context_map = {}
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
