"""Phase 2 (Loc): status outcome mapping + expected DW baseline computed from source CSVs.

Usage (from repo root):
    python3 tests/phase2_expected_baseline.py

Outputs:
    docs/02_data_dictionary_and_mapping/status_outcome_mapping.csv   (141 rows, reviewed mapping)
    docs/02_data_dictionary_and_mapping/stg_status_outcome.sql       (ready-to-use CASE WHEN for stg_status.sql)
    docs/evidence/loc_phase2_expected_baseline.json                  (expected values for dw reconciliation)

The label sets below are the single source of truth: the CSV and the SQL file are both
generated from them, and tests/test_phase2_mapping.py checks that the three agree.
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset"
NA = ["\\N"]

CLASSIFIED_EXACT = {"Finished", "Lapped"}
LAPS_PATTERN = re.compile(r"^\+[0-9]+ Laps?$")
DNS = {"Did not start", "Withdrew"}
DSQ = {"Disqualified", "Excluded", "Underweight"}
OTHER = {"Not classified", "Did not qualify", "Did not prequalify", "107% Rule", "Not restarted"}

ACCIDENT_DAMAGE = {
    "Accident", "Collision", "Collision damage", "Spun off", "Fatal accident",
    "Damage", "Debris", "Broken wing", "Front wing",
}
DRIVER_MEDICAL = {"Physical", "Injured", "Injury", "Driver unwell", "Eye injury", "Illness"}
OTHER_RETIREMENT = {"Retired", "Safety", "Safety concerns", "Out of fuel", "Refuelling", "Fuel rig"}
MECHANICAL = {
    "Engine", "Gearbox", "Transmission", "Clutch", "Hydraulics", "Electrical", "Radiator",
    "Suspension", "Brakes", "Differential", "Overheating", "Mechanical", "Tyre", "Driver Seat",
    "Puncture", "Driveshaft", "Fuel pressure", "Water pressure", "Wheel", "Throttle", "Steering",
    "Technical", "Electronics", "Heat shield fire", "Exhaust", "Oil leak", "Wheel rim",
    "Water leak", "Fuel pump", "Track rod", "Oil pressure", "Engine fire", "Engine misfire",
    "Tyre puncture", "Wheel nut", "Pneumatics", "Handling", "Rear wing", "Fire", "Wheel bearing",
    "Fuel system", "Oil line", "Launch control", "Fuel", "Power loss", "Vibrations", "Drivetrain",
    "Ignition", "Chassis", "Battery", "Stalled", "Halfshaft", "Crankshaft", "Alternator",
    "Safety belt", "Oil pump", "Fuel leak", "Injection", "Distributor", "Turbo", "CV joint",
    "Water pump", "Spark plugs", "Fuel pipe", "Oil pipe", "Axle", "Water pipe", "Magneto",
    "Supercharger", "Power Unit", "ERS", "Brake duct", "Seat", "Undertray", "Cooling system",
}
RETIREMENT = ACCIDENT_DAMAGE | DRIVER_MEDICAL | OTHER_RETIREMENT | MECHANICAL


def classify(label: str) -> tuple[str, str]:
    s = label.strip()
    if s in CLASSIFIED_EXACT or LAPS_PATTERN.match(s):
        return "CLASSIFIED", "FINISHED_OR_LAPPED"
    if s in DNS:
        return "DNS", "DID_NOT_START"
    if s in DSQ:
        return "DSQ", "DISQUALIFIED"
    if s in OTHER:
        return "OTHER", "NOT_QUALIFIED_OR_NOT_CLASSIFIED"
    if s in MECHANICAL:
        return "RETIREMENT_DNF", "MECHANICAL"
    if s in ACCIDENT_DAMAGE:
        return "RETIREMENT_DNF", "ACCIDENT_DAMAGE"
    if s in DRIVER_MEDICAL:
        return "RETIREMENT_DNF", "DRIVER_MEDICAL"
    if s in OTHER_RETIREMENT:
        return "RETIREMENT_DNF", "OTHER_RETIREMENT"
    return "OTHER", "UNREVIEWED"


LABEL_SETS = {
    "CLASSIFIED": CLASSIFIED_EXACT, "DNS": DNS, "DSQ": DSQ, "OTHER": OTHER,
    "MECHANICAL": MECHANICAL, "ACCIDENT_DAMAGE": ACCIDENT_DAMAGE,
    "DRIVER_MEDICAL": DRIVER_MEDICAL, "OTHER_RETIREMENT": OTHER_RETIREMENT,
}


def assert_disjoint() -> None:
    """Every reviewed label must belong to exactly one set (pairwise, not only all-four)."""
    names = list(LABEL_SETS)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            both = LABEL_SETS[a] & LABEL_SETS[b]
            assert not both, f"{a} and {b} overlap: {sorted(both)}"
        assert not any(LAPS_PATTERN.match(x) for x in LABEL_SETS[a] - CLASSIFIED_EXACT), a


def expected_max_winner_points(year: int) -> float:
    """Max Grand Prix points of a winner per season (stage_to_dw_mapping.md section 8.1).

    1950-59: 8 + 1 fastest lap; 1960: 8; 1961-90: 9; 1991-2009: 10; 2010+: 25,
    except 2014 (double points finale = 50) and 2019-24 (+1 fastest lap = 26).
    """
    if year <= 1959:
        return 9.0
    if year == 1960:
        return 8.0
    if year <= 1990:
        return 9.0
    if year <= 2009:
        return 10.0
    if year == 2014:
        return 50.0
    if 2019 <= year <= 2024:
        return 26.0
    return 25.0


def _sql_in(labels: set[str], indent: str) -> str:
    items = [f"N'{x.replace(chr(39), chr(39) * 2)}'" for x in sorted(labels)]
    lines, line = [], ""
    for item in items:
        if line and len(line) + len(item) + 2 > 78:
            lines.append(line + ",")
            line = ""
        line = f"{line}, {item}" if line else item
    lines.append(line)
    return ("\n" + indent).join(lines)


def render_status_sql() -> str:
    """dbt-ready body for models/staging/stg_status.sql, generated from the label sets."""
    i = " " * 34
    laps = "status_label like N'+[0-9]% Lap' or status_label like N'+[0-9]% Laps'"
    return f"""-- GENERATED by tests/phase2_expected_baseline.py - do not edit by hand.
