Subject: New "Found" scenario pattern — curated-hand teaching, with a BBO caveat

Hi Rick,

I wanted to walk you through a new pattern I've been building in Practice-Bidding-Scenarios that you may want to consider for bbo-pbs as well.

## The "Found" approach

Standard scenarios start from dealer constraints and generate fresh hands every run. The "Found" pattern goes the other direction: a Python filter scans existing `bba/*.pbn` files for hands that match a play-technique criterion, and writes the matches to a single `bba/Found_<Topic>.pbn`. The filter scripts live under `build-scripts-mac/play_filters/`. Two examples:

- **Found_Rabbis_Rule** — filters `bba/Rabbis_Rule.pbn` for hands where the contract is 4S, declarer is South, and the result was 10+ tricks. Every match is a deal where dropping West's singleton K of diamonds (Rabbi's Rule) actually mattered.
- **Found_Endplay** — scans every `bba/*.pbn` for 4-of-major contracts where declarer's side has an AJ tenace in one side suit plus solid honors in another so a strip-and-endplay is feasible.

To make these first-class in the pipeline I added a new BTN flag `# bba-direct: true`. When the pipeline sees it, it skips the dealer-side steps (pbn / rotate / bba) and starts at filter, using the pre-curated bba file as the source. The dlr / pbs / filter / biddingSheet / quiz / package steps all still run, so the @chat content reaches BBO and the bidding sheets and quiz PDFs land in `Bidding Scenarios/`.

## Pros

- **Concentrates the teaching moment.** Standard scenarios sometimes deal hands where the named play technique never actually applies; Found scenarios are 100% relevant deals.
- **Zero re-running cost.** No dealer constraints to tune; no produce-rate problems; runs in 1-2 seconds.
- **Cross-scenario harvesting.** Found_Endplay pulls candidates from every bba file in the repo, so a single scenario can surface deals from dozens of source scenarios.
- **Stable.** Once filtered and committed, the deals don't change with random seeds or BBA version bumps.

## Cons

- **No new hands.** Players who exhaust the deck have to wait for someone to re-run the filter on a larger source. With 156 Rabbi's Rule deals or 500 endplay candidates, that's not immediate, but it's finite.
- **Quality follows the source.** A weak source bba (e.g., low filter rate, BBA bidding mismatches) produces a weak Found set. You're filtering, not generating.
- **No dealer code = no BBO.** This is the one that bit me. See below.

## The BBO issue

BBO Practice tables (Start a Bidding/Teaching Table) require dealer code to generate hands at the table. Found scenarios deliberately have no dealer code — they're a curated set of pre-played deals — so when the BBO extension fetches the PBS file for a Found scenario, the `setDealerCode()` call gets empty content and the button renders in **red** with `data-missing="true"`.

The deals **do** work on bridge-classroom.com because that site reads the PBN files directly from `Bidding Scenarios/<section>/<scenario>/` — no dealer code needed.

## My workaround

I removed the Found scenarios from `btn/-button-layout-release.txt` and `btn/-button-layout-beta.txt` so the BBO extension stops listing them. The Found scenarios still:

- Exist as proper BTN files with `bba-direct: true`
- Run through the pipeline (dlr / pbs / filter / biddingSheet / quiz / package)
- Live in `Bidding Scenarios/20 Suit Contract Play/Found_Rabbis_Rule/` and `Found_Endplay/`
- Show up correctly on Bridge Classroom

So they're invisible on BBO, fully usable on Bridge Classroom. One side effect: re-running the `package` step on these scenarios prints "Not found in button layout — skipping" because the package operation routes by layout section. The existing files stay in place, but they won't be refreshed by `package`. If that becomes annoying I can add a `# package-section: 20 Suit Contract Play` directive support.

## Files to look at

- `build-scripts-mac/play_filters/find_rabbis_rule_makers.py` and `find_endplay_candidates.py` — the filter scripts
- `btn/Found_Rabbis_Rule.btn` and `btn/Found_Endplay.btn` — the BTN headers (note `bba-direct: true`)
- `build-scripts-mac/pbs-pipeline-mac.py` (lines around `BBA_DIRECT_SKIP` and `filter_operations_for_scenario`) — the pipeline branch
- `build-scripts-mac/utils/properties.py` (`get_bba_direct`) — the BTN reader

Happy to talk through it if you want to adopt the pattern in bbo-pbs, or if you see a cleaner way to handle the BBO side.

David
