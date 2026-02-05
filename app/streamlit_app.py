import json
import pandas as pd
import streamlit as st
import plotly.express as px


st.set_page_config(page_title="AI Program OS Dashboard", layout="wide")


@st.cache_data
def load_snapshot(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_heatmap_csv(path: str):
    return pd.read_csv(path)


def band_counts(df):
    counts = df["band"].value_counts().to_dict()
    return {
        "Green": counts.get("Green", 0),
        "Yellow": counts.get("Yellow", 0),
        "Red": counts.get("Red", 0),
    }


st.title("AI Program Operating System — Portfolio Dashboard")

# Paths (local default)
snapshot_path = st.sidebar.text_input("Snapshot JSON path", "prototype/snapshot_from_csv.json")
heatmap_path = st.sidebar.text_input("Heatmap CSV path", "outputs/portfolio_heatmap.csv")

snap = load_snapshot(snapshot_path)
week_ending = snap.get("portfolio", {}).get("week_ending", "unknown")
inits = snap.get("initiatives", [])

df = pd.DataFrame(inits)
if df.empty:
    st.error("No initiatives found in snapshot. Check the JSON path.")
    st.stop()

# KPIs
counts = band_counts(df)
avg_dcs = float(df["dcs_current"].mean())
worst = df.sort_values("dcs_current").iloc[0]
best = df.sort_values("dcs_current", ascending=False).iloc[0]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Week Ending", week_ending)
k2.metric("Initiatives", len(df))
k3.metric("Avg Confidence", f"{avg_dcs:.1f}")
k4.metric("Bands", f"G:{counts['Green']}  Y:{counts['Yellow']}  R:{counts['Red']}")
k5.metric("Worst / Best", f"{worst['dcs_current']} / {best['dcs_current']}")

st.divider()

left, mid, right = st.columns([1.1, 2.2, 1.1])

with left:
    st.subheader("Portfolio View")
    # Band distribution
    band_df = pd.DataFrame(
        [{"band": "Green", "count": counts["Green"]},
         {"band": "Yellow", "count": counts["Yellow"]},
         {"band": "Red", "count": counts["Red"]}]
    )
    fig_band = px.bar(band_df, x="band", y="count", title="Confidence Bands")
    st.plotly_chart(fig_band, use_container_width=True)

    # Top movers (delta)
    df["delta"] = df["dcs_current"] - df["dcs_prior"]
    movers = df.sort_values("delta").head(3)[["name", "dcs_current", "delta", "days_to_target"]]
    st.markdown("**Largest Declines (Top 3)**")
    st.dataframe(movers, use_container_width=True, hide_index=True)

with mid:
    st.subheader("Risk Driver Heatmap")
    hm = load_heatmap_csv(heatmap_path)
    if hm.empty:
        st.warning("Heatmap CSV is empty. Check file path.")
    else:
        # Plotly heatmap expects numeric matrix
        labels = [c for c in hm.columns if c != "Initiative"]
        hm_matrix = hm[labels]
        fig_hm = px.imshow(
            hm_matrix,
            x=labels,
            y=hm["Initiative"],
            title="Initiatives × Risk Drivers (0–10)",
            aspect="auto"
        )
        st.plotly_chart(fig_hm, use_container_width=True)

with right:
    st.subheader("Initiative Drilldown")
    names = df["name"].tolist()
    selected = st.selectbox("Select initiative", names, index=0)

    row = df[df["name"] == selected].iloc[0].to_dict()

    st.markdown(f"**Confidence:** {row['band']} ({row['dcs_current']} / prior {row['dcs_prior']})")
    st.markdown(f"**Days to target:** {row['days_to_target']}")
    st.markdown(f"**Blocked days:** {row['blocked_days']}")
    st.markdown(f"**Scope changes (14d):** {row['scope_changes_14d']}")
    st.markdown(f"**Dependencies:** {row['dependency_count']} {'(critical)' if row['critical_dependency'] else ''}")
    st.markdown(f"**Stagnation (days):** {row['days_stagnant']}")

    st.markdown("**Notes**")
    notes = row.get("status_notes", []) or []
    if isinstance(notes, str):
        # handle if notes accidentally stored as string
        notes = [notes]
    if notes:
        for n in notes:
            st.write(f"- {n}")
    else:
        st.write("- (none)")

st.caption("This dashboard is a demo layer on top of deterministic portfolio signals (snapshot + derived heatmap).")