-- Loc -> Truc: paste as dbt/models/staging/stg_status.sql (141 status -> 5 outcome_group).
-- Plain T-SQL test: replace {{{{ source('stg', 'status') }}}} with stg.status.
with src as (
    select
        statusId                          as status_id,
        nullif(ltrim(rtrim(status)), N'') as status_label,
        _batch_key,
        _ingested_at_utc
    from {{{{ source('stg', 'status') }}}}
),
classified as (
    select
        status_id,
        status_label,
        case
            when status_label in ({_sql_in(CLASSIFIED_EXACT, i)})
              or {laps}
                then 'FINISHED_OR_LAPPED'
            when status_label in ({_sql_in(DNS, i)})
                then 'DID_NOT_START'
            when status_label in ({_sql_in(DSQ, i)})
                then 'DISQUALIFIED'
            when status_label in ({_sql_in(OTHER, i)})
                then 'NOT_QUALIFIED_OR_NOT_CLASSIFIED'
            when status_label in ({_sql_in(MECHANICAL, i)})
                then 'MECHANICAL'
            when status_label in ({_sql_in(ACCIDENT_DAMAGE, i)})
                then 'ACCIDENT_DAMAGE'
            when status_label in ({_sql_in(DRIVER_MEDICAL, i)})
                then 'DRIVER_MEDICAL'
            when status_label in ({_sql_in(OTHER_RETIREMENT, i)})
                then 'OTHER_RETIREMENT'
            else 'UNREVIEWED'   -- new label: dbt warn test in stage_to_dw_mapping.md section 7
        end as outcome_category,
        _batch_key,
        _ingested_at_utc
    from src
)
select
    status_id,
    status_label,
    case outcome_category
        when 'FINISHED_OR_LAPPED'              then 'CLASSIFIED'
        when 'DID_NOT_START'                   then 'DNS'
        when 'DISQUALIFIED'                    then 'DSQ'
        when 'NOT_QUALIFIED_OR_NOT_CLASSIFIED' then 'OTHER'
        when 'UNREVIEWED'                      then 'OTHER'
        else 'RETIREMENT_DNF'   -- MECHANICAL, ACCIDENT_DAMAGE, DRIVER_MEDICAL, OTHER_RETIREMENT
    end as outcome_group,
    outcome_category,
    _batch_key,
    _ingested_at_utc
