elif opcao == "❌👋 Abandono":
    st.markdown("<div class='titulo-principal'>Gera Campanha - Abandono</div>", unsafe_allow_html=True)

    st.markdown("""
        <div class='manual-inicio'>
            <strong>PARA GERAR A BASE DE CAMPANHA É NECESSÁRIO:</strong><br>
            1️⃣ Gerar o relatório de <b>KPI de Eventos</b> para o período.<br>
            2️⃣ Gerar o relatório de <b>Contatos Fidelizados</b>.<br>
            3️⃣ Importe os arquivos abaixo.<br>
            4️⃣ O sistema irá processar e gerar a base final automaticamente.<br>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='card-importacao'><h5>Importe as bases aqui</h5></div>", unsafe_allow_html=True)

    file_kpi = st.file_uploader("📂 Importar base KPI", type=["xlsx", "csv"])
    file_fid = st.file_uploader("📂 Importar base Fidelizados", type=["xlsx", "csv"])

    if file_kpi and file_fid:

        # --- Função de leitura simples ---
        def read_file(f):
            from io import BytesIO
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

        df_kpi = read_file(file_kpi)
        df_fid = read_file(file_fid)

        # --- Localiza colunas por nome exato (case-insensitive) ---
        def col(df, nome):
            return next((c for c in df.columns if str(c).strip().lower() == nome.lower()), None)

        col_wpp_kpi = col(df_kpi, "whatsapp principal")
        col_wpp_fid = col(df_fid, "whatsapp principal")
        col_obs = col(df_kpi, "observação")
        col_carteiras = col(df_kpi, "carteiras")
        col_contato = col(df_kpi, "contato")
        col_data_evento = col(df_kpi, "data evento")

        if not all([col_wpp_kpi, col_wpp_fid, col_obs, col_contato]):
            st.error("❌ Colunas obrigatórias não encontradas na base.")
            st.stop()

        # --- Limpeza e filtros ---
        df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].astype(str).str.strip()
        df_kpi[col_wpp_kpi] = df_kpi[col_wpp_kpi].apply(lambda x: re.sub(r'^0+', '', x))

        # Remove clientes fidelizados
        df_kpi = df_kpi[~df_kpi[col_wpp_kpi].isin(df_fid[col_wpp_fid])]

        # Filtro por observação
        df_kpi = df_kpi[df_kpi[col_obs].astype(str).str.contains("Médio|Fundamental", case=False, na=False)]

        # Excluir carteiras indesejadas
        if col_carteiras:
            df_kpi = df_kpi[~df_kpi[col_carteiras].isin(["SAC - Pós Venda", "Secretaria"])]

        # --- Tratamento de nome ---
        def processar_nome(valor):
            texto_original = str(valor).strip()
            primeiro_nome = texto_original.split(' ')[0]
            nome_limpo = re.sub(r'[^a-zA-ZÀ-ÿ]', '', primeiro_nome)
            if len(nome_limpo) <= 3:
                return "Candidato"
            return nome_limpo.title()

        df_kpi[col_contato] = [processar_nome(nome) for nome in df_kpi[col_contato]]

        # --- Montar base final ---
        mapping = {col_contato: "Nome", col_wpp_kpi: "Numero", col_obs: "Tipo"}
        base_pronta = df_kpi.rename(columns=mapping)[["Nome", "Numero", "Tipo"]]
        base_pronta = base_pronta.drop_duplicates(subset=["Numero"], keep="first")

        # --- Layout final para exportação ---
        layout = ["TIPO_DE_REGISTRO", "VALOR_DO_REGISTRO", "MENSAGEM", "NOME_CLIENTE",
                  "CPFCNPJ", "CODCLIENTE", "TAG", "CORINGA1", "CORINGA2", "CORINGA3",
                  "CORINGA4", "CORINGA5", "PRIORIDADE"]

        base_export = pd.DataFrame(columns=layout)
        base_export["VALOR_DO_REGISTRO"] = base_pronta["Numero"].apply(lambda n: "55" + re.sub(r"\\D", "", str(n)).lstrip("0"))
        base_export["NOME_CLIENTE"] = base_pronta["Nome"]
        base_export["TIPO_DE_REGISTRO"] = "TELEFONE"
        base_export = base_export[layout]

        # --- Nome do arquivo com datas ---
        nome_arquivo = "Abandono.csv"
        if col_data_evento:
            df_kpi[col_data_evento] = pd.to_datetime(df_kpi[col_data_evento], errors='coerce', dayfirst=True)
            datas_validas = df_kpi[col_data_evento].dropna().dt.date
            if not datas_validas.empty:
                di, dfinal = min(datas_validas), max(datas_validas)
                if di == dfinal:
                    nome_arquivo = f"Abandono_{di.strftime('%d.%m')}.csv"
                else:
                    nome_arquivo = f"Abandono_{di.strftime('%d.%m')}_a_{dfinal.strftime('%d.%m')}.csv"

        # --- Exportação ---
        st.success(f"✅ Base de campanha pronta! {len(base_export)} registros.")
        output = BytesIO()
        base_export.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button("⬇️ Baixar campanha (.csv)", output, file_name=nome_arquivo, mime="text/csv")

        # Preview da base final
        st.markdown("<h4 style='color:#077339; margin-top:20px; text-align:center;'>POR DENTRO DA BASE</h4>", unsafe_allow_html=True)
        st.dataframe(base_export)
