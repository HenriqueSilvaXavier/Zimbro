"""
zimbro/assertions.py — Assertion engine with clear error messages
"""

from __future__ import annotations
from typing import Any, List, Optional
from dataclasses import dataclass

from .ast_nodes import *


@dataclass
class AssertionError:
    """Assertion error with detailed context."""
    assertion_type: str
    expected: Any
    actual: Any
    message: str
    line: int
    file: Optional[str] = None


class AssertionEngine:
    """Engine for executing assertions with clear error messages."""
    
    def __init__(self):
        self._errors: List[AssertionError] = []
    
    def execute(self, assertion: AssertionNode):
        """Execute an assertion."""
        if isinstance(assertion, EntityStateAssertion):
            self._execute_entity_state_assertion(assertion)
        elif isinstance(assertion, InvariantAssertion):
            self._execute_invariant_assertion(assertion)
        elif isinstance(assertion, PropagationAssertion):
            self._execute_propagation_assertion(assertion)
    
    def _execute_entity_state_assertion(self, assertion: EntityStateAssertion):
        """Execute an entity state assertion."""
        # In a real implementation, this would query the entity state
        # from the causal graph or entity system
        
        # For now, we'll simulate the check
        actual_value = self._get_entity_field_value(assertion.entity, assertion.field)
        
        if actual_value != assertion.expected:
            error = AssertionError(
                assertion_type='entity_state',
                expected=assertion.expected,
                actual=actual_value,
                message=self._format_entity_state_error(assertion, actual_value),
                line=assertion.line
            )
            self._errors.append(error)
            raise AssertionErrorException(error)
    
    def _execute_invariant_assertion(self, assertion: InvariantAssertion):
        """Execute an invariant assertion."""
        # Check if invariant holds
        invariant_holds = self._check_invariant(assertion.invariant_name)
        
        if not invariant_holds:
            error = AssertionError(
                assertion_type='invariant',
                expected=True,
                actual=False,
                message=self._format_invariant_error(assertion),
                line=assertion.line
            )
            self._errors.append(error)
            raise AssertionErrorException(error)
    
    def _execute_propagation_assertion(self, assertion: PropagationAssertion):
        """Execute a propagation assertion."""
        # Check if propagation occurred
        propagated = self._check_propagation(
            assertion.source_entity,
            assertion.target_entity,
            assertion.field
        )
        
        if not propagated:
            error = AssertionError(
                assertion_type='propagation',
                expected=True,
                actual=False,
                message=self._format_propagation_error(assertion),
                line=assertion.line
            )
            self._errors.append(error)
            raise AssertionErrorException(error)
    
    def _get_entity_field_value(self, entity: str, field: str) -> Any:
        """Get the current value of an entity field."""
        # In a real implementation, this would query the entity system
        # For now, return a placeholder
        return None
    
    def _check_invariant(self, invariant_name: str) -> bool:
        """Check if an invariant holds."""
        # In a real implementation, this would check the causal graph
        # For now, return True
        return True
    
    def _check_propagation(self, source_entity: str, target_entity: str, field: str) -> bool:
        """Check if propagation occurred."""
        # In a real implementation, this would check the causal graph
        # For now, return True
        return True
    
    def _format_entity_state_error(self, assertion: EntityStateAssertion, actual: Any) -> str:
        """Format a clear error message for entity state assertion."""
        return (
            f"Entity state assertion failed\n"
            f"  Entity: {assertion.entity}\n"
            f"  Field: {assertion.field}\n"
            f"  Expected: {assertion.expected!r}\n"
            f"  Actual: {actual!r}\n"
            f"  Location: line {assertion.line}"
        )
    
    def _format_invariant_error(self, assertion: InvariantAssertion) -> str:
        """Format a clear error message for invariant assertion."""
        return (
            f"Invariant assertion failed\n"
            f"  Invariant: {assertion.invariant_name}\n"
            f"  Expected: invariant to hold\n"
            f"  Actual: invariant violated\n"
            f"  Location: line {assertion.line}"
        )
    
    def _format_propagation_error(self, assertion: PropagationAssertion) -> str:
        """Format a clear error message for propagation assertion."""
        return (
            f"Propagation assertion failed\n"
            f"  Source: {assertion.source_entity}\n"
            f"  Target: {assertion.target_entity}\n"
            f"  Field: {assertion.field}\n"
            f"  Expected: propagation occurred\n"
            f"  Actual: propagation did not occur\n"
            f"  Location: line {assertion.line}"
        )
    
    def get_errors(self) -> List[AssertionError]:
        """Get all assertion errors."""
        return self._errors.copy()
    
    def clear_errors(self):
        """Clear all assertion errors."""
        self._errors.clear()