from classified
"""


def main() -> None:
    assert_disjoint()
    status = pd.read_csv(DATA / "status.csv")
    results = pd.read_csv(DATA / "results.csv", na_values=NA, keep_default_na=False)
    races = pd.read_csv(DATA / "races.csv", na_values=NA, keep_default_na=False)
    drivers = pd.read_csv(DATA / "drivers.csv", na_values=NA, keep_default_na=False)

    status[["outcome_group", "outcome_category"]] = status["status"].apply(
        lambda v: pd.Series(classify(v)))
    usage = results["statusId"].value_counts()
    status["result_rows"] = status["statusId"].map(usage).fillna(0).astype(int)
    unreviewed = status[status.outcome_category == "UNREVIEWED"]
    assert unreviewed.empty, f"Unreviewed statuses: {unreviewed.status.tolist()}"
    assert len(status) == 141 and status.statusId.is_unique

    out_csv = ROOT / "docs/02_data_dictionary_and_mapping/status_outcome_mapping.csv"
    status.sort_values("statusId")[
        ["statusId", "status", "outcome_group", "outcome_category", "result_rows"]
    ].to_csv(out_csv, index=False)
    out_sql = ROOT / "docs/02_data_dictionary_and_mapping/stg_status_outcome.sql"
    out_sql.write_text(render_status_sql(), encoding="utf-8")

    r = results.merge(status[["statusId", "outcome_group", "outcome_category"]], on="statusId")
    r = r.merge(races[["raceId", "year", "date"]], on="raceId")
    classified = r["position"].notna()
    eligible = (r["grid"] > 0) & classified

    mismatch_cls_nopos = r[(r.outcome_group == "CLASSIFIED") & ~classified]
    mismatch_dnf_pos = r[(r.outcome_group == "RETIREMENT_DNF") & classified]

    baseline = {
        "source": "dataset/*.csv (Kaggle snapshot in repo); \\N -> NULL",
        "generated_by": "tests/phase2_expected_baseline.py",
        "row_counts": {
            "fact_race_result": int(len(results)),
            "dim_race": int(len(races)),
            "dim_circuit": int(len(pd.read_csv(DATA / "circuits.csv"))),
            "dim_driver": int(len(pd.read_csv(DATA / "drivers.csv"))),
            "dim_constructor": int(len(pd.read_csv(DATA / "constructors.csv"))),
            "dim_status": int(len(status)),
            "note": "Dimension counts exclude the Unknown member (-1); add 1 when it is included.",
        },
        "dim_date": {
            "min_race_date": str(races["date"].min()),
            "max_race_date": str(races["date"].max()),
            "distinct_race_dates": int(races["date"].nunique()),
        },
        "measures": {
            "sum_points": round(float(results["points"].sum()), 2),
            "sum_laps": int(results["laps"].sum()),
            "win_rows_position_order_1": int((results["positionOrder"] == 1).sum()),
            "races_with_winner": int(results.loc[results.positionOrder == 1, "raceId"].nunique()),
            "podium_rows_position_1_to_3": int(results["position"].isin([1, 2, 3]).sum()),
            "classified_rows_position_not_null": int(classified.sum()),
            "non_classified_rows_position_null": int((~classified).sum()),
            "grid_zero_rows": int((results["grid"] == 0).sum()),
            "places_gained_eligible_rows": int(eligible.sum()),
            "places_gained_sum": int((r.grid - r.position)[eligible].sum()),
            "places_gained_avg": round(float((r.grid - r.position)[eligible].mean()), 6),
            "milliseconds_null_rows": int(results["milliseconds"].isna().sum()),
            "fastest_lap_speed_null_rows": int(results["fastestLapSpeed"].isna().sum()),
        },
        "points_eras": {
            "rule": "max winner points per season = expected_max_winner_points(year)",
            "seasons_checked": int(r.year.nunique()),
            "seasons_violating": sorted(
                int(y) for y, p in r[r.positionOrder == 1].groupby("year").points.max().items()
                if p != expected_max_winner_points(int(y))),
        },
        "outcome_group": {
            "status_codes": status.outcome_group.value_counts().sort_index().to_dict(),
            "result_rows": r.outcome_group.value_counts().sort_index().to_dict(),
            "result_rows_retirement_category": r.loc[r.outcome_group == "RETIREMENT_DNF",
                                                     "outcome_category"].value_counts().sort_index().to_dict(),
        },
        "position_text_rows": results["positionText"].where(
            ~results["positionText"].str.isdigit(), "numeric").value_counts().sort_index().to_dict(),
        "known_discrepancies": {
            "classified_group_but_position_null": int(len(mismatch_cls_nopos)),
            "retirement_group_but_position_not_null": int(len(mismatch_dnf_pos)),
            "position_differs_from_position_order": int(
                (classified & (r.position != r.positionOrder)).sum()),
            "races_with_multiple_position_order_1": sorted(
                int(x) for x, n in results[results.positionOrder == 1].raceId.value_counts().items() if n > 1),
            "status_codes_unused_in_results": status.loc[status.result_rows == 0, "statusId"].astype(int).tolist(),
            "drivers_nationality_trailing_space": drivers.loc[
                (drivers.nationality != "") & (drivers.nationality != drivers.nationality.str.strip()),
                "driverId"].astype(int).tolist(),
            "drivers_nationality_empty_string": drivers.loc[
                drivers.nationality.str.strip() == "", "driverId"].astype(int).tolist(),
            "numeric_position_text_but_position_null": results.loc[
                results.position.isna() & results.positionText.str.isdigit(), "resultId"].astype(int).tolist(),
        },
    }
    out_json = ROOT / "docs/evidence/loc_phase2_expected_baseline.json"
    out_json.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(baseline, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
