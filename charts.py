import math
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

    # Pour les petites tranches : label sur deux lignes pour éviter la troncature
    display_labels = [
        l.replace("Gold and other commodities", "Gold and<br>other commodities") if v < 10 else l
        for l, v in zip(labels, values)
    ]

    textpositions = ["outside" if v < 10 else "inside" for v in values]

    fig = go.Figure(go.Pie(
        labels=display_labels,
        values=values,
        hole=0.35,
        textposition=textpositions,
        textinfo="percent+label",
        marker=dict(colors=PALETTE[:len(labels)]),
        insidetextorientation="radial",
        pull=[0.12 if v < 10 else 0 for v in values],
    ))

    layout = {**_LAYOUT, "margin": dict(l=60, r=60, t=80, b=40)}
    fig.update_layout(
        **layout,
        title=dict(text=title, x=0.5, y=0.97, xanchor="center", yanchor="top"),
    )
    return fig


def geo_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition Géographique (Equity uniquement)")


def currency_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition par Devise")


def category_chart(df: pd.DataFrame) -> go.Figure:
    return pie_chart(df, "Répartition par Catégorie")


def categorization_gauge(pct: float) -> go.Figure:
    fig = go.Figure()

    # Arc coloré en dégradé continu rouge → vert (200 segments)
    n = 200
    r_outer, r_inner = 1.0, 0.55
    for i in range(n):
        a1 = math.pi * (1 - i / n)
        a2 = math.pi * (1 - (i + 1) / n)
        pos = i / n * 100
        t = max(0.0, min(1.0, (pos - 70) / (95 - 70)))
        r_c = int(220 * max(0, 1 - t * 2)) if t <= 0.5 else 0
        g_c = int(220 * min(1, t * 2)) if t <= 0.5 else int(180 + 20 * (t - 0.5) * 2)
        color = f"rgb({r_c},{g_c},0)"
        xs = [r_inner * math.cos(a1), r_outer * math.cos(a1),
              r_outer * math.cos(a2), r_inner * math.cos(a2), r_inner * math.cos(a1)]
        ys = [r_inner * math.sin(a1), r_outer * math.sin(a1),
              r_outer * math.sin(a2), r_inner * math.sin(a2), r_inner * math.sin(a1)]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, fill="toself", fillcolor=color,
            line=dict(color=color, width=0),
            mode="lines", showlegend=False, hoverinfo="none",
        ))

    # Grande flèche triangulaire depuis le centre
    needle_angle = math.pi * (1 - pct / 100)
    needle_len = 0.82
    needle_width = 0.05
    perp = needle_angle + math.pi / 2
    x_tip = needle_len * math.cos(needle_angle)
    y_tip = needle_len * math.sin(needle_angle)
    fig.add_trace(go.Scatter(
        x=[needle_width * math.cos(perp), x_tip, -needle_width * math.cos(perp), needle_width * math.cos(perp)],
        y=[needle_width * math.sin(perp), y_tip, -needle_width * math.sin(perp), needle_width * math.sin(perp)],
        fill="toself", fillcolor="#1f4e79",
        line=dict(color="#1f4e79", width=1),
        mode="lines", showlegend=False, hoverinfo="none",
    ))

    # Cercle central
    theta = [i * 2 * math.pi / 60 for i in range(61)]
    fig.add_trace(go.Scatter(
        x=[0.07 * math.cos(t) for t in theta],
        y=[0.07 * math.sin(t) for t in theta],
        fill="toself", fillcolor="#1f4e79",
        line=dict(color="#1f4e79"), mode="lines",
        showlegend=False, hoverinfo="none",
    ))

    # Ticks
    for val, label in [(0, "0%"), (25, "25%"), (50, "50%"), (70, "70%"), (95, "95%"), (100, "100%")]:
        a = math.pi * (1 - val / 100)
        fig.add_annotation(
            x=1.22 * math.cos(a), y=1.22 * math.sin(a),
            text=label, showarrow=False,
            font=dict(size=10, color="#555", family="Arial"),
        )

    # Valeur centrale
    fig.add_annotation(
        x=0, y=-0.25, text=f"<b>{pct:.1f}%</b>",
        showarrow=False, font=dict(size=30, color="#1f4e79", family="Arial"),
    )
    fig.add_annotation(
        x=0, y=-0.48, text="Portefeuille correctement catégorisé",
        showarrow=False, font=dict(size=11, color="#555", family="Arial"),
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[-1.4, 1.4]),
        yaxis=dict(visible=False, range=[-0.65, 1.25], scaleanchor="x"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        showlegend=False,
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
