"""
Zimbro Parser Extension for Absinto
Integrates Zimbro test syntax into the Absinto parser
"""

from typing import Optional, List, Dict, Any
from semantic.ast_nodes import ASTNode

# Register Zimbro keywords
ZIMBRO_KEYWORDS = {
    'suite',
    'test',
    'before',
    'after',
    'beforeEach',
    'afterEach',
    'replay',
    'continuous',
    'causes',
    'prevents',
    'requires',
    'precedes',
    'never',
    'within',
    'always',
    'eventually',
    'given',
    'assert',
    'mock',
    'snapshot',
    'async',
    'parametrize',
    'parameters',
    'cases',
    'clear_mocks',
    'reset_entity_states',
    'cleanup_test_data',
    'clear_causal_graph',
}

_ZIMBRO_BODY_KEYWORDS = {
    'causes', 'prevents', 'requires', 'precedes', 'never',
    'assert', 'mock', 'replay', 'continuous',
    'clear_mocks', 'reset_entity_states', 'cleanup_test_data', 'clear_causal_graph',
}


def register_zimbro_keywords(registry):
    """Register Zimbro keywords with the plugin registry"""
    from lexer.lexer import TokenType
    for keyword in ZIMBRO_KEYWORDS:
        registry.register_keyword(keyword, TokenType.IDENTIFIER, namespace=None)


def _sync_parser(tokens, current_pos, parser):
    parser.pos = current_pos
    if current_pos < len(tokens):
        parser.current_token = tokens[current_pos]


def _skip_newlines(tokens, current_pos):
    from lexer.lexer import TokenType
    while current_pos < len(tokens) and tokens[current_pos].type == TokenType.NEWLINE:
        current_pos += 1
    return current_pos


def _parse_hook_block(tokens, current_pos, parser):
    """Parse before/after/beforeEach/afterEach blocks into executable statements."""
    from semantic.ast_nodes import ZimbroStatementNode
    from lexer.lexer import TokenType

    statements = []
    current_pos += 1
    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.COLON:
        current_pos += 1

    current_pos = _skip_newlines(tokens, current_pos)
    if current_pos >= len(tokens) or tokens[current_pos].type != TokenType.INDENT:
        return statements, current_pos

    current_pos += 1
    while current_pos < len(tokens):
        token = tokens[current_pos]
        if token.type == TokenType.DEDENT:
            current_pos += 1
            break
        stmt, current_pos = _parse_zimbro_body_statement(tokens, current_pos, parser)
        if stmt is not None:
            statements.append(stmt)
        else:
            current_pos += 1
        current_pos = _skip_newlines(tokens, current_pos)

    return statements, current_pos


def _tokens_to_expr_string(tokens, start, end):
    from lexer.lexer import TokenType
    parts = []
    for i in range(start, end):
        token = tokens[i]
        if token.type == TokenType.STRING_LIT:
            parts.append(f'"{token.value}"')
        elif token.type == TokenType.DOT:
            parts.append(".")
        elif token.type in (TokenType.EQ, TokenType.NEQ, TokenType.GT, TokenType.LT):
            parts.append(token.value)
        else:
            parts.append(str(token.value))
    return " ".join(parts).replace(" . ", ".").strip()


def _parse_causal_expression(tokens, current_pos):
    """Collect tokens until a modifier or end of statement."""
    from lexer.lexer import TokenType

    start = current_pos
    while current_pos < len(tokens):
        token = tokens[current_pos]
        if token.type in (TokenType.DEDENT, TokenType.NEWLINE):
            break
        if token.type == TokenType.IDENTIFIER and token.value in (
            'within', 'always', 'eventually', 'given',
            'causes', 'prevents', 'requires', 'precedes', 'never', 'assert', 'mock',
        ):
            if current_pos == start:
                current_pos += 1
                continue
            break
        current_pos += 1
    return _tokens_to_expr_string(tokens, start, current_pos), current_pos


