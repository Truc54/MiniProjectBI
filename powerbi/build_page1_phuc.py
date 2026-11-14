import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PBIX = ROOT / "powerbi" / "F1_Analytics_Dev_Page3_Loc.pbix"
DST_PBIX = ROOT / "powerbi" / "F1_Analytics_Dev_Page1_Phuc.pbix"

PAGE1_ID = "3ae902435eec8d3460c0"  # Overview page
PAGE2_ID = "83e5ad66db596ac7559e"  # Thành tích & Biến động
PAGE3_ID = "c671a9ea38005deac8ed"  # Trường đua & Kết quả


def make_textbox(name, x, y, z, w, h, paragraphs, bg_color=None, border_color=None, radius=0):
    bg_props = {"show": {"expr": {"Literal": {"Value": "true" if bg_color else "false"}}}}
    if bg_color:
        bg_props["color"] = {"solid": {"color": {"expr": {"Literal": {"Value": f"'{bg_color}'"}}}}}
        bg_props["transparency"] = {"expr": {"Literal": {"Value": "0D"}}}

    border_props = {"show": {"expr": {"Literal": {"Value": "true" if border_color else "false"}}}}
    if border_color:
        border_props["color"] = {"solid": {"color": {"expr": {"Literal": {"Value": f"'{border_color}'"}}}}}
        if radius > 0:
            border_props["radius"] = {"expr": {"Literal": {"Value": f"{radius}D"}}}

    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z // 10},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [{"properties": {"paragraphs": paragraphs}}]
            },
            "visualContainerObjects": {
                "background": [{"properties": bg_props}],
                "border": [{"properties": border_props}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def make_slicer(name, x, y, z, w, h, entity, prop, display_name):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z // 10},
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [{
                            "field": {
                                "Column": {
                                    "Expression": {"SourceRef": {"Entity": entity}},
                                    "Property": prop
                                }
                            },
                            "queryRef": f"{entity}.{prop}",
                            "nativeQueryRef": prop,
                            "active": True,
                            "displayName": display_name
                        }]
                    }
                }
            },
            "objects": {
                "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
                "header": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#5B6070'"}}}}},
                        "textSize": {"expr": {"Literal": {"Value": "9D"}}},
                        "text": {"expr": {"Literal": {"Value": f"'{display_name}'"}}}
                    }
                }],
                "items": [{
                    "properties": {
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1B1D24'"}}}}},
                        "textSize": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }]
            },
            "visualContainerObjects": {
                "background": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    }
                }],
                "border": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E4E7EC'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "8D"}}}
                    }
                }],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def make_action_button(name, x, y, z, w, h, target_page, text):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z // 10},
        "visual": {
            "visualType": "actionButton",
            "objects": {
                "text": [{
                    "properties": {
                        "text": {"expr": {"Literal": {"Value": f"'{text}'"}}},
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "10D"}}},
                        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}}
                    },
                    "selector": {"id": "default"}
                }],
                "outline": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "lineColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                        "lineWeight": {"expr": {"Literal": {"Value": "1D"}}},
                        "radius": {"expr": {"Literal": {"Value": "8D"}}}
                    },
                    "selector": {"id": "default"}
                }],
                "fill": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "fillColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0B4F9C'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    },
                    "selector": {"id": "default"}
                }]
            },
            "visualContainerObjects": {
                "visualLink": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "type": {"expr": {"Literal": {"Value": "'PageNavigation'"}}},
                        "page": {"expr": {"Literal": {"Value": f"'{target_page}'"}}}
                    }
                }],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def make_card(name, x, y, z, w, h, projection_field, query_ref, native_query_ref, display_name, fmt="#,0"):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z // 10},
        "visual": {
            "visualType": "card",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [{
                            "field": projection_field,
                            "queryRef": query_ref,
                            "nativeQueryRef": native_query_ref,
                            "displayName": display_name,
                            "format": fmt
                        }]
                    }
                }
            },
            "objects": {
                "labels": [{
                    "properties": {
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1B1D24'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "24D"}}},
                        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                        "labelDisplayUnits": {"expr": {"Literal": {"Value": "1D"}}}
                    }
                }],
                "categoryLabels": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#5B6070'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }]
            },
            "visualContainerObjects": {
                "background": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    }
                }],
                "border": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E4E7EC'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }],
                "dropShadow": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "padding": [{
                    "properties": {
                        "top": {"expr": {"Literal": {"Value": "8D"}}},
                        "bottom": {"expr": {"Literal": {"Value": "8D"}}},
                        "left": {"expr": {"Literal": {"Value": "12D"}}},
                        "right": {"expr": {"Literal": {"Value": "12D"}}}
                    }
                }],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def make_macro_trend_line_chart(name, x, y, z, w, h):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z // 10},
        "visual": {
            "visualType": "lineChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [{
                            "field": {
                                "Column": {
                                    "Expression": {"SourceRef": {"Entity": "dw DimRace"}},
                                    "Property": "season_year"
                                }
                            },
                            "queryRef": "dw DimRace.season_year",
                            "nativeQueryRef": "season_year",
                            "active": True,
                            "displayName": "Mùa giải"
                        }]
                    },
                    "Y": {
                        "projections": [
                            {
                                "field": {
                                    "Aggregation": {
                                        "Expression": {
                                            "Column": {
                                                "Expression": {"SourceRef": {"Entity": "dw FactRaceResult"}},
                                                "Property": "race_sk"
                                            }
                                        },
                                        "Function": 2
                                    }
                                },
                                "queryRef": "CountNonNull(dw FactRaceResult.race_sk)",
                                "nativeQueryRef": "race_sk",
                                "displayName": "Số chặng Grand Prix",
                                "format": "#,0"
                            },
                            {
                                "field": {
                                    "Measure": {
                                        "Expression": {"SourceRef": {"Entity": "_Measures"}},
                                        "Property": "Total Entries"
                                    }
                                },
                                "queryRef": "_Measures.Total Entries",
                                "nativeQueryRef": "Total Entries",
                                "displayName": "Số lượt xuất phát",
                                "format": "#,0"
                            }
                        ]
                    }
                },
                "sortDefinition": {
                    "sort": [{
                        "field": {
                            "Column": {
                                "Expression": {"SourceRef": {"Entity": "dw DimRace"}},
                                "Property": "season_year"
                            }
                        },
                        "direction": "Ascending"
                    }],
                    "isDefaultSort": True
                }
            },
            "objects": {
                "categoryAxis": [{
                    "properties": {
                        "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#5B6070'"}}}}}
                    }
                }],
                "valueAxis": [{
                    "properties": {
                        "showAxisTitle": {"expr": {"Literal": {"Value": "true"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#5B6070'"}}}}},
                        "gridlineShow": {"expr": {"Literal": {"Value": "true"}}},
                        "gridlineColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#EEF0F3'"}}}}}
                    }
                }],
                "legend": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "position": {"expr": {"Literal": {"Value": "'TopLeft'"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }],
                "lineStyles": [
                    {"properties": {"strokeWidth": {"expr": {"Literal": {"Value": "3D"}}}, "showMarker": {"expr": {"Literal": {"Value": "true"}}}}}
                ]
            },
            "visualContainerObjects": {
                "background": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    }
                }],
                "border": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E4E7EC'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }],
                "title": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "text": {"expr": {"Literal": {"Value": "'Xu hướng quy mô giải đấu & số lượt tham gia qua các mùa giải (1950–2026)'"}}},
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1B1D24'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "12D"}}},
                        "bold": {"expr": {"Literal": {"Value": "true"}}},
                        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}}
                    }
                }],
                "subTitle": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def make_top_drivers_chart(name, x, y, z, w, h):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z // 10},
        "visual": {
            "visualType": "clusteredBarChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [{
                            "field": {
                                "Column": {
                                    "Expression": {"SourceRef": {"Entity": "dw DimDriver"}},
                                    "Property": "full_name"
                                }
                            },
                            "queryRef": "dw DimDriver.full_name",
                            "nativeQueryRef": "full_name",
                            "active": True,
                            "displayName": "Tay đua"
                        }]
                    },
                    "Y": {
                        "projections": [{
                            "field": {
                                "Measure": {
                                    "Expression": {"SourceRef": {"Entity": "_Measures"}},
                                    "Property": "Wins"
                                }
                            },
                            "queryRef": "_Measures.Wins",
                            "nativeQueryRef": "Wins",
                            "displayName": "Số chiến thắng",
                            "format": "#,0"
                        }]
                    }
                },
                "sortDefinition": {
                    "sort": [{
                        "field": {
                            "Measure": {
                                "Expression": {"SourceRef": {"Entity": "_Measures"}},
                                "Property": "Wins"
                            }
                        },
                        "direction": "Descending"
                    }],
                    "isDefaultSort": True
                }
            },
            "objects": {
                "categoryAxis": [{
                    "properties": {
                        "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#5B6070'"}}}}}
                    }
                }],
                "valueAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "dataPoint": [{
                    "properties": {
                        "defaultColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E10600'"}}}}}
                    }
                }],
                "labels": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1B1D24'"}}}}}
                    }
                }]
            },
            "visualContainerObjects": {
                "background": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    }
                }],
                "border": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E4E7EC'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }],
                "title": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "text": {"expr": {"Literal": {"Value": "'Top 10 Tay đua có nhiều chiến thắng nhất lịch sử F1'"}}},
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1B1D24'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "12D"}}},
                        "bold": {"expr": {"Literal": {"Value": "true"}}},
                        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}}
                    }
                }],
                "subTitle": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def make_donut_chart(name, x, y, z, w, h):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z // 10},
        "visual": {
            "visualType": "donutChart",
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [{
                            "field": {
                                "Column": {
                                    "Expression": {"SourceRef": {"Entity": "dw DimStatus"}},
                                    "Property": "outcome_group"
                                }
                            },
                            "queryRef": "dw DimStatus.outcome_group",
                            "nativeQueryRef": "outcome_group",
                            "active": True,
                            "displayName": "Nhóm kết quả"
                        }]
                    },
                    "Y": {
                        "projections": [{
                            "field": {
                                "Measure": {
                                    "Expression": {"SourceRef": {"Entity": "_Measures"}},
                                    "Property": "Total Entries"
                                }
                            },
                            "queryRef": "_Measures.Total Entries",
                            "nativeQueryRef": "Total Entries",
                            "displayName": "Số lượt",
                            "format": "#,0"
                        }]
                    }
                }
            },
            "objects": {
                "legend": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "position": {"expr": {"Literal": {"Value": "'Right'"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "10D"}}},
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#5B6070'"}}}}}
                    }
                }],
                "labels": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "labelStyle": {"expr": {"Literal": {"Value": "'Both'"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "10D"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1B1D24'"}}}}}
                    }
                }],
                "dataPoint": [
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#2A78D6'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'CLASSIFIED'"}}}}}]}
                    },
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#EB6834'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'RETIREMENT_DNF'"}}}}}]}
                    },
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1BAF7A'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'DNS'"}}}}}]}
                    },
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#EDA100'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'DSQ'"}}}}}]}
                    },
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#8A8984'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'OTHER'"}}}}}]}
                    }
                ]
            },
            "visualContainerObjects": {
                "background": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    }
                }],
                "border": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E4E7EC'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }],
                "title": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "text": {"expr": {"Literal": {"Value": "'Cơ cấu phân bổ kết quả thi đấu (5 nhóm Outcome)'"}}},
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1B1D24'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "12D"}}},
                        "bold": {"expr": {"Literal": {"Value": "true"}}},
                        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}}
                    }
                }],
                "subTitle": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def build_page1():
    print(f"Reading template from {SRC_PBIX}...")
    with zipfile.ZipFile(SRC_PBIX, "r") as z_in:
        files = {name: z_in.read(name) for name in z_in.namelist()}

    # Update pages.json to make Overview active
    pages_meta = json.loads(files["Report/definition/pages/pages.json"].decode("utf-8"))
    pages_meta["activePageName"] = PAGE1_ID
    files["Report/definition/pages/pages.json"] = json.dumps(pages_meta, ensure_ascii=False, indent=2).encode("utf-8")

    # Generate Page 1 visuals
    visuals = {}

    # 1. Header Banner Background
    v_hdr_bg = make_textbox("p1_v01_hdr_bg", 0, 0, 0, 1920, 96, [
        {"textRuns": [{"value": " ", "textStyle": {"fontSize": "4pt", "color": "#FFFFFF"}}]}
    ], bg_color="#1F6FD1")
    visuals["p1_v01_hdr_bg"] = v_hdr_bg

    # 2. Header Red Accent Line
    v_hdr_line = make_textbox("p1_v02_hdr_line", 0, 96, 1, 1920, 4, [
        {"textRuns": [{"value": " ", "textStyle": {"fontSize": "1pt", "color": "#E10600"}}]}
    ], bg_color="#E10600")
    visuals["p1_v02_hdr_line"] = v_hdr_line

    # 3. Header Title & Subtitle
    v_hdr_title = make_textbox("p1_v03_hdr_title", 24, 14, 2, 850, 68, [
        {
            "textRuns": [
                {"value": "FORMULA 1 ANALYTICS · OVERVIEW (1950–2026)\n", "textStyle": {"fontSize": "20pt", "color": "#FFFFFF", "fontFamily": "Segoe UI Semibold", "fontWeight": "bold"}},
                {"value": "Bức tranh toàn cảnh về quy mô lịch sử, hiệu suất vĩ mô và xu hướng phát triển F1 qua 77 mùa giải", "textStyle": {"fontSize": "10pt", "color": "#E2E8F0", "fontFamily": "Segoe UI"}}
            ]
        }
    ])
    visuals["p1_v03_hdr_title"] = v_hdr_title

    # 4. Slicers in Header
    v_sl_season = make_slicer("p1_v04_sl_season", 890, 14, 50, 185, 68, "dw DimRace", "season_year", "Mùa giải")
    visuals["p1_v04_sl_season"] = v_sl_season

    v_sl_constructor = make_slicer("p1_v05_sl_constructor", 1090, 14, 51, 215, 68, "dw DimConstructor", "constructor_name", "Đội đua")
    visuals["p1_v05_sl_constructor"] = v_sl_constructor

    # 5. Navigation Buttons in Header
    v_btn_p2 = make_action_button("p1_v06_btn_p2", 1320, 20, 52, 280, 56, PAGE2_ID, "Trang 2: Thành tích & Biến động ➔")
    visuals["p1_v06_btn_p2"] = v_btn_p2

    v_btn_p3 = make_action_button("p1_v07_btn_p3", 1615, 20, 53, 280, 56, PAGE3_ID, "Trang 3: Trường đua & Kết quả ➔")
    visuals["p1_v07_btn_p3"] = v_btn_p3

    # 6. Row 1: KPI Cards (y=112, h=108, w=298)
    card_race_proj = {
        "Aggregation": {
            "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": "dw FactRaceResult"}}, "Property": "race_sk"}},
            "Function": 2
        }
    }
    v_c_races = make_card("p1_v08_c_races", 24, 112, 100, 298, 108, card_race_proj, "CountNonNull(dw FactRaceResult.race_sk)", "race_sk", "Tổng số chặng Grand Prix", "#,0")
    visuals["p1_v08_c_races"] = v_c_races

    card_ent_proj = {
        "Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Total Entries"}
    }
    v_c_entries = make_card("p1_v09_c_entries", 338, 112, 110, 298, 108, card_ent_proj, "_Measures.Total Entries", "Total Entries", "Tổng số lượt tham gia", "#,0")
    visuals["p1_v09_c_entries"] = v_c_entries

    card_class_proj = {
        "Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Classified Rate"}
    }
    v_c_class = make_card("p1_v10_c_class", 652, 112, 120, 298, 108, card_class_proj, "_Measures.Classified Rate", "Classified Rate", "Tỷ lệ hoàn thành (Classified)", "0.0%")
    visuals["p1_v10_c_class"] = v_c_class

    card_pts_proj = {
        "Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Total Points"}
    }
    v_c_points = make_card("p1_v11_c_points", 966, 112, 130, 298, 108, card_pts_proj, "_Measures.Total Points", "Total Points", "Tổng điểm số lịch sử", "#,0.00")
    visuals["p1_v11_c_points"] = v_c_points

    card_drv_proj = {
        "Aggregation": {
            "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": "dw FactRaceResult"}}, "Property": "driver_sk"}},
            "Function": 2
        }
    }
    v_c_drivers = make_card("p1_v12_c_drivers", 1280, 112, 140, 298, 108, card_drv_proj, "CountNonNull(dw FactRaceResult.driver_sk)", "driver_sk", "Tổng số tay đua tham gia", "#,0")
    visuals["p1_v12_c_drivers"] = v_c_drivers

    card_con_proj = {
        "Aggregation": {
            "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": "dw FactRaceResult"}}, "Property": "constructor_sk"}},
            "Function": 2
        }
    }
    v_c_constructors = make_card("p1_v13_c_constructors", 1594, 112, 150, 298, 108, card_con_proj, "CountNonNull(dw FactRaceResult.constructor_sk)", "constructor_sk", "Tổng số đội đua tham gia", "#,0")
    visuals["p1_v13_c_constructors"] = v_c_constructors

    # 7. Main Grid Visuals (y=236 to 940)
    # Left: Macro Trend (w=1116, h=440)
    v_line_trend = make_macro_trend_line_chart("p1_v14_macro_trend", 24, 236, 200, 1116, 440)
    visuals["p1_v14_macro_trend"] = v_line_trend

    # Left Bottom: Top 10 Drivers by Wins (w=1116, h=340)
    v_top_drivers = make_top_drivers_chart("p1_v15_top_drivers", 24, 692, 210, 1116, 340)
    visuals["p1_v15_top_drivers"] = v_top_drivers

    # Right: Outcome Group Donut Chart (w=740, h=440)
    v_donut_outcome = make_donut_chart("p1_v16_outcome_donut", 1156, 236, 220, 740, 440)
    visuals["p1_v16_outcome_donut"] = v_donut_outcome

    # Right Bottom: Historical Scoring Context Footnote (w=740, h=340)
    caveat_paragraphs = [
        {
            "textRuns": [
                {"value": "LƯU Ý NGỮ CẢNH: HỆ THỐNG TÍNH ĐIỂM F1 QUA CÁC KỶ NGUYÊN\n\n", "textStyle": {"fontSize": "11pt", "fontWeight": "bold", "color": "#1B1D24", "fontFamily": "Segoe UI Semibold"}},
                {"value": "Hệ thống thang điểm của F1 đã thay đổi sâu sắc qua 77 năm lịch sử:\n", "textStyle": {"fontSize": "9.5pt", "color": "#334155"}},
                {"value": "• 1950–1960: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#1F6FD1"}},
                {"value": "Thắng được 8đ, chỉ tính điểm Top 5 (8-6-4-3-2), cộng 1đ cho Fastest Lap.\n", "textStyle": {"fontSize": "9.5pt", "color": "#334155"}},
                {"value": "• 1961–1990: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#1F6FD1"}},
                {"value": "Thắng được 9đ, tính điểm Top 6 (9-6-4-3-2-1), bỏ điểm Fastest Lap.\n", "textStyle": {"fontSize": "9.5pt", "color": "#334155"}},
                {"value": "• 1991–2002: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#1F6FD1"}},
                {"value": "Thắng được 10đ, tính điểm Top 6 (10-6-4-3-2-1).\n", "textStyle": {"fontSize": "9.5pt", "color": "#334155"}},
                {"value": "• 2003–2009: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#1F6FD1"}},
                {"value": "Thắng được 10đ, mở rộng điểm cho Top 8 (10-8-6-5-4-3-2-1).\n", "textStyle": {"fontSize": "9.5pt", "color": "#334155"}},
                {"value": "• 2010–2018: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#1F6FD1"}},
                {"value": "Thắng được 25đ, mở rộng cho Top 10 (25-18-15-12-10-8-6-4-2-1).\n", "textStyle": {"fontSize": "9.5pt", "color": "#334155"}},
                {"value": "• 2019–2026: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#1F6FD1"}},
                {"value": "Bổ sung 1đ cho Fastest Lap (áp dụng cho xe hoàn thành trong Top 10).\n\n", "textStyle": {"fontSize": "9.5pt", "color": "#334155"}},
                {"value": "⚠️ Khuyến cáo phân tích: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#C5221F"}},
                {"value": "Tuyệt đối không so sánh trực tiếp tổng điểm số thô giữa các mùa giải thuộc các kỷ nguyên khác nhau mà không có chuẩn hóa hoặc tỷ lệ phần trăm tương đối.", "textStyle": {"fontSize": "9.5pt", "fontStyle": "italic", "color": "#475569"}}
            ]
        }
    ]
    v_caveat = make_textbox("p1_v17_caveat", 1156, 692, 230, 740, 340, caveat_paragraphs, bg_color="#F8FAFC", border_color="#CBD5E1", radius=10)
    visuals["p1_v17_caveat"] = v_caveat

    # 8. Footer Status Bar
    v_footer = make_textbox("p1_v18_footer", 0, 1044, 10, 1920, 36, [
        {
            "textRuns": [
                {"value": "Formula 1 Analytics (1950–2026) · Phase 3 Semantic Model & Overview Dashboard · QA Lead: Phúc · Kho dữ liệu Kimball Star Schema", "textStyle": {"fontSize": "9pt", "color": "#94A3B8", "fontFamily": "Segoe UI"}}
            ]
        }
    ], bg_color="#0F172A")
    visuals["p1_v18_footer"] = v_footer

    # Write visuals into zip structure
    for vname, vdata in visuals.items():
        vpath = f"Report/definition/pages/{PAGE1_ID}/visuals/{vname}/visual.json"
        files[vpath] = json.dumps(vdata, ensure_ascii=False, indent=2).encode("utf-8")

    # Remove SecurityBindings so Power BI Desktop does not trigger signature mismatch corruption
    if "SecurityBindings" in files:
        del files["SecurityBindings"]

    # Remove SecurityBindings override in [Content_Types].xml
    if "[Content_Types].xml" in files:
        ct_text = files["[Content_Types].xml"].decode("utf-8")
        ct_clean = ct_text.replace('<Override PartName="/SecurityBindings" ContentType="" />', '')
        files["[Content_Types].xml"] = ct_clean.encode("utf-8")

    print(f"Writing {len(visuals)} visuals for Page 1 ({PAGE1_ID})...")
    print(f"Saving new PBIX to {DST_PBIX} (with DataModel uncompressed ZIP_STORED and SecurityBindings purged)...")

    with zipfile.ZipFile(DST_PBIX, "w") as z_out:
        for fname, fbytes in files.items():
            zinfo = zipfile.ZipInfo(fname)
            if fname == "DataModel":
                zinfo.compress_type = zipfile.ZIP_STORED
            else:
                zinfo.compress_type = zipfile.ZIP_DEFLATED
            z_out.writestr(zinfo, fbytes)

    print(f"Successfully generated {DST_PBIX} (size: {DST_PBIX.stat().st_size:,} bytes).")


if __name__ == "__main__":
    build_page1()
