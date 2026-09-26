"""Application Streamlit du TIPE : optimisation du parallélisme PPA."""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ppa.model import DEFAULT_KS, Parameters, evaluate, evaluate_all
from ppa.optimization import NORMALIZATIONS, Weights, costs, energy_optimum, ppa_optimum
from ppa.pareto import pareto_ks
from ppa.sensitivity import power_quadratic_sweep, weight_map
from ui.charts import curve, robustness_curve, tradeoff, weight_heatmap
from ui.explanations import MODEL_NOTICE, theory


st.set_page_config(page_title="TIPE · Parallélisme et PPA", page_icon="⚡", layout="wide")


def reset() -> None:
    for key in list(st.session_state):
        if key.startswith("tipe_"):
            del st.session_state[key]


def rebalance_weights(changed: str) -> None:
    """Permet de déplacer chacun des trois curseurs tout en gardant une somme de 1."""
    keys = ["tipe_alpha", "tipe_beta", "tipe_gamma"]
    selected = f"tipe_{changed}"
    other = [key for key in keys if key != selected]
    remaining = 1.0 - st.session_state[selected]
    old_total = sum(st.session_state[key] for key in other)
    first = remaining * st.session_state[other[0]] / old_total if old_total else remaining / 2
    st.session_state[other[0]] = round(first, 2)
    st.session_state[other[1]] = round(remaining - st.session_state[other[0]], 2)


def parse_ks(raw: str, n: int) -> tuple[int, ...]:
    try:
        values = tuple(int(part.strip()) for part in raw.split(","))
    except ValueError as exc:
        raise ValueError("Saisir des entiers séparés par des virgules, par exemple 1, 2, 4, 8.") from exc
    if not values or len(set(values)) != len(values) or any(k < 1 or k > n for k in values):
        raise ValueError("Les valeurs de k doivent être distinctes et comprises entre 1 et N.")
    return tuple(sorted(values))


def sidebar() -> tuple[Parameters, Weights, str]:
    st.sidebar.title("Paramètres du TIPE")
    st.sidebar.button("Réinitialiser les paramètres du TIPE", on_click=reset,
                      width="stretch")
    with st.sidebar.expander("Calcul", expanded=True):
        n = st.number_input("Taille N", min_value=1, max_value=1_000_000,
                            value=1024, step=1, key="tipe_n")
        frequency = st.number_input("Fréquence f (MHz)", min_value=0.001,
                                    value=100.0, step=1.0, key="tipe_frequency")
        k_raw = st.text_input("Valeurs de k (séparées par des virgules)",
                              value=", ".join(map(str, DEFAULT_KS)), key="tipe_ks")
        t_max = st.number_input("T max (µs)", min_value=0.001,
                                value=3.0, step=0.1, key="tipe_tmax")
    with st.sidebar.expander("Modèle avancé : Power et Area"):
        st.caption("Coefficients de modèles pédagogiques, sans mesure matérielle.")
        p0 = st.number_input("P₀ (mW)", min_value=0.0, value=40.0, step=1.0, key="tipe_p0")
        pa = st.number_input("a — Power linéaire (mW)", min_value=0.0, value=8.0, step=0.5, key="tipe_pa")
        pb = st.number_input("b — Power quadratique (mW)", min_value=0.0, value=0.5,
                             step=0.1, key="tipe_pb")
        a0 = st.number_input("A₀ — Area fixe", min_value=0.0, value=100.0, step=1.0, key="tipe_a0")
        aa = st.number_input("c — Area linéaire", min_value=0.0, value=20.0, step=1.0, key="tipe_aa")
        ab = st.number_input("d — Area quadratique", min_value=0.0, value=1.0,
                             step=0.1, key="tipe_ab")
    with st.sidebar.expander("Optimisation", expanded=True):
        for key, value in (("tipe_alpha", 0.5), ("tipe_beta", 0.3), ("tipe_gamma", 0.2)):
            if key not in st.session_state:
                st.session_state[key] = value
        st.slider("α — énergie", 0.0, 1.0, step=0.01, key="tipe_alpha",
                  on_change=rebalance_weights, args=("alpha",))
        st.slider("β — temps", 0.0, 1.0, step=0.01, key="tipe_beta",
                  on_change=rebalance_weights, args=("beta",))
        st.slider("γ — Area", 0.0, 1.0, step=0.01, key="tipe_gamma",
                  on_change=rebalance_weights, args=("gamma",))
        st.caption(f"α + β + γ = {sum(st.session_state[k] for k in ('tipe_alpha', 'tipe_beta', 'tipe_gamma')):.2f}")
        normalization = st.selectbox("Référence de normalisation", NORMALIZATIONS,
                                     key="tipe_normalization")
    params = Parameters(
        n=int(n), frequency_mhz=float(frequency), t_max_us=float(t_max),
        ks=parse_ks(k_raw, int(n)), power_fixed_mw=float(p0), power_linear_mw=float(pa),
        power_quadratic_mw=float(pb), area_fixed=float(a0), area_linear=float(aa),
        area_quadratic=float(ab))
    weights = Weights(st.session_state.tipe_alpha, st.session_state.tipe_beta,
                      st.session_state.tipe_gamma)
    return params, weights, normalization


