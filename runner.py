"""
zimbro/runner.py — Test runner with suite grouping, lifecycle hooks, and formatted output
"""

from __future__ import annotations
import os
import sys
import time
import fnmatch
import traceback
from typing import List, Optional, Set, Callable
from dataclasses import dataclass, field
from pathlib import Path

from .lexer import ZimbroLexer
from .parser import ZimbroParser
from .engine import ZimbroEngine, TestResult, SuiteResult, ExecutionConfig, ParallelTestExecutor
from .ast_nodes import TestSuiteNode, TestNode
from .mock import MockRegistry


@dataclass
class RunnerConfig:
    """Configuration for the test runner."""
    test_pattern: str = "*.zim"  # File pattern for test files
    parallel: bool = False
    workers: int = 4
    coverage: bool = False
    watch: bool = False
    verbose: bool = False
    timeout: float = 5.0
    filter_tags: Set[str] = field(default_factory=set)
    filter_names: Set[str] = field(default_factory=set)
    mode: str = "simulate"  # simulate | replay | continuous


class ZimbroRunner:
    """Main test runner for Zimbro."""
    
    def __init__(self, config: Optional[RunnerConfig] = None):
        self.config = config or RunnerConfig()
        self.engine = ZimbroEngine()
        self.mock_registry = MockRegistry()
        self._test_files: List[str] = []
        self._suites: List[TestSuiteNode] = []
        self._results: List[SuiteResult] = []
    
    def discover_tests(self, test_dir: str = ".") -> List[str]:
        """Discover test files in the given directory."""
        test_files = []
        
        for root, dirs, files in os.walk(test_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if fnmatch.fnmatch(file, self.config.test_pattern):
                    test_files.append(os.path.join(root, file))
        
        self._test_files = test_files
        return test_files
    
    def load_tests(self, test_file: str) -> List[TestSuiteNode]:
        """Load tests from a file."""
        with open(test_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        lexer = ZimbroLexer(source)
        tokens = lexer.tokenize()
        
        parser = ZimbroParser(tokens)
        suites = parser.parse()
        
        return suites
    
    def load_all_tests(self):
        """Load all tests from discovered test files."""
        all_suites = []
        
        for test_file in self._test_files:
            suites = self.load_tests(test_file)
            all_suites.extend(suites)
        
        self._suites = all_suites
        return all_suites
    
    def filter_tests(self, suites: List[TestSuiteNode]) -> List[TestSuiteNode]:
        """Filter tests based on tags and names."""
        filtered = []
        
        for suite in suites:
            # Filter by tags
            if self.config.filter_tags:
                if not any(tag in suite.tags for tag in self.config.filter_tags):
                    continue
            
            # Filter by suite name
            if self.config.filter_names:
                if not any(fnmatch.fnmatch(suite.name, pattern) for pattern in self.config.filter_names):
                    continue
            
            # Filter tests within suite
            filtered_tests = []
            for test in suite.tests:
                # Filter by tags
                if self.config.filter_tags:
                    if not any(tag in test.tags for tag in self.config.filter_tags):
                        continue
                
                # Filter by test name
                if self.config.filter_names:
                    if not any(fnmatch.fnmatch(test.name, pattern) for pattern in self.config.filter_names):
                        continue
                
                filtered_tests.append(test)
            
            if filtered_tests:
                filtered_suite = TestSuiteNode(
                    name=suite.name,
                    description=suite.description,
                    tests=filtered_tests,
                    before_all=suite.before_all,
                    after_all=suite.after_all,
                    before_each=suite.before_each,
                    after_each=suite.after_each,
                    tags=suite.tags,
                    line=suite.line
                )
                filtered.append(filtered_suite)
        
        return filtered
    
    def run(self, test_dir: str = ".") -> int:
        """Run all tests and return exit code."""
        # Discover tests
        self.discover_tests(test_dir)
        
        if not self._test_files:
            self._print_no_tests_found()
            return 0
        
        # Load tests
        self.load_all_tests()
        
        if not self._suites:
            self._print_no_tests_found()
            return 0
        
        # Filter tests
        filtered_suites = self.filter_tests(self._suites)
        
        if not filtered_suites:
            self._print_no_tests_match()
            return 0
        
        # Configure engine
        self.engine.config = ExecutionConfig(
            mode=self.config.mode,
            parallel=self.config.parallel,
            workers=self.config.workers,
            timeout=self.config.timeout,
            verbose=self.config.verbose,
            coverage=self.config.coverage
        )
        
        # Run tests
        start_time = time.time()
        
        if self.config.parallel:
            executor = ParallelTestExecutor(self.engine, self.config.workers)
            self._results = executor.execute_suites_parallel(filtered_suites)
        else:
            for suite in filtered_suites:
                result = self.engine.execute_suite(suite)
                self._results.append(result)
        
        total_duration = time.time() - start_time
        
        # Print results
        self._print_results(total_duration)
        
        # Return exit code
        total_passed = sum(r.passed for r in self._results)
        total_failed = sum(r.failed for r in self._results)
        
        return 0 if total_failed == 0 else 1
    
    def _print_no_tests_found(self):
        """Print message when no tests are found."""
        print("🔍 No test files found")
        print(f"  Pattern: {self.config.test_pattern}")
        print(f"  Directory: {os.getcwd()}")
    
    def _print_no_tests_match(self):
        """Print message when no tests match filters."""
        print("🔍 No tests match the specified filters")
        if self.config.filter_tags:
            print(f"  Tags: {', '.join(self.config.filter_tags)}")
        if self.config.filter_names:
            print(f"  Names: {', '.join(self.config.filter_names)}")
    
    def _print_results(self, total_duration: float):
        """Print formatted test results."""
        total_passed = sum(r.passed for r in self._results)
        total_failed = sum(r.failed for r in self._results)
        total_tests = total_passed + total_failed
        
        print("\n" + "=" * 70)
        print("🧪 ZIMBRO TEST RESULTS")
        print("=" * 70)
        
        # Print suite results
        for result in self._results:
            self._print_suite_result(result)
        
        # Print summary
        print("\n" + "-" * 70)
        print(f"Total: {total_tests} tests")
        print(f"✓ Passed: {total_passed}")
        print(f"✗ Failed: {total_failed}")
        print(f"⏱ Duration: {total_duration:.2f}s")
        print("=" * 70)
        
        # Print failed test details
        if total_failed > 0:
            print("\n❌ FAILED TESTS:")
            print("-" * 70)
            for result in self._results:
                for test_result in result.tests:
                    if not test_result.passed:
                        self._print_failed_test(test_result)
    
    def _print_suite_result(self, result: SuiteResult):
        """Print results for a single suite."""
        status_icon = "✓" if result.failed == 0 else "✗"
        print(f"\n{status_icon} {result.suite_name}")
        print(f"  Tests: {len(result.tests)}")
        print(f"  Passed: {result.passed}")
        print(f"  Failed: {result.failed}")
        print(f"  Duration: {result.duration:.2f}s")
        
        if self.config.verbose:
            for test_result in result.tests:
                status_icon = "✓" if test_result.passed else "✗"
                print(f"    {status_icon} {test_result.name} ({test_result.duration:.2f}s)")
    
    def _print_failed_test(self, test_result: TestResult):
        """Print details of a failed test."""
        print(f"\n  ✗ {test_result.name}")
        print(f"    Duration: {test_result.duration:.2f}s")
        
        if test_result.error:
            print(f"    Error: {test_result.error}")
        
        if test_result.causal_violations:
            print(f"    Causal Violations:")
            for violation in test_result.causal_violations:
                print(f"      - {violation}")
    
    def watch(self, test_dir: str = "."):
        """Run tests in watch mode."""
        print("👀 Watch mode enabled")
        print(f"  Watching: {test_dir}")
        print(f"  Pattern: {self.config.test_pattern}")
        print("  Press Ctrl+C to stop\n")
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class TestFileHandler(FileSystemEventHandler):
                def __init__(self, runner):
                    self.runner = runner
                
                def on_modified(self, event):
                    if not event.is_directory and fnmatch.fnmatch(
                        os.path.basename(event.src_path),
                        self.runner.config.test_pattern
                    ):
                        print(f"\n📝 File changed: {event.src_path}")
                        print("Re-running tests...\n")
                        self.runner.run(test_dir)
            
            event_handler = TestFileHandler(self)
            observer = Observer()
            observer.schedule(event_handler, test_dir, recursive=True)
            observer.start()
            
            # Initial run
            self.run(test_dir)
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            
            observer.join()
        
        except ImportError:
            print("⚠ Watch mode requires 'watchdog' package")
            print("  Install with: pip install watchdog")
            print("  Falling back to single run...\n")
            self.run(test_dir)
    
    def coverage(self, test_dir: str = "."):
        """Run tests with coverage report."""
        try:
            import coverage
            
            cov = coverage.Coverage()
            cov.start()
            
            exit_code = self.run(test_dir)
            
            cov.stop()
            cov.save()
            
            print("\n" + "=" * 70)
            print("📊 COVERAGE REPORT")
            print("=" * 70)
            cov.report()
            
            return exit_code
        
        except ImportError:
            print("⚠ Coverage requires 'coverage' package")
            print("  Install with: pip install coverage")
            print("  Running without coverage...\n")
            return self.run(test_dir)


def create_runner(
    pattern: str = "*.zim",
    parallel: bool = False,
    workers: int = 4,
    coverage: bool = False,
    watch: bool = False,
    verbose: bool = False,
    timeout: float = 5.0,
    mode: str = "simulate",
    tags: Optional[List[str]] = None,
    names: Optional[List[str]] = None
) -> ZimbroRunner:
    """Create a configured Zimbro runner."""
    config = RunnerConfig(
        test_pattern=pattern,
        parallel=parallel,
        workers=workers,
        coverage=coverage,
        watch=watch,
        verbose=verbose,
        timeout=timeout,
        mode=mode,
        filter_tags=set(tags or []),
        filter_names=set(names or [])
    )
    
    return ZimbroRunner(config)
