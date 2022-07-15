import numpy as np
import operator
from random import choice, randint, random


class PredicateGenerator:
    def __init__(self) -> None:
        self.map_op_str = {
            operator.eq: "==",
            operator.le: "<=",
            operator.ge: ">=",
            operator.ne: "!=",
            operator.lt: "<",
            operator.gt: ">",
        }
        self.positive_ops = [
            operator.eq,
            operator.le,
            operator.ge,
        ]
        self.negative_ops = [
            operator.ne,
            operator.lt,
            operator.gt,
        ]
        self.ops = self.positive_ops + self.negative_ops

    def gen_unary_comp(self):
        pos = randint(0, self.curr_input_size - 1)
        val = self.curr_input[pos]
        op = (
            choice(self.positive_ops)
            if self.is_positive
            else choice(self.negative_ops)
        )
        formula = lambda x: op(x[pos], val) if len(x) > pos else False
        formula_str = f"lambda x: x[{pos}] {self.map_op_str[op]} '{val}'"
        return formula, formula_str

    def gen_binary_comp(self):
        pos1 = randint(0, self.curr_input_size - 1)
        pos2 = randint(0, self.curr_input_size - 2)
        if pos2 >= pos1:
            pos2 += 1
        sat_ops = {op for op in self.ops if op(pos1, pos2)}
        if not self.is_positive:
            sat_ops = set(self.ops) - sat_ops
        op = choice(list(sat_ops))
        formula = (
            lambda x: op(x[pos1], x[pos2])
            if len(x) > max({pos1, pos2})
            else False
        )
        formula_str = f"lambda x: x[{pos1}] {self.map_op_str[op]} x[{pos2}]"
        return formula, formula_str

    def get_range_comp(self):
        pos = randint(0, self.curr_input_size - 1)
        posval = ord(self.curr_input[pos])
        less_range, greater_range = range(posval + 1), range(
            posval, 0x10FFFF + 1
        )
        if self.is_positive:
            lessval = chr(np.random.choice(less_range))
            greaterval = chr(np.random.choice(greater_range))
            # print(lessval, greaterval)
            formula = (
                lambda x: x[pos] >= lessval and x[pos] <= greaterval
                if len(x) > pos
                else False
            )
            formula_str = f"lambda x: '{lessval}' <= x[{pos}] <= '{greaterval}'"
        elif posval == 0:
            greaterval = chr(np.random.choice(greater_range))
            formula = lambda x: x[pos] > greaterval if len(x) > pos else False
            formula_str = f"lambda: x x[{pos}] > '{greaterval}'"
        elif posval == 0x10FFFF:
            lessval = chr(np.random.choice(less_range))
            formula = lambda x: x[pos] < lessval if len(x) > pos else False
            formula_str = f"lambda: x x[{pos}] < '{lessval}'"
        else:
            lessval = chr(np.random.choice(less_range))
            greaterval = chr(np.random.choice(greater_range))
            formula = (
                lambda x: x[pos] < lessval or x[pos] > greaterval
                if len(x) > pos
                else False
            )
            formula_str = (
                f"lambda: x x[{pos}] < '{lessval}' or x[{pos}] > '{greaterval}'"
            )
        return formula, formula_str

    def generate(self, sample_input, is_positive):
        self.curr_input = sample_input
        self.is_positive = is_positive
        self.curr_input_size = len(sample_input)
        if self.curr_input_size == 0:
            if is_positive:
                return lambda x: len(x) == 0, "lambda x: len(x) == 0"
            else:
                return lambda x: len(x) != 0, "lambda x: len(x) != 0"
        elif self.curr_input_size == 1:
            if np.random.random() < 0.5:
                return self.gen_unary_comp()
            else:
                return self.get_range_comp()
        else:
            if np.random.random() < 1 / 3:
                return self.gen_unary_comp()
            elif np.random.random() < 2 / 3:
                return self.get_range_comp()
            else:
                return self.gen_binary_comp()
