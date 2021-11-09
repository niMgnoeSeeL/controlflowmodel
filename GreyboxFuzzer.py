import random
from typing import List

from Coverage import FunctionCoverageRunner, population_coverage
from example.python.crash import crashme
from MutationFuzzer import MutationFuzzer, Mutator, PowerSchedule, Seed


class GreyboxFuzzer(MutationFuzzer):
    def reset(self):
        super().reset()
        self.coverages_seen = set()
        self.population = []

    def run(self, runner: FunctionCoverageRunner):
        result, outcome = super().run(runner)
        new_coverage = frozenset(runner.coverage())
        if new_coverage not in self.coverages_seen:
            seed = Seed(self.inp)
            seed.coverage = runner.coverage()
            self.coverages_seen.add(new_coverage)
            self.population.append(seed)

        return (result, outcome)


class GreyboxFuzzerRecorder(GreyboxFuzzer):
    def __init__(
        self, seeds: List, mutator: Mutator, schedule: PowerSchedule
    ) -> None:
        super().__init__(seeds, mutator, schedule)
        self.cov_record = {}

    def run(self, runner: FunctionCoverageRunner):
        result, outcome = super().run(runner)
        # preserve covered element order -> ordered coverage overage
        new_overage = tuple(dict.fromkeys(runner.trace()).keys())
        if new_overage not in self.cov_record:
            self.cov_record[new_overage] = set()
        if len(self.cov_record[new_overage]) < 10:
            self.cov_record[new_overage].add(self.inp)

        return (result, outcome)

    def get_record(self):
        return self.cov_record


if __name__ == "__main__":
    import time

    n = 30000
    seed_input = "good"
    greybox_fuzzer = GreyboxFuzzer([seed_input], Mutator(), PowerSchedule())

    start = time.time()
    greybox_fuzzer.runs(FunctionCoverageRunner(crashme), trials=n)
    end = time.time()

    print(
        f"It took the greybox mutation-based fuzzer {end - start:.2f} seconds to generate and execute {n} inputs."
    )

    _, greybox_coverage = population_coverage(greybox_fuzzer.inputs, crashme)
    gb_max_coverage = max(greybox_coverage)

    print(
        f"The greybox mutation-based fuzzer achieved a maximum coverage of {gb_max_coverage} statements."
    )

    covinc_inputs = [seed_input] + [
        greybox_fuzzer.inputs[idx]
        for idx in range(len(greybox_coverage))
        if greybox_coverage[idx] > greybox_coverage[idx - 1]
    ]
    print(covinc_inputs)
