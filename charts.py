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
    fig = px.pie(
        df,
        names="Catégorie",
        values="Poids (%)",
        title=title,
        color_discrete_sequence=PALETTE,
        hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(**_LAYOUT, title_x=0.5)
    return fig


def bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=title,
        color=x_col,
        color_discrete_sequence=PALETTE,
        text=y_col,
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(**_LAYOUT, title_x=0.5, showlegend=False)
    fig.update_yaxes(title="Poids (%)", range=[0, df[y_col].max() * 1.2])
    fig.update_xaxes(title="")
    return fig


def geo_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition Géographique")


def currency_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition par Devise")


def holdings_chart(df: pd.DataFrame) -> go.Figure:
    return bar_chart(df, x_col="Titre", y_col="Poids (%)", title="Répartition par Action")


def category_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition par Catégorie")


def allocation_comparison_chart(client_df: pd.DataFrame, benchmark: dict[str, float], profile_label: str) -> go.Figure:
    # Toutes les catégories présentes dans l'un ou l'autre
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
    fig.update_layout(
        **_LAYOUT,
        title=f"Allocation client vs Benchmark {profile_label}% Equity",
        title_x=0.5,
        barmode="group",
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.15),
        yaxis=dict(title="Poids (%)", range=[0, max_val * 1.25]),
        xaxis=dict(title=""),
    )
    return fig
