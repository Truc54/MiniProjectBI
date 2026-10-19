# Source profile: Formula 1 World Championship

## Provenance and snapshot

- **Kaggle page:** https://www.kaggle.com/datasets/atharvranjan/formula-1-world-championship-1950-present
- **GitHub (maintainer):** https://github.com/Arths17/f1-dataset — open issues or PRs here to contribute.
- **Maintainer:** Atharv Ranjan
- **License:** CC0: Public Domain. The derivative work (2025/2026 extension) carries no additional restrictions.
- **Dataset description:** Formula 1 World Championship historical data from 1950 through the 2026 Hungarian Grand Prix (2026-07-26). Covers race results, driver and constructor standings, qualifying, lap times, pit stops, circuits, and — for 2025/2026 only — tire stints, weather, and practice results. Intended for historical performance analysis across drivers, constructors, seasons, and circuits.
- **Data sources used by maintainer:**
  - Base dataset: downloaded via `kagglehub` from the original Kaggle dataset.
  - 2025/2026 race results: fetched from Jolpica-F1 API (`https://api.jolpi.ca/ergast/f1/`), with caching, rate limiting, and retry/backoff.
  - Tire stint data: sourced from the FastF1 library (official F1 live timing). 2025/2026 only.
  - Weather data: sourced from FastF1 (official F1 live timing). 2025/2026 only.
  - Practice results: sourced from FastF1. 2025/2026 only.
- **Local profile date:** 2026-10-18. Row counts below are this snapshot's baseline. Recount before the final demo if source files change.
- **Data scope:** Season 1950 to 2026, covering 77 seasons, 1,164 race events, and 754,398 rows across all 17 CSV files. The 2025/2026 extension adds 35 completed races (full 2025 season of 24 races + 11 rounds of 2026 through the Hungarian GP).

## File inventory

| CSV | Rows | Columns | Phase 1 decision |
|---|---:|---:|---|
| circuits.csv | 78 | 9 | Core |
| constructor_results.csv | 13,030 | 5 | Profile; optional |
| constructor_standings.csv | 13,796 | 7 | Profile; optional |
| constructors.csv | 214 | 5 | Core |
| driver_standings.csv | 35,695 | 7 | Profile; optional |
| drivers.csv | 879 | 9 | Core |
| lap_times.csv | 632,937 | 6 | Profile; optional and largest table; no 2025/2026 rows |
| pit_stops.csv | 12,783 | 7 | Profile; optional |
| practice_results.csv | 1,901 | 6 | Profile; optional, 2025/2026 extension only |
| qualifying.csv | 11,298 | 9 | Profile; optional |
| races.csv | 1,164 | 18 | Core |
| results.csv | 27,568 | 18 | Core; central event table |
| seasons.csv | 77 | 2 | Core |
| sprint_results.csv | 590 | 16 | Profile; optional |
| status.csv | 141 | 2 | Core |
| tire_stints.csv | 2,208 | 7 | Profile; optional, 2025/2026 extension only |
| weather.csv | 39 | 11 | Profile; optional, 2025/2026 extension only |

The seven core tables contain 30,121 rows in this snapshot. All 17 CSVs contain 754,398 rows. The core subset is enough to analyze one race result per driver across seasons, race events, circuits, drivers, constructors, and finishing statuses. The optional tables have other grains and should be added only when a specific analysis question needs them. In particular, lap_times has 632,937 rows and changes the scope/performance profile materially.

## Core table selection rationale

The seven core tables were selected because they jointly represent the primary business process — one driver's classified or unclassified result in a Grand Prix — at the grain required by the dimensional model.

| Table | Role | Why included |
|---|---|---|
| `results.csv` | Central fact | One row per driver per race; contains grid, finish position, points, laps, time and status |
| `races.csv` | Race dimension | Event date, round, circuit reference, session schedule; needed for season/round slicing |
| `drivers.csv` | Driver dimension | Name, nationality, DOB; required for all driver-level filtering |
| `constructors.csv` | Constructor dimension | Team name and nationality; required for all team-level filtering |
| `circuits.csv` | Circuit dimension | Location and country; required for circuit/country filters |
| `status.csv` | Status lookup | Maps statusId to human-readable finishing status (Finished, Retired, DSQ, DNS, etc.) |
| `seasons.csv` | Season dimension | One row per year; anchor for season-level filtering and era grouping |

The ten optional tables are excluded from Phase 1 scope for the following reasons:

