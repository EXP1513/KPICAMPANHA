import streamlit as st
import pandas as pd
from io import BytesIO
import re

# Configuração inicial do app
st.set_page_config(page_title="Base Pronta KPI x Fidelizados", page_icon="📊")
st.title("📊 Gerar Base Pronta KPI comparando com Fidelizados")

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

# Upload das duas bases
file_kpi = st.file_uploader("📂 Importar base **KPI** (Excel ou CSV)", type=["xlsx", "csv"])
file_fid = st.file_uploader("📂 Importar base **FIDELIZADOS** (Excel ou CSV)", type=["xlsx", "csv"])

if file_kpi and file_fid:
    df_kpi = read_file(file_kpi)
    df_fid = read_file(file_fid)

    # 1️⃣ Localizar colunas WhatsApp Principal nas duas bases
    col_whatsapp_kpi = next((col for col in df_kpi.columns if str(col).strip().lower() == "whatsapp principal"), None)
    col_whatsapp_fid = next((col for col in df_fid.columns if str(col).strip().lower() == "whatsapp principal"), None)

    if not col_whatsapp_kpi or not col_whatsapp_fid:
        st.error("❌ Não foi encontrada a coluna 'WhatsApp Principal' em uma das bases.")
    else:
        # 2️⃣ Remover da KPI os números que estão na Fidelizados
        df_kpi = df_kpi[~df_kpi[col_whatsapp_kpi].isin(df_fid[col_whatsapp_fid])]

        # 3️⃣ Localizar coluna Observação
        col_obs = next((col for col in df_kpi.columns if str(col).strip().lower() == "observação"), None)
        if not col_obs:
            st.error("❌ Coluna 'Observação' não encontrada na base KPI.")
        else:
            # Filtrar Médio e Fundamental
            filtro_medio = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio", case=False, na=False)]
            filtro_fundamental = df_kpi[df_kpi[col_obs].astype(str).str.contains("Fundamental", case=False, na=False)]
            base_pronta = pd.concat([filtro_medio, filtro_fundamental], ignore_index=True)

            # 4️⃣ Remover linhas indesejadas de Carteiras
            col_carteiras = next((col for col in base_pronta.columns if str(col).strip().lower() == "carteiras"), None)
            if col_carteiras:
                termos_excluir = ["SAC - Pós Venda", "Secretaria"]
                base_pronta = base_pronta[~base_pronta[col_carteiras].astype(str).str.strip().isin(termos_excluir)]

            # 5️⃣ Processar coluna Contato
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

            # 6️⃣ Manter apenas colunas Contato, WhatsApp Principal, Observação
            cols_desejadas = [c for c in [col_contato, col_whatsapp_kpi, col_obs] if c]
            base_pronta = base_pronta[cols_desejadas]

            # 7️⃣ Remover duplicatas pelo número de telefone
            if col_whatsapp_kpi:
                base_pronta = base_pronta.drop_duplicates(subset=[col_whatsapp_kpi], keep="first")

            # 8️⃣ Renomear e reordenar colunas
            mapping = {col_contato: "Nome", col_whatsapp_kpi: "Numero", col_obs: "Tipo"}
            base_pronta = base_pronta.rename(columns=mapping)
            base_pronta = base_pronta[["Nome", "Numero", "Tipo"]]

            # ✅ Exibir o resultado final
            st.success("✅ Base Pronta Final gerada com sucesso!")
            st.dataframe(base_pronta)

            # Botão de Download
            output = BytesIO()
            base_pronta.to_excel(output, index=False)
            output.seek(0)
            st.download_button(
                label="⬇️ Baixar Base Pronta Final",
                data=output,
                file_name="base_pronta_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


