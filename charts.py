import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

PALETTE = px.colors.qualitative.Set2

_LAYOUT = dict(
    font=dict(family="Arial", size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="v", x=1.02, y=0.5),
    margin=dict(l=20, r=20, t=50, b=20),
)


def pie_chart(df: pd.DataFrame, title: str) -> go.Figure:
    labels = df["Catégorie"].tolist()
    values = df["Poids (%)"].tolist()

    # Labels outside with arrow for slices < 10%, inside otherwise
    textpositions = ["outside" if v < 10 else "inside" for v in values]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.35,
        textposition=textpositions,
        textinfo="percent+label",
        marker=dict(colors=PALETTE[:len(labels)]),
        insidetextorientation="radial",
    ))
    fig.update_traces(
        pull=[0.05 if v < 10 else 0 for v in values],
    )
    fig.update_layout(
        **_LAYOUT,
        title=dict(text=title, x=0.5),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def geo_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition Géographique (Equity uniquement)")


def currency_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition par Devise")


def category_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition par Catégorie")


def categorization_gauge(pct: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 28, "color": "#1f4e79"}},
        title={"text": "Portefeuille correctement catégorisé", "font": {"size": 14, "color": "#1f4e79"}},
        gauge={
            "axis": {"range": [0, 100], "ticksuffix": "%", "tickfont": {"size": 11}},
            "bar": {"color": "#1f4e79", "thickness": 0.25},
            "steps": [
                {"range": [0, 33],   "color": "#d73027"},
                {"range": [33, 66],  "color": "#fee08b"},
                {"range": [66, 85],  "color": "#a6d96a"},
                {"range": [85, 100], "color": "#1a9641"},
            ],
            "threshold": {
                "line": {"color": "#1f4e79", "width": 4},
                "thickness": 0.75,
                "value": pct,
            },
            "shape": "angular",
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial"),
        margin=dict(l=30, r=30, t=60, b=20),
        height=280,
    )
    return fig


def allocation_comparison_chart(client_df: pd.DataFrame, benchmark: dict[str, float], profile_label: str) -> go.Figure:
    all_cats = sorted(set(client_df["Catégorie"].tolist()) | set(benchmark.keys()))

    client_map = dict(zip(client_df["Catégorie"], client_df["Poids (%)"]))
    client_vals = [round(client_map.get(c, 0), 2) for c in all_cats]
    bench_vals = [round(benchmark.get(c, 0), 2) for c in all_cats]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Portefeuille client",
        x=all_cats,
        y=client_vals,
        text=[f"{v:.1f}%" for v in client_vals],
        textposition="outside",
        marker_color="#2e75b6",
    ))
    fig.add_trace(go.Bar(
        name=f"Benchmark ({profile_label}% Equity)",
        x=all_cats,
        y=bench_vals,
        text=[f"{v:.1f}%" for v in bench_vals],
        textposition="outside",
        marker_color="#ed7d31",
    ))

    max_val = max(client_vals + bench_vals + [1])
    layout = {**_LAYOUT, "legend": dict(orientation="h", x=0.5, xanchor="center", y=-0.15)}
    fig.update_layout(
        **layout,
        title=f"Allocation client vs Benchmark {profile_label}% Equity",
        title_x=0.5,
        barmode="group",
        yaxis=dict(title="Poids (%)", range=[0, max_val * 1.25]),
        xaxis=dict(title=""),
    )
    return fig
