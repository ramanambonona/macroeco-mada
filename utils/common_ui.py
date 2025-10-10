# common_ui.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.ardl import ARDL
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_percentage_error
import warnings
warnings.filterwarnings("ignore")

# Prophet optionnel
try:
    from prophet import Prophet
    PROPHET_OK = True
except Exception:
    PROPHET_OK = False

# ---------- CSS ----------
def inject_css(css_path: str = "styles.css", palette: str = "clair"):
    """Injecte CSS + sélectionne la palette en écrasant les variables actives."""
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass
    # écrasement des variables actives à partir des variables de palette définies dans styles.css
    pal = palette.lower().replace("é","e")
    st.markdown(f"""
    <style>
    :root {{
      --bg: var(--bg-{pal});
      --sb: var(--sb-{pal});
      --fg: var(--fg-{pal});
      --accent: var(--accent-{pal});
    }}
    </style>
    """, unsafe_allow_html=True)

def floating_note():
    st.markdown("""
    <div class="floating-note">
      <span><strong>Ramanambonona Ambinintsoa, PhD</strong></span>
      <a href="mailto:ambinintsoa.uat.ead2@gmail.com" title="Mail"><img src="https://img.icons8.com/?size=100&id=86875&format=png&color=000000" alt="Mail"></a>
      <a href="https://github.com/ramanambonona" target="_blank" rel="noopener" title="GitHub"><img src="https://img.icons8.com/?size=100&id=3tC9EQumUAuq&format=png&color=000000" alt="GitHub"></a>
      <a href="https://www.linkedin.com/in/ambinintsoa-ramanambonona" target="_blank" rel="noopener" title="LinkedIn"><img src="https://img.icons8.com/?size=100&id=8808&format=png&color=000000" alt="LinkedIn"></a>
    </div>
    """, unsafe_allow_html=True)

# ---------- Download helpers ----------
def _to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    with BytesIO() as buf:
        with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
            df.to_excel(w, index=False, sheet_name="data")
        return buf.getvalue()

def download_box(df: pd.DataFrame, base_name: str, key_prefix: str = ""):
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ CSV", df.to_csv(index=False).encode("utf-8"),
                           file_name=f"{base_name}.csv", mime="text/csv",
                           use_container_width=True, key=f"{key_prefix}_csv")
    with c2:
        st.download_button("⬇️ Excel", _to_xlsx_bytes(df),
                           file_name=f"{base_name}.xlsx",
                           mime="application/vnd.ms-excel",
                           use_container_width=True, key=f"{key_prefix}_xlsx")

# ---------- Analyse ----------
def analyze_time_series(series: pd.Series):
    out = {'tendance':'Non détectée','saisonnalite':'Non détectée','recommandations':[]}
    try:
        if len(series) > 12:
            v = abs(series[-6:].mean() - series[:6].mean()) / (abs(series[:6].mean()) + 1e-10)
            out['tendance'] = 'Détectée' if v > 0.1 else 'Faible'
            if out['tendance'] == 'Détectée':
                out['recommandations'].append('Différenciation / ARIMA / ETS / Trend regression')
        if len(series) >= 24:
            try:
                d = seasonal_decompose(series, period=12, model='additive', extrapolate_trend='freq')
                s = np.std(d.seasonal) / (np.std(d.resid) + 1e-10)
                if s > 0.5:
                    out['saisonnalite'] = 'Forte'; out['recommandations'].append('SARIMA / Prophet / SNaive')
                elif s > 0.2:
                    out['saisonnalite'] = 'Modérée'; out['recommandations'].append('ETS saisonnier / SARIMA')
            except Exception:
                pass
    except Exception:
        pass
    return out

# ---------- Prévision ----------
def forecast_ssae(series, periods):
    fc, cur = [], series.copy()
    for _ in range(periods):
        m = cur.mean(); fc.append(m)
        cur = pd.concat([cur[1:], pd.Series([m])])
    return np.array(fc)

def forecast_ar(p, series, periods):
    try: return ARIMA(series, order=(p,0,0)).fit().forecast(steps=periods)
    except: return np.zeros(periods)

