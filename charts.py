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