def _parse_zimbro_body_statement(tokens, current_pos, parser):
    """Parse one statement inside a test or hook body."""
    from semantic.ast_nodes import (
        ZimbroStatementNode,
        ZimbroCausalTestNode,
        ZimbroAssertNode,
        ZimbroMockNode,
        BinaryExpr,
    )
    from lexer.lexer import TokenType

    current_pos = _skip_newlines(tokens, current_pos)
    if current_pos >= len(tokens):
        return None, current_pos

    token = tokens[current_pos]

    if token.type == TokenType.DEDENT:
        return None, current_pos

    if token.type == TokenType.INDENT:
        current_pos += 1
        return _parse_zimbro_body_statement(tokens, current_pos, parser)

    if token.type == TokenType.IDENTIFIER and token.value in _ZIMBRO_BODY_KEYWORDS:
        if token.value in ('clear_mocks', 'reset_entity_states', 'cleanup_test_data', 'clear_causal_graph'):
            from semantic.ast_nodes import CallExpr, IdentifierExpr
            call = CallExpr(target=IdentifierExpr(name=token.value), args=[])
            current_pos += 1
            return ZimbroStatementNode(statement=call), current_pos

        if token.value in ['replay', 'continuous']:
            current_pos += 1
            return None, current_pos

        if token.value in ['causes', 'prevents', 'requires', 'precedes', 'never']:
            causal_node = parse_causal_check(tokens, current_pos, parser)
            return causal_node, parser.pos

        if token.value == 'assert':
            assert_node = parse_assertion(tokens, current_pos, parser)
            return assert_node, parser.pos

        if token.value == 'mock':
            mock_node = parse_mock(tokens, current_pos, parser)
            return mock_node, parser.pos

    if token.type == TokenType.LET:
        _sync_parser(tokens, current_pos, parser)
        stmt = parser.parse_let()
        return ZimbroStatementNode(statement=stmt), parser.pos

    if token.type == TokenType.SET:
        _sync_parser(tokens, current_pos, parser)
        stmt = parser.parse_set()
        return ZimbroStatementNode(statement=stmt), parser.pos

    if token.type == TokenType.IDENTIFIER:
        _sync_parser(tokens, current_pos, parser)
        stmt = parser.parse_expression_statement()
        return ZimbroStatementNode(statement=stmt), parser.pos

    return None, current_pos + 1


def parse_zimbro_suite(tokens, current_pos, parser):
    """Parse a Zimbro test suite"""
    from semantic.ast_nodes import ZimbroSuiteNode
    from lexer.lexer import TokenType

    suite_name = ""
    before = []
    after = []
    before_each = []
    after_each = []
    tests = []

    if current_pos < len(tokens) and tokens[current_pos].value == 'suite':
        current_pos += 1

    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.IDENTIFIER:
        suite_name = tokens[current_pos].value
        current_pos += 1

    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.COLON:
        current_pos += 1

    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.INDENT:
        current_pos += 1

    while current_pos < len(tokens):
        token = tokens[current_pos]

        if token.type == TokenType.DEDENT:
            current_pos += 1
            break

        if token.type == TokenType.IDENTIFIER:
            if token.value == 'before':
                before, current_pos = _parse_hook_block(tokens, current_pos, parser)
                continue
            if token.value == 'after':
                after, current_pos = _parse_hook_block(tokens, current_pos, parser)
                continue
            if token.value == 'beforeEach':
                before_each, current_pos = _parse_hook_block(tokens, current_pos, parser)
                continue
            if token.value == 'afterEach':
                after_each, current_pos = _parse_hook_block(tokens, current_pos, parser)
                continue
            if token.value == 'test':
                test_result = parse_zimbro_test(tokens, current_pos, parser)
                if test_result:
                    tests.append(test_result)
                    current_pos = parser.pos
                else:
                    current_pos += 1
                continue

        current_pos += 1

    _sync_parser(tokens, current_pos, parser)

    return ZimbroSuiteNode(
        name=suite_name,
        before=before,
        after=after,
        before_each=before_each,
        after_each=after_each,
        tests=tests,
    )


def parse_zimbro_test(tokens, current_pos, parser):
    """Parse a Zimbro test"""
    from semantic.ast_nodes import ZimbroTestNode
    from lexer.lexer import TokenType

    test_name = ""

    if current_pos < len(tokens) and tokens[current_pos].value == 'test':
        current_pos += 1

    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.IDENTIFIER:
        test_name = tokens[current_pos].value
        current_pos += 1
    elif current_pos < len(tokens) and tokens[current_pos].type == TokenType.STRING_LIT:
        test_name = tokens[current_pos].value
        current_pos += 1

    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.COLON:
        current_pos += 1

    current_pos = _skip_newlines(tokens, current_pos)
    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.INDENT:
        current_pos += 1

    body = []
    while current_pos < len(tokens):
        token = tokens[current_pos]
        if token.type == TokenType.DEDENT:
            current_pos += 1
            break

        stmt, current_pos = _parse_zimbro_body_statement(tokens, current_pos, parser)
        if stmt is not None:
            body.append(stmt)
        current_pos = _skip_newlines(tokens, current_pos)

    _sync_parser(tokens, current_pos, parser)

    return ZimbroTestNode(
        name=test_name,
        execution_mode="isolated",
        body=body,
    )


