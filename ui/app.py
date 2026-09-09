"""
Streamlit dashboard for the Order Triage Agent.

Usage:
    cd projects/order_triage_agent
    streamlit run ui/app.py
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

st.set_page_config(
    page_title="NorthPeak Order Triage Agent",
    page_icon="📦",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar — run controls
# ---------------------------------------------------------------------------

st.sidebar.title("📦 Order Triage Agent")
st.sidebar.markdown("**NorthPeak Commerce** · L2 Capstone")

page = st.sidebar.radio(
    "View",
    ["🎯 Triage a Ticket", "📋 Queue Results", "🚨 Escalation Queue", "📊 Stats"],
)

# ---------------------------------------------------------------------------
# Page: Triage a single ticket
# ---------------------------------------------------------------------------

if page == "🎯 Triage a Ticket":
    st.title("Triage a Support Ticket")
    st.caption("Runs the LangGraph agent on a single ticket in real time.")

    with st.form("triage_form"):
        col1, col2 = st.columns([1, 2])
        with col1:
            order_id = st.text_input("Order ID", value="ORD-DEMO-001")
            tier = st.selectbox("Customer Tier", ["standard", "plus", "premium"])
            status = st.selectbox("Status", ["new", "in_progress"])
        with col2:
            note = st.text_area(
                "Customer Note",
                value="I ordered a size 10 boot but received a size 8. I need the correct size.",
                height=120,
            )
        submitted = st.form_submit_button("Run Triage", type="primary")

    if submitted:
        from src.agent.graph import graph

        with st.spinner("Running triage agent..."):
            try:
                result = graph.invoke({
                    "order_id": order_id,
                    "customer_tier": tier,
                    "text_note": note,
                    "status": status,
                })
                st.success("Triage complete")
            except Exception as e:
                st.error(f"Agent error: {e}")
                result = None

        if result:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Category", result.get("category", "—"))
            col_b.metric("Priority", result.get("priority", "—"))
            route = result.get("route", "—")
            route_label = "🚨 Priya (Escalate)" if route == "priya" else "✏️ Marcus (Draft)"
            col_c.metric("Route", route_label)

            with st.expander("Rationale", expanded=True):
                st.write(result.get("rationale", "—"))

            if result.get("flags"):
                st.warning("Flags: " + ", ".join(result["flags"]))

            if result.get("draft_reply"):
                st.subheader("Draft Reply (for Marcus)")
                st.info(result["draft_reply"])

            if result.get("escalation_summary"):
                st.subheader("Escalation Summary (for Priya)")
                st.error(result["escalation_summary"])

            with st.expander("Full state JSON"):
                st.json({k: v for k, v in result.items() if v is not None})


# ---------------------------------------------------------------------------
# Page: Queue Results
# ---------------------------------------------------------------------------

elif page == "📋 Queue Results":
    st.title("Full Queue Triage Results")

    results_path = ROOT / "outputs" / "triage_results.json"
    if not results_path.exists():
        st.warning("No results yet. Run `python run_triage.py` first.")
    else:
        with open(results_path, encoding="utf-8") as f:
            results = json.load(f)

        import pandas as pd
        rows = []
        for r in results:
            rows.append({
                "Order ID":    r.get("order_id", ""),
                "Tier":        r.get("customer_tier", ""),
                "Category":    r.get("category", "ERROR"),
                "Priority":    r.get("priority", "—"),
                "Route":       r.get("route", "—"),
                "Flags":       ", ".join(r.get("flags") or []),
                "Rationale":   (r.get("rationale") or "")[:80],
            })
        df = pd.DataFrame(rows)

        col_f1, col_f2 = st.columns(2)
        route_filter = col_f1.selectbox("Filter by route", ["all", "marcus", "priya"])
        tier_filter = col_f2.selectbox("Filter by tier", ["all", "standard", "plus", "premium"])

        if route_filter != "all":
            df = df[df["Route"] == route_filter]
        if tier_filter != "all":
            df = df[df["Tier"] == tier_filter]

        st.dataframe(df, use_container_width=True)
        st.caption(f"Showing {len(df)} of {len(results)} tickets")


# ---------------------------------------------------------------------------
# Page: Escalation Queue
# ---------------------------------------------------------------------------

elif page == "🚨 Escalation Queue":
    st.title("Escalation Queue — Priya's View")

    results_path = ROOT / "outputs" / "triage_results.json"
    if not results_path.exists():
        st.warning("No results yet. Run `python run_triage.py` first.")
    else:
        with open(results_path, encoding="utf-8") as f:
            results = json.load(f)

        escalations = [r for r in results if r.get("route") == "priya"]
        st.metric("Tickets requiring Priya", len(escalations))

        for r in escalations:
            with st.expander(f"🚨 {r['order_id']} · {r.get('category','')} · {r.get('priority','')} · {r.get('customer_tier','')}"):
                st.write("**Customer note:**", r.get("text_note", ""))
                st.write("**Escalation summary:**", r.get("escalation_summary") or "*(not yet generated — run full triage)*")
                st.write("**Rationale:**", r.get("rationale", ""))
                if r.get("flags"):
                    st.warning("Flags: " + ", ".join(r["flags"]))


# ---------------------------------------------------------------------------
# Page: Stats
# ---------------------------------------------------------------------------

elif page == "📊 Stats":
    st.title("Queue Statistics")

    results_path = ROOT / "outputs" / "triage_results.json"
    if not results_path.exists():
        st.warning("No results yet. Run `python run_triage.py` first.")
    else:
        with open(results_path, encoding="utf-8") as f:
            results = json.load(f)

        import pandas as pd
        from collections import Counter

        valid = [r for r in results if "error" not in r]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tickets", len(results))
        col2.metric("→ Marcus (draft)", sum(1 for r in valid if r.get("route") == "marcus"))
        col3.metric("→ Priya (escalate)", sum(1 for r in valid if r.get("route") == "priya"))
        col4.metric("Flagged", sum(1 for r in valid if r.get("flags")))

        st.subheader("By Category")
        cat_counts = Counter(r.get("category") for r in valid)
        st.bar_chart(pd.Series(dict(cat_counts)).sort_values(ascending=False))

        st.subheader("By Priority")
        pri_counts = Counter(r.get("priority") for r in valid)
        st.bar_chart(pd.Series(dict(pri_counts)))

        eval_path = ROOT / "outputs" / "eval_results.json"
        if eval_path.exists():
            st.subheader("Evaluation vs Labeled Dev Set")
            with open(eval_path, encoding="utf-8") as f:
                ev = json.load(f)
            st.metric("Category accuracy", ev.get("category_accuracy", "—"))
            st.metric("Priority accuracy", ev.get("priority_accuracy", "—"))
            st.metric("Route accuracy",    ev.get("route_accuracy", "—"))
            st.dataframe(
                pd.DataFrame([
                    {"Category": k, "Accuracy": v}
                    for k, v in ev.get("per_category", {}).items()
                ]),
                use_container_width=True,
            )
