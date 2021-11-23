import sys

from Fuzzer import FunctionRunner


class Coverage:
    def traceit(self, frame, event, arg):
        if self.original_trace_function is not None:
            self.original_trace_function(frame, event, arg)

        if event == "line":
            function_name = frame.f_code.co_name
            lineno = frame.f_lineno
            self._trace.append((function_name, lineno))

        return self.traceit

    def __init__(self) -> None:
        self._trace = []

    def __enter__(self):
        self.original_trace_function = sys.gettrace()
        sys.settrace(self.traceit)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        sys.settrace(self.original_trace_function)

    def trace(self):
        return self._trace

    def coverage(self):
        return set(self.trace())


class ContCov:
    def traceit(self, frame, event, arg):
        if self.original_trace_function is not None:
            self.original_trace_function(frame, event, arg)

        if event == "line":
            function_name = frame.f_code.co_name
            if function_name not in [
                "run_function",
                "coverage",
                "trace",
            ]:
                lineno = frame.f_lineno
                self._trace.append(
                    ("-".join(self._call_stack[1:-1]), (function_name, lineno))
                )
                self._prev_lineno = lineno

        if event == "call":
            function_name = frame.f_code.co_name
            if len(self._call_stack):
                # Update calling context
                self._call_stack[-1] = (
                    self._call_stack[-1].split(":")[0]
                    + ":"
                    + str(self._prev_lineno)
                )
            self._call_stack.append(function_name)

        if event == "return":
            self._call_stack.pop()

        return self.traceit

    def __init__(self) -> None:
        self._call_stack = []
        # todo: identify the call context
        # self._call_idx_dict = {}
        self._trace = []
        self._prev_lineno = 0

    def __enter__(self):
        self.original_trace_function = sys.gettrace()
        sys.settrace(self.traceit)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        sys.settrace(self.original_trace_function)

    def trace(self):
        return self._trace

    def coverage(self):
        return set(self.trace())


class FunctionCoverageRunner(FunctionRunner):
    def run_function(self, inp):
        with Coverage() as cov:
            try:
                result = super().run_function(inp)
            except Exception as exc:
                self._trace = cov.trace()
                self._coverage = cov.coverage()
                raise exc

        self._trace = cov.trace()
        self._coverage = cov.coverage()
        return result

    def trace(self):
        return self._trace

    def coverage(self):
        return self._coverage


class FunctionContCovRunner(FunctionRunner):
    def run_function(self, inp):
        with ContCov() as cov:
            try:
                result = super().run_function(inp)
            except Exception as exc:
                self._trace = cov.trace()
                self._coverage = cov.coverage()
                raise exc

        self._trace = cov.trace()
        self._coverage = cov.coverage()
        return result

    def trace(self):
        return self._trace

    def coverage(self):
        return self._coverage


def population_coverage(population, function):
    cumulative_coverage = []
    all_coverage = set()

    for s in population:
        with Coverage() as cov:
            try:
                function(s)
            except Exception:
                pass
        all_coverage |= cov.coverage()
        cumulative_coverage.append((len(all_coverage)))

    return all_coverage, cumulative_coverage
