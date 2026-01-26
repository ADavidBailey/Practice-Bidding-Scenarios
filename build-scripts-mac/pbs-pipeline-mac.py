#!/usr/bin/env python3
"""
Mac build pipeline for Practice-Bidding-Scenarios.
Replaces OneScriptToRuleThemAll.ps1 from Windows.

Usage:
    python build.py <scenario_pattern> <operations>

Examples:
    python build.py Smolen "*"           # All operations on Smolen
    python build.py Smolen dlr,pbn,bba   # Specific operations
    python build.py Smolen "bba+"        # From bba through end
    python build.py "*" "*"              # All scenarios, all operations
    python build.py "1N*" "*"            # Pattern match scenarios
"""
import argparse
import fnmatch
import os
import sys
import time

from config import FOLDERS, OPERATIONS_ORDER
from ssh_runner import test_ssh_connection

# ANSI color codes
RED = '\033[91m'
RESET = '\033[0m'


def print_error(msg: str):
    """Print error message in red."""
    print(f"{RED}{msg}{RESET}")

# Import operations
from operations.dlr import run_dlr
from operations.pbn import run_pbn
from operations.rotate import run_rotate
from operations.bba import run_bba
from operations.filter import run_filter
from operations.filter_stats import run_filter_stats
from operations.bidding_sheet import run_bidding_sheet


# Map operation names to functions
OPERATIONS = {
    "dlr": run_dlr,
    "pbn": run_pbn,
    "rotate": run_rotate,
    "bba": run_bba,
    "title": lambda scenario, verbose=True: True,  # Skip title (not implemented)
    "filter": run_filter,
    "filterStats": run_filter_stats,
    "biddingSheet": run_bidding_sheet,
}

# Create case-insensitive lookup: lowercase -> canonical name
OPERATIONS_LOOKUP = {name.lower(): name for name in OPERATIONS.keys()}
OPERATIONS_ORDER_LOOKUP = {name.lower(): name for name in OPERATIONS_ORDER}


def normalize_operation(op: str) -> str:
    """Convert operation name to canonical form (case-insensitive)."""
    return OPERATIONS_LOOKUP.get(op.lower(), op)


def get_scenarios(pattern: str) -> list:
    """
    Get list of scenarios matching the pattern.

    Args:
        pattern: Scenario name or wildcard pattern (e.g., "Smolen", "*", "1N*")

    Returns:
        List of scenario names
    """
    pbs_dir = FOLDERS["pbs"]

    if pattern == "*":
        # All scenarios
        scenarios = []
        for f in os.listdir(pbs_dir):
            if not f.startswith("."):  # Skip hidden files
                scenarios.append(f)
        return sorted(scenarios)
    elif "*" in pattern or "?" in pattern:
        # Wildcard pattern
        scenarios = []
        for f in os.listdir(pbs_dir):
            if fnmatch.fnmatch(f, pattern) and not f.startswith("."):
                scenarios.append(f)
        return sorted(scenarios)
    else:
        # Single scenario - find the actual folder name with correct case
        for f in os.listdir(pbs_dir):
            if f.lower() == pattern.lower():
                return [f]
        # No match found, return as-is (will fail later with clear error)
        return [pattern]


def expand_operations(operation_spec: str) -> list:
    """
    Expand operation specification into list of operations.

    Supports:
        "*" - all operations
        "op1,op2,op3" - specific operations (case-insensitive)
        "op+" - from op through end (case-insensitive)

    Args:
        operation_spec: Operation specification

    Returns:
        List of operation names (canonical form)
    """
    if operation_spec == "*" or operation_spec.lower() == "all":
        return OPERATIONS_ORDER.copy()

    # Check for "operation+" syntax
    if operation_spec.endswith("+"):
        start_op = operation_spec[:-1].lower()
        if start_op in OPERATIONS_ORDER_LOOKUP:
            canonical = OPERATIONS_ORDER_LOOKUP[start_op]
            start_idx = OPERATIONS_ORDER.index(canonical)
            return OPERATIONS_ORDER[start_idx:]
        else:
            print(f"Unknown operation: {operation_spec[:-1]}")
            return []

    # Comma-separated list
    operations = [op.strip() for op in operation_spec.split(",")]

    # Validate and normalize operations
    valid_ops = []
    for op in operations:
        canonical = normalize_operation(op)
        if canonical in OPERATIONS:
            valid_ops.append(canonical)
        else:
            print(f"Warning: Unknown operation '{op}', skipping")

    return valid_ops


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"