| Table | Reason not in Phase 1 core |
|---|---|
| `qualifying.csv` | Different grain (qualifying session); Q2/Q3 have expected NULLs; no Phase 1 business question requires qualifying times |
| `sprint_results.csv` | Different grain (sprint race); only a subset of race weekends; would need separate fact treatment |
| `driver_standings.csv` | Cumulative aggregates redundant with fact; can be derived in DAX if needed |
| `constructor_standings.csv` | Same as above for constructors |
| `constructor_results.csv` | Aggregated constructor points already derivable from `results.csv` |
| `lap_times.csv` | Grain is per lap (632,937 rows); no 2025/2026 data; materially changes pipeline scope and performance |
| `pit_stops.csv` | Optional grain (per pit stop); no Phase 1 business question targets pit strategy |
| `practice_results.csv` | 2025/2026 extension only; incomplete historical coverage; no Phase 1 question requires FP data |
| `tire_stints.csv` | 2025/2026 extension only; same coverage limitation |
| `weather.csv` | 2025/2026 extension only; only 39 rows; no Phase 1 business question targets weather |

Add any optional table to Stage only when a confirmed business question cannot be answered without it, and document the decision in this file.

## Missing-value profile

The source uses literal `\N` for missing values. It must be loaded as SQL NULL; it is not a valid category string to preserve. Empty strings (`""`) are distinct from `\N` and also present in a small number of cells. Do not convert NULLs to 0, empty string, or use them to drop otherwise valid rows.

**`\N` cell counts by file (profiled 2026-10-19, using `csv` module, Python 3):**

| File | `\N` cells | Empty string cells |
|---|---:|---:|
| circuits.csv | 0 | 0 |
| drivers.csv | 1,601 | 28 |
| constructors.csv | 0 | 0 |
| status.csv | 0 | 0 |
| seasons.csv | 0 | 0 |
| races.csv | 11,449 | 0 |
| results.csv | 124,176 | 0 |
| qualifying.csv | 12,290 | 68 |
| sprint_results.csv | 145 | 0 |
| lap_times.csv | 0 | 0 |
| driver_standings.csv | 0 | 0 |
| constructor_standings.csv | 0 | 0 |
| constructor_results.csv | 13,009 | 0 |
| pit_stops.csv | 1 | 0 |
| practice_results.csv | 0 | 0 |
| tire_stints.csv | 5 | 0 |
| weather.csv | 0 | 0 |

**Per-column `\N` breakdown for the seven core tables:**

`drivers.csv`: `number` 816 (permanent number not assigned for historical drivers), `code` 771 (three-letter code not assigned), `dob` 14 (date of birth unavailable).

`races.csv`: all session schedule columns (`fp1_date/time`, `fp2_date/time`, `fp3_date/time`, `quali_date/time`, `sprint_date/time`) are `\N` for older races that predate the structured session schedule; `sprint_date/time` is also `\N` for weekends without a sprint (~1,135–1,138 rows); race `time` (UTC start) is `\N` for 731 early races.

`results.csv`: `fastestLapSpeed` is `\N` for 19,316 rows — this includes all 2025/2026 results (source limitation documented in README) plus earlier races before this data was tracked. `time` and `milliseconds` are `\N` for 19,212 / 19,200 rows (unclassified results and leader-only time). `fastestLap`, `fastestLapTime`, and `rank` are `\N` for 18,542 / 18,284 rows (not tracked in early seasons). `position` is `\N` for 11,074 rows — these are unclassified results (DNF, DSQ, DNS, etc.) and this is the primary expected-NULL column. `number` has 6 `\N` cells (anomalies to investigate).

`circuits.csv`, `constructors.csv`, `status.csv`, `seasons.csv`: no `\N` values.

Examples of expected NULLs include unclassified finishing positions and unavailable lap/time fields in results, session schedule fields in older race records, Q2/Q3 times for drivers who did not advance, and driver code/number values not available for all historical drivers. The source README specifically says `fastestLapSpeed` is unavailable for all 2025/2026 results. Do not fill these values with zero or drop otherwise valid results.

## Core keys and relationships

- `circuits.circuitId`, `constructors.constructorId`, `drivers.driverId`, `status.statusId`, `seasons.year`, `races.raceId`, and `results.resultId` are the natural keys documented by the source schema.
- `races.circuitId` references `circuits.circuitId`; `races.year` corresponds to `seasons.year`.
- `results.raceId`, `driverId`, `constructorId`, and `statusId` reference their respective core source tables.
- Confirm uniqueness, non-null keys, and referential coverage against the current local files as part of Phase 1 profiling before adding physical constraints.
