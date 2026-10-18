# Business context and analytical requirements

## Problem and audience

Build a BI application for a Formula 1 performance analyst, team/media analyst, or F1 fan who needs to compare race outcomes across drivers, constructors, seasons, and circuits. The business process in scope is a driver's classified or unclassified result in a Grand Prix. The analysis helps identify performance trends and unusual changes; it describes associations in historical data and does not claim that grid position or circuit caused an outcome.

## Business questions

1. How do race points, wins, podiums, and classified finishes change by season for a driver or constructor?
2. Which drivers and constructors contribute the most points or wins in a selected season, race, or circuit?
3. How does starting grid relate to classified finishing position and points, after filtering to rows with valid grid and finish values?
4. Which finishing outcomes (finished, retired/accident/mechanical, disqualified, did not start, or other source statuses) contribute to changes in non-classified results by season, constructor, driver, or circuit?
5. Which race events or circuits show an unusual points/performance change compared with the prior race or season?

## KPI definitions to implement and validate

| KPI | Definition | Caveat |
|---|---|---|
| Race result rows / entries | Count of fact rows | One row per `results.resultId`; not the count of distinct races |
| Total points | Sum of `results.points` | Compare within season/era where scoring systems differ |
| Wins | Count of rows where `positionOrder = 1` | Use the source ordering field; do not infer from a NULL `position` |
| Podiums | Count of classified rows with `position` from 1 to 3 | Only rows with a valid classified position |
| Points per entry | Sum(points) / count of result rows | State denominator and filters |
| Mean classified finish | Average numeric `position` for classified rows | Lower is better; do not mix unclassified values into the average |
| Grid-to-finish places gained | `grid - position` for valid positive grid and classified position | Positive means gained places; exclude invalid/unknown positions and grid=0 |
| Non-classified rate | Count of agreed non-classified outcome groups / eligible result rows | Grouping from `status` must be explicit; DNS/DSQ are not automatically DNF |

Positions and times are non-additive measures. Points and laps are additive at the fact grain. Averages, rates, and distinct-race counts must be recalculated from numerators/denominators under the active filter context.

## Dashboard question mapping

- **Overview (Descriptive):** KPI cards for points, wins, podiums, entries and non-classified rate; season trend; points/wins by constructor and driver; race/circuit distribution; filters for season, driver, constructor, circuit/country and status.
- **Detailed/Diagnostic:** drill from season to round/race and from constructor to driver; inspect grid-to-finish contribution, status composition, points by event, and the rows behind a selected anomaly. Show counts and denominators alongside percentages so the finding can be checked.
- **AI-assisted analytics:** summarize selected KPIs and explain observed changes using only filtered dashboard measures and supporting breakdowns; include the selected period, comparison baseline and quantitative evidence. Ask the model to say when evidence is insufficient. Natural-language querying is an optional extension.