def table(results, costs_by_k, pareto, energy_k, ppa_k) -> pd.DataFrame:
    rows = []
    for r in results:
        labels = []
        if r.k == energy_k:
            labels.append("Énergie min")
        if r.k == ppa_k:
            labels.append("PPA optimal")
        rows.append({
            "k": r.k, "Cycles": r.cycles, "Temps (µs)": r.time_us,
            "Power (mW)": r.power_mw, "Énergie (µJ)": r.energy_uj,
            "Area (indice)": r.area, "Débit (Mop/s)": r.throughput_mops_s,
            "Opérations/J": r.operations_per_joule,
            "Performance/W (op/s/W)": r.performance_per_watt,
            "Coût PPA": costs_by_k[r.k], "Contrainte": "Accepté" if r.feasible else "Refusé",
            "Pareto": "Oui" if r.k in pareto else "Dominée", "Repère": " · ".join(labels),
        })
    return pd.DataFrame(rows)


try:
    parameters, weights, normalization = sidebar()
    results = evaluate_all(parameters)
    reference_k1 = evaluate(1, parameters)
    cost_by_k = costs(results, weights, normalization, reference_k1)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

energy_best = energy_optimum(results)
ppa_best = ppa_optimum(results, cost_by_k)
frontier = pareto_ks(results)
energy_k = energy_best.k if energy_best else None
ppa_k = ppa_best.k if ppa_best else None

st.title("⚡ Parallélisme et compromis PPA")
st.caption("TIPE · Sobriété, efficacité, optimisation · Produit scalaire · Simulation numérique")
st.info(MODEL_NOTICE)

overview, study, graphs, compromises, sensitivity, theory_tab = st.tabs([
    "Vue d’ensemble", "Étude PPA", "Graphiques", "Compromis PPA", "Sensibilité", "Théorie"
])

with overview:
    st.subheader("Question scientifique")
    st.write("Quel degré de parallélisme respecte le temps imposé tout en limitant l'énergie "
             "et les ressources ?")
    st.markdown("**Schéma conceptuel :** `N produits` → `k unités en parallèle` → "
                "`temps T` · `puissance P` · `Area A` → `énergie E = P × T` → "
                "`choix sous contrainte T ≤ T max`")
    st.caption(f"N = {parameters.n:,} · f = {parameters.frequency_mhz:g} MHz · "
               f"T max = {parameters.t_max_us:g} µs · k = {', '.join(map(str, parameters.ks))}")
    if ppa_best is None:
        st.warning("Aucune architecture ne respecte T max. Augmentez le seuil, la fréquence ou les valeurs de k.")
    else:
        st.success(f"Minimum d'énergie admissible : k={energy_k} · "
                   f"Minimum du coût PPA pondéré : k={ppa_k}. "
                   "Ces choix peuvent différer car le coût PPA tient aussi compte du temps et d'Area.")
    row1 = st.columns(3)
    row1[0].metric("k optimal PPA", str(ppa_k) if ppa_k is not None else "—")
    row1[1].metric("k optimal énergie", str(energy_k) if energy_k is not None else "—")
    row1[2].metric("Énergie minimale admissible", f"{energy_best.energy_uj:.3f} µJ" if energy_best else "—")
    row2 = st.columns(3)
    row2[0].metric("Temps à l'optimum énergie", f"{energy_best.time_us:.3f} µs" if energy_best else "—")
    row2[1].metric("Power à l'optimum énergie", f"{energy_best.power_mw:.1f} mW" if energy_best else "—")
    row2[2].metric("Area à l'optimum énergie", f"{energy_best.area:g}" if energy_best else "—")
    st.caption("Les trois dernières cartes décrivent l'optimum énergétique admissible. "
               "Si aucune architecture n'est admissible, aucun optimum contraint n'est défini.")

