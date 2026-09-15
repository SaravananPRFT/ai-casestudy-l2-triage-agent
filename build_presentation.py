"""
Build NorthPeak Order Triage Agent — L2 Capstone evidence presentation.
Run:  python build_presentation.py
Output: outputs/NorthPeak_OrderTriage_Evidence.pptx
"""
from __future__ import annotations
import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
C_NAVY    = RGBColor(0x1E, 0x3A, 0x5F)   # slide backgrounds / headings
C_WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
C_ACCENT  = RGBColor(0x25, 0x63, 0xEB)   # blue accent (Marcus)
C_RED     = RGBColor(0xDC, 0x26, 0x26)   # urgent / priya
C_ORANGE  = RGBColor(0xEA, 0x58, 0x0C)   # high
C_YELLOW  = RGBColor(0xCA, 0x8A, 0x04)   # medium
C_GREEN   = RGBColor(0x16, 0xA3, 0x4A)   # low / pass
C_LIGHT   = RGBColor(0xF1, 0xF5, 0xF9)   # light bg cells
C_GRAY    = RGBColor(0x64, 0x74, 0x8B)   # subtitle text
C_PURPLE  = RGBColor(0x7C, 0x3A, 0xED)   # premium tier

W, H = Inches(13.33), Inches(7.5)        # 16:9 widescreen

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_prs() -> Presentation:
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    return prs

def blank_slide(prs: Presentation):
    layout = prs.slide_layouts[6]   # completely blank
    return prs.slides.add_slide(layout)

def fill_bg(slide, color: RGBColor):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_textbox(slide, text, x, y, w, h,
                font_size=18, bold=False, color=C_WHITE,
                align=PP_ALIGN.LEFT, italic=False):
    txb = slide.shapes.add_textbox(x, y, w, h)
    tf  = txb.text_frame
    tf.word_wrap = True
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(font_size)
    run.font.bold  = bold
    run.font.color.rgb = color
    run.font.italic = italic
    return txb

