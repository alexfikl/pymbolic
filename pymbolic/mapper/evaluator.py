from __future__ import division

__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from pymbolic.mapper import RecursiveMapper




class UnknownVariableError(Exception):
    pass




class EvaluationMapper(RecursiveMapper):
    def __init__(self, context={}):
        self.context = context
        self.common_subexp_cache = {}

    def map_constant(self, expr):
        return expr

    def map_variable(self, expr):
        try:
            return self.context[expr.name]
        except KeyError:
            raise UnknownVariableError, expr.name

    def map_call(self, expr):
        return self.rec(expr.function)(*[self.rec(par) for par in expr.parameters])

    def map_subscript(self, expr):
        return self.rec(expr.aggregate)[self.rec(expr.index)]

    def map_lookup(self, expr):
        return getattr(self.rec(expr.aggregate), expr.name)

    def map_sum(self, expr):
        return sum(self.rec(child) for child in expr.children)

    def map_product(self, expr):
        from pytools import product
        return product(self.rec(child) for child in expr.children)

    def map_quotient(self, expr):
        return self.rec(expr.numerator) / self.rec(expr.denominator)

    def map_floor_div(self, expr):
        return self.rec(expr.numerator) // self.rec(expr.denominator)

    def map_remainder(self, expr):
        return self.rec(expr.numerator) % self.rec(expr.denominator)

    def map_power(self, expr):
        return self.rec(expr.base) ** self.rec(expr.exponent)

    def map_polynomial(self, expr):
        # evaluate using Horner's scheme
        result = 0
        rev_data = expr.data[::-1]
        ev_base = self.rec(expr.base)

        for i, (exp, coeff) in enumerate(rev_data):
            if i+1 < len(rev_data):
                next_exp = rev_data[i+1][0]
            else:
                next_exp = 0
            result = (result+coeff)*ev_base**(exp-next_exp)

        return result

    def map_list(self, expr):
        return [self.rec(child) for child in expr]

    def map_numpy_array(self, expr):
        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        from pytools import indices_in_shape
        for i in indices_in_shape(expr.shape):
            result[i] = self.rec(expr[i])
        return result

    def map_common_subexpression(self, expr):
        try:
            return self.common_subexp_cache[expr.child]
        except KeyError:
            self.common_subexp_cache[expr.child] = value = self.rec(expr.child)
            return value

    def map_if_positive(self, expr):
        if self.rec(expr.criterion) > 0:
            return self.rec(expr.then)
        else:
            return self.rec(expr.else_)

    def map_min(self, expr):
        return min(self.rec(child) for child in expr.children)

    def map_max(self, expr):
        return min(self.rec(child) for child in expr.children)

    def map_tuple(self, expr):
        return tuple(self.rec(child) for child in expr)




class FloatEvaluationMapper(EvaluationMapper):
    def map_constant(self, expr):
        return float(expr)

    def map_rational(self, expr):
        return self.rec(expr.numerator) / self.rec(expr.denominator)




def evaluate(expression, context={}):
    return EvaluationMapper(context)(expression)

def evaluate_kw(expression, **context):
    return EvaluationMapper(context)(expression)

def evaluate_to_float(expression, context={}):
    return FloatEvaluationMapper(context)(expression)
