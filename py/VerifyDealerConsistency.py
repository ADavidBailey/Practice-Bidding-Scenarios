#!/usr/bin/env python3
"""
Verify Dealer Consistency in Practice Bidding Scenarios

This script checks that the dealer statement in the dealer code matches
the dealer indicator in the wrapper code.

Usage:
    python verify_dealer_consistency.py <directory_or_file>
    python verify_dealer_consistency.py PBS/
    python verify_dealer_consistency.py PBS/some_scenario.txt
"""

import sys
import os
import re
from pathlib import Path
from typing import Tuple, Optional, List


class DealerConsistencyChecker:
    """Check consistency between dealer statements and wrapper indicators."""
    
    # Map dealer names to single-letter codes
    DEALER_MAP = {
        'north': 'N',
        'east': 'E',
        'south': 'S',
        'west': 'W'
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checked_files = 0
        self.inconsistent_files = 0
    
    def extract_dealer_from_code(self, content: str) -> Optional[str]:
        """
        Extract the dealer from the dealer code statement.
        Looks for patterns like: dealer south, dealer north, etc.
        """
        # Match 'dealer' followed by whitespace and a direction word
        pattern = r'\bdealer\s+(north|east|south|west)\b'
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            dealer_word = match.group(1).lower()
            return self.DEALER_MAP.get(dealer_word)
        return None
    
    def extract_dealer_from_wrapper(self, content: str) -> Optional[str]:
        """
        Extract the dealer indicator from the setDealerCode wrapper.
        Looks for patterns like: `,"S",true) or `,"N",false)
        """
        # Match the pattern: backtick, comma, quote, single letter, quote
        pattern = r'`\s*,\s*"([NESW])"\s*,\s*(true|false)\s*\)'
        match = re.search(pattern, content)
        
        if match:
            return match.group(1)
        return None
    
    def check_file(self, filepath: Path) -> bool:
        """
        Check a single file for dealer consistency.
        Returns True if consistent, False otherwise.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.warnings.append(f"Could not read {filepath}: {e}")
            return True  # Don't count as inconsistent
        
        # Extract both dealer indicators
        dealer_code = self.extract_dealer_from_code(content)
        dealer_wrapper = self.extract_dealer_from_wrapper(content)
        
        # Check if we found both
        if dealer_code is None and dealer_wrapper is None:
            self.warnings.append(f"{filepath}: No dealer information found")
            return True
        
        if dealer_code is None:
            self.warnings.append(f"{filepath}: No 'dealer' statement found in code")
            return True
        
        if dealer_wrapper is None:
            self.warnings.append(f"{filepath}: No dealer indicator found in wrapper")
            return True
        
        # Compare them
        if dealer_code != dealer_wrapper:
            self.errors.append(
                f"{filepath}:\n"
                f"  Dealer code says: {dealer_code} "
                f"({self._get_full_name(dealer_code)})\n"
                f"  Wrapper says:     {dealer_wrapper} "
                f"({self._get_full_name(dealer_wrapper)})"
            )
            return False
        
        return True
    
    def _get_full_name(self, letter: str) -> str:
        """Convert single letter back to full name."""
        reverse_map = {v: k for k, v in self.DEALER_MAP.items()}
        return reverse_map.get(letter, "unknown")
    
    def check_directory(self, directory: Path) -> None:
        """Recursively check all files in a directory."""
        # Look for .txt files and files without extensions that might be scenarios
        patterns = ['*.txt', '*']
        
        files_to_check = []
        for pattern in patterns:
            files_to_check.extend(directory.rglob(pattern))
        
        # Filter to only files (not directories)
        files_to_check = [f for f in files_to_check if f.is_file()]
        
        # Skip certain files/directories
        skip_patterns = ['.git', '__pycache__', '.pyc', '.md', '.json', '.html']
        files_to_check = [
            f for f in files_to_check 
            if not any(skip in str(f) for skip in skip_patterns)
        ]
        
        for filepath in sorted(files_to_check):
            self.checked_files += 1
            if not self.check_file(filepath):
                self.inconsistent_files += 1
    
    def print_report(self) -> None:
        """Print a summary report of the check."""
        print("\n" + "="*70)
        print("DEALER CONSISTENCY CHECK REPORT")
        print("="*70)
        
        print(f"\nFiles checked: {self.checked_files}")
        print(f"Inconsistent files: {self.inconsistent_files}")
        
        if self.errors:
            print(f"\n{'ERRORS':-^70}")
            for error in self.errors:
                print(f"\n{error}")
        
        if self.warnings:
            print(f"\n{'WARNINGS':-^70}")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✓ All files are consistent!")
        elif not self.errors:
            print("\n✓ No inconsistencies found!")
        
        print("\n" + "="*70)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python verify_dealer_consistency.py <directory_or_file>")
        print("Example: python verify_dealer_consistency.py PBS/")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if not path.exists():
        print(f"Error: {path} does not exist")
        sys.exit(1)
    
    checker = DealerConsistencyChecker()
    
    if path.is_file():
        checker.checked_files += 1
        if not checker.check_file(path):
            checker.inconsistent_files += 1
    elif path.is_dir():
        checker.check_directory(path)
    else:
        print(f"Error: {path} is neither a file nor a directory")
        sys.exit(1)
    
    checker.print_report()
    
    # Exit with error code if inconsistencies found
    sys.exit(1 if checker.inconsistent_files > 0 else 0)


if __name__ == "__main__":
    main()