def add_rect(slide, x, y, w, h, fill: RGBColor, line: RGBColor | None = None):
    shape = slide.shapes.add_shape(
        1,   # MSO_SHAPE_TYPE.RECTANGLE
        x, y, w, h
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line:
        shape.line.color.rgb = line
    else:
        shape.line.fill.background()
    return shape

def add_rule(slide, y, color=C_ACCENT, width=Inches(11)):
    shape = slide.shapes.add_shape(1, Inches(1.17), y, width, Pt(2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()

# ---------------------------------------------------------------------------
# SLIDE 1 – Title
# ---------------------------------------------------------------------------

def slide_title(prs):
    s = blank_slide(prs)
    fill_bg(s, C_NAVY)

    # left accent bar
    add_rect(s, Inches(0), Inches(0), Inches(0.18), H, C_ACCENT)

    add_textbox(s, "📦  NorthPeak Order Triage Agent",
                Inches(0.5), Inches(1.6), Inches(12), Inches(1.2),
                font_size=38, bold=True, color=C_WHITE)

    add_textbox(s, "L2 Capstone — Agentic SDLC Evidence Pack",
                Inches(0.5), Inches(2.9), Inches(10), Inches(0.7),
                font_size=22, color=RGBColor(0xA5, 0xC8, 0xFF))

    add_rule(s, Inches(3.75))

    add_textbox(s, "LangGraph  ·  Claude API  ·  Streamlit  ·  Python 3.13",
                Inches(0.5), Inches(4.0), Inches(10), Inches(0.6),
                font_size=16, color=C_GRAY)

    add_textbox(s, "September 2026",
                Inches(0.5), Inches(4.7), Inches(4), Inches(0.5),
                font_size=14, color=C_GRAY)

# ---------------------------------------------------------------------------
# SLIDE 2 – Solution Overview
# ---------------------------------------------------------------------------

def slide_overview(prs):
    s = blank_slide(prs)
    fill_bg(s, C_WHITE)
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "Solution Overview", Inches(0.4), Inches(0.12),
                Inches(12), Inches(0.8), font_size=28, bold=True, color=C_WHITE)

    items = [
        ("🔗  LangGraph Agent",
         "Five-node pipeline: classify → route → draft / escalate → audit.\n"
         "Deterministic policy engine enforces routing rules; Claude API handles\n"
         "NLP classification and reply drafting."),
        ("🖥  Streamlit Dashboard (4 pages)",
         "• Triage a Ticket  — single-ticket real-time triage (Marcus)\n"
         "• Queue Results    — filterable batch results table\n"
         "• Priya's Escalations — urgency-sorted escalation queue\n"
         "• Stats & Eval     — charts, tier×route breakdown, accuracy"),
        ("🧪  Test Suite",
         "64 automated tests across 3 modules:\n"
         "policy_engine (45) · nodes (10) · agent_loop (9)"),
        ("📊  Evaluation",
         "Held-out labeled dev set (12 tickets): 100% accuracy on\n"
         "category, priority, and routing decisions."),
    ]

    box_w = Inches(5.6)
    positions = [
        (Inches(0.35), Inches(1.25)),
        (Inches(6.9),  Inches(1.25)),
        (Inches(0.35), Inches(4.1)),
        (Inches(6.9),  Inches(4.1)),
    ]

    for (title, body), (bx, by) in zip(items, positions):
        add_rect(s, bx, by, box_w, Inches(2.6), C_LIGHT)
        add_textbox(s, title, bx+Inches(0.15), by+Inches(0.1),
                    box_w-Inches(0.3), Inches(0.5),
                    font_size=14, bold=True, color=C_NAVY)
        add_textbox(s, body, bx+Inches(0.15), by+Inches(0.6),
                    box_w-Inches(0.3), Inches(1.9),
                    font_size=11, color=RGBColor(0x1E, 0x29, 0x3B))

# ---------------------------------------------------------------------------
# SLIDE 3 – Architecture / LangGraph Flow
# ---------------------------------------------------------------------------

def slide_arch(prs):
    s = blank_slide(prs)
    fill_bg(s, C_WHITE)
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "Architecture — LangGraph Pipeline", Inches(0.4), Inches(0.12),
                Inches(12), Inches(0.8), font_size=28, bold=True, color=C_WHITE)

    # Node boxes
    nodes = [
        ("CLASSIFY",  "Claude API\nNLP + category\nextraction",      C_ACCENT,  Inches(0.5)),
        ("ROUTE",     "Policy Engine\nPriority · Flags\nDest decision", C_NAVY,   Inches(3.0)),
        ("DRAFT",     "Claude API\nDraft reply\nfor Marcus",          C_ACCENT,  Inches(5.5)),
        ("ESCALATE",  "Claude API\nEscalation\nsummary → Priya",     C_RED,     Inches(5.5)),
        ("AUDIT",     "AuditLogger\nTimestamp ·\nJSONL write",        C_GRAY,    Inches(10.0)),
    ]

    node_y   = Inches(2.2)
    node_w   = Inches(2.1)
    node_h   = Inches(2.2)
    arrow_y  = Inches(3.3)

    for label, detail, color, bx in nodes:
        add_rect(s, bx, node_y, node_w, node_h, color)
        add_textbox(s, label, bx+Inches(0.1), node_y+Inches(0.1),
                    node_w-Inches(0.2), Inches(0.5),
                    font_size=13, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        add_textbox(s, detail, bx+Inches(0.1), node_y+Inches(0.6),
                    node_w-Inches(0.2), Inches(1.4),
                    font_size=10, color=C_WHITE, align=PP_ALIGN.CENTER)

    # Arrows (simple rectangles)
    for ax in [Inches(2.65), Inches(5.15)]:
        add_rect(s, ax, arrow_y, Inches(0.3), Inches(0.1), C_GRAY)

    # Condition label between ROUTE and DRAFT/ESCALATE
    add_textbox(s, "route == marcus", Inches(4.85), Inches(1.75),
                Inches(2.5), Inches(0.35), font_size=9, color=C_ACCENT, italic=True)
    add_textbox(s, "route == priya",  Inches(4.85), Inches(4.55),
                Inches(2.5), Inches(0.35), font_size=9, color=C_RED, italic=True)

    # Arrow from DRAFT and ESCALATE to AUDIT
    add_rect(s, Inches(7.65), Inches(3.3), Inches(2.3), Inches(0.1), C_GRAY)
    add_rect(s, Inches(9.95), Inches(2.2), Inches(0.1), Inches(2.2), C_GRAY)

    # Subtitle labels
    add_textbox(s, "INPUT: order_id · customer_tier · text_note · status",
                Inches(0.5), Inches(5.8), Inches(12), Inches(0.4),
                font_size=10, color=C_GRAY, italic=True)
    add_textbox(s, "OUTPUT: category · priority · route · rationale · draft_reply / escalation_summary · processed_at",
                Inches(0.5), Inches(6.2), Inches(12), Inches(0.4),
                font_size=10, color=C_GRAY, italic=True)

# ---------------------------------------------------------------------------
# SLIDE 4 – Unit Test Results
# ---------------------------------------------------------------------------

def slide_tests(prs):
    s = blank_slide(prs)
    fill_bg(s, C_WHITE)
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "Unit Test Results", Inches(0.4), Inches(0.12),
                Inches(12), Inches(0.8), font_size=28, bold=True, color=C_WHITE)

    # Big pass badge
    add_rect(s, Inches(0.5), Inches(1.2), Inches(3.8), Inches(2.0), C_GREEN)
    add_textbox(s, "64 / 64", Inches(0.5), Inches(1.35),
                Inches(3.8), Inches(1.0),
                font_size=40, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_textbox(s, "ALL PASSED  ✓", Inches(0.5), Inches(2.15),
                Inches(3.8), Inches(0.6),
                font_size=16, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

    add_textbox(s, "pytest 9.1.1  ·  Python 3.13  ·  1.02 s",
                Inches(0.5), Inches(3.35), Inches(3.8), Inches(0.4),
                font_size=11, color=C_GRAY, align=PP_ALIGN.CENTER, italic=True)

    # Breakdown table
    rows = [
        ("Test module",           "Tests", "Coverage area"),
        ("test_policy_engine.py", "45",    "Priority bumps · base priorities per category · routing logic · multi-issue tie-breaking"),
        ("test_nodes.py",         "10",    "route_node · audit_node · classify_node (happy path & fallback)"),
        ("test_agent_loop.py",    "9",     "End-to-end graph: Marcus/Priya routing · fraud · premium escalation · audit · error propagation"),
    ]

    col_x = [Inches(4.7), Inches(6.3), Inches(7.1)]
    col_w = [Inches(1.55), Inches(0.7), Inches(5.3)]
    row_h = Inches(0.6)
    start_y = Inches(1.25)

    for ri, row in enumerate(rows):
        row_y = start_y + ri * row_h
        bg = C_NAVY if ri == 0 else (C_LIGHT if ri % 2 == 0 else C_WHITE)
        fc = C_WHITE if ri == 0 else RGBColor(0x1E, 0x29, 0x3B)
        total_w = sum(col_w)
        add_rect(s, col_x[0], row_y, total_w, row_h, bg)
        for ci, (cx, cw, cell) in enumerate(zip(col_x, col_w, row)):
            add_textbox(s, cell, cx+Inches(0.08), row_y+Inches(0.08),
                        cw-Inches(0.1), row_h-Inches(0.1),
                        font_size=11 if ri > 0 else 12,
                        bold=(ri == 0), color=fc)

    # Test category breakdown
    add_textbox(s, "Test Categories", Inches(4.7), Inches(3.8),
                Inches(8.0), Inches(0.45),
                font_size=14, bold=True, color=C_NAVY)

    cats = [
        ("Priority bumps & base priorities",    "28 tests"),
        ("Routing decisions (Marcus / Priya)",   "12 tests"),
        ("End-to-end graph integration",          "9 tests"),
        ("Node unit tests (classify, audit, route)", "10 tests"),
        ("Multi-issue & tie-breaking edge cases", "5 tests"),
    ]
    for i, (cat, cnt) in enumerate(cats):
        cy = Inches(4.3) + i * Inches(0.52)
        add_rect(s, Inches(4.7), cy, Inches(7.5), Inches(0.48),
                 C_LIGHT if i % 2 == 0 else C_WHITE)
        add_textbox(s, cat, Inches(4.85), cy+Inches(0.08),
                    Inches(6.0), Inches(0.38), font_size=11,
                    color=RGBColor(0x1E, 0x29, 0x3B))
        add_textbox(s, cnt, Inches(11.3), cy+Inches(0.08),
                    Inches(0.9), Inches(0.38), font_size=11,
                    bold=True, color=C_ACCENT)

# ---------------------------------------------------------------------------
# SLIDE 5 – Eval Accuracy
# ---------------------------------------------------------------------------

def slide_eval(prs):
    s = blank_slide(prs)
    fill_bg(s, C_WHITE)
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "Evaluation Accuracy — Labeled Dev Set (12 tickets)",
                Inches(0.4), Inches(0.12), Inches(12), Inches(0.8),
                font_size=28, bold=True, color=C_WHITE)

    # 3 big metric boxes
    metrics = [
        ("Category\nAccuracy", "100%", "12 / 12"),
        ("Priority\nAccuracy",  "100%", "12 / 12"),
        ("Route\nAccuracy",     "100%", "12 / 12"),
    ]
    for i, (label, pct, frac) in enumerate(metrics):
        bx = Inches(0.5) + i * Inches(4.1)
        add_rect(s, bx, Inches(1.2), Inches(3.7), Inches(1.9), C_GREEN)
        add_textbox(s, pct,   bx, Inches(1.3),  Inches(3.7), Inches(0.9),
                    font_size=44, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        add_textbox(s, frac,  bx, Inches(2.1),  Inches(3.7), Inches(0.4),
                    font_size=13, color=C_WHITE, align=PP_ALIGN.CENTER)
        add_textbox(s, label, bx, Inches(2.55), Inches(3.7), Inches(0.55),
                    font_size=12, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

    # Per-category table
    add_textbox(s, "Per-Category Breakdown", Inches(0.5), Inches(3.35),
                Inches(12), Inches(0.45), font_size=14, bold=True, color=C_NAVY)

    per_cat = [
        ("address_change", "1/1 (100%)"), ("cancel_request", "1/1 (100%)"),
        ("damaged",        "2/2 (100%)"), ("delivery_delay", "1/1 (100%)"),
        ("fraud_alert",    "1/1 (100%)"), ("payment_issue",  "1/1 (100%)"),
        ("product_question","1/1 (100%)"),("refund_request", "1/1 (100%)"),
        ("subscription",   "1/1 (100%)"), ("wrong_item",     "2/2 (100%)"),
    ]

    col_w2 = Inches(2.4)
    row_h2 = Inches(0.46)
    per_row = 5
    for i, (cat, acc) in enumerate(per_cat):
        row = i // per_row
        col = i %  per_row
        bx  = Inches(0.5)  + col * (col_w2 + Inches(0.18))
        by  = Inches(3.85) + row * row_h2
        add_rect(s, bx, by, col_w2, row_h2-Inches(0.04), C_LIGHT)
        add_textbox(s, cat, bx+Inches(0.1), by+Inches(0.06),
                    col_w2*0.65, row_h2-Inches(0.1), font_size=10,
                    color=RGBColor(0x1E, 0x29, 0x3B))
        add_textbox(s, acc, bx+col_w2*0.65, by+Inches(0.06),
                    col_w2*0.35, row_h2-Inches(0.1), font_size=10,
                    bold=True, color=C_GREEN)

    add_textbox(s,
                "All 10 categories classified correctly at HIGH confidence on the 12-ticket held-out dev set.",
                Inches(0.5), Inches(6.95), Inches(12), Inches(0.4),
                font_size=11, color=C_GRAY, italic=True)

# ---------------------------------------------------------------------------
# SLIDE 6 – Batch Queue Summary
# ---------------------------------------------------------------------------

def slide_queue(prs):
    s = blank_slide(prs)
    fill_bg(s, C_WHITE)
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "Batch Queue Results — 54 Tickets Processed",
                Inches(0.4), Inches(0.12), Inches(12), Inches(0.8),
                font_size=28, bold=True, color=C_WHITE)

    # Top metrics row
    top_metrics = [
        ("54",  "Total tickets",      C_ACCENT),
        ("36",  "→ Marcus",           C_ACCENT),
        ("18",  "→ Priya (escalated)",C_RED),
        ("9",   "Flagged",            C_ORANGE),
        ("51",  "High confidence",    C_GREEN),
    ]
    for i, (val, lbl, col) in enumerate(top_metrics):
        bx = Inches(0.35) + i * Inches(2.58)
        add_rect(s, bx, Inches(1.15), Inches(2.3), Inches(1.4), col)
        add_textbox(s, val, bx, Inches(1.2), Inches(2.3), Inches(0.75),
                    font_size=34, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        add_textbox(s, lbl, bx, Inches(1.9), Inches(2.3), Inches(0.45),
                    font_size=10, color=C_WHITE, align=PP_ALIGN.CENTER)

    # Priority breakdown bar-like table
    add_textbox(s, "Priority Distribution", Inches(0.35), Inches(2.75),
                Inches(6.2), Inches(0.4), font_size=13, bold=True, color=C_NAVY)

    priorities = [
        ("URGENT", 15, C_RED),
        ("HIGH",   12, C_ORANGE),
        ("MEDIUM", 21, C_YELLOW),
        ("LOW",     6, C_GREEN),
    ]
    for i, (pri, cnt, col) in enumerate(priorities):
        by = Inches(3.2) + i * Inches(0.7)
        add_rect(s, Inches(0.35), by, Inches(1.3), Inches(0.55), col)
        add_textbox(s, pri, Inches(0.35), by+Inches(0.08),
                    Inches(1.3), Inches(0.45), font_size=11, bold=True,
                    color=C_WHITE, align=PP_ALIGN.CENTER)
        bar_w = Inches(cnt / 25 * 4.5)
        add_rect(s, Inches(1.7), by+Inches(0.1), bar_w, Inches(0.35), col)
        add_textbox(s, str(cnt), Inches(1.7)+bar_w+Inches(0.1), by+Inches(0.08),
                    Inches(0.5), Inches(0.4), font_size=11, bold=True, color=col)

    # Category breakdown
    add_textbox(s, "Category Distribution", Inches(7.0), Inches(2.75),
                Inches(6.0), Inches(0.4), font_size=13, bold=True, color=C_NAVY)

    categories = [
        ("fraud_alert",      7), ("refund_request", 7),
        ("damaged",          6), ("payment_issue",  6),
        ("wrong_item",       5), ("product_question",5),
        ("subscription",     5), ("delivery_delay",  5),
        ("address_change",   4), ("cancel_request",  4),
    ]
    for i, (cat, cnt) in enumerate(categories):
        row = i // 2
        col = i %  2
        bx = Inches(7.0) + col * Inches(3.0)
        by = Inches(3.2) + row * Inches(0.65)
        add_rect(s, bx, by, Inches(2.8), Inches(0.55), C_LIGHT if col == 0 else C_WHITE)
        add_textbox(s, cat, bx+Inches(0.1), by+Inches(0.1),
                    Inches(2.0), Inches(0.38), font_size=10,
                    color=RGBColor(0x1E, 0x29, 0x3B))
        add_textbox(s, str(cnt), bx+Inches(2.1), by+Inches(0.1),
                    Inches(0.5), Inches(0.38), font_size=11, bold=True, color=C_ACCENT)

    # Tier breakdown
    add_textbox(s, "Tier: Standard 27  ·  Plus 15  ·  Premium 12",
                Inches(0.35), Inches(6.85), Inches(12), Inches(0.4),
                font_size=12, color=C_GRAY, italic=True)

# ---------------------------------------------------------------------------
# SLIDE 7 – App: Triage a Ticket (Marcus)
# ---------------------------------------------------------------------------

def slide_app_triage(prs):
    s = blank_slide(prs)
    fill_bg(s, RGBColor(0xF8, 0xFA, 0xFC))
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "App — Page 1: Triage a Ticket  (Persona: Marcus, Tier-1 Agent)",
                Inches(0.4), Inches(0.12), Inches(12.5), Inches(0.8),
                font_size=22, bold=True, color=C_WHITE)

    # Sidebar panel
    add_rect(s, Inches(0), Inches(1.05), Inches(2.3), Inches(6.45), C_NAVY)
    add_textbox(s, "📦 NorthPeak\nTriage", Inches(0.1), Inches(1.15),
                Inches(2.1), Inches(0.6), font_size=12, bold=True, color=C_WHITE)
    for i, pg in enumerate(["▸ 🎯 Triage a Ticket", "  📋 Queue Results",
                              "  🚨 Priya's Escalations", "  📊 Stats & Eval"]):
        by = Inches(1.9) + i * Inches(0.45)
        bg = C_ACCENT if i == 0 else C_NAVY
        add_rect(s, Inches(0.05), by, Inches(2.2), Inches(0.42), bg)
        add_textbox(s, pg, Inches(0.12), by+Inches(0.05),
                    Inches(2.0), Inches(0.35), font_size=10,
                    bold=(i == 0), color=C_WHITE)

    # Main panel
    mx = Inches(2.45)
    add_textbox(s, "Triage a Support Ticket", mx, Inches(1.1),
                Inches(10.5), Inches(0.5), font_size=20, bold=True, color=C_NAVY)
    add_textbox(s, "Run the LangGraph agent on a single ticket in real time.",
                mx, Inches(1.6), Inches(10.5), Inches(0.35),
                font_size=11, color=C_GRAY)

    # Form
    add_rect(s, mx, Inches(2.0), Inches(10.5), Inches(1.5),
             RGBColor(0xEF, 0xF6, 0xFF))
    form_fields = [
        ("Order ID",      "ORD-DEMO-09",  Inches(2.6),  Inches(2.1)),
        ("Customer Tier", "premium",      Inches(5.3),  Inches(2.1)),
        ("Status",        "new",          Inches(7.7),  Inches(2.1)),
    ]
    for lbl, val, fx, fy in form_fields:
        add_textbox(s, lbl, fx, fy, Inches(2.2), Inches(0.28),
                    font_size=9, bold=True, color=C_NAVY)
        add_rect(s, fx, fy+Inches(0.28), Inches(2.1), Inches(0.35),
                 C_WHITE, C_GRAY)
        add_textbox(s, val, fx+Inches(0.05), fy+Inches(0.3),
                    Inches(2.0), Inches(0.3), font_size=10, color=C_NAVY)

    add_textbox(s, "Customer Note", mx+Inches(3.5), Inches(2.1),
                Inches(6.5), Inches(0.28), font_size=9, bold=True, color=C_NAVY)
    add_rect(s, mx+Inches(3.5), Inches(2.38), Inches(6.6), Inches(0.95),
             C_WHITE, C_GRAY)
    add_textbox(s,
                "The sneakers in the box are size 9, I ordered size 11. Please send the right size.",
                mx+Inches(3.6), Inches(2.42), Inches(6.4), Inches(0.85),
                font_size=10, color=C_NAVY)

    add_rect(s, mx+Inches(7.5), Inches(3.6), Inches(2.6), Inches(0.4), C_ACCENT)
    add_textbox(s, "▶  Run Triage", mx+Inches(7.5), Inches(3.63),
                Inches(2.6), Inches(0.35), font_size=11, bold=True,
                color=C_WHITE, align=PP_ALIGN.CENTER)

    # Result
    add_rule(s, Inches(4.15), C_GREEN, Inches(10.5))
    add_textbox(s, "✅  Triage complete", mx, Inches(4.2),
                Inches(3.5), Inches(0.4), font_size=12, bold=True, color=C_GREEN)

    result_cols = [
        ("Category",   "wrong_item",  C_NAVY),
        ("Priority",   "URGENT",      C_RED),
        ("Route",      "🚨 PRIYA",    C_RED),
        ("Confidence", "HIGH",        C_GREEN),
    ]
    for i, (lbl, val, col) in enumerate(result_cols):
        cx = mx + Inches(i * 2.6)
        add_textbox(s, lbl, cx, Inches(4.65), Inches(2.4), Inches(0.3),
                    font_size=9, bold=True, color=C_GRAY)
        add_rect(s, cx, Inches(5.0), Inches(2.3), Inches(0.45), col)
        add_textbox(s, val, cx, Inches(5.0), Inches(2.3), Inches(0.45),
                    font_size=12, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

    add_textbox(s,
                "Rationale: category=wrong_item confidence=high | premium-tier bump: HIGH→URGENT | "
                "premium customer with URGENT priority → escalate to Priya",
                mx, Inches(5.6), Inches(10.5), Inches(0.5),
                font_size=10, color=C_GRAY, italic=True)

    add_rect(s, mx, Inches(6.2), Inches(10.5), Inches(0.75),
             RGBColor(0xFF, 0xF1, 0xF2))
    add_textbox(s,
                "🚨  Escalation Summary — for Priya\n"
                "Premium customer ORD-DEMO-09 received wrong item (size 9 vs ordered size 11). "
                "Priority bumped to URGENT. Immediate replacement required.",
                mx+Inches(0.1), Inches(6.25), Inches(10.2), Inches(0.65),
                font_size=10, color=C_RED)

# ---------------------------------------------------------------------------
# SLIDE 8 – App: Priya's Escalations
# ---------------------------------------------------------------------------

def slide_app_priya(prs):
    s = blank_slide(prs)
    fill_bg(s, RGBColor(0xF8, 0xFA, 0xFC))
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "App — Page 3: Priya's Escalation Queue  (Persona: Priya, Escalations Lead)",
                Inches(0.4), Inches(0.12), Inches(12.5), Inches(0.8),
                font_size=22, bold=True, color=C_WHITE)

    # Sidebar
    add_rect(s, Inches(0), Inches(1.05), Inches(2.3), Inches(6.45), C_NAVY)
    add_textbox(s, "📦 NorthPeak\nTriage", Inches(0.1), Inches(1.15),
                Inches(2.1), Inches(0.6), font_size=12, bold=True, color=C_WHITE)
    for i, pg in enumerate(["  🎯 Triage a Ticket", "  📋 Queue Results",
                              "▸ 🚨 Priya's Escalations", "  📊 Stats & Eval"]):
        by = Inches(1.9) + i * Inches(0.45)
        bg = C_RED if i == 2 else C_NAVY
        add_rect(s, Inches(0.05), by, Inches(2.2), Inches(0.42), bg)
        add_textbox(s, pg, Inches(0.12), by+Inches(0.05),
                    Inches(2.0), Inches(0.35), font_size=10,
                    bold=(i == 2), color=C_WHITE)

    mx = Inches(2.45)
    add_textbox(s, "Escalation Queue", mx, Inches(1.1),
                Inches(10.5), Inches(0.5), font_size=20, bold=True, color=C_NAVY)
    add_textbox(s, "Tickets requiring Priya's attention — sorted by urgency.",
                mx, Inches(1.6), Inches(10.5), Inches(0.3),
                font_size=11, color=C_GRAY)

    # Summary metrics
    metric_items = [
        ("18", "Total Escalations", C_NAVY),
        ("15", "🔴 URGENT",         C_RED),
        ("3",  "🟠 HIGH",           C_ORANGE),
        ("13", "⚠️ Fraud/Payment",  C_ORANGE),
    ]
    for i, (val, lbl, col) in enumerate(metric_items):
        bx = mx + i * Inches(2.6)
        add_rect(s, bx, Inches(2.05), Inches(2.4), Inches(0.95), col)
        add_textbox(s, val, bx, Inches(2.1), Inches(2.4), Inches(0.5),
                    font_size=28, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        add_textbox(s, lbl, bx, Inches(2.6), Inches(2.4), Inches(0.35),
                    font_size=9, color=C_WHITE, align=PP_ALIGN.CENTER)

    add_rule(s, Inches(3.1), C_RED, Inches(10.5))

    # Sample escalation cards
    sample_tickets = [
        ("ORD-10009", "URGENT", "standard", "fraud_alert",
         "This order was placed on my account but I did not authorize it.",
         "Unauthorized transaction flagged — URGENT. Account security review required."),
        ("ORD-10011", "URGENT", "premium",  "wrong_item",
         "The sneakers in the box are size 9, I ordered size 11.",
         "Premium customer received wrong item — bumped to URGENT. Immediate replacement required."),
        ("ORD-10004", "URGENT", "standard", "payment_issue",
         "I was charged twice for the same order, please reverse the duplicate.",
         "Duplicate charge — money-movement rule → always escalate to Priya."),
    ]
    pri_colors = {"URGENT": C_RED, "HIGH": C_ORANGE}
    for i, (oid, pri, tier, cat, note, esc) in enumerate(sample_tickets):
        by = Inches(3.25) + i * Inches(1.35)
        col = pri_colors.get(pri, C_GRAY)
        add_rect(s, mx, by, Inches(0.06), Inches(1.2), col)
        add_rect(s, mx+Inches(0.1), by, Inches(10.3), Inches(1.2),
                 RGBColor(0xFF, 0xF1, 0xF2) if pri == "URGENT" else C_LIGHT)
        hdr = f"{oid}   [{pri}]  {tier.upper()}  {cat}"
        add_textbox(s, hdr, mx+Inches(0.2), by+Inches(0.05),
                    Inches(9.8), Inches(0.35), font_size=11, bold=True, color=col)
        add_textbox(s, f"Note: {note}", mx+Inches(0.2), by+Inches(0.4),
                    Inches(9.8), Inches(0.3), font_size=10,
                    color=RGBColor(0x1E, 0x29, 0x3B))
        add_textbox(s, f"↳ {esc}", mx+Inches(0.2), by+Inches(0.75),
                    Inches(9.8), Inches(0.35), font_size=10,
                    color=C_RED, italic=True)

# ---------------------------------------------------------------------------
# SLIDE 9 – App: Stats & Eval page
# ---------------------------------------------------------------------------

def slide_app_stats(prs):
    s = blank_slide(prs)
    fill_bg(s, RGBColor(0xF8, 0xFA, 0xFC))
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "App — Page 4: Stats & Eval  (Persona: Dev, Ops Manager)",
                Inches(0.4), Inches(0.12), Inches(12.5), Inches(0.8),
                font_size=22, bold=True, color=C_WHITE)

    # Sidebar
    add_rect(s, Inches(0), Inches(1.05), Inches(2.3), Inches(6.45), C_NAVY)
    add_textbox(s, "📦 NorthPeak\nTriage", Inches(0.1), Inches(1.15),
                Inches(2.1), Inches(0.6), font_size=12, bold=True, color=C_WHITE)
    for i, pg in enumerate(["  🎯 Triage a Ticket", "  📋 Queue Results",
                              "  🚨 Priya's Escalations", "▸ 📊 Stats & Eval"]):
        by = Inches(1.9) + i * Inches(0.45)
        bg = C_ACCENT if i == 3 else C_NAVY
        add_rect(s, Inches(0.05), by, Inches(2.2), Inches(0.42), bg)
        add_textbox(s, pg, Inches(0.12), by+Inches(0.05),
                    Inches(2.0), Inches(0.35), font_size=10,
                    bold=(i == 3), color=C_WHITE)

    mx = Inches(2.45)
    add_textbox(s, "Queue Statistics & Evaluation",
                mx, Inches(1.1), Inches(10.5), Inches(0.5),
                font_size=20, bold=True, color=C_NAVY)

    # Top metrics
    tm = [("54","Total"),("36","→ Marcus"),("18","→ Priya"),("9","Flagged"),("0","Errors")]
    for i,(v,l) in enumerate(tm):
        bx = mx + i*Inches(2.1)
        add_rect(s, bx, Inches(1.7), Inches(2.0), Inches(0.8),
                 C_GREEN if l=="Errors" else C_ACCENT if i<2 else C_RED if i==2 else C_ORANGE)
        add_textbox(s, v, bx, Inches(1.75), Inches(2.0), Inches(0.45),
                    font_size=22, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        add_textbox(s, l, bx, Inches(2.17), Inches(2.0), Inches(0.3),
                    font_size=8, color=C_WHITE, align=PP_ALIGN.CENTER)

    add_rule(s, Inches(2.62), C_GRAY, Inches(10.5))

    # Category bar chart (as horizontal bars)
    add_textbox(s, "By Category", mx, Inches(2.72),
                Inches(5.0), Inches(0.35), font_size=12, bold=True, color=C_NAVY)
    cats = [("fraud_alert",7),("refund_request",7),("damaged",6),("payment_issue",6),
            ("wrong_item",5),("product_question",5),("subscription",5),("delivery_delay",5),
            ("address_change",4),("cancel_request",4)]
    for i,(c,n) in enumerate(cats):
        by = Inches(3.12)+i*Inches(0.42)
        add_textbox(s, c, mx, by, Inches(1.7), Inches(0.38), font_size=8, color=C_NAVY)
        add_rect(s, mx+Inches(1.75), by+Inches(0.05),
                 Inches(n/7*2.8), Inches(0.3), C_ACCENT)
        add_textbox(s, str(n), mx+Inches(1.75)+Inches(n/7*2.8)+Inches(0.05),
                    by+Inches(0.05), Inches(0.3), Inches(0.3),
                    font_size=8, bold=True, color=C_ACCENT)

    # Priority bar chart
    add_textbox(s, "By Priority", mx+Inches(5.2), Inches(2.72),
                Inches(5.0), Inches(0.35), font_size=12, bold=True, color=C_NAVY)
    pris = [("URGENT",15,C_RED),("HIGH",12,C_ORANGE),("MEDIUM",21,C_YELLOW),("LOW",6,C_GREEN)]
    for i,(p,n,col) in enumerate(pris):
        by = Inches(3.12)+i*Inches(0.72)
        add_textbox(s, p, mx+Inches(5.2), by, Inches(1.0), Inches(0.38),
                    font_size=9, bold=True, color=col)
        add_rect(s, mx+Inches(6.3), by+Inches(0.05),
                 Inches(n/21*3.5), Inches(0.35), col)
        add_textbox(s, str(n), mx+Inches(6.35)+Inches(n/21*3.5),
                    by+Inches(0.05), Inches(0.35), Inches(0.35),
                    font_size=9, bold=True, color=col)

    # Eval accuracy row
    add_rule(s, Inches(6.05), C_GREEN, Inches(10.5))
    for i,(lbl,val) in enumerate([
        ("Category Accuracy","100% (12/12)"),
        ("Priority Accuracy", "100% (12/12)"),
        ("Route Accuracy",    "100% (12/12)"),
    ]):
        bx = mx + i*Inches(3.5)
        add_rect(s, bx, Inches(6.1), Inches(3.3), Inches(0.65), C_GREEN)
        add_textbox(s, lbl+":  "+val, bx+Inches(0.1), Inches(6.15),
                    Inches(3.1), Inches(0.55), font_size=11, bold=True,
                    color=C_WHITE, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------------------
# SLIDE 10 – Summary
# ---------------------------------------------------------------------------

def slide_summary(prs):
    s = blank_slide(prs)
    fill_bg(s, C_NAVY)
    add_rect(s, Inches(0), Inches(0), Inches(0.18), H, C_ACCENT)

    add_textbox(s, "Summary — What Was Delivered",
                Inches(0.5), Inches(0.5), Inches(12), Inches(0.8),
                font_size=32, bold=True, color=C_WHITE)
    add_rule(s, Inches(1.4))

    points = [
        ("✅  64 / 64 unit tests passing",
         "3 test modules — policy engine, nodes, end-to-end graph.  Runtime: 1.02 s."),
        ("✅  100% evaluation accuracy",
         "12-ticket labeled dev set: perfect category, priority & routing accuracy."),
        ("✅  54-ticket batch queue processed",
         "36 → Marcus  ·  18 → Priya  ·  9 flagged  ·  94% high-confidence classifications."),
        ("✅  4-page Streamlit dashboard",
         "Real-time triage · filterable queue · Priya's escalation view · stats & eval page."),
        ("✅  LangGraph 5-node pipeline",
         "classify → route → draft/escalate → audit, with deterministic policy engine."),
    ]

    for i, (title, detail) in enumerate(points):
        by = Inches(1.6) + i * Inches(1.0)
        add_rect(s, Inches(0.5), by, Inches(12.5), Inches(0.9),
                 RGBColor(0x1E, 0x3F, 0x6E) if i % 2 else RGBColor(0x16, 0x32, 0x5A))
        add_textbox(s, title, Inches(0.65), by+Inches(0.04),
                    Inches(12.0), Inches(0.38),
                    font_size=14, bold=True, color=C_WHITE)
        add_textbox(s, detail, Inches(0.65), by+Inches(0.44),
                    Inches(12.0), Inches(0.38),
                    font_size=11, color=RGBColor(0xA5, 0xC8, 0xFF))

    add_textbox(s, "NorthPeak Order Triage Agent  ·  L2 Capstone  ·  September 2026",
                Inches(0.5), Inches(7.1), Inches(12), Inches(0.35),
                font_size=10, color=C_GRAY, italic=True)

# ---------------------------------------------------------------------------
# SLIDE 11 – Competency Self-Assessment
# ---------------------------------------------------------------------------

def slide_competencies(prs):
    s = blank_slide(prs)
    fill_bg(s, C_WHITE)
    add_rect(s, Inches(0), Inches(0), Inches(13.33), Inches(1.05), C_NAVY)
    add_textbox(s, "Competencies Applied — Self-Assessment",
                Inches(0.4), Inches(0.12), Inches(12.5), Inches(0.8),
                font_size=28, bold=True, color=C_WHITE)

    rows = [
        ("Spec Driven Development\nSpec · Plan · Tasks · Implement",
         "Partially Applied",
         "specs/personas.md defined the three personas; DESIGN_NOTE.md captured architecture\n"
         "decisions — no formal Spec→Plan→Tasks→Implement loop tracked in the workflow.",
         C_YELLOW),
        ("AI-Powered Development\n(Claude Code / GitHub Copilot)",
         "Applied",
         "Claude Code was used throughout to build, debug, and iterate on the entire codebase.",
         C_GREEN),
        ("LLM Evaluation & Interpretability",
         "Applied",
         "eval/evaluate.py + outputs/eval_results.json — 100% accuracy metrics, per-category\n"
         "breakdown, and rationale trail on every ticket.",
         C_GREEN),
        ("Agent Design & Orchestration\n(n8n, LangGraph, LangChain, LlamaIndex)",
         "Applied",
         "Full LangGraph 5-node pipeline with conditional edges and deterministic policy engine.",
         C_GREEN),
        ("Agentic Operations\n— failure handling, recovery, observability",
         "Applied",
         "src/observability/audit_logger.py, timestamped JSONL audit trail,\n"
         "test_classify_failure_propagates test covering error propagation.",
         C_GREEN),
        ("AI Tool Integration & Extensibility\n(MCP, hooks, skills/tools)",
         "Partially Applied",
         "src/tools/lookup_tool.py and draft_tool.py are custom tools wired into the agent\n"
         "— no MCP server, hooks, or skills extensibility implemented.",
         C_YELLOW),
    ]

    # Column header
    hdr_y = Inches(1.1)
    hdr_h = Inches(0.42)
    col_x  = [Inches(0.35), Inches(4.3),  Inches(6.5)]
    col_w  = [Inches(3.85), Inches(2.1),  Inches(6.55)]
    hdrs   = ["Competency",  "Assessment", "Evidence / Reason"]
    for cx, cw, lbl in zip(col_x, col_w, hdrs):
        add_rect(s, cx, hdr_y, cw, hdr_h, C_NAVY)
        add_textbox(s, lbl, cx+Inches(0.1), hdr_y+Inches(0.07),
                    cw-Inches(0.15), hdr_h-Inches(0.1),
                    font_size=12, bold=True, color=C_WHITE)

    row_h = Inches(0.92)
    for ri, (comp, assess, reason, badge_color) in enumerate(rows):
        ry = Inches(1.55) + ri * row_h
        bg = C_LIGHT if ri % 2 == 0 else C_WHITE

        # Competency cell
        add_rect(s, col_x[0], ry, col_w[0], row_h - Inches(0.04), bg)
        add_textbox(s, comp, col_x[0]+Inches(0.1), ry+Inches(0.1),
                    col_w[0]-Inches(0.15), row_h-Inches(0.15),
                    font_size=10, bold=True, color=C_NAVY)

        # Assessment badge
        add_rect(s, col_x[1], ry, col_w[1], row_h - Inches(0.04), bg)
        badge_w = Inches(1.75)
        badge_h = Inches(0.38)
        bx = col_x[1] + (col_w[1] - badge_w) / 2
        by = ry + (row_h - badge_h) / 2 - Inches(0.04)
        add_rect(s, bx, by, badge_w, badge_h, badge_color)
        add_textbox(s, assess, bx, by+Inches(0.05),
                    badge_w, badge_h-Inches(0.05),
                    font_size=10, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)

        # Reason cell
        add_rect(s, col_x[2], ry, col_w[2], row_h - Inches(0.04), bg)
        add_textbox(s, reason, col_x[2]+Inches(0.1), ry+Inches(0.08),
                    col_w[2]-Inches(0.15), row_h-Inches(0.12),
                    font_size=9, color=RGBColor(0x1E, 0x29, 0x3B))

    add_textbox(s, "Green = Applied  ·  Yellow = Partially Applied",
                Inches(0.35), Inches(7.1), Inches(12), Inches(0.3),
                font_size=10, color=C_GRAY, italic=True)


# ---------------------------------------------------------------------------
# BUILD
# ---------------------------------------------------------------------------

def main():
    prs = new_prs()
    slide_title(prs)
    slide_overview(prs)
    slide_arch(prs)
    slide_tests(prs)
    slide_eval(prs)
    slide_queue(prs)
    slide_app_triage(prs)
    slide_app_priya(prs)
    slide_app_stats(prs)
    slide_competencies(prs)
    slide_summary(prs)

    out = Path("outputs") / "NorthPeak_OrderTriage_Evidence_v2.pptx"
    prs.save(str(out))
    print(f"Saved: {out}  ({out.stat().st_size // 1024} KB,  {len(prs.slides)} slides)")

if __name__ == "__main__":
    main()
