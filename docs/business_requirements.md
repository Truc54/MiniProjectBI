# Business Context, Analytical Requirements, and KPI Contract

> Document Version: P4-v1.1 (Merged) · Date: 2026-10-23 · Owners/Contributors: Phúc (Data Source & Profiling), Trực (Dimensional Design & QA) · Reviewers: Dũng (SQL Server), Lộc (Mage ETL)

---

## 1. Problem Statement, Audience, and Business Context

Formula 1 World Championship (1950–2026) spans 77 seasons, over 1,164 Grand Prix events, and tens of thousands of individual race entries. The BI application supports a Formula 1 performance analyst, team/media analyst, or informed F1 follower who needs to compare official race outcomes across drivers, constructors, seasons, and circuits. The decision supported is where performance changed and which result entries explain that change.

The business decisions supported include:

- Where and when performance or reliability changed over time.
- Which specific race result entries, drivers, or constructors explain that change.
- How qualifying execution relates to race conversion under different circuit constraints.

### Scope, Grain, and Non-Causal Boundaries

- **Source scope:** The seven core CSVs documented in [source profile](source_profile.md).
- **Core process and grain:** Exactly one driver result per Grand Prix (`results.resultId`) in `FactRaceResult`, as defined in [dimensional model](dimensional_model.md).
- **Out of scope for this grain:** Lap, pit-stop, sprint, practice, and standings analyses require separate grains and are not implied by this contract.
- **Analytical stance:** Observational, descriptive, and diagnostic BI. The model describes historical association. Grid position or circuit characteristics are descriptive factors, not proof of cause; accidents, strategy, and mechanical failures are possible confounders.

---

## 2. Business Questions

### Race performance analysis

1. Analyze points, wins, podiums, and classified finishes by season and race date.
2. Compare points, wins, and podiums by driver and constructor within a selected season, race, or circuit.
3. Compare race results by circuit and country.
4. Compare starting grid with finishing position and points by season, circuit, driver, and constructor.

### Finishing outcome analysis

5. Analyze non-classified results by status and outcome group across seasons, races, circuits, drivers, and constructors.
6. Identify races or circuits that explain performance changes compared with the previous race or season.

For grid analysis, include only rows with `grid > 0` and a valid classified finish; describe association without claiming causation. For outcome analysis, show both the source status and its outcome group, and keep DNS and DSQ distinct from retirement/DNF. State the comparison baseline when explaining a change. Show result counts and rate denominators where applicable.

---

## 3. KPI Definitions, Reproducible Logic, and Caveats

All KPI calculations obey active report filters. Recompute rates and averages from row-level numerators and denominators; do not average displayed subtotals.

| KPI | Reproducible definition | DAX / SQL aggregation logic | Denominator, filter, and interpretation |
|---|---|---|---|
| **Result entries** | Count of race participation rows; equivalent to count of unique source `resultId` at the fact grain | `COUNT(FactRaceResult[resultId])` | One row is one driver entry in one Grand Prix, not one Grand Prix event. Show alongside totals when useful. |
| **Total points** | Total points awarded in the selected result rows | `SUM(FactRaceResult[points])` | Additive in the selected context. Raw points across eras are not directly comparable; compare within a season/era or use a clearly documented normalized measure. |
| **Wins** | Official race wins | `CALCULATE(COUNTROWS(FactRaceResult), FactRaceResult[positionOrder] = 1)` | Use source-defined winner ordering. Do not infer a win from points or a non-null finish position. |
| **Podiums** | Classified finishes in positions 1 through 3 | `CALCULATE(COUNTROWS(FactRaceResult), FactRaceResult[position] IN {1, 2, 3})` | Require a valid numeric classified position. |
| **Classified entries** | Rows with a valid numeric finish `position` | `CALCULATE(COUNTROWS(FactRaceResult), NOT(ISBLANK(FactRaceResult[position])))` | Position is the classification criterion; do not use `positionText` alone. Report its share with the selected entry count. |
| **Points per entry** | Total points divided by all result rows | `DIVIDE([Total Points], [Result entries])` | The denominator includes every result entry in the selected context, including non-classified entries. Return blank when the denominator is zero. |
| **Mean classified finish** | Average numeric finish position among classified entries | `CALCULATE(AVERAGE(FactRaceResult[position]), NOT(ISBLANK(FactRaceResult[position])))` | Exclude NULL/unclassified positions. Lower is better; show classified-entry count. Median may be added as a separate measure. |
| **Grid-to-finish places gained** | Per eligible row, `grid - position`; summarize as mean, median, or distribution | `CALCULATE(AVERAGE(FactRaceResult[grid] - FactRaceResult[position]), FactRaceResult[grid] > 0, NOT(ISBLANK(FactRaceResult[position])))` | Include only `grid > 0` and a valid classified finish. Positive means gained places, zero means held, negative means lost. Show eligible `n` and excluded NULL/zero-grid counts. |
| **Non-classified rate** | Rows with NULL numeric position divided by all result rows | `DIVIDE(CALCULATE(COUNTROWS(FactRaceResult), ISBLANK(FactRaceResult[position])), [Result entries])` | Denominator is all selected result entries. Show numerator, denominator, and `OutcomeGroup` breakdown. The outcome group does not replace the source-position rule. |
| **Contribution share** | A member's selected KPI divided by the same KPI for its selected parent population | `DIVIDE([Member KPI], [Parent Context KPI])` | Name the parent population (for example, constructor points divided by season points). Do not divide by an unfiltered global total when report filters are active. |

