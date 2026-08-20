from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from dashboard_data import DEFAULT_API_URL, format_currency, load_dashboard_bundle


st.set_page_config(page_title="Imaginarium Dashboard", layout="wide")
st_autorefresh(interval=30_000, key="imaginarium-dashboard-refresh")


def _default_api_url() -> str:
    return st.secrets.get("api_url", os.getenv("IMAGINARIUM_API_URL", DEFAULT_API_URL))


st.title("Imaginarium Revenue & Business Progress Dashboard")
st.caption("Auto-refreshes every 30 seconds. Figures are informational and should be checked before filing returns.")

with st.sidebar:
    base_url = st.text_input("API URL", value=_default_api_url())
    activity_type = st.selectbox("Activity filter", options=["all", "sales", "expenses", "product", "marketing", "agent", "tax"], index=0)
    activity_days = st.slider("Activity lookback (days)", min_value=7, max_value=90, value=30, step=1)

try:
    data = load_dashboard_bundle(base_url, activity_type=activity_type, activity_days=activity_days)
except Exception as exc:  # pragma: no cover - streamlit runtime path
    st.error(f"Dashboard data could not be loaded from {base_url}: {exc}")
    st.stop()

summary = data["summary"]
products_payload = data["products"]
forecast = data["forecast"]
agents_payload = data["agents"]
activity_payload = data["activity"]

revenue = summary["revenue"]
tax = summary["tax"]
financial = summary["financial_health"]
products = pd.DataFrame(products_payload["products"])
agents = pd.DataFrame(agents_payload["agents"])
morale_trend = pd.DataFrame(agents_payload["morale_trend"])
activity = pd.DataFrame(activity_payload["items"])

metric_columns = st.columns(5)
metric_columns[0].metric("Current balance", summary["current_balance_gbp"])
metric_columns[1].metric("Today's revenue", revenue["today_net_gbp"])
metric_columns[2].metric("This week", revenue["week_net_gbp"], f"{revenue['week_change_pct']}%")
metric_columns[3].metric("This month", revenue["month_net_gbp"], f"{revenue['month_change_pct']}%")
metric_columns[4].metric("YTD net", revenue["ytd_net_gbp"])

left, right = st.columns((2, 1))
with left:
    velocity = pd.DataFrame([
        {"period": "Day", "value_gbp": revenue["velocity"]["daily_pence"] / 100},
        {"period": "Week", "value_gbp": revenue["velocity"]["weekly_pence"] / 100},
        {"period": "Month", "value_gbp": revenue["velocity"]["monthly_pence"] / 100},
    ])
    st.subheader("Revenue velocity")
    st.plotly_chart(px.bar(velocity, x="period", y="value_gbp", text_auto=".2f"), use_container_width=True)
with right:
    st.subheader("Alerts")
    if summary["alerts"]:
        for alert in summary["alerts"]:
            st.warning(alert["message"])
    else:
        st.success("No active alerts.")

st.subheader("Milestone progress")
for milestone in summary["milestones"]:
    st.write(f"**{milestone['label']}** — {milestone['current_gbp']} / {milestone['target_gbp']}")
    st.progress(min(100, int(round(milestone["progress_pct"]))) / 100)
    status = "Achieved" if milestone["achieved"] else f"Need {milestone['remaining_gbp']} more"
    eta = f" • ETA: {milestone['projected_date']}" if milestone["projected_date"] else ""
    st.caption(f"{status}{eta}")

tax_col, health_col = st.columns(2)
with tax_col:
    st.subheader("Tax & compliance")
    st.metric("Trading allowance used", tax["trading_allowance_used_gbp"])
    st.progress(min(100, int(round(tax["trading_allowance_progress_pct"]))) / 100)
    st.write(tax["position"])
    st.write(f"Estimated tax due: **{tax['estimated_tax_due_gbp']}**")
    st.write(f"Best deduction route right now: **{tax['deduction_strategy']}**")
    deadlines = pd.DataFrame([
        {"deadline": "Self Assessment registration", **tax["deadlines"]["self_assessment_registration"]},
        {"deadline": "Self Assessment filing", **tax["deadlines"]["self_assessment_filing"]},
        {"deadline": "VAT registration", **tax["deadlines"]["vat_registration"]},
    ])
    st.dataframe(deadlines, use_container_width=True, hide_index=True)
with health_col:
    st.subheader("Financial health")
    st.metric("Profit margin", f"{financial['profit_margin_pct']}%")
    st.metric("Reinvestment budget", financial["reinvestment_budget_gbp"])
    st.metric("Burn rate / day", financial["burn_rate_gbp_per_day"])
    runway = "∞" if financial["runway_days"] is None else str(financial["runway_days"])
    st.metric("Runway", runway)

st.subheader("Product performance")
if not products.empty:
    product_pie = products[products["revenue_all_time_pence"] > 0]
    if not product_pie.empty:
        st.plotly_chart(
            px.pie(
                product_pie.assign(revenue_gbp=product_pie["revenue_all_time_pence"] / 100),
                names="product_name",
                values="revenue_gbp",
            ),
            use_container_width=True,
        )
    view_products = products[[
        "product_name",
        "status",
        "sales_count_this_month",
        "sales_count_all_time",
        "revenue_this_month_pence",
        "revenue_all_time_pence",
        "average_price_pence",
        "is_new",
        "is_underperformer",
    ]].copy()
    for column in ("revenue_this_month_pence", "revenue_all_time_pence", "average_price_pence"):
        view_products[column] = view_products[column].map(format_currency)
    st.dataframe(view_products, use_container_width=True, hide_index=True)
    st.download_button(
        "Export product performance CSV",
        data=products.to_csv(index=False),
        file_name="imaginarium-product-performance.csv",
        mime="text/csv",
    )
else:
    st.info("No product proposals recorded yet.")

forecast_col, agents_col = st.columns(2)
with forecast_col:
    st.subheader("Growth projections")
    projections = pd.DataFrame(forecast["projections"])
    projections["projected_revenue_gbp"] = projections["projected_revenue_pence"].map(format_currency)
    st.dataframe(projections[["days", "projected_revenue_gbp"]], use_container_width=True, hide_index=True)
    st.write("**What-if scenarios**")
    for scenario in forecast["what_if_scenarios"]:
        st.write(f"- {scenario['name']}: {scenario['projected_date'] or 'No ETA yet'}")
with agents_col:
    st.subheader("Agent performance & morale")
    if not agents.empty:
        display_agents = agents.copy()
        display_agents["contribution_to_revenue_pence"] = display_agents["contribution_to_revenue_pence"].map(
            lambda value: format_currency(value) if value is not None else "N/A"
        )
        st.dataframe(display_agents, use_container_width=True, hide_index=True)
    if not morale_trend.empty:
        st.plotly_chart(px.line(morale_trend, x="date", y="average_morale"), use_container_width=True)

st.subheader("Recent activity")
if not activity.empty:
    st.dataframe(activity, use_container_width=True, hide_index=True)
    st.download_button(
        "Export activity CSV",
        data=activity.to_csv(index=False),
        file_name="imaginarium-activity-feed.csv",
        mime="text/csv",
    )
else:
    st.info("No recent activity found for the selected filters.")
