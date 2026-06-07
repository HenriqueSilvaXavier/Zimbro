"""
zimbro/unit_assertions.py — General unit testing assertions (Jest/Pytest style)
"""

from __future__ import annotations
from typing import Any, Callable, Optional, List
import math


class AssertionError(Exception):
    """Assertion error with detailed context."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
    
    def __str__(self) -> str:
        return self.message


def assert_equal(actual: Any, expected: Any, message: Optional[str] = None):
    """Assert that two values are equal."""
    if actual != expected:
        msg = message or f"Expected {expected!r} but got {actual!r}"
        raise AssertionError(msg)


def assert_not_equal(actual: Any, expected: Any, message: Optional[str] = None):
    """Assert that two values are not equal."""
    if actual == expected:
        msg = message or f"Expected {actual!r} to not equal {expected!r}"
        raise AssertionError(msg)


def assert_true(value: Any, message: Optional[str] = None):
    """Assert that a value is truthy."""
    if not value:
        msg = message or f"Expected {value!r} to be truthy"
        raise AssertionError(msg)


def assert_false(value: Any, message: Optional[str] = None):
    """Assert that a value is falsy."""
    if value:
        msg = message or f"Expected {value!r} to be falsy"
        raise AssertionError(msg)


def assert_is_none(value: Any, message: Optional[str] = None):
    """Assert that a value is None."""
    if value is not None:
        msg = message or f"Expected {value!r} to be None"
        raise AssertionError(msg)


def assert_is_not_none(value: Any, message: Optional[str] = None):
    """Assert that a value is not None."""
    if value is None:
        msg = message or "Expected value to not be None"
        raise AssertionError(msg)


def assert_in(item: Any, container: Any, message: Optional[str] = None):
    """Assert that an item is in a container."""
    if item not in container:
        msg = message or f"Expected {item!r} to be in {container!r}"
        raise AssertionError(msg)


def assert_not_in(item: Any, container: Any, message: Optional[str] = None):
    """Assert that an item is not in a container."""
    if item in container:
        msg = message or f"Expected {item!r} to not be in {container!r}"
        raise AssertionError(msg)


def assert_raises(exception_type: type, func: Callable, *args, **kwargs):
    """Assert that a function raises a specific exception."""
    try:
        func(*args, **kwargs)
        raise AssertionError(f"Expected {exception_type.__name__} to be raised")
    except exception_type:
        pass  # Expected exception was raised
    except Exception as e:
        raise AssertionError(f"Expected {exception_type.__name__} but got {type(e).__name__}: {e}")


def assert_almost_equal(actual: float, expected: float, places: int = 7, message: Optional[str] = None):
    """Assert that two floats are almost equal."""
    if not math.isclose(actual, expected, rel=10**-places):
        msg = message or f"Expected {expected!r} but got {actual!r} (within {places} decimal places)"
        raise AssertionError(msg)


class Expect:
    """Jest-style expect API."""
    
    def __init__(self, actual: Any):
        self.actual = actual
        self._negated = False
    
    def to_equal(self, expected: Any) -> 'Expect':
        if self._negated:
            assert_not_equal(self.actual, expected)
        else:
            assert_equal(self.actual, expected)
        return self
    
    def to_be(self, expected: Any) -> 'Expect':
        if self._negated:
            assert_not_equal(self.actual, expected)
        else:
            assert_equal(self.actual, expected)
        return self
    
    def to_be_truthy(self) -> 'Expect':
        if self._negated:
            assert_false(self.actual)
        else:
            assert_true(self.actual)
        return self
    
    def to_be_falsy(self) -> 'Expect':
        if self._negated:
            assert_true(self.actual)
        else:
            assert_false(self.actual)
        return self
    
    def to_be_none(self) -> 'Expect':
        if self._negated:
            assert_is_not_none(self.actual)
        else:
            assert_is_none(self.actual)
        return self
    
    def to_contain(self, item: Any) -> 'Expect':
        if self._negated:
            assert_not_in(item, self.actual)
        else:
            assert_in(item, self.actual)
        return self
    
    def to_throw(self, exception_type: Optional[type] = None) -> 'Expect':
        if not callable(self.actual):
            raise AssertionError("Expected a callable to check if it throws")
        
        try:
            self.actual()
            if not self._negated:
                raise AssertionError("Expected function to throw an exception")
        except Exception as e:
            if self._negated:
                raise AssertionError(f"Expected function not to throw, but got {type(e).__name__}: {e}")
            if exception_type and not isinstance(e, exception_type):
                raise AssertionError(f"Expected {exception_type.__name__} but got {type(e).__name__}: {e}")
        
        return self
    
    def to_be_close_to(self, expected: float, precision: int = 7) -> 'Expect':
        if self._negated:
            try:
                assert_almost_equal(self.actual, expected, precision)
                raise AssertionError(f"Expected {self.actual!r} to not be close to {expected!r}")
            except AssertionError:
                pass  # Expected to fail
        else:
            assert_almost_equal(self.actual, expected, precision)
        return self
    
    def not_(self) -> 'Expect':
        """Negate the assertion."""
        self._negated = not self._negated
        return self


def expect(actual: Any) -> Expect:
    """Create an Expect object for Jest-style assertions."""
    return Expect(actual)
