import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PBIX = ROOT / "powerbi" / "F1_Analytics_Dev_Page3_Loc.pbix"
DST_PBIX = ROOT / "powerbi" / "F1_Analytics_Dev_Page1_Phuc.pbix"

PAGE1_ID = "3ae902435eec8d3460c0"  # Overview page (Phúc)
PAGE2_ID = "83e5ad66db596ac7559e"  # Thành tích & Biến động (Dung)
# Lộc's pages to be completely removed from Phúc's code and report:
PAGE3_ID = "c671a9ea38005deac8ed"  # Trường đua & Kết quả (Lộc - REMOVED)
PAGE4_ID = "a7d3f0c1b9e24d5f8c61"  # Hồ sơ trường đua (Lộc - REMOVED)
LOC_PAGES = {PAGE3_ID, PAGE4_ID}


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
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#475569'"}}}}},
                        "textSize": {"expr": {"Literal": {"Value": "9D"}}},
                        "text": {"expr": {"Literal": {"Value": f"'{display_name}'"}}}
                    }
                }],
                "items": [{
                    "properties": {
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}},
                        "background": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
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
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#CBD5E1'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "8D"}}}
                    }
                }],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def make_action_button(name, x, y, z, w, h, text, action_type="PageNavigation", target_page=None, fill_color="#E10600", outline_color="#E10600", font_color="#FFFFFF"):
    link_props = {
        "show": {"expr": {"Literal": {"Value": "true"}}},
        "type": {"expr": {"Literal": {"Value": f"'{action_type}'"}}}
    }
    if target_page:
        link_props["page"] = {"expr": {"Literal": {"Value": f"'{target_page}'"}}}

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
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{font_color}'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "10D"}}},
                        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}}
                    },
                    "selector": {"id": "default"}
                }],
                "outline": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "lineColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{outline_color}'"}}}}},
                        "lineWeight": {"expr": {"Literal": {"Value": "1D"}}},
                        "radius": {"expr": {"Literal": {"Value": "8D"}}}
                    },
                    "selector": {"id": "default"}
                }],
                "fill": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "fillColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{fill_color}'"}}}}},
                        "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                    },
                    "selector": {"id": "default"}
                }]
            },
            "visualContainerObjects": {
                "visualLink": [{"properties": link_props}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "drillFilterOtherVisuals": True
    }


def make_card(name, x, y, z, w, h, projection_field, query_ref, native_query_ref, display_name, fmt="#,0", value_color="#0F172A"):
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
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{value_color}'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "22D"}}},
                        "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                        "labelDisplayUnits": {"expr": {"Literal": {"Value": "1D"}}}
                    }
                }],
                "categoryLabels": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#64748B'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "9.5D"}}}
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
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}},
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
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#64748B'"}}}}}
                    }
                }],
                "valueAxis": [{
                    "properties": {
                        "showAxisTitle": {"expr": {"Literal": {"Value": "true"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#64748B'"}}}}},
                        "gridlineShow": {"expr": {"Literal": {"Value": "true"}}},
                        "gridlineColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F1F5F9'"}}}}}
                    }
                }],
                "legend": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "position": {"expr": {"Literal": {"Value": "'TopRight'"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "9.5D"}}},
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#334155'"}}}}}
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
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }],
                "title": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "text": {"expr": {"Literal": {"Value": "'Xu hướng quy mô giải đấu & số lượt tham gia qua các mùa giải (1950–2026)'"}}},
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "11.5D"}}},
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
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#334155'"}}}}}
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
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}}
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
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }],
                "title": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "text": {"expr": {"Literal": {"Value": "'Top 10 Tay đua có nhiều chiến thắng nhất lịch sử F1'"}}},
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "11.5D"}}},
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
                        "fontSize": {"expr": {"Literal": {"Value": "9.5D"}}},
                        "labelColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#475569'"}}}}}
                    }
                }],
                "labels": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "labelStyle": {"expr": {"Literal": {"Value": "'Both'"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "9.5D"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}}
                    }
                }],
                "dataPoint": [
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#059669'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'CLASSIFIED'"}}}}}]}
                    },
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E10600'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'RETIREMENT_DNF'"}}}}}]}
                    },
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F59E0B'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'DNS'"}}}}}]}
                    },
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#7C3AED'"}}}}}},
                        "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dw DimStatus"}}, "Property": "outcome_group"}}, "Right": {"Literal": {"Value": "'DSQ'"}}}}}]}
                    },
                    {
                        "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#94A3B8'"}}}}}},
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
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}},
                        "radius": {"expr": {"Literal": {"Value": "10D"}}}
                    }
                }],
                "title": [{
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "text": {"expr": {"Literal": {"Value": "'Cơ cấu phân bổ kết quả thi đấu (5 nhóm Outcome)'"}}},
                        "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}},
                        "fontSize": {"expr": {"Literal": {"Value": "11.5D"}}},
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

    # 1. PURGE LOC'S PAGES COMPLETELY:
    # Remove files belonging to Loc's Page 3 (Trường đua & Kết quả) and Page 4 (Hồ sơ trường đua)
    print(f"Purging Loc's pages ({PAGE3_ID}, {PAGE4_ID}) from report definition...")
    files = {
        name: fbytes for name, fbytes in files.items()
        if not any(f"pages/{p_id}/" in name for p_id in LOC_PAGES)
    }

    # Update pages.json: exclude Loc's pages from pageOrder, active page = PAGE1_ID (Overview)
    pages_meta = json.loads(files["Report/definition/pages/pages.json"].decode("utf-8"))
    pages_meta["pageOrder"] = [p for p in pages_meta.get("pageOrder", []) if p not in LOC_PAGES]
    pages_meta["activePageName"] = PAGE1_ID
    files["Report/definition/pages/pages.json"] = json.dumps(pages_meta, ensure_ascii=False, indent=2).encode("utf-8")

    # 2. SET OVERVIEW CANVAS LIGHT BACKGROUND (same light base #F4F7FC as other tabs):
    page1_meta = json.loads(files[f"Report/definition/pages/{PAGE1_ID}/page.json"].decode("utf-8"))
    page1_meta["displayName"] = "Overview"
    page1_meta["objects"] = {
        "background": [{
            "properties": {
                "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F4F7FC'"}}}}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}}
            }
        }],
        "outspace": [{
            "properties": {
                "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F4F7FC'"}}}}}
            }
        }]
    }
    files[f"Report/definition/pages/{PAGE1_ID}/page.json"] = json.dumps(page1_meta, ensure_ascii=False, indent=2).encode("utf-8")

    # 3. GENERATE OVERVIEW VISUALS (MODERN LIGHT EXECUTIVE BENTO LAYOUT):
    # Completely different from Loc's blue banner and horizontal stripes:
    # - Header: Clean White Floating Card (x=24, y=14, w=1872, h=80) with F1 Red Left Pill
    # - Left Column (x=24, w=516): 6 KPI Cards in a 2x3 Grid + Historical Regulation Guide below
    # - Right Column (x=556, w=1340): Widescreen Macro Trend Line Chart top + Bottom Top 10 Drivers & Outcome Donut
    visuals = {}

    # 1. Header Floating Container (White card, sleek border, radius 10D)
    v_hdr_bg = make_textbox("p1_v01_hdr_bg", 24, 14, 0, 1872, 80, [
        {"textRuns": [{"value": " ", "textStyle": {"fontSize": "4pt", "color": "#FFFFFF"}}]}
    ], bg_color="#FFFFFF", border_color="#E2E8F0", radius=10)
    visuals["p1_v01_hdr_bg"] = v_hdr_bg

    # 2. Header F1 Red Left Pill Accent (x=24, y=14, w=6, h=80)
    v_hdr_accent = make_textbox("p1_v02_hdr_accent", 24, 14, 1, 6, 80, [
        {"textRuns": [{"value": " ", "textStyle": {"fontSize": "1pt", "color": "#E10600"}}]}
    ], bg_color="#E10600", radius=3)
    visuals["p1_v02_hdr_accent"] = v_hdr_accent

    # 3. Header Title (Clean single title, perfectly centered vertically in header)
    v_hdr_title = make_textbox("p1_v03_hdr_title", 48, 28, 2, 840, 52, [
        {
            "textRuns": [
                {"value": "FORMULA 1 WORLD CHAMPIONSHIP : LỊCH SỬ & QUY MÔ (1950–2026)", "textStyle": {"fontSize": "16pt", "color": "#0F172A", "fontFamily": "Segoe UI Semibold", "fontWeight": "bold"}}
            ]
        }
    ])
    visuals["p1_v03_hdr_title"] = v_hdr_title

    # 4. Slicers in Header (x=900 and x=1095)
    v_sl_season = make_slicer("p1_v04_sl_season", 900, 20, 50, 180, 68, "dw DimRace", "season_year", "Mùa giải")
    visuals["p1_v04_sl_season"] = v_sl_season

    v_sl_constructor = make_slicer("p1_v05_sl_constructor", 1095, 20, 51, 220, 68, "dw DimConstructor", "constructor_name", "Đội đua")
    visuals["p1_v05_sl_constructor"] = v_sl_constructor

    # 5. Header Action Buttons (Reset Slicers & Navigate to Page 2 only)
    v_btn_reset = make_action_button("p1_v06_btn_reset", 1330, 26, 52, 160, 54, "↺ Xóa bộ lọc", action_type="ClearAllSlicers", fill_color="#F8FAFC", outline_color="#CBD5E1", font_color="#334155")
    visuals["p1_v06_btn_reset"] = v_btn_reset

    v_btn_p2 = make_action_button("p1_v07_btn_p2", 1505, 26, 53, 375, 54, "Khám phá Trang 2: Thành tích & Biến động ➔", action_type="PageNavigation", target_page=PAGE2_ID, fill_color="#E10600", outline_color="#E10600", font_color="#FFFFFF")
    visuals["p1_v07_btn_p2"] = v_btn_p2

    # 6. LEFT SECTION: 6 KPI Cards arranged in a 2-Column x 3-Row Grid (w=252 each)
    # Row 1 (y=106, h=106): Races & Entries
    card_race_proj = {
        "Aggregation": {
            "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": "dw FactRaceResult"}}, "Property": "race_sk"}},
            "Function": 2
        }
    }
    v_c_races = make_card("p1_v08_c_races", 24, 106, 100, 252, 106, card_race_proj, "CountNonNull(dw FactRaceResult.race_sk)", "race_sk", "Tổng chặng Grand Prix", "#,0", value_color="#0284C7")
    visuals["p1_v08_c_races"] = v_c_races

    card_ent_proj = {
        "Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Total Entries"}
    }
    v_c_entries = make_card("p1_v09_c_entries", 288, 106, 110, 252, 106, card_ent_proj, "_Measures.Total Entries", "Total Entries", "Tổng lượt tham gia", "#,0", value_color="#0F172A")
    visuals["p1_v09_c_entries"] = v_c_entries

    # Row 2 (y=224, h=106): Classified Rate & Total Points
    card_class_proj = {
        "Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Classified Rate"}
    }
    v_c_class = make_card("p1_v10_c_class", 24, 224, 120, 252, 106, card_class_proj, "_Measures.Classified Rate", "Classified Rate", "Tỷ lệ hoàn thành (Classified)", "0.0%", value_color="#059669")
    visuals["p1_v10_c_class"] = v_c_class

    card_pts_proj = {
        "Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": "Total Points"}
    }
    v_c_points = make_card("p1_v11_c_points", 288, 224, 130, 252, 106, card_pts_proj, "_Measures.Total Points", "Total Points", "Tổng điểm số lịch sử", "#,0.00", value_color="#D97706")
    visuals["p1_v11_c_points"] = v_c_points

    # Row 3 (y=342, h=106): Total Drivers & Constructors
    card_drv_proj = {
        "Aggregation": {
            "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": "dw FactRaceResult"}}, "Property": "driver_sk"}},
            "Function": 2
        }
    }
    v_c_drivers = make_card("p1_v12_c_drivers", 24, 342, 140, 252, 106, card_drv_proj, "CountNonNull(dw FactRaceResult.driver_sk)", "driver_sk", "Tổng số tay đua", "#,0", value_color="#7C3AED")
    visuals["p1_v12_c_drivers"] = v_c_drivers

    card_con_proj = {
        "Aggregation": {
            "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": "dw FactRaceResult"}}, "Property": "constructor_sk"}},
            "Function": 2
        }
    }
    v_c_constructors = make_card("p1_v13_c_constructors", 288, 342, 150, 252, 106, card_con_proj, "CountNonNull(dw FactRaceResult.constructor_sk)", "constructor_sk", "Tổng số đội đua", "#,0", value_color="#E11D48")
    visuals["p1_v13_c_constructors"] = v_c_constructors

    # 7. LEFT BOTTOM: Historical Scoring Context Footnote (x=24, y=460, w=516, h=574)
    caveat_paragraphs = [
        {
            "textRuns": [
                {"value": "HƯỚNG DẪN NGỮ CẢNH: HỆ THỐNG TÍNH ĐIỂM F1\n\n", "textStyle": {"fontSize": "11pt", "fontWeight": "bold", "color": "#0F172A", "fontFamily": "Segoe UI Semibold"}},
                {"value": "Hệ thống thang điểm F1 đã thay đổi sâu sắc qua 77 năm lịch sử:\n\n", "textStyle": {"fontSize": "9.5pt", "color": "#334155"}},
                {"value": "• 1950–1960: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#0284C7"}},
                {"value": "Thắng 8đ, tính điểm Top 5 (8-6-4-3-2), +1đ Fastest Lap.\n\n", "textStyle": {"fontSize": "9.5pt", "color": "#475569"}},
                {"value": "• 1961–1990: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#0284C7"}},
                {"value": "Thắng 9đ, tính điểm Top 6 (9-6-4-3-2-1), bỏ Fastest Lap.\n\n", "textStyle": {"fontSize": "9.5pt", "color": "#475569"}},
                {"value": "• 1991–2002: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#0284C7"}},
                {"value": "Thắng 10đ, tính điểm Top 6 (10-6-4-3-2-1).\n\n", "textStyle": {"fontSize": "9.5pt", "color": "#475569"}},
                {"value": "• 2003–2009: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#0284C7"}},
                {"value": "Thắng 10đ, mở rộng điểm cho Top 8 (10-8-6-5-4-3-2-1).\n\n", "textStyle": {"fontSize": "9.5pt", "color": "#475569"}},
                {"value": "• 2010–2018: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#0284C7"}},
                {"value": "Thắng 25đ, mở rộng cho Top 10 (25-18-15-12-10-8-6-4-2-1).\n\n", "textStyle": {"fontSize": "9.5pt", "color": "#475569"}},
                {"value": "• 2019–2026: ", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#0284C7"}},
                {"value": "Bổ sung 1đ cho Fastest Lap (áp dụng cho xe Top 10).\n\n", "textStyle": {"fontSize": "9.5pt", "color": "#475569"}},
                {"value": "⚠️ Khuyến cáo phân tích:\n", "textStyle": {"fontSize": "9.5pt", "fontWeight": "bold", "color": "#DC2626"}},
                {"value": "Tuyệt đối không so sánh trực tiếp tổng điểm số thô giữa các mùa giải thuộc các kỷ nguyên khác nhau mà không có chuẩn hóa hoặc tỷ lệ phần trăm tương đối.", "textStyle": {"fontSize": "9.5pt", "fontStyle": "italic", "color": "#64748B"}}
            ]
        }
    ]
    v_caveat = make_textbox("p1_v17_caveat", 24, 460, 230, 516, 574, caveat_paragraphs, bg_color="#FFFFFF", border_color="#E2E8F0", radius=10)
    visuals["p1_v17_caveat"] = v_caveat

    # 8. RIGHT TOP: Macro Trend Widescreen Line Chart (x=556, y=106, w=1340, h=450)
    v_line_trend = make_macro_trend_line_chart("p1_v14_macro_trend", 556, 106, 200, 1340, 450)
    visuals["p1_v14_macro_trend"] = v_line_trend

    # 9. RIGHT BOTTOM LEFT: Top 10 Drivers by Wins (x=556, y=568, w=780, h=466)
    v_top_drivers = make_top_drivers_chart("p1_v15_top_drivers", 556, 568, 210, 780, 466)
    visuals["p1_v15_top_drivers"] = v_top_drivers

    # 10. RIGHT BOTTOM RIGHT: Outcome Group Donut Chart (x=1352, y=568, w=544, h=466)
    v_donut_outcome = make_donut_chart("p1_v16_outcome_donut", 1352, 568, 220, 544, 466)
    visuals["p1_v16_outcome_donut"] = v_donut_outcome

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
