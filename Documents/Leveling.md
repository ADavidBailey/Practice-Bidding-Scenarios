# Dealer3 Leveling System Analysis

## Problem Statement

When generating bridge deals filtered for specific properties (opening bids, conventions, HCP ranges, etc.), dealer3 naturally produces deals according to their combinatorial probability. This creates a distribution problem for training purposes:

- **Example**: Generating balanced hands with 12-24 HCP produces many more 12-14 HCP hands than 22-24 HCP hands
- **Desired**: Equal frequency across ranges for balanced student training
- **Solution**: "Leveling" - adding frequency reduction constraints to over-represented categories

## Current Leveling Mechanism

### Core Concept

Leveling uses **card placement constraints** to reduce acceptance rates for common deal types. By requiring specific cards to be in specific hands (conditions that may or may not be met), we filter out a predictable fraction of generated deals.

### The Leveling Include File

```btn
### Imported Leveling Code ###
c1 = hascard(west,2C)
c2 = hascard(east,2D)
c3 = hascard(west,3C)
c4 = hascard(east,3D)

keep06 = c1 and c2          // ~6% acceptance
keep44 = c3 or c4           // ~44% acceptance (used as building block)

keep015 = keep06 and c3
keep03 = keep06 and keep44
keep045 = keep06 and not c3
####06 = c1 and c2
keep11 = c1 and keep44
keep14 = c1 and not keep44
keep19 = c1 and not c2
keep25 = c1
keep30 = keep06 or c3
keep33 = c1 or (c2 and keep44)
####44 = c3 or c4
keep47 = keep44 or keep06

keep53 = not keep47
keep56 = not keep44
keep67 = not keep33
keep70 = not keep30
keep75 = not keep25
keep81 = not keep19
keep86 = not keep14
keep89 = not keep11
keep94 = not keep06
keep955 = not keep045
keep97 = not keep03
keep985 = not keep015
keep   = 1
keep0  = 0
### End of Imported Leveling Code ###
```

### Usage Example (NT Ladder)

```btn
# Level the ranges (12-14 is most common, 22-24 is rarest)
level12_14 = hcp12_14 and keep03    # Most restrictive for most common
level15_17 = hcp15_17 and keep045
level18_19 = hcp18_19 and keep19
level20_21 = hcp20_21 and keep56
level22_24 = hcp22_24 and keep      # No restriction for rarest
levelTheDeal = level12_14 or level15_17 or level18_19 or level20_21 or level22_24
```

## Mathematical Framework

### Idealized Model

For range $i$ with natural frequency $f_i$ and keep filter with pass-through rate $p_i$:

$$\text{Output frequency}_i = \frac{f_i \times p_i}{\sum_j f_j \times p_j}$$

To equalize all output frequencies, we need:

$$f_i \times p_i = k \quad \text{(constant for all } i \text{)}$$

Therefore:

$$p_i = \frac{k}{f_i}$$

Where $k$ is determined by the rarest category (which gets $p = 1$, i.e., `keep`).

### Complication: Context Dependence

The pass-through rate of a keep filter is **not independent** of the scenario constraints. 

**Example**: `keep03` requires `hascard(west,2C) and hascard(east,2D) and (hascard(west,3C) or hascard(east,3D))`

If the scenario already constrains South to have 8 clubs:
- West having the 2C becomes less likely (fewer clubs available)
- The effective pass-through rate of `keep03` changes

This means: **the same keep level has different effective rates in different scenarios**.

### Implication

There is no purely theoretical/closed-form solution. Leveling must be calibrated empirically for each scenario, OR we need to measure the interaction effects systematically.

## Proposed Calibration System

### Phase 1: Baseline Keep Level Measurements

Measure the pass-through rate of each keep level in isolation (no other constraints).

**Test Script Template:**
```btn
produce 10000

#include "script/Leveling"

condition keepXX

action printoneline
```

Run for each keep level and record:
- Deals generated (attempted)
- Deals produced (passed filter)
- Acceptance rate = produced / generated

**Expected Output Table:**

