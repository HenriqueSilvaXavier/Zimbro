"""
zimbro/lexer.py — Lexer for Zimbro test syntax
"""

from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Token:
    """A lexical token."""
    type: str
    value: str
    line: int
    column: int


class ZimbroLexer:
    """Lexer for Zimbro test language."""
    
    # Token types
    KEYWORDS = {
        'test', 'suite', 'describe', 'it',
        'before', 'after', 'beforeEach', 'afterEach',
        'causes', 'prevents', 'requires', 'precedes', 'never',
        'within', 'always', 'eventually', 'given',
        'mock', 'expect', 'assert',
        'snapshot', 'parametrize',
        'simulate', 'replay', 'continuous',
        'true', 'false', 'null',
        'and', 'or', 'not',
        'async', 'await',
    }
    
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.pos = 0
        self.line = 1
        self.column = 1
    
    def tokenize(self) -> List[Token]:
        """Tokenize the source code."""
        while self.pos < len(self.source):
            self._skip_whitespace()
            
            if self.pos >= len(self.source):
                break
            
            char = self.source[self.pos]
            
            # Comments
            if char == '#' and (self.pos == 0 or self.source[self.pos - 1] == '\n'):
                self._skip_comment()
                continue
            
            # Strings
            if char in ('"', "'"):
                self._read_string(char)
                continue
            
            # Numbers
            if char.isdigit() or (char == '.' and self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit()):
                self._read_number()
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self._read_identifier()
                continue
            
            # Operators and punctuation
            self._read_operator_or_punctuation()
        
        self.tokens.append(Token('EOF', '', self.line, self.column))
        return self.tokens
    
    def _skip_whitespace(self):
        """Skip whitespace characters."""
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def _skip_comment(self):
        """Skip single-line comment."""
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.pos += 1
    
    def _read_string(self, quote: str):
        """Read a string literal."""
        start_pos = self.pos
        start_line = self.line
        start_column = self.column
        
        self.pos += 1  # Skip opening quote
        self.column += 1
        
        value = ''
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == '\\':
                self.pos += 1
                if self.pos < len(self.source):
                    # Handle escape sequences
                    escape_char = self.source[self.pos]
                    if escape_char == 'n':
                        value += '\n'
                    elif escape_char == 't':
                        value += '\t'
                    elif escape_char == 'r':
                        value += '\r'
                    elif escape_char == '\\':
                        value += '\\'
                    elif escape_char == quote:
                        value += quote
                    else:
                        value += escape_char
            else:
                value += self.source[self.pos]
            self.pos += 1
            self.column += 1
        
        if self.pos < len(self.source):
            self.pos += 1  # Skip closing quote
            self.column += 1
        
        self.tokens.append(Token('STRING', value, start_line, start_column))
    
    def _read_number(self):
        """Read a number literal."""
        start_line = self.line
        start_column = self.column
        
        value = ''
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            value += self.source[self.pos]
            self.pos += 1
            self.column += 1
        
        # Check for scientific notation
        if self.pos < len(self.source) and self.source[self.pos].lower() == 'e':
            value += self.source[self.pos]
            self.pos += 1
            self.column += 1
            if self.pos < len(self.source) and self.source[self.pos] in '+-':
                value += self.source[self.pos]
                self.pos += 1
                self.column += 1
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                value += self.source[self.pos]
                self.pos += 1
                self.column += 1
        
        # Determine if integer or float
        if '.' in value or 'e' in value.lower():
            self.tokens.append(Token('NUMBER', float(value), start_line, start_column))
        else:
            self.tokens.append(Token('NUMBER', int(value), start_line, start_column))
    
    def _read_identifier(self):
        """Read an identifier or keyword."""
        start_line = self.line
        start_column = self.column
        
        value = ''
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            value += self.source[self.pos]
            self.pos += 1
            self.column += 1
        
        # Check if keyword
        if value.lower() in self.KEYWORDS:
            self.tokens.append(Token(value.upper(), value, start_line, start_column))
        else:
            self.tokens.append(Token('IDENTIFIER', value, start_line, start_column))
    
    def _read_operator_or_punctuation(self):
        """Read operators and punctuation."""
        start_line = self.line
        start_column = self.column
        char = self.source[self.pos]
        
        # Multi-character operators
        if self.pos + 1 < len(self.source):
            two_char = char + self.source[self.pos + 1]
            if two_char in ('==', '!=', '>=', '<=', '=>', '->', '&&', '||', '..'):
                self.tokens.append(Token('OPERATOR', two_char, start_line, start_column))
                self.pos += 2
                self.column += 2
                return
        
        # Single-character tokens
        single_char_map = {
            '=': 'ASSIGN',
            '+': 'PLUS',
            '-': 'MINUS',
            '*': 'MULTIPLY',
            '/': 'DIVIDE',
            '%': 'MODULO',
            '<': 'LT',
            '>': 'GT',
            '(': 'LPAREN',
            ')': 'RPAREN',
            '[': 'LBRACKET',
            ']': 'RBRACKET',
            '{': 'LBRACE',
            '}': 'RBRACE',
            ':': 'COLON',
            ',': 'COMMA',
            '.': 'DOT',
            '?': 'QUESTION',
            '!': 'BANG',
            '|': 'PIPE',
            '&': 'AMPERSAND',
        }
        
        if char in single_char_map:
            self.tokens.append(Token(single_char_map[char], char, start_line, start_column))
            self.pos += 1
            self.column += 1
        else:
            # Unknown character - skip or error
            self.pos += 1
            self.column += 1