If a source numeric field cannot be parsed, keep the source row, record a conversion discrepancy, and exclude the invalid value from that KPI until resolved. Preserve SQL NULL separately from zero and empty string. Status groups and position semantics are defined in the [dimensional model](dimensional_model.md).

---

## 4. Status Outcome Grouping Taxonomy

Source table `status.csv` contains 141 distinct statuses. To avoid ad-hoc aggregation errors and maintain semantic integrity, outcomes are standardized into five groups in `DimStatus`:

~~~mermaid
graph TD
    SourceStatus["141 Source Statuses<br/>(status.csv)"] --> G1["1. Finished / Lapped<br/>('Finished', '+1 Lap', '+2 Laps'...)"]
    SourceStatus --> G2["2. Mechanical / Technical Failure<br/>('Engine', 'Gearbox', 'Brakes', 'Hydraulics'...)"]
    SourceStatus --> G3["3. Accident / Incident<br/>('Accident', 'Collision', 'Spun off'...)"]
    SourceStatus --> G4["4. Disqualified / Excluded<br/>('Disqualified', 'Excluded')"]
    SourceStatus --> G5["5. Did Not Start / Non-Participant<br/>('Did not start', 'Withdrew', 'Not qualified'...)"]
~~~

### Critical status integrity rules

1. **Never merge DNS/DSQ into DNF:**
   - Disqualified (DSQ) means excluded due to a sporting or technical regulation infringement.
   - Did Not Start (DNS) means the vehicle never crossed the start line to participate.
   - Merging these into generic Did Not Finish (DNF) distorts mechanical reliability and sporting-penalty statistics.
2. **Classified vs. unclassified with status:**
   - Cars retiring after completing more than 90% of race distance can be officially classified with a finishing `position` even if their status is Engine or Accident.
   - The authoritative criterion for classified finish is `position IS NOT NULL`.

---

## 5. Regulatory and Historical Data-Use Caveats

Any consumer of this BI semantic model or AI narrative agent must follow these data boundaries.

### 5.1 F1 championship points are not comparable across eras

- **1950–1959:** 8-6-4-3-2 points; only the best four or five results counted toward the title, and one point was awarded for fastest lap.
- **1960:** 8-6-4-3-2-1.
- **1961–1990:** 9-6-4-3-2-1, with dropped-score rules in some seasons.
- **1991–2002:** 10-6-4-3-2-1, with all races counted.
- **2003–2009:** 10-8-6-5-4-3-2-1.
- **2010 onward:** 25-18-15-12-10-8-6-4-2-1; fastest-lap bonus points applied in 2019–2024, and sprint-race points began in 2021.
- **Guideline:** Do not evaluate cross-era driver point totals without normalizing by the maximum available points per season or presenting career win/podium conversion percentages.

### 5.2 Source extension coverage limitations

- `practice_results.csv`, `weather.csv`, and `tire_stints.csv` exist only for the 2025/2026 seasons (35 Grand Prix events).
- `lap_times.csv` (632,937 rows) covers 1950–2024 only; the source has no records for 2025/2026.
- `fastestLapSpeed` in `results.csv` is NULL for all 2025/2026 races due to an upstream source API limitation.
- Do not interpret the lack of historical weather or tire data before 2025 as zero or clear weather.

### 5.3 Track and grid attributes are not causal evidence

A strong correlation between starting on pole (`grid = 1`) and winning at Monaco does not imply pole position alone guarantees victory; strategy, safety cars, and mechanical reliability are possible confounders. Reports must frame findings as descriptive likelihoods, not causal claims.

---

## 6. Dashboard Question Mapping and Visual Hierarchy

### Dashboard 1: Overview (descriptive analytics)

