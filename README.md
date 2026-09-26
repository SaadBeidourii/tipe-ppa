# TIPE — Parallélisme et compromis Power, Performance, Area

Application Python interactive pour étudier, **sans FPGA ni logiciel propriétaire**, le degré de parallélisme d'un produit scalaire. Elle sert de support pédagogique au thème « Sobriété, efficacité, optimisation ».

Ce projet de simulation est indépendant du script expérimental Mac déjà présent dans le dossier parent. Les nombres affichés par l'application proviennent exclusivement des équations ci-dessous.

## Démarrage

Depuis le dossier `tipe-ppa` :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Sous Windows, l'activation est `.venv\Scripts\activate`. Pour lancer les tests :

```bash
python -m pytest -q
```

## Question scientifique

Comment choisir un degré de parallélisme `k` qui respecte un temps limite `T_max`, tout en réduisant énergie et ressources ? Le produit scalaire est `S = Σ aᵢbᵢ`, avec par défaut `N = 1024`, `f = 100 MHz`, `k ∈ {1,2,4,8,16,32}` et `T_max = 3 µs`.

## Modèles et unités

- Cycles idéaux : `N/k` ; temps : `T(k) = N/(kf)` en µs si `f` est en MHz.
- Power : `P(k) = P₀ + ak + bk²` en mW, initialement `40 + 8k + 0,5k²`.
- Area : `A(k) = A₀ + ck + dk²`, initialement `100 + 20k + k²`. C'est un **indice abstrait de ressources**, jamais un nombre réel de LUT.
- Énergie : `E(k) = P(k)T(k)` ; `mW × µs / 1000 = µJ`.
- Débit : `N/T` en millions d'opérations/s ; efficacité énergétique : `N/E` en opérations/J ; performance par watt : débit/puissance en opérations/s/W. Les deux dernières sont égales puisque `E = PT`.
- Coût PPA : `C(k) = α E/E_ref + β T/T_ref + γ A/A_ref`, avec `α+β+γ=1`. Les références sont, au choix, les valeurs à `k=1`, les maxima ou les minima des configurations étudiées. La référence `k=1` reste calculée même si `k=1` est retiré de la liste affichée.

Les optima d'énergie et de coût sont cherchés **uniquement parmi les architectures avec `T ≤ T_max`**. La frontière de Pareto, elle, décrit l'ensemble des configurations calculées, indépendamment du seuil. Une solution domine une autre si elle est au moins aussi bonne sur `(E,T,A)` et strictement meilleure sur au moins un critère.

Avec les valeurs initiales : l'optimum énergétique est **k=8** (`E≈0,174 µJ`) ; le coût pondéré avec `(α,β,γ)=(0,5;0,3;0,2)` préfère **k=4**. Les valeurs `k=1` et `k=2` ne satisfont pas les 3 µs.

## Utiliser l'interface

La barre latérale modifie `N`, la fréquence, la liste des `k`, `T_max`, tous les coefficients des deux modèles, les trois poids et la méthode de normalisation. Chaque curseur de poids redistribue automatiquement le reste sur les deux autres. Le bouton de réinitialisation restaure les valeurs du TIPE.

Les onglets présentent le bilan, le tableau complet (export CSV et paramètres JSON), cinq graphiques Plotly, trois vues de compromis avec Pareto, une carte de sensibilité des poids, une étude de robustesse lorsque le coefficient quadratique `b` varie de 0 à 2 mW, et les explications théoriques. Un graphique peut être téléchargé en HTML interactif.

## Structure

```text
app.py                 interface Streamlit
ppa/model.py           calculs et validation des paramètres
ppa/optimization.py    références, coût et optima contraints
ppa/pareto.py          dominance et frontière
ppa/sensitivity.py     balayages de poids et du coefficient b
ui/charts.py           figures Plotly
ui/explanations.py     théorie et avertissement scientifique
tests/                 tests pytest des résultats de référence
```

## Portée et limites

**Power et Area sont des modèles numériques pédagogiques, pas des mesures sur un FPGA.** Le temps `N/k` est idéal : il ne modélise ni cycles entiers, ni accès mémoire, ni réduction finale, ni fréquence variable, ni coûts de synchronisation. L'objectif est de comprendre les mécanismes du compromis PPA et la dépendance de l'optimum aux hypothèses. Un prolongement possible serait d'ajouter des contraintes de bande passante ou de comparer à des mesures, en les distinguant explicitement de cette simulation.
