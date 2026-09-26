"""Graphiques interactifs avec unités et repères d'optimum."""

import plotly.graph_objects as go

from ppa.model import Result


BLUE = "#2563eb"
GREEN = "#059669"
ORANGE = "#ea580c"
GRAY = "#94a3b8"


def _layout(fig: go.Figure, title: str, x_title: str, y_title: str) -> go.Figure:
    fig.update_layout(title=title, xaxis_title=x_title, yaxis_title=y_title,
                      template="plotly_white", hovermode="closest", height=390,
                      margin=dict(l=25, r=20, t=55, b=30), legend_title_text="Légende")
    return fig


def curve(results: list[Result], field: str, title: str, unit: str,
          highlighted_k: int | None = None, threshold: float | None = None) -> go.Figure:
    x = [r.k for r in results]
    y = [getattr(r, field) for r in results]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers+text", name=title,
                             text=[f"{v:.3g}" for v in y], textposition="top center",
                             line=dict(color=BLUE, width=3), marker=dict(size=9),
                             customdata=x,
                             hovertemplate="k=%{customdata}<br>Valeur=%{y:.4g} " + unit + "<extra></extra>"))
    if threshold is not None:
        fig.add_hline(y=threshold, line_dash="dash", line_color=ORANGE,
                      annotation_text=f"T max = {threshold:g} µs")
    if highlighted_k is not None and highlighted_k in x:
        position = x.index(highlighted_k)
        fig.add_trace(go.Scatter(x=[highlighted_k], y=[y[position]], mode="markers",
                                 name=f"Optimum k={highlighted_k}",
                                 marker=dict(color=GREEN, size=17, symbol="star"),
                                 hovertemplate=f"Optimum k={highlighted_k}<br>%{{y:.4g}} {unit}<extra></extra>"))
    fig.update_xaxes(tickvals=x)
    return _layout(fig, title, "Parallélisme k", unit)


def tradeoff(results: list[Result], pareto: set[int], x_field: str, y_field: str,
             x_title: str, y_title: str) -> go.Figure:
    fig = go.Figure()
    for status, subset, color, symbol in (
        ("Pareto", [r for r in results if r.k in pareto], GREEN, "circle"),
        ("Dominée", [r for r in results if r.k not in pareto], GRAY, "x"),
    ):
        if not subset:
            continue
        fig.add_trace(go.Scatter(
            x=[getattr(r, x_field) for r in subset],
            y=[getattr(r, y_field) for r in subset],
            mode="markers+text", name=status,
            text=[f"k={r.k}" for r in subset], textposition="top center",
            marker=dict(size=13, color=color, symbol=symbol),
            customdata=[[r.k, "oui" if r.feasible else "non", r.area, r.time_us, r.energy_uj]
                        for r in subset],
            hovertemplate="k=%{customdata[0]}<br>Admissible : %{customdata[1]}"
                          "<br>Area : %{customdata[2]:.3g}"
                          "<br>T : %{customdata[3]:.3g} µs"
                          "<br>E : %{customdata[4]:.3g} µJ<extra></extra>"))
    return _layout(fig, f"{y_title} selon {x_title}", x_title, y_title)


def weight_heatmap(grid_x: list[float], grid_y: list[float], matrix: list[list[int | None]],
                   available_ks: list[int], alpha: float, beta: float) -> go.Figure:
    ks = sorted(set(available_ks))
    palette = ["#2563eb", "#059669", "#ea580c", "#9333ea", "#dc2626", "#0f766e", "#ca8a04"]
    colorscale = []
    for i, _ in enumerate(ks):
        color = palette[i % len(palette)]
        colorscale.extend([(i / len(ks), color), ((i + 1) / len(ks), color)])
    z = [[ks.index(k) + 0.5 if k is not None else None for k in row] for row in matrix]
    fig = go.Figure(go.Heatmap(x=grid_x, y=grid_y, z=z, zmin=0, zmax=len(ks),
                                colorscale=colorscale, hoverongaps=False,
                                colorbar=dict(title="k optimal", tickvals=[i + 0.5 for i in range(len(ks))],
                                              ticktext=[str(k) for k in ks]),
                                customdata=matrix,
                                hovertemplate="β=%{x:.2f}<br>α=%{y:.2f}<br>γ=1−α−β"
                                              "<br>k optimal=%{customdata}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[beta], y=[alpha], mode="markers", name="Poids actuels",
                             marker=dict(size=13, symbol="circle-open", color="black", line=dict(width=3)),
                             hovertemplate=f"α={alpha:.2f}, β={beta:.2f}<extra></extra>"))
    return _layout(fig, "Sensibilité du k optimal aux poids", "β — poids du temps", "α — poids de l'énergie")


def robustness_curve(values: list[tuple[float, int | None]], current_b: float) -> go.Figure:
    fig = go.Figure(go.Scatter(x=[b for b, _ in values], y=[k for _, k in values],
                               mode="lines", line=dict(color=BLUE, width=3, shape="hv"),
                               name="k énergie", hovertemplate="b=%{x:.3f} mW<br>k=%{y}<extra></extra>"))
    fig.add_vline(x=current_b, line_dash="dash", line_color=ORANGE,
                  annotation_text=f"b actuel = {current_b:g}")
    fig.update_yaxes(tickvals=sorted({k for _, k in values if k is not None}))
    return _layout(fig, "Robustesse de l'optimum énergétique", "b — coefficient quadratique (mW)", "k optimal")
