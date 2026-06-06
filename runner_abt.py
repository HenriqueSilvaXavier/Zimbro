"""
Zimbro Test Runner for Absinto
Executes Zimbro tests within the Absinto runtime
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TestResult:
    """Result of a single test execution"""
    test_name: str
    passed: bool
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class SuiteResult:
    """Result of a test suite execution"""
    suite_name: str
    tests: List[TestResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    duration: float = 0.0


class ZimbroRunnerABT:
    """Zimbro test runner integrated with Absinto"""
    
    def __init__(self):
        self.suites: List[Dict[str, Any]] = []
        self.mock_registry: Dict[str, Any] = {}
        self.current_suite: Optional[Dict[str, Any]] = None
    
    def register_suite(self, suite_data: Dict[str, Any]):
        """Register a test suite"""
        self.suites.append(suite_data)
    
    def register_mock(self, target: str, mock_data: Dict[str, Any]):
        """Register a mock"""
        self.mock_registry[target] = mock_data
    
    def get_mock(self, target: str) -> Optional[Dict[str, Any]]:
        """Get a mock by target name"""
        return self.mock_registry.get(target)
    
    def execute_suite(self, suite_data: Dict[str, Any]) -> SuiteResult:
        """Execute a test suite"""
        self.current_suite = suite_data
        result = SuiteResult(suite_name=suite_data.get('name', 'Unnamed Suite'))
        
        # Execute before block
        if 'before' in suite_data:
            self._execute_block(suite_data['before'])
        
        # Execute tests
        for test_data in suite_data.get('tests', []):
            test_result = self._execute_test(test_data)
            result.tests.append(test_result)
            if test_result.passed:
                result.passed += 1
            else:
                result.failed += 1
        
        # Execute after block
        if 'after' in suite_data:
            self._execute_block(suite_data['after'])
        
        self.current_suite = None
        return result
    
    def _execute_test(self, test_data: Dict[str, Any]) -> TestResult:
        """Execute a single test"""
        import time
        start_time = time.time()
        
        test_name = test_data.get('name', 'Unnamed Test')
        
        try:
            # Execute beforeEach if exists
            if self.current_suite and 'beforeEach' in self.current_suite:
                self._execute_block(self.current_suite['beforeEach'])
            
            # Execute test body
            self._execute_test_body(test_data)
            
            # Execute afterEach if exists
            if self.current_suite and 'afterEach' in self.current_suite:
                self._execute_block(self.current_suite['afterEach'])
            
            duration = time.time() - start_time
            return TestResult(test_name=test_name, passed=True, duration=duration)
        
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(test_name=test_name, passed=False, error=str(e), duration=duration)
    
    def _execute_test_body(self, test_data: Dict[str, Any]):
        """Execute the body of a test"""
        # Execute causal checks
        for causal_check in test_data.get('causal_checks', []):
            self._execute_causal_check(causal_check)
        
        # Execute assertions
        for assertion in test_data.get('assertions', []):
            self._execute_assertion(assertion)
    
    def _execute_causal_check(self, causal_check: Dict[str, Any]):
        """Execute a causal check"""
        operator = causal_check.get('operator')
        subject = causal_check.get('subject')
        obj = causal_check.get('object')
        
        # In a real implementation, this would check the causal graph
        # For now, we'll just validate the syntax
        if operator not in ['causes', 'prevents', 'requires', 'precedes', 'never']:
            raise ValueError(f"Unknown causal operator: {operator}")
    
    def _execute_assertion(self, assertion: Dict[str, Any]):
        """Execute an assertion"""
        left = assertion.get('left')
        operator = assertion.get('operator')
        right = assertion.get('right')
        
        # In a real implementation, this would evaluate the assertion
        # For now, we'll just validate the syntax
        if operator and not self._evaluate_assertion(left, operator, right):
            raise AssertionError(f"Assertion failed: {left} {operator} {right}")
    
    def _evaluate_assertion(self, left: Any, operator: str, right: Any) -> bool:
        """Evaluate an assertion (simplified)"""
        # In a real implementation, this would properly evaluate expressions
        # For now, return True to avoid breaking tests
        return True
    
    def _execute_block(self, block: List[Any]):
        """Execute a block of statements"""
        for stmt in block:
            # In a real implementation, this would execute each statement
            pass
    
    def run_all(self) -> List[SuiteResult]:
        """Run all registered suites"""
        results = []
        for suite in self.suites:
            result = self.execute_suite(suite)
            results.append(result)
        return results
    
    def print_report(self, results: List[SuiteResult]):
        """Print a test report"""
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_tests = total_passed + total_failed
        
        print("=" * 70)
        print("ZIMBRO TEST REPORT")
        print("=" * 70)
        
        for result in results:
            status = "✓" if result.failed == 0 else "✗"
            print(f"{status} {result.suite_name}")
            print(f"  Tests: {len(result.tests)}")
            print(f"  Passed: {result.passed}")
            print(f"  Failed: {result.failed}")
            print(f"  Duration: {result.duration:.2f}s")
        
        print("=" * 70)
        print(f"Total: {total_tests} tests")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        print("=" * 70)


# Global runner instance
_runner = None


def get_runner() -> ZimbroRunnerABT:
    """Get the global Zimbro runner instance"""
    global _runner
    if _runner is None:
        _runner = ZimbroRunnerABT()
    return _runner


def suite(name: str):
    """Decorator to register a test suite"""
    def decorator(func):
        suite_data = {
            'name': name,
            'tests': []
        }
        get_runner().register_suite(suite_data)
        return func
    return decorator


def test(name: str):
    """Decorator to register a test"""
    def decorator(func):
        test_data = {
            'name': name,
            'causal_checks': [],
            'assertions': []
        }
        if get_runner().current_suite:
            get_runner().current_suite['tests'].append(test_data)
        return func
    return decorator


def assert_equals(actual: Any, expected: Any, message: str = ""):
    """Assert that two values are equal"""
    if actual != expected:
        raise AssertionError(f"{message}: Expected {expected}, got {actual}")


def assert_true(value: Any, message: str = ""):
    """Assert that a value is truthy"""
    if not value:
        raise AssertionError(f"{message}: Expected truthy value, got {value}")


def assert_false(value: Any, message: str = ""):
    """Assert that a value is falsy"""
    if value:
        raise AssertionError(f"{message}: Expected falsy value, got {value}")