| Keep Level | Boolean Expression | Theoretical Rate | Measured Rate |
|------------|-------------------|------------------|---------------|
| keep0 | 0 | 0.000 | — |
| keep015 | c1 ∧ c2 ∧ c3 | 0.125? | TBD |
| keep03 | c1 ∧ c2 ∧ (c3 ∨ c4) | 0.188? | TBD |
| keep045 | c1 ∧ c2 ∧ ¬c3 | 0.125? | TBD |
| keep06 | c1 ∧ c2 | 0.250? | TBD |
| keep11 | c1 ∧ (c3 ∨ c4) | 0.375? | TBD |
| keep14 | c1 ∧ ¬(c3 ∨ c4) | 0.125? | TBD |
| keep19 | c1 ∧ ¬c2 | 0.250? | TBD |
| keep25 | c1 | 0.500? | TBD |
| keep30 | (c1 ∧ c2) ∨ c3 | 0.625? | TBD |
| keep33 | c1 ∨ (c2 ∧ (c3 ∨ c4)) | 0.688? | TBD |
| keep44 | c3 ∨ c4 | 0.750? | TBD |
| keep47 | (c3 ∨ c4) ∨ (c1 ∧ c2) | 0.813? | TBD |
| keep53 | ¬keep47 | 0.187? | TBD |
| keep56 | ¬keep44 | 0.250? | TBD |
| keep67 | ¬keep33 | 0.312? | TBD |
| keep70 | ¬keep30 | 0.375? | TBD |
| keep75 | ¬keep25 | 0.500? | TBD |
| keep81 | ¬keep19 | 0.750? | TBD |
| keep86 | ¬keep14 | 0.875? | TBD |
| keep89 | ¬keep11 | 0.625? | TBD |
| keep94 | ¬keep06 | 0.750? | TBD |
| keep955 | ¬keep045 | 0.875? | TBD |
| keep97 | ¬keep03 | 0.812? | TBD |
| keep985 | ¬keep015 | 0.875? | TBD |
| keep | 1 | 1.000 | 1.000 |

Note: Theoretical rates assume independent 0.5 probability for each card placement, which may not hold exactly due to dealing mechanics.

### Phase 2: Scenario-Specific Calibration

For a specific scenario (e.g., NT Ladder), measure:

1. **Natural frequencies** - Run without leveling to get baseline distribution
2. **Keep rates per category** - For each HCP range, measure acceptance rate of candidate keep levels

**Natural Frequency Test:**
```btn
produce 10000
dealer south

balanced = shape(south, any 4333 + any 4432 + any 5332)

hcp12_14 = hcp(south) >= 12 and hcp(south) <= 14
hcp15_17 = hcp(south) >= 15 and hcp(south) <= 17
hcp18_19 = hcp(south) >= 18 and hcp(south) <= 19
hcp20_21 = hcp(south) >= 20 and hcp(south) <= 21
hcp22_24 = hcp(south) >= 22 and hcp(south) <= 24

condition balanced and hcp(south) >= 12 and hcp(south) <= 24

action
average "1. 12-14 HCP" 100 * hcp12_14,
average "2. 15-17 HCP" 100 * hcp15_17,
average "3. 18-19 HCP" 100 * hcp18_19,
average "4. 20-21 HCP" 100 * hcp20_21,
average "5. 22-24 HCP" 100 * hcp22_24,
```

**Per-Category Keep Rate Test:**
```btn
produce 5000
dealer south

balanced = shape(south, any 4333 + any 4432 + any 5332)
hcp12_14 = hcp(south) >= 12 and hcp(south) <= 14

#include "script/Leveling"

condition balanced and hcp12_14 and keep03

action printoneline
```

Record generated/produced ratio for each (category, keep level) pair.

### Phase 3: Solver/Calculator

Given:
- Natural frequencies: $[f_1, f_2, ..., f_n]$
- Available keep levels: $[p_1, p_2, ..., p_m]$ (measured rates)
- Target: equal output frequencies

**Algorithm:**
1. Identify the rarest category $r$ with frequency $f_r$
2. Assign `keep` (rate 1.0) to category $r$
3. For each other category $i$, find keep level $j$ such that:
   $$p_j \approx \frac{f_r}{f_i}$$
4. Report the assignment and predicted output distribution

**Refinement Option:** If available keep levels don't provide fine enough granularity, suggest:
- Combining scenarios with different keep assignments
- Creating new keep levels with intermediate rates

## Future Enhancements

### Automated Calibration Tool

Build a script that:
1. Takes a base .btn file (without leveling)
2. Automatically runs calibration experiments
3. Outputs the optimal leveling block
4. Validates by running the leveled version and reporting actual distribution

### Additional Keep Levels

The current system uses 4 card placements giving ~25 distinct levels. Could expand to 5 or 6 cards for finer granularity:

```btn
c5 = hascard(west,4C)
c6 = hascard(east,4D)
```

This would provide many more intermediate rates.

### Context-Aware Keep Selection

Build a database of how keep rates vary with common constraints:
- South has long suit (7+, 8+ cards)
- Specific HCP ranges
- Void/singleton requirements

This could enable more accurate first-guess keep assignments before running calibration.

## Open Questions

1. **Why these specific cards?** (2C, 2D, 3C, 3D) - Are these chosen to minimize interaction with typical scenario constraints? Low cards less likely to be constrained by HCP requirements.

2. **Naming convention accuracy** - The keep level names (keep03, keep44, etc.) appear to be approximate percentages. How were these originally measured?

3. **Cross-scenario stability** - How much do effective keep rates vary between very different scenarios? Is it enough to matter?

4. **Computational cost** - How much does heavy leveling (e.g., keep015) slow down generation? Is there a practical lower bound on useful keep rates?

## References

- dealer3 documentation
- BBO practice tables (use legacy mode)
- Bridge scenario definition files (300+ in current library)