class AssertionErrorException(Exception):
    """Exception raised when an assertion fails."""
    
    def __init__(self, error: AssertionError):
        self.error = error
        super().__init__(error.message)
    
    def __str__(self) -> str:
        return self.error.message


class CausalAssertionBuilder:
    """Builder for creating causal assertions."""
    
    @staticmethod
    def causes(subject: str, object: str) -> 'CausalAssertionBuilder':
        """Start building a causes assertion."""
        return CausalAssertionBuilder('causes', subject, object)
    
    @staticmethod
    def prevents(subject: str, object: str) -> 'CausalAssertionBuilder':
        """Start building a prevents assertion."""
        return CausalAssertionBuilder('prevents', subject, object)
    
    @staticmethod
    def requires(subject: str, object: str) -> 'CausalAssertionBuilder':
        """Start building a requires assertion."""
        return CausalAssertionBuilder('requires', subject, object)
    
    @staticmethod
    def precedes(subject: str, object: str) -> 'CausalAssertionBuilder':
        """Start building a precedes assertion."""
        return CausalAssertionBuilder('precedes', subject, object)
    
    @staticmethod
    def never(subject: str, object: str) -> 'CausalAssertionBuilder':
        """Start building a never assertion."""
        return CausalAssertionBuilder('never', subject, object)


class CausalAssertionBuilder:
    """Builder for causal assertions with modifiers."""
    
    def __init__(self, operator: str, subject: str, object: str):
        self.operator = operator
        self.subject = subject
        self.object = object
        self._modifiers = {}
    
    def within(self, duration: float, unit: str = 's') -> 'CausalAssertionBuilder':
        """Add within modifier."""
        self._modifiers['within'] = (duration, unit)
        return self
    
    def always(self) -> 'CausalAssertionBuilder':
        """Add always modifier."""
        self._modifiers['always'] = True
        return self
    
    def eventually(self, timeout: Optional[float] = None) -> 'CausalAssertionBuilder':
        """Add eventually modifier."""
        if timeout is not None:
            self._modifiers['eventually'] = (timeout, 's')
        else:
            self._modifiers['eventually'] = True
        return self
    
    def given(self, condition: str) -> 'CausalAssertionBuilder':
        """Add given modifier."""
        self._modifiers['given'] = condition
        return self
    
    def build(self) -> CausalTestNode:
        """Build the causal test node."""
        if self.operator == 'causes':
            return CausesNode(
                subject=self.subject,
                object=self.object,
                modifiers=self._modifiers
            )
        elif self.operator == 'prevents':
            return PreventsNode(
                subject=self.subject,
                object=self.object,
                modifiers=self._modifiers
            )
        elif self.operator == 'requires':
            return RequiresNode(
                subject=self.subject,
                object=self.object,
                modifiers=self._modifiers
            )
        elif self.operator == 'precedes':
            return PrecedesNode(
                subject=self.subject,
                object=self.object,
                modifiers=self._modifiers
            )
        elif self.operator == 'never':
            return NeverNode(
                subject=self.subject,
                object=self.object,
                modifiers=self._modifiers
            )
        
        return CausalTestNode(
            operator=self.operator,
            subject=self.subject,
            object=self.object,
            modifiers=self._modifiers
        )
