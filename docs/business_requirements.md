# Business context, questions, and KPI contract

## Problem and audience

The BI application supports a Formula 1 performance analyst, team/media analyst, or informed F1 follower who needs to compare official race outcomes across drivers, constructors, seasons, and circuits. The decision supported is where performance changed and which result entries explain that change. The model describes historical association; grid position or circuit is not evidence of cause.

The Phase 1 source scope is the seven core CSVs documented in [source profile](source_profile.md). The analysis grain is one driver result per Grand Prix (`results.resultId`), as defined in the [dimensional model](dimensional_model.md). Lap, pit-stop, sprint, practice, and standings analyses require separate grains and are not implied by this contract.

## Business questions

| ID | Question | Required dimensions/fields | Required population or breakdown |
|---|---|---|---|
| BQ1 | How do race points, wins, podiums, entries, and classified finishes change by season for a selected driver or constructor? | `DimRace` season; `DimDriver`; `DimConstructor`; points, `positionOrder`, `position` | Show result-entry count and scoring-era caveat with points. |
| BQ2 | Which drivers and constructors contribute the most points or wins in a selected season, race, or circuit? | `DimRace`; `DimCircuit`; `DimDriver`; `DimConstructor`; points and win flag | State selected period and count of result entries. |
| BQ3 | How does starting grid relate to classified finish and points? | `grid`, numeric `position`, points; race/season, driver/constructor, circuit | Include only rows with `grid > 0` and valid classified finish; show eligible `n`. This is descriptive, not causal. |
| BQ4 | Which finishing outcomes contribute to non-classified entries by season, constructor, driver, or circuit? | `DimStatus` source label and `OutcomeGroup`; `position`; race and other dimensions | Show both source status and mapped group; do not merge DNS or DSQ into retirement/DNF. |
| BQ5 | Which race events or circuits show an unusual points/performance change versus a prior race or season? | Race order, circuit, driver/constructor; points, wins, podiums, classified finish | Name the comparison baseline and show event-level entries behind the change. Do not call a change anomalous without a stated threshold or comparison rule. |

## KPI definitions

All KPI calculations obey current report filters. Rates and averages are recomputed from row-level numerators and denominators, not averaged from displayed subtotals.

| KPI | Reproducible definition | Denominator/filter and interpretation |
|---|---|---|
| Result entries | Count rows in `FactRaceResult` (equivalent to count of unique source `resultId`) | One row is one driver entry in one Grand Prix. Show alongside totals when useful. |
| Total points | `SUM(points)` | Additive over selected result entries. Raw points across seasons/eras are not directly comparable because scoring systems changed; compare within a season/era or add a clearly documented normalized measure. |
| Wins | `SUM(CASE WHEN positionOrder = 1 THEN 1 ELSE 0 END)` | Source-defined winner ordering. Do not infer from a NULL finish position. |
| Podiums | `SUM(CASE WHEN numeric position BETWEEN 1 AND 3 THEN 1 ELSE 0 END)` | Only valid classified finish positions count. |
| Classified entries | Count rows with a valid numeric finish `position` | Position is a finish classification, not `positionText` alone. Report its share only with the selected entry count. |
| Points per entry | `SUM(points) / COUNT(result rows)` | Denominator includes every result entry in the selected context, including entries with a non-classified finish. Display the entry count. Return blank when denominator is zero. |
| Mean classified finish | `AVG(numeric position)` over classified entries | Exclude NULL/unclassified positions. Lower is better; show classified-entry count. Median may be added as a separate measure. |
| Grid-to-finish places gained | Per eligible row, `grid - position`; summarize as mean/median or distribution | Include only `grid > 0` and valid classified finish. Positive means gained places, zero means held, negative means lost. Show eligible count; do not turn grid `0` or NULL into a real start. |
| Non-classified rate | `COUNT(rows with NULL numeric position) / COUNT(all result rows)` | Denominator is all result entries after active report filters. Show numerator, denominator, and `OutcomeGroup` breakdown. `OutcomeGroup` explains the outcome; it does not replace the source-position rule. |
| Constructor/circuit contribution | Selected KPI for the member divided by the same KPI across the currently selected parent population | Name the parent population (for example, season total points); do not divide by an unfiltered global total when report filters are active. |

