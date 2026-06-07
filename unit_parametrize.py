"""
zimbro/unit_parametrize.py — Parametrized test support (Jest/Pytest style)
"""

from __future__ import annotations
from typing import Any, Callable, List, Dict, Optional
from dataclasses import dataclass, field
from functools import wraps


@dataclass
class ParametrizeCase:
    """A single test case for parametrized tests."""
    name: str
    parameters: Dict[str, Any]
    index: int


class Parametrize:
    """Parametrized test decorator."""
    
    def __init__(self, test_name: str, parameters: List[str], cases: List[Dict[str, Any]]):
        self.test_name = test_name
        self.parameter_names = parameters
        self.cases = cases
        self._test_func: Optional[Callable] = None
    
    def __call__(self, test_func: Callable) -> Callable:
        """Decorator to parametrize a test function."""
        self._test_func = test_func
        
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            # This will be called by the test runner
            pass
        
        wrapper._is_parametrized = True
        wrapper._parametrize_config = {
            'test_name': self.test_name,
            'parameter_names': self.parameter_names,
            'cases': self.cases,
            'test_func': test_func
        }
        
        return wrapper
    
    def get_cases(self) -> List[ParametrizeCase]:
        """Get all test cases."""
        cases = []
        for i, case_data in enumerate(self.cases):
            case_name = f"{self.test_name} (case {i + 1})"
            cases.append(ParametrizeCase(
                name=case_name,
                parameters=case_data,
                index=i
            ))
        return cases
    
    def run_case(self, case: ParametrizeCase):
        """Run a specific test case."""
        if self._test_func is None:
            raise ValueError("Test function not set")
        
        return self._test_func(**case.parameters)


def parametrize(test_name: str, parameters: List[str], cases: List[Dict[str, Any]]) -> Callable:
    """
    Create a parametrized test.
    
    Args:
        test_name: Name of the test
        parameters: List of parameter names
        cases: List of dictionaries with parameter values
    
    Example:
        @parametrize("Addition", ["a", "b", "expected"], [
            {"a": 1, "b": 2, "expected": 3},
            {"a": 5, "b": 10, "expected": 15},
        ])
        def test_addition(a, b, expected):
            assert_equal(a + b, expected)
    """
    return Parametrize(test_name, parameters, cases)


class ParametrizeMatrix:
    """Create a matrix of test cases from parameter combinations."""
    
    def __init__(self, test_name: str, parameters: Dict[str, List[Any]]):
        self.test_name = test_name
        self.parameters = parameters
    
    def generate_cases(self) -> List[Dict[str, Any]]:
        """Generate all combinations of parameters."""
        import itertools
        
        param_names = list(self.parameters.keys())
        param_values = list(self.parameters.values())
        
        cases = []
        for combination in itertools.product(*param_values):
            case = dict(zip(param_names, combination))
            cases.append(case)
        
        return cases
    
    def __call__(self, test_func: Callable) -> Callable:
        """Decorator to parametrize a test function with matrix."""
        cases = self.generate_cases()
        param_names = list(self.parameters.keys())
        
        return parametrize(self.test_name, param_names, cases)(test_func)


def parametrize_matrix(test_name: str, parameters: Dict[str, List[Any]]) -> Callable:
    """
    Create a parametrized test from a matrix of parameter combinations.
    
    Args:
        test_name: Name of the test
        parameters: Dictionary mapping parameter names to lists of values
    
    Example:
        @parametrize_matrix("String operations", {
            "input": ["hello", "world"],
            "operation": ["upper", "lower"],
        })
        def test_string_operations(input, operation):
            if operation == "upper":
                assert_equal(input.upper(), input.upper())
            else:
                assert_equal(input.lower(), input.lower())
    """
    return ParametrizeMatrix(test_name, parameters)
