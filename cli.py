"""
zimbro/cli.py — Command-line interface for Zimbro
"""

import argparse
import sys
from zimbro.runner import create_runner


def main():
    parser = argparse.ArgumentParser(
        description="Zimbro — Biblioteca Oficial de Testes do Absinto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  zimbro run                          # Run all tests
  zimbro run --pattern "*.test.zim"   # Run with specific pattern
  zimbro run --parallel --workers 4   # Run in parallel
  zimbro run --coverage               # Run with coverage
  zimbro run --watch                 # Run in watch mode
  zimbro run --tags integration       # Run with specific tags
  zimbro run --name "Order*"          # Run with name pattern
  zimbro run --verbose                # Verbose output
  zimbro run --timeout 10s            # Custom timeout
  zimbro run --mode simulate          # Execution mode
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run tests')
    run_parser.add_argument('--pattern', default='*.zim', help='File pattern for test files')
    run_parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    run_parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    run_parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    run_parser.add_argument('--watch', action='store_true', help='Run in watch mode')
    run_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    run_parser.add_argument('--timeout', type=float, default=5.0, help='Test timeout in seconds')
    run_parser.add_argument('--mode', choices=['simulate', 'replay', 'continuous'], 
                          default='simulate', help='Execution mode')
    run_parser.add_argument('--tags', nargs='+', help='Filter by tags')
    run_parser.add_argument('--name', nargs='+', help='Filter by name pattern')
    run_parser.add_argument('--dir', default='.', help='Test directory')
    
    # Watch command (alias for run --watch)
    watch_parser = subparsers.add_parser('watch', help='Run tests in watch mode')
    watch_parser.add_argument('--pattern', default='*.zim', help='File pattern for test files')
    watch_parser.add_argument('--dir', default='.', help='Test directory')
    
    # Coverage command (alias for run --coverage)
    coverage_parser = subparsers.add_parser('coverage', help='Run tests with coverage')
    coverage_parser.add_argument('--pattern', default='*.zim', help='File pattern for test files')
    coverage_parser.add_argument('--dir', default='.', help='Test directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Create runner
    if args.command == 'watch':
        runner = create_runner(
            pattern=args.pattern,
            watch=True
        )
        runner.watch(args.dir)
    elif args.command == 'coverage':
        runner = create_runner(
            pattern=args.pattern,
            coverage=True
        )
        return runner.coverage(args.dir)
    else:  # run
        runner = create_runner(
            pattern=args.pattern,
            parallel=args.parallel,
            workers=args.workers,
            coverage=args.coverage,
            watch=args.watch,
            verbose=args.verbose,
            timeout=args.timeout,
            mode=args.mode,
            tags=args.tags,
            names=args.name
        )
        
        if args.watch:
            runner.watch(args.dir)
        elif args.coverage:
            return runner.coverage(args.dir)
        else:
            return runner.run(args.dir)


if __name__ == '__main__':
    sys.exit(main())
