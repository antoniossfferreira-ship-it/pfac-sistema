from pywebio.input import select, input_group, input, NUMBER, actions, radio
from pywebio.output import put_markdown, put_table, clear, put_text, toast, put_file
from pywebio.platform.tornado_http import start_server
import pandas as pd
import os
from io import BytesIO
import fitz  # PyMuPDF

ARQUIVO = "cursos_data.xlsx"
COLUNAS = ["Nome do Servidor", "Email", "Curso", "Carga Horaria"]

def carregar_dados():
    if not os.path.exists(ARQUIVO):
        return pd.DataFrame(columns=COLUNAS)
    return pd.read_excel(ARQUIVO, sheet_name="Cursos Realizados")

def salvar_dados(df):
    df.to_excel(ARQUIVO, index=False, sheet_name="Cursos Realizados")

def calcular_status(df):
    carga = df.groupby("Nome do Servidor")["Carga Horaria"].sum().reset_index()
    carga["Status"] = carga["Carga Horaria"].apply(lambda x: "Aprovado" if x >= 40 else "Reprovado")
    return carga

def gerar_pdf_compacto(df_filtrado):
    status_df = calcular_status(df_filtrado)
    servidores_info = []

    for nome in df_filtrado["Nome do Servidor"].unique():
        cursos = df_filtrado[df_filtrado["Nome do Servidor"] == nome][["Curso", "Carga Horaria"]]
        cursos_list = cursos["Curso"].tolist()
        carga_total = cursos["Carga Horaria"].sum()
        status = "Aprovado" if carga_total >= 40 else "Reprovado"
        servidores_info.append({
            "nome": nome,
            "cursos": ", ".join(cursos_list),
            "carga": carga_total,
            "status": status
        })

    pdf = fitz.open()
    page = pdf.new_page()
    title = "Relatório Compacto - PFAC 2025"
    page.insert_text((50, 50), title, fontsize=14)
    y = 80
    headers = ["Servidor", "Cursos", "Total (h)", "Status"]
    x_pos = [50, 180, 450, 520]
    for i, h in enumerate(headers):
        page.insert_text((x_pos[i], y), h, fontsize=11)
    y += 20

    for item in servidores_info:
        page.insert_text((x_pos[0], y), item["nome"], fontsize=10)
        page.insert_text((x_pos[1], y), item["cursos"], fontsize=10)
        page.insert_text((x_pos[2], y), str(item["carga"]), fontsize=10)
        page.insert_text((x_pos[3], y), item["status"], fontsize=10)
        y += 15
        if y > 780:
            page = pdf.new_page()
            y = 50

    buffer = BytesIO()
    pdf.save(buffer)
    buffer.seek(0)
    return buffer, servidores_info

