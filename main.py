from pywebio.input import select, input_group, input, NUMBER, actions, radio
from pywebio.output import put_markdown, put_table, clear, put_text, toast
from pywebio.platform.tornado_http import start_server
import pandas as pd
import os

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

def menu_acoes_servidor(nome):
    while True:
        clear()
        put_markdown(f"## Gerenciar cursos para: **{nome}**")
        acao = actions("O que deseja fazer?", 
                       buttons=["Inserir curso", "Editar curso", "Excluir curso", "Voltar"])

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

        elif acao == "Voltar":
            break

def app():
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
        return

    nome = select("Selecione o servidor:", servidores)
    df_servidor = df[df["Nome do Servidor"] == nome]
    cursos = df_servidor[["Curso", "Carga Horaria"]].values.tolist()
    carga_total = df_servidor["Carga Horaria"].sum()
    status = "✅ Aprovado no PFAC 2025" if carga_total >= 40 else "❌ Não atingiu a carga mínima"

    put_markdown(f"### Cursos realizados por **{nome}**:")
    put_table([["Curso", "Carga Horária"]] + cursos)
    put_markdown(f"**Carga horária total:** `{carga_total}` horas")
    put_markdown(f"**Status:** `{status}`")

    acao = actions("Escolha uma ação:", buttons=["Gerenciar cursos", "Voltar"])
    if acao == "Gerenciar cursos":
        menu_acoes_servidor(nome)
    elif acao == "Voltar":
        app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    start_server(app, port=port, host="0.0.0.0", debug=False)