with study:
    st.subheader("Comparaison des architectures")
    st.write("Rouge : seuil non respecté. Vert : optimum énergétique admissible. "
             "Bleu : optimum PPA admissible. La colonne « Repère » conserve ces indications dans le CSV.")
    data = table(results, cost_by_k, frontier, energy_k, ppa_k)

    def highlight(row):
        if row["Contrainte"] == "Refusé":
            color = "#fee2e2"
        elif row["k"] == ppa_k and row["k"] == energy_k:
            color = "#dcfce7"
        elif row["k"] == ppa_k:
            color = "#dbeafe"
        elif row["k"] == energy_k:
            color = "#dcfce7"
        else:
            color = ""
        return [f"background-color: {color}" if color else "" for _ in row]

    st.dataframe(data.style.apply(highlight, axis=1).format({
        "Cycles": "{:.2f}", "Temps (µs)": "{:.3f}", "Power (mW)": "{:.2f}",
        "Énergie (µJ)": "{:.4f}", "Area (indice)": "{:.2f}",
        "Débit (Mop/s)": "{:.2f}", "Opérations/J": "{:.3e}",
        "Performance/W (op/s/W)": "{:.3e}", "Coût PPA": "{:.4f}",
    }), width="stretch", hide_index=True)
    with st.expander("Que signifient les métriques ?"):
        st.write("**Débit (Mop/s)** : nombre de multiplications du produit scalaire par seconde, en millions.")
        st.write("**Opérations/J** : nombre de multiplications obtenues pour un joule. Plus haut est meilleur.")
        st.write("**Performance/W (op/s/W)** : débit divisé par la puissance. "
                 "Elle est numériquement égale aux opérations/J dans ce modèle, car E = PT.")
        st.write("**Coût PPA** : somme pondérée et sans unité d'énergie, temps et Area normalisés. Plus bas est meilleur.")
    c1, c2 = st.columns(2)
    c1.download_button("Télécharger le tableau CSV", data.to_csv(index=False).encode("utf-8-sig"),
                       "resultats_ppa.csv", "text/csv", width="stretch")
    export = {"parameters": parameters.to_dict(), "weights": vars(weights),
              "normalization": normalization, "reference_k1": {
                  "energy_uj": reference_k1.energy_uj, "time_us": reference_k1.time_us,
                  "area": reference_k1.area}}
    c2.download_button("Télécharger les paramètres JSON", json.dumps(export, ensure_ascii=False, indent=2),
                       "parametres_ppa.json", "application/json", width="stretch")

