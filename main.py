from pywebio.output import put_text, put_markdown
from pywebio.platform.tornado_http import start_server
import os

def app():
    put_markdown("# Sistema PFAC 2025")
    put_text("Servidor funcionando corretamente no Render 🚀")
    put_text("Agora podemos reativar as funcionalidades passo a passo.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    start_server(app, port=port, host="0.0.0.0", debug=False)
