"""
zimbro/ast_nodes.py — AST nodes for Zimbro test constructs
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# =========================================================
# BASE
# =========================================================

class ZimbroNode:
    """Base class for all Zimbro AST nodes."""
    pass


# =========================================================
# TEST SUITE
# =========================================================

@dataclass
class TestSuiteNode(ZimbroNode):
    """A collection of related tests."""
    name: str
    description: Optional[str] = None
    tests: List['TestNode'] = field(default_factory=list)
    before_all: List['HookNode'] = field(default_factory=list)
    after_all: List['HookNode'] = field(default_factory=list)
    before_each: List['HookNode'] = field(default_factory=list)
    after_each: List['HookNode'] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    line: int = 0


# =========================================================
# TEST
# =========================================================

@dataclass
class TestNode(ZimbroNode):
    """A single test case."""
    name: str
    body: List[ZimbroNode] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    mode: str = "simulate"  # simulate | replay | continuous
    line: int = 0


# =========================================================
# CAUSAL TEST OPERATORS
# =========================================================

@dataclass
class CausalTestNode(ZimbroNode):
    """Base for causal test operators."""
    operator: str = ""  # causes | prevents | requires | precedes | never
    subject: str = ""   # Entity.field or event
    object: str = ""    # Entity.field or event
    modifiers: Dict[str, Any] = field(default_factory=dict)  # within, always, eventually, given
    line: int = 0


@dataclass
class CausesNode(CausalTestNode):
    """Test that subject causes object."""
    operator: str = "causes"


@dataclass
class PreventsNode(CausalTestNode):
    """Test that subject prevents object."""
    operator: str = "prevents"


@dataclass
class RequiresNode(CausalTestNode):
    """Test that subject requires object."""
    operator: str = "requires"


@dataclass
class PrecedesNode(CausalTestNode):
    """Test that subject precedes object."""
    operator: str = "precedes"


@dataclass
class NeverNode(CausalTestNode):
    """Test that subject never causes object."""
    operator: str = "never"


# =========================================================
# MODIFIERS
# =========================================================

@dataclass
class WithinModifier(ZimbroNode):
    """Time constraint: within 5s, within 100ms."""
    duration: float
    unit: str  # s | ms | us


@dataclass
class AlwaysModifier(ZimbroNode):
    """Always true: always holds."""
    pass


@dataclass
class EventuallyModifier(ZimbroNode):
    """Eventually true: eventually holds."""
    timeout: Optional[float] = None


@dataclass
class GivenModifier(ZimbroNode):
    """Precondition: given Entity.field == value."""
    condition: str
    value: Any


# =========================================================
# MOCK
# =========================================================

@dataclass
class MockNode(ZimbroNode):
    """Mock declaration."""
    target: str  # Entity, Capability, or infrastructure
    behavior: str  # returns | raises | causes | prevents
    config: Dict[str, Any] = field(default_factory=dict)
    line: int = 0


@dataclass
class MockBehaviorNode(ZimbroNode):
    """Mock behavior specification."""
    when: str  # condition
    then: str  # action
    causal_effect: Optional[str] = None  # optional causal effect


# =========================================================
# ASSERTIONS
# =========================================================

@dataclass
class AssertionNode(ZimbroNode):
    """Base assertion."""
    assertion_type: str = ""
    left: Any = None
    right: Any = None
    message: Optional[str] = None
    line: int = 0


@dataclass
class EntityStateAssertion(AssertionNode):
    """Assert entity state: Entity.field == value."""
    entity: str = ""
    field: str = ""
    expected: Any = None
    line: int = 0


@dataclass
class InvariantAssertion(AssertionNode):
    """Assert invariant holds."""
    invariant_name: str = ""
    line: int = 0


@dataclass
class PropagationAssertion(AssertionNode):
    """Assert propagation occurred."""
    source_entity: str = ""
    target_entity: str = ""
    field: str = ""
    line: int = 0


# =========================================================
# HOOKS
# =========================================================

@dataclass
class HookNode(ZimbroNode):
    """Lifecycle hook: before, after, beforeEach, afterEach."""
    hook_type: str  # before | after | beforeEach | afterEach
    body: List[ZimbroNode] = field(default_factory=list)
    line: int = 0


# =========================================================
# PARAMETRIZED TEST
# =========================================================

@dataclass
class ParametrizedTestNode(ZimbroNode):
    """Test with multiple parameter sets."""
    name: str
    parameters: List[str]  # parameter names
    cases: List[Dict[str, Any]]  # parameter values for each case
    body: List[ZimbroNode] = field(default_factory=list)
    line: int = 0


# =========================================================
# SNAPSHOT
# =========================================================

@dataclass
class SnapshotNode(ZimbroNode):
    """Snapshot assertion."""
    target: str  # Entity or expression
    snapshot_name: Optional[str] = None
    line: int = 0


# =========================================================
# ASYNC TEST
# =========================================================

@dataclass
class AsyncTestNode(TestNode):
    """Async test case."""
    is_async: bool = True


# =========================================================
# CONFIGURATION
# =========================================================

@dataclass
class ZimbroConfigNode(ZimbroNode):
    """Zimbro configuration."""
    parallel: bool = False
    workers: int = 4
    coverage: bool = False
    watch: bool = False
    verbose: bool = False
    timeout: float = 5.0
    line: int = 0
