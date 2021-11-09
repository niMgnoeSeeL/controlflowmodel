import random
from typing import List

from Coverage import FunctionCoverageRunner, population_coverage
from example.python.crash import crashme
from Fuzzer import Fuzzer


class Mutator:
    def __init__(self):
        self.mutators = [
            self.delete_random_character,
            self.insert_random_character,
            self.flip_random_character,
        ]

    def insert_random_character(self, s):
        pos = random.randint(0, len(s))
        random_character = chr(random.randrange(32, 127))
        return s[:pos] + random_character + s[pos:]

    def delete_random_character(self, s):
        if s == "":
            return self.insert_random_character(s)

        pos = random.randint(0, len(s) - 1)
        return s[:pos] + s[pos + 1 :]

    def flip_random_character(self, s):
        if s == "":
            return self.insert_random_character(s)

        pos = random.randint(0, len(s) - 1)
        c = s[pos]
        bit = 1 << random.randint(0, 6)
        new_c = chr(ord(c) ^ bit)
        return s[:pos] + new_c + s[pos + 1 :]

    def mutate(self, inp):
        mutator = random.choice(self.mutators)
        return mutator(inp)


class PowerSchedule:
    def assign_energy(self, population):
        for seed in population:
            seed.energy = 1

    def normalized_energy(self, population):
        energy = [seed.energy for seed in population]
        sum_energy = sum(energy)
        return [nrg / sum_energy for nrg in energy]

    def choose(self, population):
        self.assign_energy(population)
        norm_energy = self.normalized_energy(population)
        return random.choices(population, weights=norm_energy)[0]


class Seed:
    def __init__(self, data) -> None:
        self.data = data

    def __str__(self) -> str:
        return self.data

    __repr__ = __str__


class MutationFuzzer(Fuzzer):
    def __init__(
        self, seeds: List, mutator: Mutator, schedule: PowerSchedule
    ) -> None:
        self.seeds = seeds
        self.mutator = mutator
        self.schedule = schedule
        self.inputs = []
        self.reset()

    def reset(self):
        self.population = [Seed(x) for x in self.seeds]
        self.seed_index = 0

    def create_candidate(self):
        seed = self.schedule.choose(self.population)

        candidate = seed.data
        trials = min(len(candidate), 1 << random.randint(1, 5))
        for _ in range(trials):
            candidate = self.mutator.mutate(candidate)
        return candidate

    def fuzz(self):
        if self.seed_index < len(self.seeds):
            self.inp = self.seeds[self.seed_index]
            self.seed_index += 1
        else:
            self.inp = self.create_candidate()

        self.inputs.append(self.inp)
        return self.inp


if __name__ == "__main__":
    import time

    n = 30000
    seed_input = "good"
    blackbox_fuzzer = MutationFuzzer([seed_input], Mutator(), PowerSchedule())
    start = time.time()
    blackbox_fuzzer.runs(FunctionCoverageRunner(crashme), trials=n)
    end = time.time()

    print(
        f"It took the blackbox mutation-based fuzzer {end - start:.2f} seconds to generate and execute {n} inputs."
    )

    _, blackbox_coverage = population_coverage(blackbox_fuzzer.inputs, crashme)
    bb_max_coverage = max(blackbox_coverage)

    print(
        f"The blackbox mutation-based fuzzer achieved a maximum coverage of {bb_max_coverage} statements."
    )

    covinc_inputs = [seed_input] + [
        blackbox_fuzzer.inputs[idx]
        for idx in range(len(blackbox_coverage))
        if blackbox_coverage[idx] > blackbox_coverage[idx - 1]
    ]
    print(covinc_inputs)
