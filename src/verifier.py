# verifier.py
# Deductive verifier using wp rules and Z3
# Usage: python verifier.py program.txt

import sys
from typing import Dict, Set
from ast_verif import Program, Assign, Seq, If, Var, Const, BinOp, UnOp
from lexer import Lexer
from parser import Parser
from z3 import Solver, Not, Implies, And, Or, BoolVal, IntVal, Int, Bool, sat, unsat, simplify

def clone_expr(e):
    if e is None:
        return None
    if isinstance(e, Const):
        return Const(e.value)
    if isinstance(e, Var):
        return Var(e.name)
    if isinstance(e, UnOp):
        return UnOp(e.op, clone_expr(e.expr))
    if isinstance(e, BinOp):
        return BinOp(clone_expr(e.left), e.op, clone_expr(e.right))
    raise Exception(f"clone_expr: unknown type {type(e)}")

# Substitution Q[x := e]
def substitute(expr, varname: str, replacement):
    if expr is None:
        return None
    if isinstance(expr, Const):
        return Const(expr.value)
    if isinstance(expr, Var):
        if expr.name == varname:
            return clone_expr(replacement)
        return Var(expr.name)
    if isinstance(expr, UnOp):
        return UnOp(expr.op, substitute(expr.expr, varname, replacement))
    if isinstance(expr, BinOp):
        return BinOp(
            substitute(expr.left, varname, replacement),
            expr.op,
            substitute(expr.right, varname, replacement),
        )
    raise Exception(f"substitute: unknown expr type {type(expr)}")

# WP Rules
def wp(stmt, post):
    if stmt is None:
        return clone_expr(post)
    if isinstance(stmt, Assign):
        return substitute(post, stmt.var.name, stmt.expr)
    if isinstance(stmt, Seq):
        inner = wp(stmt.second, post)
        return wp(stmt.first, inner)
    if isinstance(stmt, If):
        wp_then = wp(stmt.then_block, post)
        wp_else = wp(stmt.else_block, post)
        part1 = BinOp(stmt.cond, "->", wp_then)
        part2 = BinOp(UnOp("!", stmt.cond), "->", wp_else)
        return BinOp(part1, "&&", part2)
    raise Exception(f"wp: unknown stmt type {type(stmt)}")

# Collect var usages for infering var types
def collect_var_usage(expr, usage: Dict[str, Set[str]]):
    if expr is None:
        return
    if isinstance(expr, Const):
        return
    if isinstance(expr, Var):
        usage.setdefault(expr.name, set())
        return
    if isinstance(expr, UnOp):
        if expr.op == "!":
            tag_bool(expr.expr, usage)
        collect_var_usage(expr.expr, usage)
        return
    if isinstance(expr, BinOp):
        op = expr.op
        if op in {"+", "-"}:
            tag_int(expr.left, usage)
            tag_int(expr.right, usage)
        elif op in {"==", "!=", ">", "<", ">=", "<="}:
            is_bool_compare = isinstance(expr.left, Const) and isinstance(expr.left.value, bool) or \
                              isinstance(expr.right, Const) and isinstance(expr.right.value, bool)
            if is_bool_compare:
                tag_bool(expr.left, usage)
                tag_bool(expr.right, usage)
            else:
                tag_int(expr.left, usage)
                tag_int(expr.right, usage)
        elif op in {"&&", "||", "->"}:
            tag_bool(expr.left, usage)
            tag_bool(expr.right, usage)
        else:
            collect_var_usage(expr.left, usage)
            collect_var_usage(expr.right, usage)

def tag_int(expr, usage):
    if isinstance(expr, Var):
        usage.setdefault(expr.name, set()).add("int")
    elif isinstance(expr, (BinOp, UnOp)):
        collect_var_usage(expr, usage)

def tag_bool(expr, usage):
    if isinstance(expr, Var):
        usage.setdefault(expr.name, set()).add("bool")
    elif isinstance(expr, (BinOp, UnOp)):
        collect_var_usage(expr, usage)

# Infer var types
def infer_var_types(program: Program) -> Dict[str, str]:
    usage: Dict[str, Set[str]] = {}
    collect_var_usage(program.pre, usage)
    collect_var_usage(program.post, usage)
    def walk(s):
        if s is None:
            return
        if isinstance(s, Assign):
            collect_var_usage(s.expr, usage)
            usage.setdefault(s.var.name, usage.get(s.var.name, set()))
        elif isinstance(s, Seq):
            walk(s.first); walk(s.second)
        elif isinstance(s, If):
            collect_var_usage(s.cond, usage)
            walk(s.then_block); walk(s.else_block)
    walk(program.body)
    types: Dict[str, str] = {}
    for v, hints in usage.items():
        if "int" in hints and "bool" in hints:
            types[v] = "int"  # heuristic
        elif "int" in hints:
            types[v] = "int"
        elif "bool" in hints:
            types[v] = "bool"
        else:
            types[v] = "int"
    return types

# Convert AST to Z3
def expr_to_z3(expr, env):
    if expr is None:
        return BoolVal(True)
    if isinstance(expr, Const):
        if isinstance(expr.value, bool):
            return BoolVal(expr.value)
        return IntVal(expr.value)
    if isinstance(expr, Var):
        return env[expr.name]
    if isinstance(expr, UnOp):
        if expr.op == "!":
            return Not(expr_to_z3(expr.expr, env))
        raise Exception(f"Unknown UnOp: {expr.op}")
    if isinstance(expr, BinOp):
        L = expr_to_z3(expr.left, env)
        R = expr_to_z3(expr.right, env)
        op = expr.op
        if op == "+": return L + R
        if op == "-": return L - R
        if op == "==": return L == R
        if op == "!=": return L != R
        if op == ">": return L > R
        if op == "<": return L < R
        if op == ">=": return L >= R
        if op == "<=": return L <= R
        if op == "&&": return And(L, R)
        if op == "||": return Or(L, R)
        if op == "->": return Implies(L, R)
        raise Exception(f"Unknown BinOp: {op}")
    raise Exception(f"expr_to_z3: unknown type {type(expr)}")

# Z3 Environment
def build_env(var_types: Dict[str, str]):
    env = {}
    for name, typ in var_types.items():
        if typ == "int":
            env[name] = Int(name)
        else:
            env[name] = Bool(name)
    return env

# Check VCs
def check_verification(program: Program, simplify_vc=True):
    wp_expr = wp(program.body, program.post)
    var_types = infer_var_types(program)
    env = build_env(var_types)
    pre_z3 = expr_to_z3(program.pre, env)
    wp_z3 = expr_to_z3(wp_expr, env)
    vc = Implies(pre_z3, wp_z3)
    if simplify_vc:
        vc = simplify(vc)
    s = Solver()
    s.add(Not(vc))
    res = s.check()
    if res == unsat:
        return True, None
    elif res == sat:
        return False, s.model()
    else:
        return False, None

# Verify programs
def main(argv):
    if len(argv) < 2:
        print("Usage: python verifier.py [program_file]")
        sys.exit(1)
    path = argv[1]
    text = open(path).read()
    tokens = Lexer(text).tokenize()
    parser = Parser(tokens)
    program = parser.parse_program()

    ok, model = check_verification(program)
    if ok:
        print("VERIFIED: the Hoare triple is valid (VC is valid).")
    else:
        print("NOT VERIFIED: the Hoare triple is NOT valid (VC is NOT valid).")
        if model is not None:
            print("Counterexample (model):")
            for d in model.decls():
                print(f"  {d.name()} = {model[d]}")
        else:
            print("Unknown or no model.")

if __name__ == "__main__":
    main(sys.argv)

