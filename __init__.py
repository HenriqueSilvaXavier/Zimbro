"""
Zimbro — Biblioteca Oficial de Testes do Absinto

Zimbro testa relações causais, estados de entidades, invariantes e propagação.
Não testa funções nem implementação.

Filosofia:
- O programador declara intenção e comportamento, não implementação
- Testes que quebram por refatoração interna mas comportamento correto são mal escritos
- Mocks falam a língua causal do Absinto, não parecem mocks de JavaScript/Python
"""

# Register parser extension
try:
    from .parser_ext import register_zimbro_keywords
    from core.plugin_system.registry import PluginRegistry
    register_zimbro_keywords(PluginRegistry)
except ImportError:
    pass

from .runner import ZimbroRunner
from .lexer import ZimbroLexer
from .parser import ZimbroParser
from .engine import ZimbroEngine
from .mock import MockRegistry
from .assertions import AssertionEngine

__version__ = "1.0.0"
__all__ = [
    "ZimbroRunner",
    "ZimbroLexer",
    "ZimbroParser",
    "ZimbroEngine",
    "MockRegistry",
    "AssertionEngine",
]
