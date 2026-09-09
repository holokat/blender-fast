"""Numeric expressions only. Never evaluate Python or resolve attributes."""
import ast
import math
import operator

OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod}
FUNCS={'sin':math.sin,'cos':math.cos,'sqrt':math.sqrt,'abs':abs,'min':min,'max':max}


def evaluate(value,variables):
    def finite(number):
        if isinstance(number,bool) or not isinstance(number,(int,float)) or not math.isfinite(number) or abs(number)>1e6:
            raise ValueError('Expected a finite number with magnitude at most one million')
        return number
    if isinstance(value,(int,float)):
        return finite(value)
    if not isinstance(value,str) or not value.startswith('=') or len(value)>256:
        raise ValueError('Numeric values are numbers or expressions beginning with =')
    try:
        tree=ast.parse(value[1:],mode='eval')
        if sum(1 for _ in ast.walk(tree))>80:raise ValueError('Expression is too complex')
        def visit(node):
            if isinstance(node,ast.Expression):return visit(node.body)
            if isinstance(node,ast.Constant):return finite(node.value)
            if isinstance(node,ast.Name):
                if node.id=='pi':return math.pi
                if node.id not in variables:raise ValueError('Unknown numeric variable: '+node.id)
                return finite(variables[node.id])
            if isinstance(node,ast.BinOp) and type(node.op) in OPS:
                return finite(OPS[type(node.op)](visit(node.left),visit(node.right)))
            if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
                return finite(visit(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1))
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in FUNCS and not node.keywords and 1<=len(node.args)<=4:
                return finite(FUNCS[node.func.id](*[visit(a) for a in node.args]))
            raise ValueError('Unsupported numeric expression')
        return visit(tree)
    except (SyntaxError,ZeroDivisionError,OverflowError,TypeError) as error:
        raise ValueError('Invalid numeric expression') from error


def vector(value,variables,length=3):
    if not isinstance(value,list) or len(value)!=length:raise ValueError(f'Expected a {length}-component vector')
    return [evaluate(v,variables) for v in value]
