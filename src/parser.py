# parser.py parses a list of tokens into an abstract syntax tree (AST)

from ast_verif import Const, Var, BinOp, UnOp, Assign, Seq, If, While, Program
from lexer import Lexer

# Given a filename, build the AST for the file's program
def buildProgramAST(filename):
    with open(filename, "r") as f:
        text = f.read()

    text = open(filename).read()
    tokens = Lexer(text).tokenize()
    parser = Parser(tokens)
    program = parser.parse_program()
    return program

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None 
    
    # returns the current token and advances
    def eat(self, type):
        token = self.current()
        if token is not None and token.type == type:
            self.pos += 1
            return token
        raise Exception(f"Expected {type}, got {token}")
    
    # same as eat but returns None if no match
    def match(self, *types):
        token = self.current()
        if token is not None and token.type in types:
            self.pos += 1
            return token
        return None
    
    def parse_program(self):
        self.eat("PRE")
        pre = self.parse_expr()
        self.eat(";")

        self.eat("POST")
        post = self.parse_expr()
        self.eat(";")

        self.eat("{")
        body = self.parse_stmt_list()
        self.eat("}")

        return Program(pre, body, post)
    
    def parse_stmt_list(self):
        if self.current() is None or self.current().type in ("}", "EOF"):
            return None
        stmts = self.parse_stmt()
        while self.current() is not None and self.current().type not in ("}", "EOF"):
            stmts = Seq(stmts, self.parse_stmt())
        return stmts
    
    def parse_stmt(self):
        token = self.current()
        if token.type == "VAR":
            name = self.eat("VAR").value
            self.eat(":=")
            expr = self.parse_expr()
            self.eat(";")
            return Assign(Var(name), expr)
        if token.type == "IF":
            self.eat("IF")
            cond = self.parse_expr()
            self.eat("{")
            then_block = self.parse_stmt_list()
            self.eat("}")
            self.eat("ELSE")
            self.eat("{")
            else_block = self.parse_stmt_list()
            self.eat("}")
            return If(cond, then_block, else_block)
        # NEW: While loop: while (e) invariant I { S }
        if token.type == "WHILE":
            self.eat("WHILE")
            cond = self.parse_expr()
            self.eat("INVARIANT")
            invariant = self.parse_expr()
            self.eat("{")
            body = self.parse_stmt_list()
            self.eat("}")
            return While(cond, invariant, body)
        
        raise Exception(f"Unknown token {token}")
    
    # Expression precedence
    # 1. !
    # 2. +, -
    # 3. ==, !=, >, <, >=, <=
    # 4. &&
    # 5. ||
    # 6. ->
    # 7. parentheses

    def parse_expr(self):
        return self.parse_implication()
    
    def parse_implication(self):
        left = self.parse_or()
        while self.match("->"):
            right = self.parse_or()
            left = BinOp(left, "->", right)
        return left
    
    def parse_or(self):
        left = self.parse_and()
        while self.match("||"):
            right = self.parse_and()
            left = BinOp(left, "||", right)
        return left
    
    def parse_and(self):
        left = self.parse_compare()
        while self.match("&&"):
            right = self.parse_compare()
            left = BinOp(left, "&&", right)
        return left
    
    def parse_compare(self):
        left = self.parse_add_sub()
        while self.match("==", "!=", ">", "<", ">=", "<="):
            op = self.tokens[self.pos - 1].type
            right = self.parse_add_sub()
            left = BinOp(left, op, right)
        return left
    
    def parse_add_sub(self):
        left = self.parse_unary()
        while self.match("+", "-"):
            op = self.tokens[self.pos - 1].type
            right = self.parse_unary()
            left = BinOp(left, op, right)
        return left
    
    def parse_unary(self):
        if self.match("!"):
            expr = self.parse_unary()
            return UnOp("!", expr)
        return self.parse_atom()
    
    def parse_atom(self):
        token = self.current()
        if token.type == "INT":
            self.eat("INT")
            return Const(token.value)
        if token.type == "BOOL":
            self.eat("BOOL")
            return Const(token.value)
        if token.type == "VAR":
            self.eat("VAR")
            return Var(token.value)
        if token.type == "(":
            self.eat("(")
            expr = self.parse_expr()
            self.eat(")")
            return expr
        raise Exception(f"Unknown token {token}")