def forecast_arima(order, series, periods):
    try: return ARIMA(series, order=order).fit().forecast(steps=periods)
    except: return np.zeros(periods)

def forecast_var(lag, series_dict, target, periods):
    try:
        dfv = pd.DataFrame(series_dict)
        if dfv.shape[1] < 2: return forecast_ar(lag, series_dict[target], periods)
        return VAR(dfv).fit(lag).forecast(dfv.values[-lag:], steps=periods)[:, dfv.columns.get_loc(target)]
    except: return np.zeros(periods)

def forecast_ardl(lags, series, periods=1):
    try: return ARDL(series, lags=lags, order=0).fit().forecast(steps=periods)
    except: return np.zeros(periods)

def forecast_ets(series, periods, trend='add', seasonal='add', sp=12):
    try:
        if seasonal and sp and len(series) < sp*2: return np.zeros(periods)
        return ExponentialSmoothing(series, trend=trend, seasonal=seasonal, seasonal_periods=sp).fit().forecast(steps=periods)
    except: return np.zeros(periods)

def forecast_snaive(series, periods, sp=12):
    if sp <= 0 or len(series) < sp: return np.zeros(periods)
    last = series.iloc[-sp:].values
    reps = int(np.ceil(periods/sp))
    return np.resize(last, reps*sp)[:periods]

def forecast_reg(series, periods):
    try:
        X = np.arange(len(series)).reshape(-1,1); y = series.values
        m = LinearRegression().fit(X,y)
        return m.predict(np.arange(len(series), len(series)+periods).reshape(-1,1))
    except: return np.zeros(periods)

