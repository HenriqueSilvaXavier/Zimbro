"""
Zimbro — Biblioteca Geral de Testes Unitários

Zimbro é uma biblioteca geral de testes unitários para todos os projetos, similar ao Jest, JUnit e Pytest.
Fornece funcionalidades completas de testes unitários incluindo testes causais para o Absinto.

Modo Geral (Jest/JUnit/Pytest style):
- Testes unitários tradicionais
- Assertions padrão
- Mocks tradicionais
- Setup/teardown hooks
- Testes parametrizados
- Testes assíncronos
- Snapshot testing
- Coverage reporting
- Watch mode
- Execução paralela

Modo Causal (Absinto style):
- Testa relações causais
- Testa estados de entidades
- Testa invariantes
- Testa propagação
"""

# Register parser extension
try:
    from .parser_ext import register_zimbro_keywords
    from core.plugin_system.registry import PluginRegistry
    register_zimbro_keywords(PluginRegistry)
except ImportError:
    pass

from .runner import ZimbroRunner, create_runner
from .lexer import ZimbroLexer
from .parser import ZimbroParser
from .engine import ZimbroEngine
from .mock import MockRegistry
from .assertions import AssertionEngine

# General unit testing functions
from .unit_assertions import (
    assert_equal,
    assert_not_equal,
    assert_true,
    assert_false,
    assert_is_none,
    assert_is_not_none,
    assert_in,
    assert_not_in,
    assert_raises,
    assert_almost_equal,
    expect
)

from .unit_mocks import Mock, when, spy
from .unit_hooks import before_all, after_all, before_each, after_each
from .unit_parametrize import parametrize

__version__ = "2.0.0"
__all__ = [
    # Core Zimbro (causal testing)
    "ZimbroRunner",
    "ZimbroLexer",
    "ZimbroParser",
    "ZimbroEngine",
    "MockRegistry",
    "AssertionEngine",
    "create_runner",
    # General unit testing functions
    "assert_equal",
    "assert_not_equal",
    "assert_true",
    "assert_false",
    "assert_is_none",
    "assert_is_not_none",
    "assert_in",
    "assert_not_in",
    "assert_raises",
    "assert_almost_equal",
    "expect",
    "Mock",
    "when",
    "spy",
    "before_all",
    "after_all",
    "before_each",
    "after_each",
    "parametrize",
]