def run_operations(scenario: str, operations: list, verbose: bool = True) -> bool:
    """
    Run a list of operations on a scenario.

    Args:
        scenario: Scenario name
        operations: List of operation names
        verbose: Whether to print progress

    Returns:
        True if all operations succeeded
    """
    success = True
    durations = {}

    for op in operations:
        if op not in OPERATIONS:
            print(f"Unknown operation: {op}")
            continue

        op_func = OPERATIONS[op]
        start_time = time.time()
        try:
            result = op_func(scenario, verbose=verbose)
            elapsed = time.time() - start_time
            durations[op] = elapsed
            if not result:
                print_error(f"Operation {op} failed for {scenario} ({format_duration(elapsed)})")
                success = False
                break  # Stop on first failure
        except Exception as e:
            elapsed = time.time() - start_time
            durations[op] = elapsed
            print_error(f"Error in operation {op} for {scenario}: {e} ({format_duration(elapsed)})")
            success = False
            break  # Stop on first failure

    # Print duration summary
    if durations and verbose:
        total = sum(durations.values())
        print(f"\n  Duration summary:")
        for op, dur in durations.items():
            print(f"    {op:15} {format_duration(dur):>10}")
        print(f"    {'─' * 26}")
        print(f"    {'Total':15} {format_duration(total):>10}")

    return success


def main():
    parser = argparse.ArgumentParser(
        description="Mac build pipeline for Practice-Bidding-Scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python build.py Smolen "*"           # All operations on Smolen
    python build.py Smolen dlr,pbn,bba   # Specific operations
    python build.py Smolen "bba+"        # From bba through end
    python build.py "*" "*"              # All scenarios, all operations
    python build.py "1N*" "*"            # Pattern match scenarios

Operations (in order):
    dlr         - Extract dealer code from PBS file
    pbn         - Generate PBN from DLR (Windows: dealer.exe)
    rotate      - Create rotated files for 4-player (Windows: SetDealerMulti.js)
    bba         - Generate BBA with bidding (Windows: BBA.exe)
    title       - Set title (skipped)
    filter      - Filter by auction pattern (Windows: Filter.js)
    filterStats - Show filter statistics
    biddingSheet - Generate bidding sheets PDF
        """,
    )

    parser.add_argument(
        "scenario_pattern",
        help="Scenario name or pattern (e.g., 'Smolen', '*', '1N*')",
    )
    parser.add_argument(
        "operations",
        help="Operations to run: '*' for all, 'op1,op2' for specific, 'op+' from op to end",
    )
    parser.add_argument(
        "--no-ssh-check",
        action="store_true",
        help="Skip SSH connection check at startup",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Reduce output verbosity",
    )

    args = parser.parse_args()

    # Check SSH connection unless skipped
    if not args.no_ssh_check:
        print("Checking SSH connection to Windows VM...")
        if not test_ssh_connection():
            print("\nSSH connection failed. Options:")
            print("  1. Ensure Windows VM is running")
            print("  2. Check SSH server is enabled on Windows")
            print("  3. Use --no-ssh-check to skip this test")
            sys.exit(1)
        print("  SSH connection OK\n")

    # Get scenarios
    scenarios = get_scenarios(args.scenario_pattern)
    if not scenarios:
        print(f"No scenarios found matching: {args.scenario_pattern}")
        sys.exit(1)

    # Get operations
    operations = expand_operations(args.operations)
    if not operations:
        print(f"No valid operations specified: {args.operations}")
        sys.exit(1)

    print(f"Scenarios: {', '.join(scenarios)}")
    print(f"Operations: {', '.join(operations)}")
    print()

    # Run operations on each scenario
    verbose = not args.quiet
    failed_scenarios = []

    for scenario in scenarios:
        print(f"{'=' * 60}")
        print(f"Processing: {scenario}")
        print(f"{'=' * 60}")

        if not run_operations(scenario, operations, verbose=verbose):
            failed_scenarios.append(scenario)
            print_error(f"\nFailed: {scenario} - continuing with next scenario")
        else:
            print(f"\nCompleted: {scenario}")

        print()

    # Summary
    if not failed_scenarios:
        print("All scenarios completed successfully!")
    else:
        print_error(f"\n{len(failed_scenarios)} scenario(s) had errors:")
        for s in failed_scenarios:
            print_error(f"  - {s}")
        sys.exit(1)


if __name__ == "__main__":
    main()