def forecast_rf(series, periods, n_estimators=120, max_depth=10):
    try:
        lags = min(12, max(1, len(series)//2))
        if len(series) < lags + 10: return np.zeros(periods)
        X,y = [],[]
        for i in range(lags, len(series)):
            X.append(series.iloc[i-lags:i].values); y.append(series.iloc[i])
        X,y = np.array(X), np.array(y)
        model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42).fit(X,y)
        fc, last = [], series.iloc[-lags:].values
        for _ in range(periods):
            pred = model.predict(last.reshape(1,-1))[0]
            fc.append(pred); last = np.roll(last,-1); last[-1]=pred
        return np.array(fc)
    except: return np.zeros(periods)

def forecast_mlp(series, periods, hidden=(100,), max_iter=300):
    try:
        lags = min(12, max(1, len(series)//2))
        if len(series) < lags + 10: return np.zeros(periods)
        X,y = [],[]
        for i in range(lags, len(series)):
            X.append(series.iloc[i-lags:i].values); y.append(series.iloc[i])
        X,y = np.array(X), np.array(y)
        m = MLPRegressor(hidden_layer_sizes=hidden, max_iter=max_iter, random_state=42).fit(X,y)
        fc, last = [], series.iloc[-lags:].values
        for _ in range(periods):
            pred = m.predict(last.reshape(1,-1))[0]
            fc.append(pred); last = np.roll(last,-1); last[-1]=pred
        return np.array(fc)
    except: return np.zeros(periods)

def forecast_prophet(df, col, periods, changepoint=0.05, seasonality=10.0):
    if not PROPHET_OK: return np.zeros(periods)
    try:
        pdf = df[["Date", col]].dropna().rename(columns={"Date":"ds", col:"y"})
        m = Prophet(changepoint_prior_scale=changepoint, seasonality_prior_scale=seasonality,
                    yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(pdf); fut = m.make_future_dataframe(periods=periods, freq="M")
        return m.predict(fut)["yhat"].tail(periods).values
    except: return np.zeros(periods)

def get_mape_status_html(mape):
    if mape < 0.10: color,label="#28a745","🟢 Excellent"
    elif mape <= 0.20: color,label="#ffc107","🟠 Bon"
    else: color,label="#dc3545","🔴 Mauvais"
    return f"""
    <div style="display:flex;align-items:center;gap:10px;margin-top:5px;font-size:16px;font-weight:500;">
      <span>Précision (MAPE): <strong>{mape:.2%}</strong></span>
      <span style="background:{color}20;color:{color};padding:4px 8px;border-radius:6px;font-weight:600;font-size:.9em;">{label}</span>
    </div>"""

# ---------- Rendu 4 onglets standard ----------
def build_module(df: pd.DataFrame, module_title: str):
    """Rendu standard: Traitement / Visualisation / Analyse / Prévisions + téléchargements."""
    st.header(module_title)

    # ——— Outils de traitement simples (filtre période, transformation) ———
    tab1, tab2, tab3, tab4 = st.tabs(["Traitement", "Visualisation", "Analyse", "Prévisions"])

    with tab1:
        st.subheader("Traitement (historique)")
        st.caption("Les données proviennent de tes sources existantes (FMI, World Bank, INSTAT, BFM…).")
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            c1,c2,c3 = st.columns(3)
            with c1:
                dmin = st.date_input("Début", value=df["Date"].min().date())
            with c2:
                dmax = st.date_input("Fin", value=df["Date"].max().date())
            with c3:
                transform = st.selectbox("Transformation", ["Niveau","Log","YoY %","MoM %"], index=0)

            dff = df[(df["Date"]>=pd.to_datetime(dmin)) & (df["Date"]<=pd.to_datetime(dmax))].copy()

            if transform in ["YoY %","MoM %"]:
                freq = 12 if dff["Date"].diff().dt.days.median() >= 28 else 1  # heuristique
                for c in dff.columns.drop("Date"):
                    s = dff.set_index("Date")[c]
                    dff[c] = (s.pct_change(12) if transform=="YoY %" else s.pct_change()).values*100
            elif transform == "Log":
                for c in dff.columns.drop("Date"):
                    dff[c] = np.log(dff[c].astype(float).replace({0:np.nan}))

            st.dataframe(dff.head(30), use_container_width=True)
            download_box(dff, f"{module_title.lower().replace(' ','_')}_traite")
        else:
            st.error("Colonne 'Date' manquante dans le DataFrame.")

    with tab2:
        st.subheader("Visualisation")
        if "Date" in df.columns:
            vars_sel = st.multiselect("Variables", df.columns.drop("Date").tolist(),
                                      default=df.columns.drop("Date").tolist()[:2])
            if vars_sel:
                fig = px.line(df, x="Date", y=vars_sel, labels={"value":"Valeur","variable":"Variable"}, height=520,
                              title=f"Évolution — {module_title}")
                fig.update_layout(font_family="EB Garamond", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})
                download_box(df[["Date"]+vars_sel], f"{module_title.lower().replace(' ','_')}_viz")
            else:
                st.info("Sélectionne au moins une variable.")
        else:
            st.error("Colonne 'Date' manquante.")

    with tab3:
        st.subheader("Analyse")
        if "Date" in df.columns:
            v = st.selectbox("Variable à analyser", df.columns.drop("Date"))
            s = df.set_index("Date")[v].dropna()
            if len(s) < 12:
                st.warning("Données insuffisantes (≥ 12 points).")
            else:
                rep = analyze_time_series(s)
                c1,c2,c3 = st.columns(3)
                c1.metric("Tendance", rep["tendance"])
                c2.metric("Saisonnalité", rep["saisonnalite"])
                c3.metric("Points", len(s))
                for r in rep["recommandations"]: st.write("•", r)

                # Décomposition
                try:
                    d = seasonal_decompose(s, period=12, model="additive", extrapolate_trend="freq")
                    comp = pd.DataFrame({"Date": s.index, "observed": d.observed, "trend": d.trend,
                                         "seasonal": d.seasonal, "resid": d.resid})
                    fig = go.Figure()
                    for k in ["observed","trend","seasonal","resid"]:
                        fig.add_trace(go.Scatter(x=comp["Date"], y=comp[k], mode="lines", name=k.title()))
                    fig.update_layout(height=600, hovermode="x unified", font_family="EB Garamond",
                                      title=f"Décomposition — {v}")
                    st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})
                    download_box(comp, f"{module_title.lower().replace(' ','_')}_decomposition_{v}")
                except Exception as e:
                    st.info("Décomposition non disponible.")
        else:
            st.error("Colonne 'Date' manquante.")

    with tab4:
        st.subheader("Prévisions")
        if "Date" not in df.columns:
            st.error("Colonne 'Date' manquante."); return

        # Choix modèles (Prophet s'affiche si dispo)
        models = ["NAIVE","AR(p)","ARIMA","VAR","ARDL","Régression Linéaire","Random Forest",
                  "MLP","Exponential Smoothing (ETS)","SNaive","Auto (min MAPE)"]
        if PROPHET_OK: models.insert(5, "Prophet")
        model = st.selectbox("Modèle", models)
        var = st.selectbox("Indicateur", df.columns.drop("Date"))
        periods = st.slider("Horizon (mois)", 3, 60, 12)

        params = {}
        if model == "AR(p)":
            params['p'] = st.slider("p", 1, 12, 1)
        elif model == "ARIMA":
            p = st.slider("p",0,5,1); d = st.slider("d",0,2,1); q = st.slider("q",0,5,0)
            params['order'] = (p,d,q)
        elif model == "VAR":
            params['lag'] = st.slider("Lag", 1, 4, 1)
        elif model == "ARDL":
            params['lags'] = st.slider("Lags", 1, 12, 1)
        elif model == "Prophet" and PROPHET_OK:
            params['changepoint'] = st.slider("Changepoint prior", 0.001, 0.5, 0.05)
            params['seasonality'] = st.slider("Saisonnalité prior", 0.01, 100.0, 10.0)
        elif model == "Random Forest":
            params['n_estimators'] = st.slider("n_estimators", 10, 200, 120)
            params['max_depth'] = st.slider("max_depth", 3, 20, 10)
        elif model == "MLP":
            params['hidden'] = tuple(st.multiselect("Couches cachées", [50,100,200], [100]) or [100])
            params['max_iter'] = st.slider("max_iter", 50, 1000, 300)
        elif model in ["Exponential Smoothing (ETS)","SNaive","Auto (min MAPE)"]:
            params['trend'] = st.selectbox("Tendance (ETS)", ['add','mul', None], index=0 if model!="SNaive" else 2)
            params['seasonal'] = st.selectbox("Saisonnalité (ETS)", ['add','mul', None], index=0 if model!="SNaive" else 2)
            params['sp'] = st.slider("Périodes saisonnières", 4, 24, 12)

        # Prévision + MAPE simple
        dfc = df.copy(); dfc["Date"] = pd.to_datetime(dfc["Date"])
        s = dfc.set_index("Date")[var].dropna()

        if st.button("Lancer la prévision", type="primary"):
            if len(s) < 2:
                st.error("Série trop courte.")
            else:
                if model == "NAIVE": fc = forecast_ssae(s, periods)
                elif model == "AR(p)": fc = forecast_ar(params.get("p",1), s, periods)
                elif model == "ARIMA": fc = forecast_arima(params.get("order",(1,1,0)), s, periods)
                elif model == "VAR":
                    others = [var] + [c for c in dfc.columns if c not in ["Date",var]][:1]
                    data = {v: dfc.set_index("Date")[v].dropna() for v in others}
                    fc = forecast_var(params.get("lag",1), data, var, periods)
                elif model == "ARDL": fc = forecast_ardl(params.get("lags",1), s, periods)
                elif model == "Prophet" and PROPHET_OK":
                    fc = forecast_prophet(dfc, var, periods, params.get("changepoint",0.05), params.get("seasonality",10.0))
                elif model == "Régression Linéaire": fc = forecast_reg(s, periods)
                elif model == "Random Forest": fc = forecast_rf(s, periods, params.get("n_estimators",120), params.get("max_depth",10))
                elif model == "MLP": fc = forecast_mlp(s, periods, params.get("hidden",(100,)), params.get("max_iter",300))
                elif model == "Exponential Smoothing (ETS)": fc = forecast_ets(s, periods, params.get("trend","add"), params.get("seasonal","add"), params.get("sp",12))
                elif model == "SNaive": fc = forecast_snaive(s, periods, params.get("sp",12))
                else:
                    # Auto (min MAPE) — petit tournoi interne
                    cand = [
                        ("NAIVE", forecast_ssae(s, periods)),
                        ("ARIMA", forecast_arima((1,1,0), s, periods)),
                        ("ETS", forecast_ets(s, periods)),
                        ("SNaive", forecast_snaive(s, periods)),
                        ("Reg", forecast_reg(s, periods)),
                    ]
                    if PROPHET_OK: cand.append(("Prophet", forecast_prophet(dfc, var, periods)))
                    # évalue sur 12 derniers si possible
                    def mape_last(name):
                        if len(s) <= 14: return np.inf
                        tr, te = s[:-12], s[-12:]
                        if name=="NAIVE": pr = forecast_ssae(tr, 12)
                        elif name=="ARIMA": pr = forecast_arima((1,1,0), tr, 12)
                        elif name=="ETS": pr = forecast_ets(tr, 12)
                        elif name=="SNaive": pr = forecast_snaive(tr, 12)
                        elif name=="Reg": pr = forecast_reg(tr, 12)
                        elif name=="Prophet" and PROPHET_OK: pr = forecast_prophet(pd.DataFrame({"Date":tr.index,var:tr.values}), var, 12)
                        else: return np.inf
                        return mean_absolute_percentage_error(te, pr) if len(pr)==len(te) else np.inf
                    ranked = sorted([(mape_last(n), n, f) for (n,f) in cand], key=lambda x: x[0])
                    model = f"Auto→{ranked[0][1]}"; fc = ranked[0][2]

                # Assemblage historique + prévision
                future = pd.date_range(start=dfc["Date"].max()+pd.DateOffset(months=1), periods=periods, freq="M")
                hist = pd.DataFrame({"Date": dfc["Date"], var: dfc[var], "Type":"Historique"})
                fut  = pd.DataFrame({"Date": future, var: fc, "Type":"Prévision"})
                full = pd.concat([hist, fut], ignore_index=True)

                # Affichage
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist["Date"], y=hist[var], mode="lines", name="Historique"))
                fig.add_trace(go.Scatter(x=pd.concat([hist.tail(1)["Date"], fut["Date"]]),
                                         y=pd.concat([hist.tail(1)[var], fut[var]]),
                                         mode="lines", name="Prévision"))
                fig.update_layout(font_family="EB Garamond", hovermode="x unified",
                                  title=f"{module_title} — {var} ({model})", height=520)
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})

                # MAPE simple sur 12 derniers
                if len(s) >= 12:
                    tr, te = s[:-12], s[-12:]
                    # recalcule rapide pour mape
                    if model == "NAIVE": pr = forecast_ssae(tr, 12)
                    elif model == "AR(p)": pr = forecast_ar(params.get("p",1), tr, 12)
                    elif model == "ARIMA": pr = forecast_arima(params.get("order",(1,1,0)), tr, 12)
                    elif model == "VAR":
                        # même logique qu'au-dessus
                        pr = np.zeros(12)
                    elif model == "ARDL": pr = forecast_ardl(params.get("lags",1), tr, 12)
                    elif model == "Prophet" and PROPHET_OK:
                        trdf = pd.DataFrame({"Date": tr.index, var: tr.values})
                        pr = forecast_prophet(trdf, var, 12, params.get("changepoint",0.05), params.get("seasonality",10.0))
                    elif model == "Régression Linéaire": pr = forecast_reg(tr, 12)
                    elif model == "Random Forest": pr = forecast_rf(tr, 12, params.get("n_estimators",120), params.get("max_depth",10))
                    elif model == "MLP": pr = forecast_mlp(tr, 12, params.get("hidden",(100,)), params.get("max_iter",300))
                    elif model == "Exponential Smoothing (ETS)": pr = forecast_ets(tr, 12, params.get("trend","add"), params.get("seasonal","add"), params.get("sp",12))
                    elif model == "SNaive": pr = forecast_snaive(tr, 12, params.get("sp",12))
                    else: pr = np.zeros(12)

                    if len(pr)==len(te) and len(te)>0:
                        mape = mean_absolute_percentage_error(te, pr)
                        st.markdown(get_mape_status_html(mape), unsafe_allow_html=True)

                # Téléchargements
                st.caption("Télécharger l’indicateur (Historique + Prévision)")
                download_box(full[["Date",var,"Type"]], f"{module_title.lower().replace(' ','_')}_serie_{var}")