If a source numeric field cannot be parsed, keep the source row, record a conversion discrepancy, and exclude the invalid value from that KPI until resolved. Preserve SQL NULL separately from zero and empty string. Status groups and position semantics are defined in the [dimensional model](dimensional_model.md).

## Dashboard question mapping

### Dashboard 1: Overview (descriptive)

- KPI cards: points, wins, podiums, result entries, classified entries, and non-classified rate. Put selected season/period and non-classified numerator/denominator in the visible context.
- Trend: points and wins by season, with a scoring-system/era caveat for cross-era comparisons.
- Contribution: points and wins by constructor and driver within the selected season.
- Distribution: result entries, points, and outcomes by race/circuit/country.
- Filters: season, race/round, driver, constructor, circuit/country, and source status/outcome group.

### Dashboard 2: Detailed / Diagnostic

- Drill from season to round/race and from constructor to driver; use drill-through to a result-row detail view keyed by source `resultId`.
- Show status composition by exact source label and `OutcomeGroup`, with row counts and share denominator.
- Show grid-to-finish distribution only for the eligible population, with eligible `n`, and expose excluded NULL/zero-grid counts.
- Explain points or podium changes with event-level contribution for the selected driver/constructor and circuit; make comparison baseline explicit (prior event, prior season, or user-selected period).
- Provide a reconciliation view for a selected race/driver/constructor with source IDs, source measures, status label, and derived values. This is a Phase 2 dashboard requirement; no dashboard is claimed to exist in Phase 1.

## Quantitative evidence for acceptance and report

For the diagnostic page/report, retain evidence for:

1. source and Stage counts for all seven core tables, plus the selected result count;
2. one sampled race and driver/constructor traced from `results.csv` through `stg.results`, including source IDs, optional NULL fields, and ETL run/batch log;
3. points and result-entry contribution by status group, constructor, and circuit for a stated season/race selection;
4. grid-to-finish sample size, the exact eligibility predicate, and a small set of row-level examples;
5. numerator/denominator for every displayed rate, and the comparison period used for every change explanation.

Phase 1 defines these evidence needs and SQL acceptance checks. Actual pipeline evidence remains pending until the Stage loader is integrated and run; record file paths, run IDs, counts, and any discrepancy in the evidence/runbook location selected by the team.

## Traceability to project requirements

| Requirement | Contract contribution | Delivery phase |
|---|---|---|
| 3.1 Mage ingestion into SQL Server Staging; validation, full/incremental load, status/count/error logging, rerun | Operational ETL requirement; the business/KPI design here does not claim it has been implemented | Phase 1 |
| 3.2 dbt cleaning, standardization, integration, tests, dependencies, documentation | Lineage and natural-key/relationship tests in [dimensional model](dimensional_model.md) | Phase 2 |
| 3.3 SQL Server DW, business process/grain, fact/dimensions/measures and star schema | One-fact star-schema contract in [dimensional model](dimensional_model.md) | Design Phase 1; implementation Phase 2 |
| 3.4 Semantic model, relationships, DAX, hierarchies, two dashboards | KPI definitions, drill/filter behavior, and diagnostic evidence above | Phase 2 |
| 3.5 AI summary/explanation grounded in measures and verifiable | Use active filters, period, baseline, KPIs and supporting breakdowns; say when evidence is insufficient | Phase 3 / final delivery |

AI-assisted explanations must use only measures and breakdowns present in the selected dashboard context, name the period and baseline, cite quantitative evidence visible to the user, and state when the selected data cannot support a conclusion. Natural-language querying is an optional extension unless the course team receives a different instruction.
