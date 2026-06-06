"""
zimbro/mock.py — Mock system that speaks the causal language of Absinto
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from .ast_nodes import MockNode


@dataclass
class MockBehavior:
    """Mock behavior specification."""
    when_condition: str
    then_action: str
    causal_effect: Optional[str] = None
    return_value: Any = None
    raises: Optional[Exception] = None


@dataclass
class MockTarget:
    """A mocked target (Entity, Capability, or infrastructure)."""
    target_name: str
    behaviors: List[MockBehavior] = field(default_factory=list)
    is_active: bool = True
    call_count: int = 0
    call_history: List[Dict[str, Any]] = field(default_factory=list)


class MockRegistry:
    """Registry for all mocks in a test suite."""
    
    def __init__(self):
        self._mocks: Dict[str, MockTarget] = {}
        self._causal_effects: List[str] = []
    
    def register(self, mock_node: MockNode):
        """Register a mock from AST node."""
        target = mock_node.target
        
        if target not in self._mocks:
            self._mocks[target] = MockTarget(target_name=target)
        
        mock_target = self._mocks[target]
        
        # Parse behavior
        behavior = MockBehavior(
            when_condition=mock_node.config.get('when', 'always'),
            then_action=mock_node.behavior,
            causal_effect=mock_node.config.get('causal_effect'),
            return_value=mock_node.config.get('returns'),
            raises=mock_node.config.get('raises')
        )
        
        mock_target.behaviors.append(behavior)
    
    def get_mock(self, target: str) -> Optional[MockTarget]:
        """Get a mock by target name."""
        return self._mocks.get(target)
    
    def is_mocked(self, target: str) -> bool:
        """Check if a target is mocked."""
        return target in self._mocks and self._mocks[target].is_active
    
    def record_call(self, target: str, call_data: Dict[str, Any]):
        """Record a call to a mocked target."""
        if target in self._mocks:
            self._mocks[target].call_count += 1
            self._mocks[target].call_history.append(call_data)
    
    def get_call_count(self, target: str) -> int:
        """Get the number of calls to a mocked target."""
        if target in self._mocks:
            return self._mocks[target].call_count
        return 0
    
    def get_call_history(self, target: str) -> List[Dict[str, Any]]:
        """Get the call history for a mocked target."""
        if target in self._mocks:
            return self._mocks[target].call_history
        return []
    
    def activate(self, target: str):
        """Activate a mock."""
        if target in self._mocks:
            self._mocks[target].is_active = True
    
    def deactivate(self, target: str):
        """Deactivate a mock."""
        if target in self._mocks:
            self._mocks[target].is_active = False
    
    def reset(self):
        """Reset all mocks."""
        for mock in self._mocks.values():
            mock.call_count = 0
            mock.call_history.clear()
    
    def clear(self):
        """Clear all mocks."""
        self._mocks.clear()
        self._causal_effects.clear()
    
    def record_causal_effect(self, effect: str):
        """Record a causal effect from a mock."""
        self._causal_effects.append(effect)
    
    def get_causal_effects(self) -> List[str]:
        """Get all recorded causal effects."""
        return self._causal_effects.copy()


class CausalMockBuilder:
    """Builder for creating causal mocks that speak Absinto's language."""
    
    def __init__(self, registry: MockRegistry):
        self.registry = registry
    
    def mock_entity(self, entity_name: str) -> 'EntityMockBuilder':
        """Start mocking an entity."""
        return EntityMockBuilder(entity_name, self.registry)
    
    def mock_capability(self, capability_name: str) -> 'CapabilityMockBuilder':
        """Start mocking a capability."""
        return CapabilityMockBuilder(capability_name, self.registry)
    
    def mock_intention(self, intention_name: str) -> 'IntentionMockBuilder':
        """Start mocking an intention."""
        return IntentionMockBuilder(intention_name, self.registry)


