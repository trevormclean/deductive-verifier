# lexer.py converts program file text into a list of tokens for the parser
class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f"{self.type}:{self.value}"
        return self.type

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)

    # shows the current character without advancing
    def peek(self, k=0):
        if self.pos + k < self.length:
            return self.text[self.pos + k]
        return None

    # builds and returns a string while condition is true
    def eat_while(self, condition):
        s = ''
        while self.pos < self.length and condition(self.peek()):
            s += self.peek()
            self.pos += 1
        return s
    
    # main function: converts text into list of tokens
    def tokenize(self):
        tokens = []

        while self.pos < self.length:
            c = self.peek()

            if c.isspace():
                self.eat_while(lambda ch: ch.isspace())
                continue
            
            if c == "#":
                self.eat_while(lambda ch: ch != '\n')
                continue

            twoc = c + (self.peek(1) or '')
            if twoc in {"==", "!=", ">=", "<=", "&&", "||", "->", ":="}:
                tokens.append(Token(twoc, None))
                self.pos += 2
                continue

            if c in {'+', '-', '!', '<', '>', '(', ')', '{', '}', ';'}:
                tokens.append(Token(c, None))
                self.pos += 1
                continue

            if c.isdigit():
                num = self.eat_while(lambda ch: ch.isdigit())
                tokens.append(Token("INT", int(num)))
                continue

            if c.isalpha():
                word = self.eat_while(lambda ch: ch.isalnum() or ch == '_')
                if word in {"true", "false"}:
                    tokens.append(Token("BOOL", word == "true"))
                elif word in {"if", "else", "pre", "post"}:
                    tokens.append(Token(word.upper(), None))
                else:
                    tokens.append(Token("VAR", word))
                continue

            raise Exception(f"Unkown character: {c}")
        
        tokens.append(Token("EOF", None))
        return tokens
            
                

            






    