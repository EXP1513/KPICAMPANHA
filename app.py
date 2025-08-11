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
        nome_arquivo = "Abandono.csv"
        col_data_evento = next((c for c in df_kpi.columns if str(c).strip().lower() == "data evento"), None)
        
        if col_data_evento:
            try:
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

        # ---------- FILTRAR E LIMPAR BASE ----------
        df_kpi = df_kpi[~df_kpi[col_whatsapp_kpi].isin(df_fid[col_whatsapp_fid])]

        col_obs = next((c for c in df_kpi.columns if str(c).strip().lower() == "observação"), None)
        filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
        filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
        base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)

        col_carteiras = next((c for c in base_pronta.columns if str(c).strip().lower() == "carteiras"), None)
        if col_carteiras:
            # Lista de termos que devem ser removidos
            termos_excluir = ["SAC - Pós Venda", "Secretaria"]
            base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(termos_excluir)]

        col_contato = next((c for c in base_pronta.columns if str(c).strip().lower() == "contato"), None)
        
        if col_contato:
            def processar_contato(valor):
                texto_original = str(valor).strip()
                if not texto_original or texto_original.lower() == "nan":
                    return "Candidato"
                primeira_palavra = texto_original.split(" ")[0].capitalize()
                if len(primeira_palavra) <= 3:
                    return "Candidato"
                return primeira_palavra

            base_pronta[col_contato] = base_pronta[col_contato].apply(processar_contato)

        # ---------- RENOMEAR E LIMPAR NÚMEROS ----------
        mapping = {col_contato: "Nome", col_whatsapp_kpi: "Numero", col_obs: "Tipo"}
        base_pronta = base_pronta.rename(columns=mapping)[["Nome", "Numero", "Tipo"]]

        def limpar_numero(num):
            num_limpo = re.sub(r"\D", "", str(num))  # Remove não numéricos
            if num_limpo.startswith("55"):
                num_limpo = num_limpo[2:]  # Remove prefixo 55 se existir
            if num_limpo.startswith("0"):
                num_limpo = num_limpo[1:]  # Remove zero logo após o DDI
            return "55" + num_limpo

        base_pronta["Numero"] = base_pronta["Numero"].apply(limpar_numero)
        base_pronta = base_pronta[base_pronta["Numero"].str.len().between(12, 13)]
        base_pronta = base_pronta.drop_duplicates(subset=["Numero"], keep="first")

        # ---------- MONTAR LAYOUT ----------
        layout_colunas = [
            "TIPO_DE_REGISTRO", "VALOR_DO_REGISTRO", "MENSAGEM", "NOME_CLIENTE",
            "CPFCNPJ", "CODCLIENTE", "TAG", "CORINGA1", "CORINGA2", "CORINGA3",
            "CORINGA4", "CORINGA5", "PRIORIDADE"
        ]
        base_importacao = pd.DataFrame(columns=layout_colunas)
        base_importacao["VALOR_DO_REGISTRO"] = base_pronta["Numero"].values
        base_importacao["NOME_CLIENTE"] = base_pronta["Nome"].values
        base_importacao["TIPO_DE_REGISTRO"] = "TELEFONE"
        base_importacao = base_importacao[layout_colunas]

        # ---------- SAÍDA ----------
        st.success(f"✅ Base de campanha gerada para importação! {len(base_importacao)} registros.")
        st.dataframe(base_importacao)

        output = BytesIO()
        base_importacao.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button(
            label="⬇️ Baixar base de campanha (formato .csv)",
            data=output,
            file_name=nome_arquivo,
            mime="text/csv"
        )