with graphs:
    st.subheader("Effet de k sur les grandeurs du modèle")
    figures = [
        curve(results, "time_us", "Temps de calcul", "µs", threshold=parameters.t_max_us),
        curve(results, "power_mw", "Power", "mW"),
        curve(results, "energy_uj", "Énergie", "µJ", highlighted_k=energy_k),
        curve(results, "area", "Area", "indice de ressources"),
    ]
    # Le coût n'est pas un attribut de Result : on trace ses valeurs calculées séparément.
    cost_figure = go.Figure()
    cost_figure.add_trace(go.Scatter(x=[r.k for r in results], y=[cost_by_k[r.k] for r in results],
                                     mode="lines+markers+text", name="Coût PPA",
                                     text=[f"{cost_by_k[r.k]:.3f}" for r in results],
                                     textposition="top center", line=dict(color="#2563eb", width=3),
                                     marker=dict(size=9),
                                     hovertemplate="k=%{x}<br>C=%{y:.4f}<extra></extra>"))
    if ppa_k is not None:
        cost_figure.add_trace(go.Scatter(x=[ppa_k], y=[cost_by_k[ppa_k]], mode="markers",
                                         name=f"Optimum k={ppa_k}",
                                         marker=dict(color="#059669", size=17, symbol="star")))
    cost_figure.update_layout(title="Coût PPA pondéré", xaxis_title="Parallélisme k",
                              yaxis_title="Coût sans unité", template="plotly_white", height=390,
                              legend_title_text="Légende")
    cost_figure.update_xaxes(tickvals=[r.k for r in results])
    figures.append(cost_figure)
    for i in range(0, len(figures), 2):
        cols = st.columns(2)
        for j, fig in enumerate(figures[i:i + 2]):
            cols[j].plotly_chart(fig, width="stretch", key=f"graph_{i+j}")
    chart_index = st.selectbox("Exporter un graphique interactif en HTML", range(len(figures)),
                               format_func=lambda i: ["Temps", "Power", "Énergie", "Area", "Coût PPA"][i])
    st.download_button("Télécharger ce graphique", figures[chart_index].to_html(include_plotlyjs=True),
                       f"graphique_ppa_{chart_index+1}.html", "text/html")

with compromises:
    st.subheader("Compromis et frontière de Pareto")
    st.write("Une solution est dominée si une autre utilise au plus autant d'énergie et de ressources, "
             "tout en étant au moins aussi rapide, avec une amélioration stricte sur un critère. "
             "La frontière de Pareto est calculée sur toutes les valeurs de k ; le seuil T max "
             "reste indiqué dans les infobulles.")
    st.caption("Avec un Area strictement croissant et un temps strictement décroissant, "
               "tous les k sont naturellement non dominés : chacun échange du temps contre des ressources. "
               "Des points dominés peuvent apparaître si le coût Area devient constant.")
    st.write(f"**Solutions de Pareto :** {', '.join(f'k={k}' for k in sorted(frontier)) or 'aucune'}")
    st.write(f"**Solutions dominées :** {', '.join(f'k={r.k}' for r in results if r.k not in frontier) or 'aucune'}")
    pairs = [
        ("time_us", "energy_uj", "Temps (µs)", "Énergie (µJ)"),
        ("area", "energy_uj", "Area (indice)", "Énergie (µJ)"),
        ("area", "time_us", "Area (indice)", "Temps (µs)"),
    ]
    for i, (xf, yf, xl, yl) in enumerate(pairs):
        st.plotly_chart(tradeoff(results, frontier, xf, yf, xl, yl),
                        width="stretch", key=f"pareto_{i}")

with sensitivity:
    st.subheader("Sensibilité aux priorités")
    st.write("Les trois curseurs de la barre latérale gardent α + β + γ = 1. La carte balaie "
             "les couples valides (β, α) ; γ vaut 1 − α − β. Les zones blanches sont impossibles. "
             "Chaque case montre le meilleur k admissible ; la couleur est stable tant que les "
             "hypothèses du modèle restent identiques.")
    x_grid, y_grid, matrix = weight_map(results, normalization, reference_k1)
    if ppa_best:
        st.plotly_chart(weight_heatmap(x_grid, y_grid, matrix,
                                      [r.k for r in results if r.feasible],
                                      weights.alpha, weights.beta),
                        width="stretch", key="weight_heatmap")
    else:
        st.warning("Aucune architecture admissible : la carte de sensibilité n'a pas d'optimum.")
    st.subheader("Robustesse à l'hypothèse quadratique de Power")
    st.write("On fait varier b de 0 à 2 mW dans P(k) = P₀ + ak + bk², "
             "en conservant les autres paramètres et le seuil T max. "
             "Un changement de k optimal signale que la conclusion dépend de l'hypothèse choisie.")
    sweep = power_quadratic_sweep(parameters)
    st.plotly_chart(robustness_curve(sweep, parameters.power_quadratic_mw),
                    width="stretch", key="robustness")
    distinct = sorted({k for _, k in sweep if k is not None})
    st.caption(f"Optima observés sur ce balayage : {', '.join('k='+str(k) for k in distinct) or 'aucun'}.")

with theory_tab:
    theory()