def parse_causal_check(tokens, current_pos, parser):
    """Parse a causal check with full subject/object expressions."""
    from semantic.ast_nodes import ZimbroCausalTestNode
    from lexer.lexer import TokenType

    operator = ""
    modifiers = {}

    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.IDENTIFIER:
        operator = tokens[current_pos].value
        current_pos += 1

    subject_expr, current_pos = _parse_causal_expression(tokens, current_pos)

    if operator in ['causes', 'prevents', 'requires', 'precedes']:
        if current_pos < len(tokens) and tokens[current_pos].type == TokenType.IDENTIFIER and tokens[current_pos].value == operator:
            current_pos += 1
        object_expr, current_pos = _parse_causal_expression(tokens, current_pos)
    elif operator == 'never':
        if current_pos < len(tokens) and tokens[current_pos].type == TokenType.IDENTIFIER and tokens[current_pos].value == 'before':
            current_pos += 1
        object_expr, current_pos = _parse_causal_expression(tokens, current_pos)
    else:
        object_expr = ""

    while current_pos < len(tokens):
        token = tokens[current_pos]
        if token.type == TokenType.IDENTIFIER and token.value in ['within', 'always', 'eventually', 'given']:
            modifier_name = token.value
            current_pos += 1
            if modifier_name == 'given':
                modifier_value, current_pos = _parse_causal_expression(tokens, current_pos)
            elif current_pos < len(tokens):
                modifier_value = tokens[current_pos].value
                current_pos += 1
            else:
                modifier_value = ""
            modifiers[modifier_name] = modifier_value
        else:
            break

    _sync_parser(tokens, current_pos, parser)

    return ZimbroCausalTestNode(
        operator=operator,
        subject=subject_expr.split(".")[0] if subject_expr else "",
        object=object_expr.split(".")[0] if object_expr else "",
        subject_expr=subject_expr,
        object_expr=object_expr,
        modifiers=modifiers,
    )


def parse_assertion(tokens, current_pos, parser):
    """Parse an assertion using the main expression parser."""
    from semantic.ast_nodes import ZimbroAssertNode, BinaryExpr
    from lexer.lexer import TokenType

    if current_pos < len(tokens) and tokens[current_pos].value == 'assert':
        current_pos += 1

    _sync_parser(tokens, current_pos, parser)
    expr = parser.parse_expr()

    assertion_type = "truthy"
    left_expr = expr
    right_expr = None

    if isinstance(expr, BinaryExpr):
        op_map = {
            "==": "equals",
            "!=": "not_equals",
            ">": "greater_than",
            "<": "less_than",
            ">=": "greater_than_or_equal",
            "<=": "less_than_or_equal",
        }
        assertion_type = op_map.get(expr.op, "equals")
        left_expr = expr.left
        right_expr = expr.right

    _sync_parser(tokens, parser.pos, parser)

    return ZimbroAssertNode(
        assertion_type=assertion_type,
        left_expr=left_expr,
        right_expr=right_expr,
        left=None,
        right=None,
    )


def _skip_indented_block(tokens, current_pos):
    """Skip an indented block body, returning the position after its closing DEDENT."""
    from lexer.lexer import TokenType

    current_pos = _skip_newlines(tokens, current_pos)
    if current_pos >= len(tokens) or tokens[current_pos].type != TokenType.INDENT:
        return current_pos

    depth = 0
    while current_pos < len(tokens):
        token = tokens[current_pos]
        if token.type == TokenType.INDENT:
            depth += 1
            current_pos += 1
        elif token.type == TokenType.DEDENT:
            depth -= 1
            current_pos += 1
            if depth == 0:
                break
        else:
            current_pos += 1

    return current_pos


def parse_mock(tokens, current_pos, parser):
    """Parse a mock declaration"""
    from semantic.ast_nodes import ZimbroMockNode
    from lexer.lexer import TokenType

    if current_pos < len(tokens) and tokens[current_pos].value == 'mock':
        current_pos += 1

    target_parts = []
    while current_pos < len(tokens) and tokens[current_pos].type in (TokenType.IDENTIFIER, TokenType.DOT):
        if tokens[current_pos].type == TokenType.DOT:
            target_parts.append(".")
        else:
            target_parts.append(tokens[current_pos].value)
        current_pos += 1
    target = "".join(target_parts)

    if current_pos < len(tokens) and tokens[current_pos].type == TokenType.COLON:
        current_pos += 1

    current_pos = _skip_indented_block(tokens, current_pos)
    _sync_parser(tokens, current_pos, parser)

    return ZimbroMockNode(
        target=target,
        behavior="causal",
        config={"active": True},
    )


try:
    from core.plugin_system.registry import PluginRegistry
    register_zimbro_keywords(PluginRegistry)
except ImportError:
    pass