def menu_acoes_servidor(nome):
    while True:
        clear()
        put_markdown(f"## Gerenciar servidor: **{nome}**")
        acao = actions("Escolha uma ação:", 
                       buttons=["Inserir curso", "Editar curso", "Excluir curso", 
                                "Editar servidor", "Excluir servidor", "Voltar"])

        df = carregar_dados()
        if acao == "Inserir curso":
            form = input_group("Novo Curso", [
                input("Nome do curso", name="curso"),
                input("Carga horária", name="carga", type=NUMBER)
            ])
            email = df[df["Nome do Servidor"] == nome]["Email"].iloc[0]
            novo = pd.DataFrame([[nome, email, form["curso"], form["carga"]]], columns=COLUNAS)
            df = pd.concat([df, novo], ignore_index=True)
            salvar_dados(df)
            toast("Curso inserido com sucesso!", duration=3)

        elif acao == "Editar curso":
            df_servidor = df[df["Nome do Servidor"] == nome]
            cursos = df_servidor["Curso"].unique().tolist()
            if not cursos:
                toast("Nenhum curso encontrado.", color="warn")
                continue
            curso_sel = select("Escolha o curso para editar", cursos)
            curso_row = df_servidor[df_servidor["Curso"] == curso_sel].index[0]
            form = input_group("Editar Curso", [
                input("Novo nome do curso", name="curso", value=curso_sel),
                input("Nova carga horária", name="carga", type=NUMBER, value=int(df.loc[curso_row, "Carga Horaria"]))
            ])
            df.loc[curso_row, "Curso"] = form["curso"]
            df.loc[curso_row, "Carga Horaria"] = form["carga"]
            salvar_dados(df)
            toast("Curso editado com sucesso!", duration=3)

        elif acao == "Excluir curso":
            df_servidor = df[df["Nome do Servidor"] == nome]
            cursos = df_servidor["Curso"].unique().tolist()
            if not cursos:
                toast("Nenhum curso encontrado.", color="warn")
                continue
            curso_sel = select("Escolha o curso para excluir", cursos)
            confirmar = actions(f"Deseja excluir o curso '{curso_sel}'?", buttons=["Sim", "Cancelar"])
            if confirmar == "Sim":
                df = df[~((df["Nome do Servidor"] == nome) & (df["Curso"] == curso_sel))]
                salvar_dados(df)
                toast("Curso excluído!", duration=3)

        elif acao == "Editar servidor":
            email_antigo = df[df["Nome do Servidor"] == nome]["Email"].iloc[0]
            form = input_group("Editar servidor", [
                input("Novo nome", name="novo_nome", value=nome),
                input("Novo email", name="novo_email", value=email_antigo)
            ])
            df.loc[df["Nome do Servidor"] == nome, "Nome do Servidor"] = form["novo_nome"]
            df.loc[df["Nome do Servidor"] == form["novo_nome"], "Email"] = form["novo_email"]
            salvar_dados(df)
            toast("Servidor editado com sucesso!", duration=3)
            nome = form["novo_nome"]

        elif acao == "Excluir servidor":
            confirmar = actions(f"Excluir TODOS os cursos de '{nome}'?", buttons=["Sim", "Cancelar"])
            if confirmar == "Sim":
                df = df[df["Nome do Servidor"] != nome]
                salvar_dados(df)
                toast("Servidor excluído!", duration=3)
                break

        elif acao == "Voltar":
            break

def app():
    while True:
        clear()
        put_markdown("# Sistema PFAC 2025")

        df = carregar_dados()
        if df.empty:
            put_text("Nenhum dado encontrado.")
            return

        status_df = calcular_status(df)
        filtro = radio("Filtrar por status:", options=["Todos", "Aprovado", "Reprovado"])

        if filtro != "Todos":
            status_df = status_df[status_df["Status"] == filtro]

        servidores = sorted(status_df["Nome do Servidor"].unique())
        if not servidores:
            put_text("Nenhum servidor encontrado para o filtro selecionado.")
            continue

        nome = select("Selecione o servidor:", servidores)
        df_servidor = df[df["Nome do Servidor"] == nome]
        cursos = df_servidor[["Curso", "Carga Horaria"]].values.tolist()
        carga_total = df_servidor["Carga Horaria"].sum()
        status = "✅ Aprovado no PFAC 2025" if carga_total >= 40 else "❌ Não atingiu a carga mínima"

        put_markdown(f"### Cursos realizados por **{nome}**:")
        put_table([["Curso", "Carga Horária"]] + cursos)
        put_markdown(f"**Carga horária total:** `{carga_total}` horas")
        put_markdown(f"**Status:** `{status}`")

        acao = actions("Escolha uma ação:", buttons=["Gerenciar servidor", "Gerar relatório PDF", "Voltar"])
        if acao == "Gerenciar servidor":
            menu_acoes_servidor(nome)
        elif acao == "Gerar relatório PDF":
            df_filtrado = df[df["Nome do Servidor"].isin(servidores)]
            pdf_buffer, dados_resumo = gerar_pdf_compacto(df_filtrado)

            tabela = [["Servidor", "Cursos", "Total (h)", "Status"]]
            for item in dados_resumo:
                tabela.append([item["nome"], item["cursos"], item["carga"], item["status"]])
            clear()
            put_markdown("## Relatório Compacto (com base no filtro)")
            put_table(tabela)
            put_file("relatorio_pfac_2025.pdf", pdf_buffer.read(), "📄 Baixar Relatório PDF")
            actions("Voltar para início", buttons=["Voltar"])
        elif acao == "Voltar":
            continue

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    start_server(app, port=port, host="0.0.0.0", debug=False)
