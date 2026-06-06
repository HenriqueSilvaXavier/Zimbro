"""
zimbro/parser.py — Parser for Zimbro test syntax
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .lexer import ZimbroLexer, Token
from .ast_nodes import *


class ParseError(Exception):
    """Parse error with location information."""
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"Parse error at line {token.line}, column {token.column}: {message}")


class ZimbroParser:
    """Parser for Zimbro test language."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> List[TestSuiteNode]:
        """Parse the token list into a list of test suites."""
        suites = []
        
        while self._current().type != 'EOF':
            if self._current().type == 'SUITE' or self._current().type == 'DESCRIBE':
                suite = self._parse_suite()
                suites.append(suite)
            elif self._current().type == 'TEST' or self._current().type == 'IT':
                # Create implicit suite
                suite = TestSuiteNode(name="default")
                test = self._parse_test()
                suite.tests.append(test)
                suites.append(suite)
            elif self._current().type == 'MOCK':
                # Mock declarations at top level
                self._advance()
            else:
                self._advance()
        
        return suites
    
    def _current(self) -> Token:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF
    
    def _advance(self) -> Token:
        """Advance to next token and return previous."""
        token = self._current()
        self.pos += 1
        return token
    
    def _expect(self, token_type: str) -> Token:
        """Expect a specific token type."""
        if self._current().type == token_type:
            return self._advance()
        raise ParseError(f"Expected {token_type}, got {self._current().type}", self._current())
    
    def _parse_suite(self) -> TestSuiteNode:
        """Parse a test suite."""
        start_token = self._current()
        
        # suite or describe
        if start_token.type in ('SUITE', 'DESCRIBE'):
            self._advance()
        
        # Suite name
        name = self._expect('IDENTIFIER').value
        
        # Optional colon
        if self._current().type == 'COLON':
            self._advance()
        
        suite = TestSuiteNode(name=name, line=start_token.line)
        
        # Parse suite body
        while self._current().type not in ('EOF',):
            token_type = self._current().type
            
            if token_type == 'BEFORE':
                hook = self._parse_hook('before')
                suite.before_all.append(hook)
            elif token_type == 'AFTER':
                hook = self._parse_hook('after')
                suite.after_all.append(hook)
            elif token_type == 'BEFOREEACH':
                hook = self._parse_hook('beforeEach')
                suite.before_each.append(hook)
            elif token_type == 'AFTEREACH':
                hook = self._parse_hook('afterEach')
                suite.after_each.append(hook)
            elif token_type in ('TEST', 'IT'):
                test = self._parse_test()
                suite.tests.append(test)
            elif token_type in ('SUITE', 'DESCRIBE'):
                # Nested suite - for now, just add to parent
                nested_suite = self._parse_suite()
                suite.tests.extend(nested_suite.tests)
            else:
                break
        
        return suite
    
    def _parse_test(self) -> TestNode:
        """Parse a test case."""
        start_token = self._current()
        
        # test or it
        if start_token.type in ('TEST', 'IT'):
            self._advance()
        
        # Test name
        name = self._expect('IDENTIFIER').value
        
        # Optional colon
        if self._current().type == 'COLON':
            self._advance()
        
        test = TestNode(name=name, line=start_token.line)
        
        # Parse test body
        while self._current().type not in ('EOF',):
            token_type = self._current().type
            
            if token_type in ('CAUSES', 'PREVENTS', 'REQUIRES', 'PRECEDES', 'NEVER'):
                causal_test = self._parse_causal_test(token_type.lower())
                test.body.append(causal_test)
            elif token_type == 'ASSERT':
                assertion = self._parse_assertion()
                test.body.append(assertion)
            elif token_type == 'MOCK':
                mock = self._parse_mock()
                test.body.append(mock)
            elif token_type == 'SNAPSHOT':
                snapshot = self._parse_snapshot()
                test.body.append(snapshot)
            elif token_type == 'SIMULATE':
                test.mode = 'simulate'
                self._advance()
            elif token_type == 'REPLAY':
                test.mode = 'replay'
                self._advance()
            elif token_type == 'CONTINUOUS':
                test.mode = 'continuous'
                self._advance()
            else:
                break
        
        return test
    
    def _parse_causal_test(self, operator: str) -> CausalTestNode:
        """Parse a causal test operator."""
        start_token = self._current()
        self._advance()
        
        # Subject: Entity.field or event
        subject = self._expect('IDENTIFIER').value
        if self._current().type == 'DOT':
            self._advance()
            subject += '.' + self._expect('IDENTIFIER').value
        
        # Object: Entity.field or event
        object_val = self._expect('IDENTIFIER').value
        if self._current().type == 'DOT':
            self._advance()
            object_val += '.' + self._expect('IDENTIFIER').value
        
        # Modifiers
        modifiers = {}
        while self._current().type in ('WITHIN', 'ALWAYS', 'EVENTUALLY', 'GIVEN'):
            mod_type = self._current().type.lower()
            self._advance()
            
            if mod_type == 'within':
                duration = self._expect('NUMBER').value
                unit = self._expect('IDENTIFIER').value  # s, ms, us
                modifiers['within'] = (duration, unit)
            elif mod_type == 'always':
                modifiers['always'] = True
            elif mod_type == 'eventually':
                if self._current().type == 'NUMBER':
                    timeout = self._expect('NUMBER').value
                    unit = self._expect('IDENTIFIER').value
                    modifiers['eventually'] = (timeout, unit)
                else:
                    modifiers['eventually'] = True
            elif mod_type == 'given':
                condition = self._expect('IDENTIFIER').value
                if self._current().type == 'ASSIGN' or self._current().type == 'OPERATOR':
                    op = self._advance().value
                    value = self._expect('IDENTIFIER').value
                    modifiers['given'] = f"{condition} {op} {value}"
        
        # Create appropriate node type
        if operator == 'causes':
            return CausesNode(subject=subject, object=object_val, modifiers=modifiers, line=start_token.line)
        elif operator == 'prevents':
            return PreventsNode(subject=subject, object=object_val, modifiers=modifiers, line=start_token.line)
        elif operator == 'requires':
            return RequiresNode(subject=subject, object=object_val, modifiers=modifiers, line=start_token.line)
        elif operator == 'precedes':
            return PrecedesNode(subject=subject, object=object_val, modifiers=modifiers, line=start_token.line)
        elif operator == 'never':
            return NeverNode(subject=subject, object=object_val, modifiers=modifiers, line=start_token.line)
        
        return CausalTestNode(operator=operator, subject=subject, object=object_val, modifiers=modifiers, line=start_token.line)
    
    def _parse_assertion(self) -> AssertionNode:
        """Parse an assertion."""
        start_token = self._current()
        self._advance()
        
        # Entity.field
        entity = self._expect('IDENTIFIER').value
        field = ''
        if self._current().type == 'DOT':
            self._advance()
            field = self._expect('IDENTIFIER').value
        
        # Operator
        op = self._expect('OPERATOR').value if self._current().type == 'OPERATOR' else self._expect('ASSIGN').value
        
        # Value
        value_token = self._current()
        if value_token.type == 'NUMBER':
            value = self._advance().value
        elif value_token.type == 'STRING':
            value = self._advance().value
        elif value_token.type == 'TRUE':
            value = True
            self._advance()
        elif value_token.type == 'FALSE':
            value = False
            self._advance()
        elif value_token.type == 'NULL':
            value = None
            self._advance()
        else:
            value = self._expect('IDENTIFIER').value
        
        return EntityStateAssertion(
            assertion_type='entity_state',
            entity=entity,
            field=field,
            expected=value,
            line=start_token.line
        )
    
    def _parse_mock(self) -> MockNode:
        """Parse a mock declaration."""
        start_token = self._current()
        self._advance()
        
        # Target: Entity, Capability, or infrastructure
        target = self._expect('IDENTIFIER').value
        if self._current().type == 'DOT':
            self._advance()
            target += '.' + self._expect('IDENTIFIER').value
        
        # Behavior
        behavior = self._expect('IDENTIFIER').value
        
        # Config
        config = {}
        if self._current().type == 'COLON':
            self._advance()
            while self._current().type not in ('EOF',):
                key = self._expect('IDENTIFIER').value
                self._expect('ASSIGN')
                value_token = self._current()
                if value_token.type == 'NUMBER':
                    config[key] = self._advance().value
                elif value_token.type == 'STRING':
                    config[key] = self._advance().value
                elif value_token.type == 'TRUE':
                    config[key] = True
                    self._advance()
                elif value_token.type == 'FALSE':
                    config[key] = False
                    self._advance()
                else:
                    config[key] = self._advance().value
                
                if self._current().type != 'COMMA':
                    break
                self._advance()
        
        return MockNode(target=target, behavior=behavior, config=config, line=start_token.line)
    
    def _parse_snapshot(self) -> SnapshotNode:
        """Parse a snapshot assertion."""
        start_token = self._current()
        self._advance()
        
        # Target
        target = self._expect('IDENTIFIER').value
        if self._current().type == 'DOT':
            self._advance()
            target += '.' + self._expect('IDENTIFIER').value
        
        # Optional snapshot name
        snapshot_name = None
        if self._current().type == 'AS':
            self._advance()
            snapshot_name = self._expect('IDENTIFIER').value
        
        return SnapshotNode(target=target, snapshot_name=snapshot_name, line=start_token.line)
    
    def _parse_hook(self, hook_type: str) -> HookNode:
        """Parse a lifecycle hook."""
        start_token = self._current()
        self._advance()
        
        hook = HookNode(hook_type=hook_type, line=start_token.line)
        
        # Parse hook body (simplified - just skip for now)
        while self._current().type not in ('EOF',):
            if self._current().type in ('TEST', 'IT', 'BEFORE', 'AFTER', 'BEFOREEACH', 'AFTEREACH'):
                break
            self._advance()
        
        return hook
