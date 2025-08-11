import streamlit as st
import pandas as pd
from io import BytesIO
import re

# ==============================
# CONFIG DO APP
# ==============================
st.set_page_config(
    page_title="Gera Campanha", 
    page_icon="📢", 
    layout="centered"
)

# ====== ESTILO CSS INSPIRADO NO SITE EJABRASILEAD ======
st.markdown("""
    <style>
    /* Fundo e fonte */
    body {
        background-color: #f4f6f8;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Cabeçalho principal */
    .titulo-principal {
        background-color: #004aad;
        color: white;
        padding: 18px;
        border-radius: 8px;
        text-align: center;
        font-size: 2em;
        font-weight: bold;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }

    /* Botão download e upload */
    div.stDownloadButton > button, div.stFileUploader > div > button {
        background-color: #ffb703;
        color: black;
        font-weight: bold;
        border-radius: 5px;
        padding: 8px 16px;
        border: none;
    }
    div.stDownloadButton > button:hover, div.stFileUploader > div > button:hover {
        background-color: #fb8500;
        color: white;
    }

    /* Mensagens de sucesso */
    .stSuccess {
        background-color: #e6f4ea;
    }
    </style>
""", unsafe_allow_html=True)

# ====== TÍTULO PRINCIPAL ======
st.markdown("<div class='titulo-principal'>📢 Gera Campanha</div>", unsafe_allow_html=True)

# ====== FUNÇÃO LEITURA DE ARQUIVOS ======
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

# ====== UPLOAD DAS BASES ======
file_kpi = st.file_uploader("📂 Importar base **KPI**", type=["xlsx", "csv"])
file_fid = st.file_uploader("📂 Importar base **FIDELIZADOS**", type=["xlsx", "csv"])

if file_kpi and file_fid:
    df_kpi = read_file(file_kpi)
    df_fid = read_file(file_fid)

    # Localizar WhatsApp Principal nas duas bases
    col_whatsapp_kpi = next((c for c in df_kpi.columns if str(c).strip().lower() == "whatsapp principal"), None)
    col_whatsapp_fid = next((c for c in df_fid.columns if str(c).strip().lower() == "whatsapp principal"), None)

    if not col_whatsapp_kpi or not col_whatsapp_fid:
        st.error("❌ Coluna 'WhatsApp Principal' não encontrada em uma das bases.")
    else:
        # Remover números da KPI que estão na Fidelizados
        df_kpi = df_kpi[~df_kpi[col_whatsapp_kpi].isin(df_fid[col_whatsapp_fid])]

        # Filtrar Observação
        col_obs = next((c for c in df_kpi.columns if str(c).strip().lower() == "observação"), None)
        if not col_obs:
            st.error("❌ Coluna 'Observação' não encontrada.")
        else:
            filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
            filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
            base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)

            # Excluir Carteiras indesejadas
            col_carteiras = next((c for c in base_pronta.columns if str(c).strip().lower() == "carteiras"), None)
            if col_carteiras:
                termos_excluir = ["SAC - Pós Venda", "Secretaria"]
                base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(termos_excluir)]

            # Processar Contato com nova regra
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

            # Manter colunas desejadas
            cols_desejadas = [c for c in [col_contato, col_whatsapp_kpi, col_obs] if c]
            base_pronta = base_pronta[cols_desejadas]

            # Remover duplicatas pelo WhatsApp
            base_pronta = base_pronta.drop_duplicates(subset=[col_whatsapp_kpi], keep="first")

            # Renomear
            mapping = {col_contato: "Nome", col_whatsapp_kpi: "Numero", col_obs: "Tipo"}
            base_pronta = base_pronta.rename(columns=mapping)
            base_pronta = base_pronta[["Nome", "Numero", "Tipo"]]

            # Exibir final
            st.success("✅ Base Pronta Final gerada!")
            st.dataframe(base_pronta)

            # Download
            output = BytesIO()
            base_pronta.to_excel(output, index=False)
            output.seek(0)
            st.download_button(
                label="⬇️ Baixar Base Pronta Final",
                data=output,
                file_name="base_pronta_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
