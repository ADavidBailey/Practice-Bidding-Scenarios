# pbn-diff

A semantic comparison tool for PBN (Portable Bridge Notation) files.

## Overview

`pbn-diff` compares PBN files with awareness of their structure, making it easy to identify meaningful differences while ignoring formatting variations. It's designed to help validate the Mac build pipeline port by comparing artifacts between builds.

## Installation

The tool is part of the Practice-Bidding-Scenarios project. Add an alias to your shell:

```bash
# Add to ~/.zshrc
alias pbn-diff='python3 /path/to/build-scripts-mac/pbn-diff.py'
```

## Quick Start

```bash
# Compare two files semantically
pbn-diff file1.pbn file2.pbn

# Compare local file against git HEAD
pbn-diff bba/1N.pbn --git

# Compare across pipeline stages
pbn-diff 1N --cross-stage pbn bba

# Generate HTML report
pbn-diff file1.pbn file2.pbn --output html -o report.html
```

## Comparison Modes

### Semantic Diff (Default)

Compares PBN structure by matching records based on their `Deal` tag (card distribution). This identifies actual content differences while ignoring:
- Tag ordering within records
- Whitespace and formatting
- Comment lines (starting with `%`)

```bash
pbn-diff bba/1N.pbn bba-backup/1N.pbn
```

### Raw Diff

Line-by-line text comparison using unified diff format:

```bash
pbn-diff file1.pbn file2.pbn --raw
pbn-diff file1.pbn file2.pbn --raw --ignore-comments
```

### Git Comparison

Compare the working copy against a committed version:

```bash
pbn-diff bba/1N.pbn --git              # vs HEAD
pbn-diff bba/1N.pbn --git --commit HEAD~5
pbn-diff bba/1N.pbn --git --commit abc123
```

### Cross-Stage Comparison

Compare the same scenario across different pipeline stages:

```bash
pbn-diff 1N --cross-stage pbn bba
pbn-diff Smolen --cross-stage bba filtered
```

Available stages:
- `pbn` - Initial deals from dealer
- `bba` - After BBA analysis (adds Auction, Contract, Declarer)
- `filtered` / `bba-filtered` - Matching deals after filtering
- `filtered-out` / `bba-filtered-out` - Non-matching deals
- `bidding-sheets` - Formatted for bidding practice
- `rotated` / `pbn-rotated` - Rotated for 4-player practice

List all stages:
```bash
pbn-diff --list-stages
```

## Output Options

### Console (Default)

Colored terminal output with ANSI codes:
- Green: Added tags/records
- Red: Removed tags/records
- Yellow: Modified tags/records

```bash
pbn-diff file1.pbn file2.pbn
pbn-diff file1.pbn file2.pbn --no-color  # Disable colors
```

### HTML Report

Generate a standalone HTML file:

```bash
pbn-diff file1.pbn file2.pbn --output html -o diff.html
```

### Summary Only

Show statistics without detailed differences:

```bash
pbn-diff file1.pbn file2.pbn --summary
```

## Filtering Options

### Filter by Board

Show differences for specific boards only:

```bash
pbn-diff file1.pbn file2.pbn --board 42
pbn-diff file1.pbn file2.pbn --board 1 --board 2 --board 3
```

### Filter by Tag

Compare only specific tags:

```bash
pbn-diff file1.pbn file2.pbn --tags Deal,Contract,Auction
```

Ignore specific tags:

```bash
pbn-diff file1.pbn file2.pbn --ignore-tags Date,Event,Site
```

Default ignored tags: `Site`, `Event`, `Date`, `North`, `South`, `East`, `West`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No differences found |
| 1 | Differences found |
| 2 | Error (file not found, invalid arguments, etc.) |

Use in scripts:

```bash
if pbn-diff file1.pbn file2.pbn --quiet; then
    echo "Files match"
else
    echo "Files differ"
fi
```

## Examples

### Validate a rebuild

```bash
# Check if regenerated file matches original
pbn-diff bba/Smolen.pbn bba-backup/Smolen.pbn --summary
```

### Investigate BBA version changes

```bash
# Compare before/after BBA update
pbn-diff bba/1N.pbn --git --commit v1.0
```

### Check what BBA adds

```bash
# See tags added by BBA processing
pbn-diff 1N --cross-stage pbn bba --board 1
```

Output:
```
[~] Board 1 (MODIFIED)
    Deal: N:7632.K952.A42.73...
    + [Auction]: S
    + [BidSystemEW]: 2/1GF - 2/1 Game Force
    + [BidSystemNS]: 2/1GF - 2/1 Game Force
    ~ [Contract]:
        - ?
        + 4H
    ~ [Declarer]:
        - ?
        + N
```

### Batch comparison

```bash
# Compare all scenarios
for f in pbn/*.pbn; do
    name=$(basename "$f" .pbn)
    echo "=== $name ==="
    pbn-diff "$name" --cross-stage pbn bba --summary
done
```

## How Matching Works

Records are matched by their `Deal` tag value, which contains the card distribution for all four hands. This ensures that even if board numbers change, the same hands are compared.

Example Deal tag:
```
[Deal "N:7632.K952.A42.73 KJ5.J8.Q765.Q542 AT.AT76.J8.AKJ96 Q984.Q43.KT93.T8"]
```

Format: `{starting_position}:{hand1} {hand2} {hand3} {hand4}`
- Each hand: `Spades.Hearts.Diamonds.Clubs`

## Command Reference

```
pbn-diff [options] file1 [file2]

Positional arguments:
  file1                 First PBN file or scenario name
  file2                 Second PBN file (not needed with --git/--cross-stage)

Comparison modes:
  --raw                 Raw text diff (line-by-line)
  --semantic            Semantic diff (default)
  --git                 Compare against git version
  --cross-stage S1 S2   Compare across pipeline stages

Git options:
  --commit REF          Git reference (default: HEAD)

Output options:
  --output FORMAT       console or html (default: console)
  -o, --output-file F   Write to file
  --no-color            Disable ANSI colors
  --summary             Summary statistics only

Filtering:
  --tags TAGS           Compare only these tags (comma-separated)
  --ignore-tags TAGS    Ignore these tags (comma-separated)
  --ignore-comments     Ignore % comments in raw diff
  --board N             Show only board N (repeatable)

Other:
  --list-stages         List available pipeline stages
  -v, --verbose         Verbose error output
  -q, --quiet           Exit code only, no output
  -h, --help            Show help
```
