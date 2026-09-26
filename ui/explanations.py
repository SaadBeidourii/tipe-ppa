"""Texte pédagogique affiché dans l'interface."""

import streamlit as st


MODEL_NOTICE = ("Les valeurs de Power et Area utilisées ici proviennent d’un modèle numérique "
                "pédagogique. Elles ne constituent pas des mesures expérimentales effectuées "
                "sur un FPGA réel. L’objectif est d’étudier mathématiquement et numériquement "
                "les mécanismes du compromis PPA.")


def theory() -> None:
    st.subheader("1. Produit scalaire et parallélisme")
    st.latex(r"S=\sum_{i=1}^{N} a_i b_i")
    st.write("Chaque paire est multipliée, puis les produits sont additionnés. Avec k unités de calcul, "
             "le modèle idéal traite k paires par cycle. Il ignore ici les accès mémoire, la latence "
             "d'addition finale et les coûts de synchronisation.")
    st.subheader("2. Performance et contrainte")
    st.latex(r"N_{cycles}(k)=\frac{N}{k},\qquad T(k)=\frac{N}{kf},\qquad T(k)\leq T_{max}")
    st.write("Ce nombre de cycles est une approximation continue : pour un circuit réel, il faudrait "
             "tenir compte de cycles entiers et de surcoûts. Une configuration hors du seuil n'est "
             "pas candidate à l'optimisation.")
    st.subheader("3. Power : puissance électrique")
    st.latex(r"P(k)=P_0+ak+bk^2,\qquad P=P_{statique}+P_{dynamique}")
    st.latex(r"P_{dyn}\approx\alpha_{act}CV^2f")
    st.write("Le terme fixe représente la puissance de base. Plus d'unités parallèles augmentent "
             "la capacité électrique effective et le nombre de commutations. Le terme quadratique "
             "représente simplement leur surcoût croissant. Les coefficients sont des hypothèses numériques.")
    st.subheader("4. Area : indice abstrait de ressources")
    st.latex(r"A(k)=A_0+ck+dk^2")
    st.write("A₀ = ressources fixes ; ck = coût des unités de calcul ; dk² = coût croissant des "
             "interconnexions, multiplexeurs, accumulation et routage. Area n'est pas un nombre de LUT.")
    st.subheader("5. Énergie et efficacité")
    st.latex(r"E(k)=P(k)T(k),\qquad \eta_E=\frac{N}{E(k)}")
    st.latex(r"D(k)=\frac{N}{T(k)},\qquad \eta_P=\frac{D(k)}{P(k)}")
    st.write("D est le débit en opérations par seconde. ηE est le nombre d'opérations par joule. "
             "ηP est la performance par watt ; dans ce modèle, ηP = ηE puisque E = PT. "
             "Le temps baisse avec k, mais la puissance monte : l'énergie peut atteindre un minimum intermédiaire.")
    st.subheader("6. Coût PPA et argmin")
    st.latex(r"C(k)=\alpha\frac{E(k)}{E_{ref}}+\beta\frac{T(k)}{T_{ref}}+\gamma\frac{A(k)}{A_{ref}}")
    st.latex(r"\alpha+\beta+\gamma=1,\qquad k_{opt}=\mathop{\mathrm{argmin}}_{k:\,T(k)\leq T_{max}} C(k)")
    st.write("Les références rendent les trois termes sans unité. Les poids reflètent la priorité "
             "accordée à l'énergie, au temps et aux ressources. L'argmin est la valeur de k dont "
             "le coût est le plus petit parmi les architectures admissibles.")
    st.subheader("7. Frontière de Pareto")
    st.write("Une solution domine une autre si elle n'est pas moins bonne en énergie, temps et Area, "
             "et si elle est strictement meilleure pour au moins un de ces trois critères. "
             "Les solutions de Pareto ne sont dominées par aucune autre. La frontière présentée "
             "porte sur toutes les configurations, indépendamment du seuil de temps.")
    st.info(MODEL_NOTICE)
