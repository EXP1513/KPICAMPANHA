import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Gera Campanha", page_icon="🚀", layout="centered")

# ---------- ESTILO ----------
st.markdown("""
    <style>
    body {background-color: #f4f6f8; font-family: 'Segoe UI', sans-serif;}
    .titulo-principal {
        background-color: #004aad; color: white; padding: 18px; border-radius: 8px;
        text-align: center; font-size: 2em; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    div.stDownloadButton > button, div.stFileUploader > div > button {
        background-color: #ffb703; color: black; font-weight: bold; border-radius: 5px;
        padding: 8px 16px; border: none;
    }
    div.stDownloadButton > button:hover, div.stFileUploader > div > button:hover {
        background-color: #fb8500; color: white;
    }
    .stSuccess {background-color: #e6f4ea;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='titulo-principal'>📢 Gera Campanha</div>", unsafe_allow_html=True)

# ---------- FUNÇÃO PARA LEITURA DE ARQUIVOS ----------
def read_file(f):
    bytes_data = f.read()
    data_io = BytesIO(bytes_data)
    if f.name.lower().endswith(".csv"):
        try:
            return pd.read_csv(data_io, encoding="utf-8", sep=None, engine="python")
        except UnicodeDecodeError:
            data_io.seek(0)
            return pd.read_csv(data_io, encoding="ISO-8859-1", sep=None, engine="python")
    else:
        return pd.read_excel(data_io)

# ---------- UPLOAD ----------
file_kpi = st.file_uploader("📂 Importar base **KPI**", type=["xlsx", "csv"])
file_fid = st.file_uploader("📂 Importar base **FIDELIZADOS**", type=["xlsx", "csv"])

if file_kpi and file_fid:
    df_kpi = read_file(file_kpi)
    df_fid = read_file(file_fid)

    col_whatsapp_kpi = next((c for c in df_kpi.columns if str(c).strip().lower() == "whatsapp principal"), None)
    col_whatsapp_fid = next((c for c in df_fid.columns if str(c).strip().lower() == "whatsapp principal"), None)

    if not col_whatsapp_kpi or not col_whatsapp_fid:
        st.error("❌ Coluna 'WhatsApp Principal' não encontrada.")
    else:
        # ---------- PEGAR DATAS PARA O NOME DO ARQUIVO ----------
        col_data_evento = next((c for c in df_kpi.columns if str(c).strip().lower() == "data evento"), None)
        nome_arquivo = "Abandono.csv"  # nome padrão

        if col_data_evento:
            try:
                # Força a interpretação dia/mês/ano
                df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
                datas_validas = df_kpi[col_data_evento].dropna().dt.date

                if not datas_validas.empty:
                    data_inicial = min(datas_validas)
                    data_final = max(datas_validas)
                    if data_inicial == data_final:
                        nome_arquivo = f"Abandono_{data_inicial.strftime('%d.%m')}.csv"
                    else:
                        nome_arquivo = f"Abandono_{data_inicial.strftime('%d.%m')}_a_{data_final.strftime('%d.%m')}.csv"
            except Exception as e:
                st.warning(f"⚠️ Não foi possível processar as datas: {e}")

        # Remove números da KPI que estão nos fidelizados
        df_kpi = df_kpi[~df_kpi[col_whatsapp_kpi].isin(df_fid[col_whatsapp_fid])]

        col_obs = next((c for c in df_kpi.columns if str(c).strip().lower() == "observação"), None)
        filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
        filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
        base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)

        col_carteiras = next((c for c in base_pronta.columns if str(c).strip().lower() == "carteiras"), None)
        if col_carteiras:
            termos_excluir = ["SAC - Pós Venda", "Secretaria"]
            base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(termos_excluir)]

        col_contato = next((c for c in base_pronta.columns if str(c).strip().lower() == "contato"), None)
        if col_contato:
            def processar_contato(valor):
                texto_original = str(valor).strip()
                if not texto_original:
                    return texto_original
                primeira_palavra = texto_original.split(" ")[0].capitalize()
                if len(primeira_palavra) < 3:
                    return "Candidato"
                return primeira_palavra
            base_pronta[col_contato] = base_pronta[col_contato].apply(processar_contato)

        mapping = {col_contato: "Nome", col_whatsapp_kpi: "
