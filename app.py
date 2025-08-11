import streamlit as st
import pandas as pd
from io import BytesIO
import re

# Configuração inicial do app
st.set_page_config(page_title="Base Pronta Organizada", page_icon="📊")
st.title("📊 Gerar Base Pronta Final")

# Função robusta para leitura de arquivos CSV ou Excel
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

# Upload da base KPI
file_kpi = st.file_uploader("📂 Importar base **KPI** (Excel ou CSV)", type=["xlsx", "csv"])

if file_kpi:
    df_kpi = read_file(file_kpi)

    # 1️⃣ Localizar coluna Observação
    col_obs = next((col for col in df_kpi.columns if str(col).strip().lower() == "observação"), None)
    if not col_obs:
        st.error("❌ Coluna 'Observação' não encontrada na base.")
    else:
        # Filtrar Médio e Fundamental
        filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
        filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
        base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)

        # 2️⃣ Remover linhas indesejadas da coluna Carteiras
        col_carteiras = next((col for col in base_pronta.columns if str(col).strip().lower() == "carteiras"), None)
        if col_carteiras:
            termos_excluir = ["SAC - Pós Venda", "Secretaria"]
            base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(termos_excluir)]

        # 3️⃣ Processar coluna Contato
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

        # 4️⃣ Manter apenas colunas desejadas
        col_whatsapp = next(
            (col for col in base_pronta.columns if str(col).strip().lower() == "whatsapp principal"), None
        )
        cols_desejadas = [c for c in [col_contato, col_whatsapp, col_obs] if c]
        base_pronta = base_pronta[cols_desejadas]

        # 5️⃣ Remover duplicatas pelo número de telefone
        if col_whatsapp:
            base_pronta = base_pronta.drop_duplicates(subset=[col_whatsapp], keep="first")

        # 6️⃣ Reorganizar e renomear colunas
        mapping = {col_contato: "Nome", col_whatsapp: "Numero", col_obs: "Tipo"}
        base_pronta = base_pronta.rename(columns=mapping)
        base_pronta = base_pronta[["Nome", "Numero", "Tipo"]]

        # ✅ Exibir resultado final
        st.success("✅ Base Pronta Final gerada com sucesso!")
        st.dataframe(base_pronta)

        # Botão para baixar Excel final
        output = BytesIO()
        base_pronta.to_excel(output, index=False)
        output.seek(0)
        st.download_button(
            label="⬇️ Baixar Base Pronta Final",
            data=output,
            file_name="base_pronta_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