- **Summary cards:** Points, wins, podiums, result entries, classified entries, and non-classified rate. Put the selected season/period and non-classified numerator/denominator in visible context.
- **Season trend:** Group points and wins by `DimRace` season → round → race. Offer `DimDate` calendar year → quarter → month → date as a calendar hierarchy where useful. Include scoring-era caveats for cross-era point comparisons.
- **Contribution:** Group points, wins, and podiums by constructor, with drill-through to its drivers. Also support grouping by driver or constructor nationality within the selected season, race, or circuit.
- **Distribution:** Group result entries, points, and outcomes by circuit country → circuit and status outcome group → exact source status label.
- **Filters:** Season, race/round, driver, constructor, circuit/country, and source status/outcome group.

### Dashboard 2: Detailed / Diagnostic

- **Drill paths:** Drill through `DimRace` season → round → race, `DimConstructor` nationality → constructor, `DimDriver` nationality → driver, `DimCircuit` country → circuit, and `DimStatus` outcome group → source label. From a constructor selection, filter or drill through to its drivers.
- **Status composition:** Show `OutcomeGroup` and exact source label, with breakdown by season/race, circuit, constructor, or driver. Include row counts and the share denominator.
- **Grid-to-finish analysis:** Compare measures by race, circuit, constructor, or driver using only the eligible population. Display eligible `n` and excluded NULL/zero-grid counts.
- **Change explanation:** Explain points or podium changes with event-level contributions grouped by constructor/driver, circuit, and optionally status. Make the comparison baseline explicit: prior event, prior season, or user-selected period.
- **Result detail:** Provide a result-row detail view keyed by source `resultId`.
- **Reconciliation:** For a selected race/driver/constructor, show source IDs, source measures, status label, and derived values. This is a Phase 2 dashboard requirement; no dashboard is claimed to exist in Phase 1.
- **Anomaly inspection:** Highlight extreme place gains only with the underlying row available for drill-through and a defined threshold.

### AI Analytics Module: Verified Generative Explanations

- Generate natural-language summaries strictly from computed measures and visible filter context.
- State sample sizes, reference baselines, and data limitations such as scoring-system changes.
- Use only measures and breakdowns present in the selected dashboard context; name the period and baseline and cite quantitative evidence visible to the user.
- Decline speculative root-cause explanations when the selected data cannot support them, such as when only an unclassified status is available without telemetry evidence.
- Natural-language querying is optional unless the course team gives a different instruction.

---

## 7. Quantitative Evidence for Acceptance and Report

For the diagnostic page/report, retain evidence for:

1. Source and Stage counts for all seven core tables, plus the selected result count.
2. One sampled race and driver/constructor traced from `results.csv` through `stg.results`, including source IDs, optional NULL fields, and ETL run/batch log.
3. Points and result-entry contribution by status group, constructor, and circuit for a stated season/race selection.
4. Grid-to-finish sample size, the exact eligibility predicate, and row-level examples.
5. Numerator/denominator for every displayed rate and the comparison period used for every change explanation.

Phase 1 defines these evidence needs and SQL acceptance checks. Actual pipeline evidence remains pending until the Stage loader is integrated and run. Record evidence file paths, run IDs, counts, and discrepancies in the evidence/runbook location selected by the team.

---

## 8. Traceability to Course Project Requirements

| Requirement | Contract contribution | Delivery phase |
|---|---|---|
| **3.1 Mage ingestion into SQL Server Staging**; validation, full/incremental load, status/count/error logging, rerun | Operational ETL requirement; mapping and null-token rules are defined in [source-to-stage mapping](source_to_stage_mapping.md). This business/KPI contract does not claim the implementation is complete. | Phase 1 |
| **3.2 dbt transformations**; cleaning, standardization, integration, tests, dependencies, documentation | Lineage, natural-key, and relationship tests are defined in [dimensional model](dimensional_model.md). | Phase 2 |
| **3.3 SQL Server DW**; business process/grain, fact/dimensions/measures, star schema | One-fact star-schema contract at `FactRaceResult` grain `resultId`. | Design Phase 1; implementation Phase 2 |
| **3.4 Semantic model and dashboards**; relationships, DAX, hierarchies, two dashboards | KPI definitions, status grouping taxonomy, drill/filter behavior, and diagnostic evidence above. | Phase 2 |
| **3.5 AI summary/explanation** grounded in measures and verifiable | Use active filters, period, baseline, KPIs, and supporting breakdowns; state when evidence is insufficient. | Phase 3 / final delivery |

---

## 9. Sign-off and Hand-off Alignment

- **Phúc (Author):** Confirms business requirements map 1:1 to validated columns in `docs/source_to_stage_mapping.md`.
- **Trực (Dimensional Model & QA):** Confirms `dw.FactRaceResult` and dimensions satisfy all five business questions and KPI requirements without snowflake complexity.
- **Dũng (SQL Server Staging):** Confirms status categories and numeric data types preserve calculation fidelity.
- **Lộc (Mage ETL):** Confirms NULL values in position and time measures are preserved without zero-padding.
