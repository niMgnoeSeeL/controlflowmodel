class Runner:
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"

    def __init__(self) -> None:
        pass

    def run(self, inp):
        return (inp, Runner.UNRESOLVED)


class PrintRunner(Runner):
    def run(self, inp):
        print(inp)
        return (inp, Runner.UNRESOLVED)


class FunctionRunner(Runner):
    def __init__(self, function) -> None:
        self.function = function

    def run_function(self, inp):
        return self.function(inp)

    def run(self, inp):
        try:
            result = self.run_function(inp)
            outcome = self.PASS
        except Exception:
            result = None
            outcome = self.FAIL

        return result, outcome


class Fuzzer:
    def __init__(self) -> None:
        pass

    def fuzz(self):
        return ""

    def run(self, runner: Runner):
        return runner.run(self.fuzz())

    def runs(self, runner: Runner, trials=10):
        return [self.run(runner) for _ in range(trials)]
