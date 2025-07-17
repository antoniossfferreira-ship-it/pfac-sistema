
from pywebio.input import select, input_group, input, NUMBER, actions, radio
from pywebio.output import put_markdown, put_table, clear, put_text, toast, put_file, put_buttons
from pywebio.platform.tornado_http import start_server
import pandas as pd
from openpyxl import load_workbook
import os
from io import BytesIO
import fitz  # PyMuPDF

ARQUIVO = "cursos_data.xlsx"
COLUNAS = ["Nome do Servidor", "Email", "Curso", "Carga Horaria"]

def carregar_dados():
    if not os.path.exists(ARQUIVO):
        return pd.DataFrame(columns=COLUNAS)
    return pd.read_excel(ARQUIVO, sheet_name="Cursos Realizados", engine="openpyxl")

def salvar_dados(df):
    df.to_excel(ARQUIVO, index=False, sheet_name="Cursos Realizados")

def calcular_status(df):
    carga = df.groupby("Nome do Servidor")["Carga Horaria"].sum().reset_index()
    carga["Status"] = carga["Carga Horaria"].apply(lambda x: "Aprovado" if x >= 40 else "Reprovado")
    return carga

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
        put_text("Nenhum servidor encontrado para o filtro aplicado.")
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    start_server(app, port=port, host="0.0.0.0", debug=False)
