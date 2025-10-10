import streamlit as st
import pandas as pd
import plotly.express as px
from utils.imf_api import get_imf_data 
from utils.excel_loader import load_excel
from utils.forecast_tools import streamlit_forecast_interface

INDICATEURS_IMF = {
    "Recettes publiques (% PIB)": "G1_S13_POGDP_PT.A",              # Revenue/GDP
    "Dépenses publiques (% PIB)": "G2M_S13_POGDP_PT.A",             # Expenditure/GDP
    "Dette brute (% PIB)": "G63G_S13_POGDP_PT.A",                  # Gross Debt/GDP
    "Solde budgétaire (% PIB)": "GNLB_S13_POGDP_PT.A",             # Net Lending (+) / Net Borrowing (-), General Government, % of GDP
    "Solde primaire (% PIB)": "GPB_S13_POGDP_PT.A"                 # Primary Balance, General Government, % of GDP
}

def app():
    st.title("📊 Finances Publiques de Madagascar")
    onglet_data, onglet_prev = st.tabs(["📈 Historical Data", "🔮 Forecast"])

    with onglet_data:
        source = st.radio("📦 Data Source", ["IMF", "Import Excel"])

        if source == "Import Excel":
            if 'load_excel' in globals():
                df = load_excel() # Load data from an Excel file
            else:
                st.warning("Module 'utils.excel_loader' not found. Please create it or uncomment if available.")
                df = None
        else:
            dfs = []
            for display_name, sdmx_code in INDICATEURS_IMF.items():
                data = get_imf_data(indicator_code=sdmx_code, country_code="MDG", start_year=1991)
                if not data.empty and "Année" in data.columns:
                    if "Indicateur" in data.columns:
                        data = data.drop(columns=["Indicateur"])
                    dfs.append(data.rename(columns={"Valeur": display_name}).set_index("Année"))
            df = pd.concat(dfs, axis=1).dropna(how="all").reset_index() if dfs else None
        if df is None or df.empty:
            st.warning("⚠️ No data available for display. Please check the data source or API connection.")
            return
        st.subheader("Historical Data")
        st.dataframe(df.set_index("Année"), use_container_width=True)

        all_columns = df.columns.tolist()
        if "Année" in all_columns:
            all_columns.remove("Année") # Do not allow selection of 'Année' for the Y-axis
        
        selection = st.multiselect(
            "Select variables to display", 
            all_columns, 
            default=all_columns # Select all columns by default
        )

        if not selection:
            st.warning("Please select at least one variable to display.")
        else:
            fig = px.line(
                df, 
                x="Année", 
                y=selection, 
                title="Visualization of Selected Variables",
                labels={"value": "Value", "variable": "Indicator"}, # Rename default labels
                line_shape="linear", # Options: 'linear', 'spline', 'vhv', 'hvh', 'hv'
                render_mode="svg" # For better graphic quality
            )
            fig.update_layout(
                hovermode="x unified", # Display information for all lines at the selected year
                xaxis_title="Year",
                yaxis_title="Percentage of GDP",
                legend_title_text="Indicators",
                plot_bgcolor='#f8f9fa', # Plot background color
                paper_bgcolor='#f8f9fa' # Figure background color
            )
            if "Solde budgétaire (% PIB)" in selection or "Solde primaire (% PIB)" in selection:
                fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Zero line")
            
            if "Dette brute (% PIB)" in selection:
                fig.add_hline(y=50, line_dash="dot", line_color="orange", annotation_text="Prudence Threshold (50%)", annotation_position="top right")
                fig.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="Alert Threshold (70%)", annotation_position="top right")


            st.plotly_chart(fig, use_container_width=True)

    with onglet_prev:
        if df is not None and not df.empty:
            st.markdown("### 🔮 Forecast of Selected Variables")
            if 'streamlit_forecast_interface' in globals():
                streamlit_forecast_interface(df, selection, multivariate=len(selection) > 1)
            else:
                st.warning("Module 'utils.forecast_tools' not found. Please create it or uncomment if available.")
        else:
            st.warning("Import or retrieve data first to perform a forecast.")

