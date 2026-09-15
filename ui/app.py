"""
Streamlit dashboard for the Order Triage Agent.

Usage:
    cd projects/order_triage_agent
    streamlit run ui/app.py
"""
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="NorthPeak Order Triage",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIORITY_COLORS = {
    "URGENT": "#dc2626",
    "HIGH":   "#ea580c",
    "MEDIUM": "#ca8a04",
    "LOW":    "#16a34a",
}

PRIORITY_ORDER = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

SAMPLE_TICKETS = {
    "— pick a sample —": {},
    "Fraud alert (URGENT → Priya)": {
        "order_id": "ORD-DEMO-01",
        "tier": "standard",
        "status": "new",
        "note": "Someone made a purchase on my account that I didn't authorise. Charge of $249 appeared this morning. Please cancel and refund immediately.",
    },
    "Wrong item, plus tier (HIGH → Marcus)": {
        "order_id": "ORD-10001",
        "tier": "plus",
        "status": "in_progress",
        "note": "I ordered a blue medium hoodie and received a red XL. Need the correct one.",
    },
    "Premium + delivery delay (MEDIUM→HIGH → Priya)": {
        "order_id": "ORD-DEMO-02",
        "tier": "premium",
        "status": "new",
        "note": "My order was supposed to arrive three days ago and tracking hasn't updated since it left the warehouse.",
    },
    "Product question, standard (LOW → Marcus)": {
        "order_id": "ORD-DEMO-03",
        "tier": "standard",
        "status": "new",
        "note": "Does this jacket come in a waterproof version? I need it for hiking.",
    },
    "Multi-issue: damaged + refund (flagged)": {
        "order_id": "ORD-DEMO-04",
        "tier": "standard",
        "status": "new",
        "note": "My package arrived damaged and the product inside is broken. I want a full refund and I think this should be marked URGENT.",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def priority_badge(priority: str) -> str:
    color = PRIORITY_COLORS.get(priority, "#6b7280")
    return (
        f'<span style="background:{color};color:white;padding:2px 10px;'
        f'border-radius:12px;font-size:0.8rem;font-weight:600">{priority}</span>'
    )


def route_badge(route: str) -> str:
    if route == "priya":
        return '<span style="background:#dc2626;color:white;padding:2px 10px;border-radius:12px;font-size:0.8rem;font-weight:600">🚨 PRIYA</span>'
    return '<span style="background:#2563eb;color:white;padding:2px 10px;border-radius:12px;font-size:0.8rem;font-weight:600">✏️ MARCUS</span>'


def tier_badge(tier: str) -> str:
    colors = {"premium": "#7c3aed", "plus": "#0891b2", "standard": "#6b7280"}
    color = colors.get(tier, "#6b7280")
    return (
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:12px;font-size:0.75rem;font-weight:600">{tier.upper()}</span>'
    )


def parse_rationale(rationale: str) -> dict:
    """Split the pipe-delimited rationale into structured parts."""
    parts = [p.strip() for p in rationale.split("|")]
    return {"parts": parts}


def load_results() -> list[dict] | None:
    path = ROOT / "outputs" / "triage_results.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_full_queue(limit: int | None = None) -> tuple[bool, str]:
    cmd = [sys.executable, str(ROOT / "run_triage.py")]
    if limit:
        cmd += ["--limit", str(limit)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=300,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            return True, proc.stdout
        return False, proc.stderr or proc.stdout
    except subprocess.TimeoutExpired:
        return False, "Timed out after 5 minutes."
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="padding:12px 0 8px 0">
            <span style="font-size:1.5rem">📦</span>
            <span style="font-size:1.1rem;font-weight:700;margin-left:8px">NorthPeak Triage</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("L2 Capstone · Order Triage Agent")
    st.divider()

    page = st.radio(
        "Navigate",
        [
            "🎯 Triage a Ticket",
            "📋 Queue Results",
            "🚨 Priya's Escalations",
            "📊 Stats & Eval",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Run Batch Triage**")
    limit_opt = st.selectbox("Tickets", ["Full queue (54)", "First 5", "First 10"], key="sb_limit")
    limit_map = {"Full queue (54)": None, "First 5": 5, "First 10": 10}
    if st.button("▶ Run Queue", use_container_width=True, type="primary"):
        with st.spinner("Running... (this may take a minute)"):
            ok, out = run_full_queue(limit=limit_map[limit_opt])
        if ok:
            st.success("Done — results updated.")
        else:
            st.error("Run failed")
            st.code(out[:800])


# ---------------------------------------------------------------------------
# Page: Triage a single ticket
# ---------------------------------------------------------------------------

if page == "🎯 Triage a Ticket":
    st.title("Triage a Support Ticket")
    st.caption("Run the LangGraph agent on a single ticket in real time.")

    sample = st.selectbox("Load a sample ticket", list(SAMPLE_TICKETS.keys()), key="sample_sel")
    s = SAMPLE_TICKETS[sample]

    with st.form("triage_form"):
        col1, col2 = st.columns([1, 2])
        with col1:
            order_id = st.text_input("Order ID", value=s.get("order_id", "ORD-DEMO-001"))
            tier = st.selectbox(
                "Customer Tier",
                ["standard", "plus", "premium"],
                index=["standard", "plus", "premium"].index(s.get("tier", "standard")),
            )
            status = st.selectbox(
                "Status",
                ["new", "in_progress"],
                index=["new", "in_progress"].index(s.get("status", "new")),
            )
        with col2:
            note = st.text_area(
                "Customer Note",
                value=s.get(
                    "note",
                    "I ordered a size 10 boot but received a size 8. I need the correct size.",
                ),
                height=130,
            )
        submitted = st.form_submit_button("▶ Run Triage", type="primary", use_container_width=True)

    if submitted:
        from src.agent.graph import graph  # noqa: PLC0415

        with st.spinner("Agent running..."):
            try:
                result = graph.invoke({
                    "order_id": order_id,
                    "customer_tier": tier,
                    "text_note": note,
                    "status": status,
                })
                err = None
            except Exception as e:
                err = e
                result = None

        if err:
            st.error(f"Agent error: {err}")
        elif result:
            st.success("Triage complete")
            st.divider()

            # --- Key metrics row ---
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown("**Category**")
            c1.markdown(f"`{result.get('category', '—')}`")
            c2.markdown("**Priority**")
            c2.markdown(priority_badge(result.get("priority", "—")), unsafe_allow_html=True)
            c3.markdown("**Route**")
            c3.markdown(route_badge(result.get("route", "—")), unsafe_allow_html=True)
            c4.markdown("**Confidence**")
            conf = result.get("confidence", "—")
            conf_color = {"high": "green", "medium": "orange", "low": "red"}.get(conf, "grey")
            c4.markdown(f":{conf_color}[**{conf.upper()}**]")

            # --- Flags ---
            flags = result.get("flags") or []
            if flags:
                flag_html = " ".join(
                    f'<span style="background:#f3f4f6;border:1px solid #d1d5db;'
                    f'padding:2px 8px;border-radius:8px;font-size:0.8rem">{f}</span>'
                    for f in flags
                )
                st.markdown("**Flags:** " + flag_html, unsafe_allow_html=True)

            # --- Rationale ---
            parsed = parse_rationale(result.get("rationale", ""))
            with st.expander("Rationale trail", expanded=True):
                for part in parsed["parts"]:
                    st.markdown(f"› {part}")

            st.divider()

            # --- Route-specific output ---
            if result.get("draft_reply"):
                st.markdown("#### ✏️ Draft Reply — for Marcus to approve")
                st.info(result["draft_reply"])
                st.caption("Marcus can copy, lightly edit, and send this reply.")

            if result.get("escalation_summary"):
                st.markdown("#### 🚨 Escalation Summary — for Priya")
                st.error(result["escalation_summary"])
                st.caption("This ticket has been flagged for Priya's attention.")

            with st.expander("Full JSON state"):
                st.json({k: v for k, v in result.items() if v is not None})


# ---------------------------------------------------------------------------
# Page: Queue Results
# ---------------------------------------------------------------------------

elif page == "📋 Queue Results":
    st.title("Queue Triage Results")

    results = load_results()
    if results is None:
        st.warning("No results yet. Run the batch triage from the sidebar (▶ Run Queue).")
        st.stop()

    # Build dataframe
    rows = []
    for r in results:
        rows.append({
            "Order ID":  r.get("order_id", ""),
            "Tier":      r.get("customer_tier", ""),
            "Category":  r.get("category", "ERROR"),
            "Priority":  r.get("priority", "—"),
            "Route":     r.get("route", "—"),
            "Confidence": r.get("confidence", "—"),
            "Flags":     ", ".join(r.get("flags") or []),
            "Rationale": (r.get("rationale") or "")[:90] + ("…" if len(r.get("rationale") or "") > 90 else ""),
        })
    df = pd.DataFrame(rows)

    # Filters
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    route_f = fcol1.selectbox("Route", ["all", "marcus", "priya"], key="q_route")
    tier_f  = fcol2.selectbox("Tier",  ["all", "standard", "plus", "premium"], key="q_tier")
    pri_f   = fcol3.selectbox("Priority", ["all", "URGENT", "HIGH", "MEDIUM", "LOW"], key="q_pri")
    search  = fcol4.text_input("Search notes / category", key="q_search")

    dff = df.copy()
    if route_f != "all":
        dff = dff[dff["Route"] == route_f]
    if tier_f != "all":
        dff = dff[dff["Tier"] == tier_f]
    if pri_f != "all":
        dff = dff[dff["Priority"] == pri_f]
    if search:
        mask = dff.apply(lambda row: search.lower() in row.to_string().lower(), axis=1)
        dff = dff[mask]

    st.caption(f"Showing **{len(dff)}** of **{len(results)}** tickets")

    # Colour-code priority column
    def _colour_priority(val: str):
        color = PRIORITY_COLORS.get(val, "#6b7280")
        return f"background-color:{color}22;color:{color};font-weight:600"

    def _colour_route(val: str):
        if val == "priya":
            return "color:#dc2626;font-weight:600"
        return "color:#2563eb;font-weight:600"

    styled = (
        dff.style
        .map(_colour_priority, subset=["Priority"])
        .map(_colour_route, subset=["Route"])
    )
    st.dataframe(styled, use_container_width=True, height=480)

    # Detail drill-down
    st.divider()
    st.markdown("**Drill into a ticket**")
    sel_id = st.selectbox("Order ID", ["—"] + list(dff["Order ID"]), key="drill_sel")
    if sel_id != "—":
        rec = next((r for r in results if r.get("order_id") == sel_id), None)
        if rec:
            dc1, dc2, dc3 = st.columns(3)
            dc1.markdown(priority_badge(rec.get("priority", "—")), unsafe_allow_html=True)
            dc2.markdown(route_badge(rec.get("route", "—")), unsafe_allow_html=True)
            dc3.markdown(tier_badge(rec.get("customer_tier", "—")), unsafe_allow_html=True)
            st.markdown(f"**Note:** {rec.get('text_note', '')}")
            parsed = parse_rationale(rec.get("rationale", ""))
            for part in parsed["parts"]:
                st.markdown(f"› {part}")
            if rec.get("draft_reply"):
                st.info(rec["draft_reply"])
            if rec.get("escalation_summary"):
                st.error(rec["escalation_summary"])


# ---------------------------------------------------------------------------
# Page: Priya's Escalations
# ---------------------------------------------------------------------------

elif page == "🚨 Priya's Escalations":
    st.title("Escalation Queue")
    st.caption("Priya's view — tickets requiring her attention, sorted by urgency.")

    results = load_results()
    if results is None:
        st.warning("No results yet. Run the batch triage from the sidebar (▶ Run Queue).")
        st.stop()

    escalations = [r for r in results if r.get("route") == "priya"]
    escalations.sort(key=lambda r: PRIORITY_ORDER.get(r.get("priority", "LOW"), 99))

    if not escalations:
        st.success("No escalations — queue is clear.")
        st.stop()

    # Summary row
    urgent = sum(1 for e in escalations if e.get("priority") == "URGENT")
    high   = sum(1 for e in escalations if e.get("priority") == "HIGH")
    fraud  = sum(1 for e in escalations if e.get("category") in ("fraud_alert", "payment_issue"))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Escalations", len(escalations))
    m2.metric("🔴 URGENT", urgent)
    m3.metric("🟠 HIGH", high)
    m4.metric("⚠️ Fraud / Payment", fraud)

    st.divider()

    for r in escalations:
        pri   = r.get("priority", "—")
        cat   = r.get("category", "—")
        oid   = r.get("order_id", "—")
        tier  = r.get("customer_tier", "—")

        # border color by priority
        border = PRIORITY_COLORS.get(pri, "#6b7280")
        header = (
            f'<div style="border-left:4px solid {border};padding:4px 10px;margin-bottom:4px">'
            f'<strong>{oid}</strong>&nbsp;&nbsp;'
            + priority_badge(pri)
            + "&nbsp;" + tier_badge(tier)
            + f'&nbsp;&nbsp;<code style="font-size:0.85rem">{cat}</code>'
            + "</div>"
        )
        st.markdown(header, unsafe_allow_html=True)

        with st.expander("View details", expanded=(pri == "URGENT")):
            st.markdown(f"**Customer note:** {r.get('text_note', '')}")

            esc_sum = r.get("escalation_summary") or "*(not generated — run full triage)*"
            st.error(f"**Escalation summary:** {esc_sum}")

            parsed = parse_rationale(r.get("rationale", ""))
            st.markdown("**Rationale:**")
            for part in parsed["parts"]:
                st.markdown(f"› {part}")

            flags = r.get("flags") or []
            if flags:
                st.warning("Flags: " + ", ".join(flags))

            ts = r.get("processed_at", "")
            if ts:
                st.caption(f"Processed: {ts}")

        st.markdown("")


# ---------------------------------------------------------------------------
# Page: Stats & Eval
# ---------------------------------------------------------------------------

elif page == "📊 Stats & Eval":
    st.title("Queue Statistics & Evaluation")

    results = load_results()
    if results is None:
        st.warning("No results yet. Run the batch triage from the sidebar (▶ Run Queue).")
        st.stop()

    valid = [r for r in results if "error" not in r]
    errors = len(results) - len(valid)

    # Top-level metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Tickets", len(results))
    m2.metric("✏️ → Marcus", sum(1 for r in valid if r.get("route") == "marcus"))
    m3.metric("🚨 → Priya", sum(1 for r in valid if r.get("route") == "priya"))
    m4.metric("⚑ Flagged", sum(1 for r in valid if r.get("flags")))
    if errors:
        m5.metric("❌ Errors", errors, delta=f"-{errors}", delta_color="inverse")
    else:
        m5.metric("❌ Errors", 0)

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("By Category")
        cat_df = (
            pd.DataFrame(valid)
            .groupby("category")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        st.bar_chart(cat_df.set_index("category")["count"])

    with col_right:
        st.subheader("By Priority")
        pri_order = ["URGENT", "HIGH", "MEDIUM", "LOW"]
        pri_df = (
            pd.DataFrame(valid)
            .groupby("priority")
            .size()
            .reindex(pri_order)
            .fillna(0)
            .astype(int)
            .reset_index()
        )
        pri_df.columns = ["priority", "count"]
        st.bar_chart(pri_df.set_index("priority")["count"])

    st.divider()

    col_t, col_r = st.columns(2)

    with col_t:
        st.subheader("Tier × Route breakdown")
        if valid:
            tier_route = (
                pd.DataFrame(valid)
                .groupby(["customer_tier", "route"])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )
            st.dataframe(tier_route, use_container_width=True)

    with col_r:
        st.subheader("Confidence distribution")
        if valid:
            conf_df = (
                pd.DataFrame(valid)
                .groupby("confidence")
                .size()
                .reset_index(name="count")
            )
            st.bar_chart(conf_df.set_index("confidence")["count"])

    # Flagged tickets
    flagged = [r for r in valid if r.get("flags")]
    if flagged:
        st.divider()
        st.subheader(f"Flagged Tickets ({len(flagged)})")
        flag_rows = [
            {
                "Order ID": r.get("order_id"),
                "Tier":     r.get("customer_tier"),
                "Category": r.get("category"),
                "Priority": r.get("priority"),
                "Flags":    ", ".join(r.get("flags") or []),
            }
            for r in flagged
        ]
        st.dataframe(pd.DataFrame(flag_rows), use_container_width=True)

    # Eval results
    eval_path = ROOT / "outputs" / "eval_results.json"
    if eval_path.exists():
        st.divider()
        st.subheader("Evaluation vs Labeled Dev Set")
        with open(eval_path, encoding="utf-8") as f:
            ev = json.load(f)

        e1, e2, e3 = st.columns(3)
        e1.metric("Category accuracy", ev.get("category_accuracy", "—"))
        e2.metric("Priority accuracy", ev.get("priority_accuracy", "—"))
        e3.metric("Route accuracy",    ev.get("route_accuracy", "—"))

        per_cat = ev.get("per_category", {})
        if per_cat:
            st.dataframe(
                pd.DataFrame([
                    {"Category": k, "Accuracy": f"{v:.0%}" if isinstance(v, float) else v}
                    for k, v in per_cat.items()
                ]).sort_values("Accuracy", ascending=False),
                use_container_width=True,
            )