class EntityMockBuilder:
    """Builder for mocking entities with causal semantics."""
    
    def __init__(self, entity_name: str, registry: MockRegistry):
        self.entity_name = entity_name
        self.registry = registry
        self._behaviors: List[MockBehavior] = []
    
    def when_state(self, field: str, operator: str, value: Any) -> 'EntityMockBuilder':
        """Define behavior when entity field has specific state."""
        condition = f"{self.entity_name}.{field} {operator} {value!r}"
        self._current_when = condition
        return self
    
    def then_causes(self, effect: str) -> 'EntityMockBuilder':
        """Define that this state causes a causal effect."""
        if hasattr(self, '_current_when'):
            behavior = MockBehavior(
                when_condition=self._current_when,
                then_action='causes',
                causal_effect=effect
            )
            self._behaviors.append(behavior)
        return self
    
    def then_prevents(self, effect: str) -> 'EntityMockBuilder':
        """Define that this state prevents a causal effect."""
        if hasattr(self, '_current_when'):
            behavior = MockBehavior(
                when_condition=self._current_when,
                then_action='prevents',
                causal_effect=effect
            )
            self._behaviors.append(behavior)
        return self
    
    def then_returns(self, value: Any) -> 'EntityMockBuilder':
        """Define return value."""
        if hasattr(self, '_current_when'):
            behavior = MockBehavior(
                when_condition=self._current_when,
                then_action='returns',
                return_value=value
            )
            self._behaviors.append(behavior)
        return self
    
    def build(self) -> MockNode:
        """Build the mock node."""
        config = {}
        for behavior in self._behaviors:
            if behavior.causal_effect:
                config['causal_effect'] = behavior.causal_effect
            if behavior.return_value is not None:
                config['returns'] = behavior.return_value
        
        return MockNode(
            target=self.entity_name,
            behavior=self._behaviors[0].then_action if self._behaviors else 'returns',
            config=config
        )


class CapabilityMockBuilder:
    """Builder for mocking capabilities with causal semantics."""
    
    def __init__(self, capability_name: str, registry: MockRegistry):
        self.capability_name = capability_name
        self.registry = registry
        self._behaviors: List[MockBehavior] = []
    
    def when_called_with(self, params: Dict[str, Any]) -> 'CapabilityMockBuilder':
        """Define behavior when capability is called with specific parameters."""
        condition = f"called_with({params})"
        self._current_when = condition
        return self
    
    def then_causes(self, effect: str) -> 'CapabilityMockBuilder':
        """Define that this call causes a causal effect."""
        if hasattr(self, '_current_when'):
            behavior = MockBehavior(
                when_condition=self._current_when,
                then_action='causes',
                causal_effect=effect
            )
            self._behaviors.append(behavior)
        return self
    
    def then_returns(self, value: Any) -> 'CapabilityMockBuilder':
        """Define return value."""
        if hasattr(self, '_current_when'):
            behavior = MockBehavior(
                when_condition=self._current_when,
                then_action='returns',
                return_value=value
            )
            self._behaviors.append(behavior)
        return self
    
    def build(self) -> MockNode:
        """Build the mock node."""
        config = {}
        for behavior in self._behaviors:
            if behavior.causal_effect:
                config['causal_effect'] = behavior.causal_effect
            if behavior.return_value is not None:
                config['returns'] = behavior.return_value
        
        return MockNode(
            target=self.capability_name,
            behavior=self._behaviors[0].then_action if self._behaviors else 'returns',
            config=config
        )


class IntentionMockBuilder:
    """Builder for mocking intentions with causal semantics."""
    
    def __init__(self, intention_name: str, registry: MockRegistry):
        self.intention_name = intention_name
        self.registry = registry
        self._behaviors: List[MockBehavior] = []
    
    def when_executed(self) -> 'IntentionMockBuilder':
        """Define behavior when intention is executed."""
        condition = "executed"
        self._current_when = condition
        return self
    
    def then_causes(self, effect: str) -> 'IntentionMockBuilder':
        """Define that this execution causes a causal effect."""
        if hasattr(self, '_current_when'):
            behavior = MockBehavior(
                when_condition=self._current_when,
                then_action='causes',
                causal_effect=effect
            )
            self._behaviors.append(behavior)
        return self
    
    def then_prevents(self, effect: str) -> 'IntentionMockBuilder':
        """Define that this execution prevents a causal effect."""
        if hasattr(self, '_current_when'):
            behavior = MockBehavior(
                when_condition=self._current_when,
                then_action='prevents',
                causal_effect=effect
            )
            self._behaviors.append(behavior)
        return self
    
    def build(self) -> MockNode:
        """Build the mock node."""
        config = {}
        for behavior in self._behaviors:
            if behavior.causal_effect:
                config['causal_effect'] = behavior.causal_effect
        
        return MockNode(
            target=self.intention_name,
            behavior=self._behaviors[0].then_action if self._behaviors else 'causes',
            config=config
        )
