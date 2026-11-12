"""Evaluate the small integer parameter expressions in the frozen RTL top.

This deliberately rejects unsupported SystemVerilog rather than extracting a
numeric prefix (which would incorrectly report C=5 for C=5*L+1).
"""
import ast
import operator
import re


def integer_expression(expression, values):
    node = ast.parse(expression.replace('$clog2', 'clog2'), mode='eval').body
    operations = {ast.Add: operator.add, ast.Sub: operator.sub,
                  ast.Mult: operator.mul, ast.LShift: operator.lshift,
                  ast.RShift: operator.rshift}

    def visit(n):
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return n.value
        if isinstance(n, ast.Name):
            return values[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in operations:
            return operations[type(n.op)](visit(n.left), visit(n.right))
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == 'clog2' and len(n.args) == 1 and not n.keywords):
            value = visit(n.args[0])
            if value <= 0:
                raise ValueError('positive clog2 argument required')
            return (value - 1).bit_length()
        raise ValueError('unsupported parameter expression: ' + expression)

    return visit(node)


def top_parameters(source, overrides):
    declaration = re.search(r'\bmodule\s+r2_many_tile\s*#\((.*?)\)\s*\(', source, re.S)
    if not declaration:
        raise ValueError('missing many_tile parameter declaration')
    values = {}
    for assignment in declaration[1].split(','):
        name, expression = assignment.strip().removeprefix('parameter ').split('=', 1)
        name = name.strip()
        values[name] = (overrides[name] if name in overrides
                        else integer_expression(expression.strip(), values))
    if set(overrides) - set(values):
        raise ValueError('unknown parameter override')
    return values
