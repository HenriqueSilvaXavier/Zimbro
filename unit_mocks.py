"""
zimbro/unit_mocks.py — General mocking functionality (Jest/Pytest style)
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from functools import wraps


@dataclass
class MockCall:
    """Record of a mock call."""
    args: tuple
    kwargs: dict
    return_value: Any = None
    exception: Optional[Exception] = None


class Mock:
    """General mock object for functions and objects."""
    
    def __init__(self, name: str = "mock"):
        self.name = name
        self._return_value: Any = None
        self._return_values: List[Any] = []
        self._exception: Optional[Exception] = None
        self._implementation: Optional[Callable] = None
        self._call_history: List[MockCall] = []
        self._call_count: int = 0
        self._when_conditions: List[Dict[str, Any]] = []
    
    def __call__(self, *args, **kwargs):
        """Record the call and return configured value."""
        self._call_count += 1
        call = MockCall(args=args, kwargs=kwargs)
        self._call_history.append(call)
        
        # Check if there's a matching when condition
        for condition in self._when_conditions:
            if self._matches_condition(condition, args, kwargs):
                if condition.get('raises'):
                    raise condition['raises']
                return condition.get('returns')
        
        # Use implementation if provided
        if self._implementation:
            return self._implementation(*args, **kwargs)
        
        # Use exception if configured
        if self._exception:
            raise self._exception
        
        # Use return values queue if available
        if self._return_values:
            if len(self._return_values) > self._call_count - 1:
                return self._return_values[self._call_count - 1]
        
        # Use default return value
        return self._return_value
    
    def _matches_condition(self, condition: Dict[str, Any], args: tuple, kwargs: dict) -> bool:
        """Check if the call matches a when condition."""
        when_args = condition.get('args', ())
        when_kwargs = condition.get('kwargs', {})
        
        # Check args
        if when_args != args:
            return False
        
        # Check kwargs
        for key, value in when_kwargs.items():
            if kwargs.get(key) != value:
                return False
        
        return True
    
    def returns(self, value: Any) -> 'Mock':
        """Set the return value."""
        self._return_value = value
        return self
    
    def returns_sequence(self, values: List[Any]) -> 'Mock':
        """Set a sequence of return values."""
        self._return_values = values
        return self
    
    def raises(self, exception: Exception) -> 'Mock':
        """Set the exception to raise."""
        self._exception = exception
        return self
    
    def implements(self, func: Callable) -> 'Mock':
        """Set the implementation function."""
        self._implementation = func
        return self
    
    @property
    def call_count(self) -> int:
        """Get the number of times the mock was called."""
        return self._call_count
    
    @property
    def called(self) -> bool:
        """Check if the mock was called."""
        return self._call_count > 0
    
    def reset(self):
        """Reset the mock state."""
        self._call_history.clear()
        self._call_count = 0
        self._return_value = None
        self._return_values.clear()
        self._exception = None
        self._implementation = None
        self._when_conditions.clear()
    
    def get_calls(self) -> List[MockCall]:
        """Get all recorded calls."""
        return self._call_history.copy()
    
    def called_with(self, *args, **kwargs) -> bool:
        """Check if the mock was called with specific arguments."""
        for call in self._call_history:
            if call.args == args and call.kwargs == kwargs:
                return True
        return False


class WhenBuilder:
    """Builder for when() conditions."""
    
    def __init__(self, mock: Mock):
        self.mock = mock
        self._args: tuple = ()
        self._kwargs: dict = {}
    
    def called_with(self, *args, **kwargs) -> 'WhenBuilder':
        """Set the condition arguments."""
        self._args = args
        self._kwargs = kwargs
        return self
    
    def then_returns(self, value: Any) -> Mock:
        """Set the return value for this condition."""
        self.mock._when_conditions.append({
            'args': self._args,
            'kwargs': self._kwargs,
            'returns': value
        })
        return self.mock
    
    def then_raises(self, exception: Exception) -> Mock:
        """Set the exception to raise for this condition."""
        self.mock._when_conditions.append({
            'args': self._args,
            'kwargs': self._kwargs,
            'raises': exception
        })
        return self.mock


def when(mock: Mock) -> WhenBuilder:
    """Create a WhenBuilder for a mock."""
    return WhenBuilder(mock)


class Spy:
    """Spy on function calls without modifying behavior."""
    
    def __init__(self, func: Callable, name: Optional[str] = None):
        self._original_func = func
        self.name = name or func.__name__
        self._call_history: List[MockCall] = []
        self._call_count: int = 0
        self._enabled = True
    
    def __call__(self, *args, **kwargs):
        """Record the call and call the original function."""
        if not self._enabled:
            return self._original_func(*args, **kwargs)
        
        self._call_count += 1
        try:
            result = self._original_func(*args, **kwargs)
            call = MockCall(args=args, kwargs=kwargs, return_value=result)
            self._call_history.append(call)
            return result
        except Exception as e:
            call = MockCall(args=args, kwargs=kwargs, exception=e)
            self._call_history.append(call)
            raise
    
    @property
    def call_count(self) -> int:
        """Get the number of times the spy was called."""
        return self._call_count
    
    @property
    def called(self) -> bool:
        """Check if the spy was called."""
        return self._call_count > 0
    
    def reset(self):
        """Reset the spy state."""
        self._call_history.clear()
        self._call_count = 0
    
    def get_calls(self) -> List[MockCall]:
        """Get all recorded calls."""
        return self._call_history.copy()
    
    def disable(self):
        """Disable the spy (calls pass through without recording)."""
        self._enabled = False
    
    def enable(self):
        """Enable the spy."""
        self._enabled = True


def spy(func: Callable, name: Optional[str] = None) -> Spy:
    """Create a spy for a function."""
    return Spy(func, name)


def mock_function(name: str = "mock") -> Mock:
    """Create a new mock function."""
    return Mock(name)


def mock_object(obj: Any) -> Any:
    """Create a mock of an object."""
    mock = Mock(name=obj.__class__.__name__)
    return mock
