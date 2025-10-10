# forecast_tools.py
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import VECM, select_order, select_coint_rank
import streamlit as st

from statsmodels.tsa.holtwinters import ExponentialSmoothing



def plot_forecast(df, forecast, variable_name, steps):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[variable_name], mode='lines', name='Historique'))
    future_index = pd.date_range(start=df.index[-1], periods=steps + 1, freq='Y')[1:]
    fig.add_trace(go.Scatter(x=future_index, y=forecast, mode='lines+markers', name='Prévision'))
    fig.update_layout(title=f"Prévision de {variable_name}", xaxis_title="Année", yaxis_title=variable_name)
    return fig


def forecast_arima(df, variable, steps=5, order=(1, 1, 1)):
    ts = df[variable].dropna()
    model = ARIMA(ts, order=order)
    results = model.fit()
    forecast = results.forecast(steps=steps)
    return forecast, plot_forecast(df, forecast, variable, steps)


def forecast_sarima(df, variable, steps=5, order=(1, 1, 1), seasonal_order=(1, 0, 1, 12)):
    ts = df[variable].dropna()
    model = SARIMAX(ts, order=order, seasonal_order=seasonal_order)
    results = model.fit(disp=False)
    forecast = results.forecast(steps=steps)
    return forecast, plot_forecast(df, forecast, variable, steps)


def forecast_var(df, variables, steps=5):
    df_var = df[variables].dropna()
    model = VAR(df_var)
    results = model.fit(maxlags=15, ic='aic')
    forecast = results.forecast(df_var.values[-results.k_ar:], steps)
    forecast_df = pd.DataFrame(forecast, columns=variables)
    return forecast_df, results


def forecast_vecm(df, variables, steps=5):
    df_vecm = df[variables].dropna()
    det_order = select_order(df_vecm, maxlags=10, deterministic="ci")
    coint_rank = select_coint_rank(df_vecm, det_order.aic, 0.05, method="trace")
    model = VECM(df_vecm, k_ar_diff=det_order.aic, coint_rank=coint_rank.rank)
    results = model.fit()
    forecast = results.predict(steps=steps)
    forecast_df = pd.DataFrame(forecast, columns=variables)
    return forecast_df, results


def streamlit_forecast_interface(df, variables, multivariate=False):
    st.subheader("🔮 Lancement de la Prévision")
    model_choice = st.selectbox("Choisissez un modèle", ["ARIMA", "SARIMA", "VAR", "VECM"])
    steps = st.slider("Nombre de périodes à prévoir", min_value=1, max_value=10, value=5)

    if multivariate:
        selected_vars = st.multiselect("Choisissez les variables (au moins 2)", variables, default=variables[:2])
        if len(selected_vars) >= 2:
            if model_choice == "VAR":
                forecast_df, _ = forecast_var(df.set_index("Année"), selected_vars, steps)
                st.write(forecast_df)
            elif model_choice == "VECM":
                forecast_df, _ = forecast_vecm(df.set_index("Année"), selected_vars, steps)
                st.write(forecast_df)
        else:
            st.warning("Veuillez sélectionner au moins deux variables.")
    else:
        variable = st.selectbox("Variable à prévoir", variables)
        if model_choice == "ARIMA":
            forecast, fig = forecast_arima(df.set_index("Année"), variable, steps)
            st.plotly_chart(fig, use_container_width=True)
        elif model_choice == "SARIMA":
            forecast, fig = forecast_sarima(df.set_index("Année"), variable, steps)
            st.plotly_chart(fig, use_container_width=True)

			
def forecast_variable(df, periods=5, method="ARIMA"):
    df = df.dropna()
    df = df.set_index("Année")
    df.index = pd.to_datetime(df.index, format="%Y")
    y = df.iloc[:, 0]

    model = None
    forecast = None

    if method == "ARIMA":
        model = ARIMA(y, order=(1, 1, 1)).fit()
        forecast = model.forecast(steps=periods)
    elif method == "SARIMA":
        model = SARIMAX(y, order=(1, 1, 1), seasonal_order=(1, 1, 1, 4)).fit()
        forecast = model.forecast(steps=periods)
    elif method == "Holt-Winters":
        model = ExponentialSmoothing(y, trend="add", seasonal=None).fit()
        forecast = model.forecast(periods)

    future_index = pd.date_range(start=y.index[-1] + pd.DateOffset(years=1), periods=periods, freq="Y")
    forecast_series = pd.Series(forecast.values, index=future_index)

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    y.plot(ax=ax, label="Historique")
    forecast_series.plot(ax=ax, label="Prévision", linestyle="--")
    ax.set_title(f"Prévision ({method})")
    ax.legend()
    ax.grid(True)
    return fig

