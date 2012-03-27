from __future__ import division
import pymbolic.primitives as prim
import sympy as sp




class _SympyMapper(object):
    def __call__(self, expr, *args, **kwargs):
        return self.rec(expr, *args, **kwargs)

    def rec(self, expr, *args, **kwargs):
        mro = list(type(expr).__mro__)
        dispatch_class = kwargs.pop("dispatch_class", type(self))

        while mro:
            method_name = "map_"+mro.pop(0).__name__

            try:
                method = getattr(dispatch_class, method_name)
            except AttributeError:
                pass
            else:
                return method(self, expr, *args, **kwargs)

        return self.not_supported(expr)

    def not_supported(self, expr):
        raise NotImplementedError(
                "%s does not know how to map type '%s'"
                % (type(self).__name__,
                    type(expr).__name__))




class ToPymbolicMapper(_SympyMapper):
    def map_Symbol(self, expr):
        return prim.Variable(expr.name)

    def map_ImaginaryUnit(self, expr):
        return 1j

    def map_Add(self, expr):
        return prim.Sum(tuple(self.rec(arg) for arg in expr.args))

    def map_Mul(self, expr):
        return prim.Product(tuple(self.rec(arg) for arg in expr.args))

    def map_Rational(self, expr):
        num = self.rec(expr.p)
        denom = self.rec(expr.q)

        if prim.is_zero(denom-1):
            return num
        return prim.Quotient(num, denom)

    def map_Pow(self, expr):
        return prim.Power(self.rec(expr.base), self.rec(expr.exp))

    def map_Subs(self, expr):
        return prim.Substitution(self.rec(expr.expr),
                tuple(v.name for v in expr.variables),
                tuple(self.rec(v) for v in expr.point),
                )

    def map_Derivative(self, expr):
        return prim.Derivative(self.rec(expr.expr),
                tuple(v.name for v in expr.variables))

    def not_supported(self, expr):
        if isinstance(expr, int):
            return expr
        elif getattr(expr, "is_Function", False):
            return prim.Variable(type(expr).__name__)(
                    *tuple(self.rec(arg) for arg in expr.args))
        else:
            return _SympyMapper.not_supported(self, expr)
