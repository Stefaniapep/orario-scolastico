# File: run_app.py
import os
import sys
import webbrowser
from threading import Timer

# Aggiunge il percorso dell'eseguibile alla path di sistema
# Questo è necessario perché l'eseguibile si decomprime in una cartella temporanea
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(application_path)

# Importa la funzione per avviare Streamlit solo dopo aver impostato il percorso
from streamlit.web import cli as stcli

# Funzione per aprire il browser dopo un breve ritardo
def open_browser():
    webbrowser.open("http://localhost:8501")

# Funzione principale
def main():
    # Costruisce il percorso completo al file app.py
    app_path = os.path.join(application_path, 'app.py')

    # Argomenti per l'avvio programmatico di Streamlit
    args = [
        app_path,
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.port=8501",
        "--client.toolbarMode=viewer",
        "--runner.spinner.type=spinner"
    ]
    
    # Apri il browser 2 secondi dopo l'avvio del server
    Timer(2, open_browser).start()
    
    # Avvia il server di Streamlit in modo sicuro e programmatico
    sys.argv = ["streamlit", "run"] + args
    stcli.main()


if __name__ == "__main__":
    main()