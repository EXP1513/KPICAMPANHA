import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Base Pronta Organizada", page_icon="📊")
st.title("📊 Gerar Base Pronta Final")

file_kpi = st.file_uploader("📂 Importar base **KPI**", type=["xlsx", "csv"])

def read_file(f):
    if f.name.endswith(".csv"):
        return pd.read_csv(f, encoding="utf-8", sep=None, engine="python")
    else:
        return pd.read_excel(f)

if file_kpi:
    df_kpi = read_file(file_kpi)

    # 1️⃣ Identificar coluna Observação
    col_obs = next((col for col in df_kpi.columns if str(col).strip().lower() == "observação"), None)
    if col_obs is None:
        st.error("❌ Coluna 'Observação' não encontrada na base KPI.")
    else:
        # Filtrar Médio e Fundamental
        filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
        filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
        base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)

        # 2️⃣ Filtro de Carteiras
        col_carteiras = next((col for col in base_pronta.columns if str(col).strip().lower() == "carteiras"), None)
        if col_carteiras:
            termos_excluir = ["SAC - Pós Venda", "Secretaria"]
            base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(termos_excluir)]

        # 3️⃣ Ajuste da coluna "Contato"
        col_contato = next((col for col in base_pronta.columns if str(col).strip().lower() == "contato"), None)
        if col_contato:
            def processar_contato(valor):
                texto_original = str(valor).strip()
                if not texto_original:
                    return texto_original
                primeira_palavra = texto_original.split(" ")[0]
                if 0 <= len(primeira_palavra) <= 3 and re.search(r"\d", texto_original):
                    primeira_palavra = "Candidato"
                return primeira_palavra.capitalize()
            base_pronta[col_contato] = base_pronta[col_contato].apply(processar_contato)

        # 4️⃣ Manter apenas as colunas desejadas
        col_whatsapp = next((col for col in base_pronta.columns if str(col).strip().lower() == "whatsapp principal"), None)
        cols_desejadas = [c for c in [col_contato, col_whatsapp, col_obs] if c is not None]
        base_pronta = base_pronta[cols_desejadas]

        # 5️⃣ Remover duplicatas por numero de telefone
        if col_whatsapp:
            base_pronta = base_pronta.drop_duplicates(subset=[col_whatsapp], keep="first")

        # 6️⃣ Reorganizar e renomear colunas
        mapping = {
            col_contato: "Nome",
            col_whatsapp: "Numero",
            col_obs: "Tipo"
        }
        base_pronta = base_pronta[[col_contato, col_whatsapp, col_obs]]
        base_pronta = base_pronta.rename(columns=mapping)

        # ✅ Exibir apenas no final
        st.success("✅ Base Pronta Final gerada com sucesso!")
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
