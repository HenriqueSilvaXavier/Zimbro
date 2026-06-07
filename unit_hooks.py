"""
zimbro/unit_hooks.py — Setup/teardown hooks for test suites (Jest/Pytest style)
"""

from __future__ import annotations
from typing import Callable, List, Optional
from functools import wraps


class HookRegistry:
    """Registry for test hooks."""
    
    def __init__(self):
        self._before_all_hooks: List[Callable] = []
        self._after_all_hooks: List[Callable] = []
        self._before_each_hooks: List[Callable] = []
        self._after_each_hooks: List[Callable] = []
    
    def register_before_all(self, hook: Callable):
        """Register a beforeAll hook."""
        self._before_all_hooks.append(hook)
    
    def register_after_all(self, hook: Callable):
        """Register an afterAll hook."""
        self._after_all_hooks.append(hook)
    
    def register_before_each(self, hook: Callable):
        """Register a beforeEach hook."""
        self._before_each_hooks.append(hook)
    
    def register_after_each(self, hook: Callable):
        """Register an afterEach hook."""
        self._after_each_hooks.append(hook)
    
    def run_before_all(self):
        """Run all beforeAll hooks."""
        for hook in self._before_all_hooks:
            hook()
    
    def run_after_all(self):
        """Run all afterAll hooks."""
        for hook in reversed(self._after_all_hooks):
            hook()
    
    def run_before_each(self):
        """Run all beforeEach hooks."""
        for hook in self._before_each_hooks:
            hook()
    
    def run_after_each(self):
        """Run all afterEach hooks."""
        for hook in reversed(self._after_each_hooks):
            hook()
    
    def clear(self):
        """Clear all hooks."""
        self._before_all_hooks.clear()
        self._after_all_hooks.clear()
        self._before_each_hooks.clear()
        self._after_each_hooks.clear()


# Global hook registry
_global_registry = HookRegistry()


def before_all(hook: Optional[Callable] = None):
    """Decorator or function to register a beforeAll hook."""
    def decorator(func: Callable) -> Callable:
        _global_registry.register_before_all(func)
        return func
    
    if hook is not None:
        return decorator(hook)
    return decorator


def after_all(hook: Optional[Callable] = None):
    """Decorator or function to register an afterAll hook."""
    def decorator(func: Callable) -> Callable:
        _global_registry.register_after_all(func)
        return func
    
    if hook is not None:
        return decorator(hook)
    return decorator


def before_each(hook: Optional[Callable] = None):
    """Decorator or function to register a beforeEach hook."""
    def decorator(func: Callable) -> Callable:
        _global_registry.register_before_each(func)
        return func
    
    if hook is not None:
        return decorator(hook)
    return decorator


def after_each(hook: Optional[Callable] = None):
    """Decorator or function to register an afterEach hook."""
    def decorator(func: Callable) -> Callable:
        _global_registry.register_after_each(func)
        return func
    
    if hook is not None:
        return decorator(hook)
    return decorator


def get_global_registry() -> HookRegistry:
    """Get the global hook registry."""
    return _global_registry


def create_registry() -> HookRegistry:
    """Create a new hook registry."""
    return HookRegistry()
