def aba_carrinho():
    st.markdown("<div class='titulo-principal'>Carrinho Abandonado - Unificado</div>", unsafe_allow_html=True)
    file_carrinho = st.file_uploader("📂 Carrinho Abandonado", type=["xlsx", "csv"], key="carrinho_file")
    file_nao_pagos = st.file_uploader("📂 Não Pagos", type=["xlsx", "csv"], key="naopagos_file")
    file_pedidos = st.file_uploader("📂 Pedidos", type=["xlsx", "csv"], key="pedidos_file")
    if file_carrinho and file_nao_pagos and file_pedidos:
        df_carrinho = read_file_carrinho_abandonado(file_carrinho)
        df_nao_pagos = read_file(file_nao_pagos)
        df_pedidos = read_file(file_pedidos)
        for nome, df in zip(
            ["Carrinho Abandonado", "Não Pagos", "Pedidos"], 
            [df_carrinho, df_nao_pagos, df_pedidos]
        ):
            if df is None or df.empty:
                st.error(f"Arquivo '{nome}' inválido ou está vazio.")
                return
        df_carrinho = importar_excel_tratamento_carrinho(df_carrinho)
        df_nao_pagos = importar_excel_tratamento_nao_pagos(df_nao_pagos)
        df_unificado = pd.concat([df_carrinho, df_nao_pagos], ignore_index=True)
        if 'E-mail (cobrança)' in df_pedidos.columns:
            emails_unif = df_unificado['e-mail'].str.strip().str.lower()
            emails_ped = df_pedidos['E-mail (cobrança)'].astype(str).str.strip().str.lower()
            df_unificado = df_unificado[~emails_unif.isin(emails_ped)]
        df_unificado = df_unificado[['Nome','Numero']]
        layout_cols = ["TIPO_DE_REGISTRO","VALOR_DO_REGISTRO","MENSAGEM","NOME_CLIENTE","CPFCNPJ",
                       "CODCLIENTE","TAG","CORINGA1","CORINGA2","CORINGA3","CORINGA4","CORINGA5","PRIORIDADE"]
        df_saida = pd.DataFrame(columns=layout_cols)
        df_saida["VALOR_DO_REGISTRO"] = df_unificado["Numero"]
        df_saida["NOME_CLIENTE"] = df_unificado["Nome"].str.strip().str.lower().str.capitalize()
        df_saida["TIPO_DE_REGISTRO"] = df_saida["VALOR_DO_REGISTRO"].apply(lambda x: "TELEFONE" if str(x).strip() else "")
        email_bloqueado = "ederaldosalustianodasilvaresta@gmail.com"
        numeros_bloqueados = {"5521969999549"}
        df_saida = df_saida[
            ~(df_saida["VALOR_DO_REGISTRO"].isin(numeros_bloqueados)) &
            ~(df_saida["NOME_CLIENTE"].str.lower() == email_bloqueado.lower())
        ]
        df_saida = df_saida.drop_duplicates(subset=["VALOR_DO_REGISTRO"], keep="first")
        df_saida = df_saida[df_saida["VALOR_DO_REGISTRO"].astype(str).str.strip() != ""]
        qtd_total_final, nome_arquivo = len(df_saida), gerar_nome_arquivo_carrinho()
        st.success(f"✅ Base Carrinho pronta! Total de Leads Gerados: {qtd_total_final}")
        output = BytesIO()
        df_saida.to_csv(output, sep=";", index=False, encoding="utf-8-sig")
        output.seek(0)
        st.download_button("⬇️ Baixar (.csv)", output, file_name=nome_arquivo, mime="text/csv")
        # Exibe apenas as primeiras 100 linhas para performance local
        st.dataframe(df_saida.head(100), width=750)
        if len(df_saida) > 100:
            st.warning("Exibindo apenas as primeiras 100 linhas para melhor performance.")
