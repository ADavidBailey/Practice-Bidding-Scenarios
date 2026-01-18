#!/usr/bin/env python3
"""
PBN file comparison tool for Practice-Bidding-Scenarios.

Compares PBN files with support for:
- Raw text diff (line-by-line)
- Semantic diff (structure-aware, ignoring formatting/comments)
- Git integration (compare against committed versions)
- Cross-stage comparison (compare across pipeline stages)

Usage:
    python pbn-diff.py file1.pbn file2.pbn           # Semantic diff (default)
    python pbn-diff.py file1.pbn file2.pbn --raw     # Raw text diff
    python pbn-diff.py bba/1N.pbn --git              # Compare vs git HEAD
    python pbn-diff.py 1N --cross-stage pbn bba      # Cross-stage comparison
    python pbn-diff.py --list-stages                 # List available stages

See --help for full options.
"""
import os
import sys

# Add module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pbn_diff.cli import main

if __name__ == "__main__":
    sys.exit(main())
