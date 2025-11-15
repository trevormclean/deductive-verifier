# ast.py defines the abstract syntax tree (AST) node classes
# will be used to apply weakest precondition rules and generate verification condition
class Expr: pass

class Const(Expr):
    def __init__(self, value):
        self.value = value # int (-1, 3, etc.) or bool (true, false)

class Var(Expr):
    def __init__(self, name: str):
        self.name = name

class BinOp(Expr):
    def __init__(self, left: Expr, op: str, right: Expr):
        self.left = left
        self.op = op # "+", "-", "==", "!=", ">", "<", ">=", "<=", "&&", "||", "->"
        self.right = right

class UnOp(Expr):
    def __init__(self, op: str, expr: Expr):
        self.op = op # "!"
        self.expr = expr


class Stmt: pass

class Assign(Stmt):
    def __init__(self, var: Var, expr: Expr):
        self.var = var
        self.expr = expr

class Seq(Stmt):
    def __init__(self, first: Stmt, second: Stmt):
        self.first = first
        self.second = second

class If(Stmt):
    def __init__(self, cond: Expr, then_block: Stmt, else_block: Stmt):
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block


class Program:
    def __init__(self, pre: Expr, body: Stmt, post: Expr):
        self.pre = pre
        self.body = body
        self.post = post
