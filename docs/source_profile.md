# Source profile: Formula 1 World Championship

## Provenance and snapshot

- Kaggle page: https://www.kaggle.com/datasets/atharvranjan/formula-1-world-championship-1950-present
- Local source description: `dataset/README.md`; column definitions: `dataset/SCHEMA.md`.
- The local README identifies the dataset as Formula 1 World Championship 1950-2026, maintained by Atharv Ranjan, with completed 2025 and 2026 races through the Hungarian Grand Prix (2026-07-26). It describes the derivative data as CC0/Public Domain and lists Jolpica-F1/FastF1 additions.
- The counts below are the local workspace baseline profiled on 2026-10-18. Recount before the final demo if source files change.

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

## Missing-value profile

The source uses literal `\N` for missing values; it is not a string to preserve as a valid category. The local profile counted 124,176 such cells in `results.csv`, 11,449 in `races.csv`, 12,290 in `qualifying.csv`, 1,601 in `drivers.csv`, 145 in `sprint_results.csv`, 13,009 in `constructor_results.csv`, and 5 in `tire_stints.csv`. These are cell counts, not missing-row counts. The files also have a small number of empty fields distinct from `\N`.

Examples of expected NULLs include unclassified finishing positions and unavailable lap/time fields in results, session schedule fields in older race records, Q2/Q3 times for drivers who did not advance, and driver code/number values not available for all historical drivers. The source README specifically says `fastestLapSpeed` is unavailable for all 2025/2026 results. Do not fill these values with zero or drop otherwise valid results.

## Core keys and relationships

- `circuits.circuitId`, `constructors.constructorId`, `drivers.driverId`, `status.statusId`, `seasons.year`, `races.raceId`, and `results.resultId` are the natural keys documented by the source schema.
- `races.circuitId` references `circuits.circuitId`; `races.year` corresponds to `seasons.year`.
- `results.raceId`, `driverId`, `constructorId`, and `statusId` reference their respective core source tables.
- Confirm uniqueness, non-null keys, and referential coverage against the current local files as part of Phase 1 profiling before adding physical constraints.
