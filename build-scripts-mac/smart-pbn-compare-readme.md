# Smart PBN Compare Tool

A specialized comparison tool for PBN (Portable Bridge Notation) files in the Practice-Bidding-Scenarios build pipeline.

## Purpose

This tool helps validate the Mac build pipeline port by providing:
- **Raw diff**: Standard text comparison for exact differences
- **Semantic diff**: Structure-aware comparison that ignores formatting, comments, and whitespace while comparing actual bridge game content
- **Git integration**: Compare local changes against committed versions
- **Cross-stage comparison**: Compare the same scenario across different pipeline stages (pbn → bba → filtered)

## Why Not Just Use `diff`?

Standard `diff` tools don't understand PBN structure:

1. **Field ordering**: PBN tags can appear in any order within a record. `[Deal "..."]` followed by `[Dealer "S"]` is semantically identical to the reverse order.

2. **Comments**: Lines starting with `%` are comments. BridgeComposer adds extensive formatting metadata as comments that don't affect game semantics.

3. **Whitespace**: Blank lines between records, trailing spaces, and inconsistent formatting create noise in raw diffs.

4. **Pipeline-stage differences**: The BBA tool adds tags like `[Auction]`, `[Contract]`, `[Declarer]`, `[Note]`. Comparing pbn/ to bba/ versions shows these as additions, not semantic differences in the original deals.

5. **Record matching**: With 500 deals per file, matching records by board number vs by deal distribution matters when board numbers get renumbered.

## Requirements

### Core Features

| Feature | Description |
|---------|-------------|
| Raw diff | Line-by-line text comparison with colored output |
| Semantic diff | Compare PBN structure, matching records by Deal tag |
| Git comparison | Compare working copy vs committed version |
| Cross-stage | Compare same scenario across pipeline folders |
| Output formats | Console (ANSI colors) + HTML report |

### Semantic Comparison Rules

**Matching**: Records are matched by their `[Deal]` tag value (the card distribution), which uniquely identifies each hand.

**Compared tags**: All tags are significant except:
- `Site`, `Event`, `Date` (metadata, often empty)
- `North`, `South`, `East`, `West` (player names, not game content)
- Comments (lines starting with `%`)

**Difference types**:
- **ADDED**: Record exists in file2 but not file1
- **REMOVED**: Record exists in file1 but not file2
- **MODIFIED**: Same deal exists in both, but tag values differ

### Tag Filtering

Users can customize comparison with:
- `--tags Deal,Auction,Contract`: Only compare these specific tags
- `--ignore-tags Date,Event`: Ignore these tags in comparison

## Usage Examples

```bash
# Compare two files semantically (default mode)
python pbn-diff.py bba/1N.pbn bba-backup/1N.pbn

# Raw text diff
python pbn-diff.py bba/1N.pbn bba-backup/1N.pbn --raw

# Compare local changes against git HEAD
python pbn-diff.py bba/1N.pbn --git

# Compare against specific commit
python pbn-diff.py bba/1N.pbn --git --commit HEAD~5

# Cross-stage comparison (pbn before BBA vs bba after BBA)
python pbn-diff.py 1N --cross-stage pbn bba

# Generate HTML report
python pbn-diff.py bba/1N.pbn bba-old/1N.pbn --output html --output-file diff.html

# Summary only (no detailed differences)
python pbn-diff.py bba/1N.pbn bba-old/1N.pbn --summary

# Focus on specific boards
python pbn-diff.py bba/1N.pbn bba-old/1N.pbn --board 42 --board 156

# Compare only certain tags
python pbn-diff.py bba/1N.pbn bba-old/1N.pbn --tags Deal,Contract,Auction
```

## Output Examples

### Console Output (Semantic Diff)
```
PBN Comparison Summary
  File 1: bba/1N.pbn
  File 2: bba-old/1N.pbn
  Mode: semantic

  Records in file 1: 500
  Records in file 2: 500
  Matched records:   500
  Modified records:  12
  Added records:     0
  Removed records:   0

[~] Board 42 (MODIFIED)
    Deal: N:7632.K952.A42.73 KJ5.J8.Q765.Q542...
    ~ [Contract]:
        - 3N
        + 4H
    ~ [Auction]:
        - 1C-1D-2N-3N-P-P-P
        + 1C-1D-2N-4H-P-P-P

[~] Board 156 (MODIFIED)
    Deal: N:AQT5.KJ3.Q84.K92 J87.A976.JT5.Q43...
    ~ [Note "1:..."]:
        - Transfer
        + Jacoby Transfer
```

### Cross-Stage Output
```
PBN Comparison Summary
  File 1: pbn/1N.pbn (pre-BBA)
  File 2: bba/1N.pbn (post-BBA)
  Mode: semantic

  Records in file 1: 500
  Records in file 2: 500
  Matched records:   500
  Modified records:  500   <-- All modified (expected)
  Added records:     0
  Removed records:   0

Expected differences (BBA-added tags):
  + [Auction] added to all 500 records
  + [Contract] added to all 500 records
  + [Declarer] added to all 500 records
  ~ [Declarer] changed from "?" to actual value
  ~ [Contract] changed from "?" to actual value
```

## Use Cases for Pipeline Validation

### 1. Validate Mac vs Windows Build

Compare Mac-built output against known-good Windows output:
```bash
python pbn-diff.py bba/1N.pbn bba-windows/1N.pbn --semantic
```

### 2. Check BBA Version Changes

If BBA.exe is updated, compare outputs:
```bash
python pbn-diff.py bba-old/Smolen.pbn bba-new/Smolen.pbn --summary
```

### 3. Investigate Convention Card Impact

Different convention cards produce different auctions:
```bash
python pbn-diff.py bba/1N.pbn --git --commit <before-cc-change>
```

### 4. Batch Validation

Compare all scenarios (script integration):
```bash
for scenario in pbn/*.pbn; do
    name=$(basename "$scenario" .pbn)
    python pbn-diff.py "$name" --cross-stage pbn bba --summary
done
```

## PBN File Format Reference

### Record Structure
```
[Event "Hand simulated by dealer, seed 5"]
[Board "1"]
[Dealer "S"]
[Vulnerable "None"]
[Deal "N:7632.K952.A42.73 KJ5.J8.Q765.Q542 AT.AT76.J8.AKJ96 Q984.Q43.KT93.T8"]
[Declarer "N"]
[Contract "3N"]
[Auction "S"]
1C Pass 1D Pass
2N Pass 3N Pass
Pass Pass
[Note "1:Stayman"]
```

### Deal Tag Format
```
[Deal "N:7632.K952.A42.73 KJ5.J8.Q765.Q542 AT.AT76.J8.AKJ96 Q984.Q43.KT93.T8"]
       ^  ^
       |  +-- Four hands: Spades.Hearts.Diamonds.Clubs
       +-- Starting position (usually N)
```

### Pipeline Stages

| Stage | Folder | Description |
|-------|--------|-------------|
| pbn | `pbn/` | Initial deals from dealer tool, placeholders for contract |
| bba | `bba/` | After BBA analysis, includes Auction/Contract/Declarer |
| filtered | `bba-filtered/` | Subset matching auction filter pattern |
| filtered-out | `bba-filtered-out/` | Inverse (non-matching deals) |
| bidding-sheets | `bidding-sheets/` | Formatted for N/S bidding practice |
| rotated | `pbn-rotated-for-4-players/` | Rotated for 4-player practice |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No differences found |
| 1 | Differences found |
| 2 | Error (file not found, parse error, etc.) |

## Dependencies

- Python 3.8+
- No external dependencies (uses standard library only)
