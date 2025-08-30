"""
Eseguibile wrapper per avviare Streamlit in un'app PyInstaller onefile.
- Include esplicitamente i moduli necessari così PyInstaller li congela.
- Risolve i percorsi di 'orario_app.py' e 'config.json' anche dentro il bundle (sys._MEIPASS).
- Avvia Streamlit sulla prima porta libera, apre il browser di default.
- In caso di errore, scrive un log accanto all'eseguibile e mostra un messaggio.
"""

import os
import sys
import traceback
import ctypes

# Import necessari affinché PyInstaller includa questi moduli nel bundle
import engine  # noqa: F401
import utils  # noqa: F401
import version  # noqa: F401
import pandas as _pandas  # noqa: F401
import openpyxl  # noqa: F401
from ortools.sat.python import cp_model as _cp_model  # noqa: F401
from streamlit.web import cli as stcli


def _bundle_base_path():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def _exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _get_free_port(preferred: int = 8501) -> int:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            port = s.getsockname()[1]
        except OSError:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
    return port


def _message_box(title: str, text: str):
    try:
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x10)
    except Exception:
        pass


def main():
    try:
        # settiamo la cartella di lavoro accanto all'eseguibile, così i file di output
        # (es. orario_settimanale.xlsx) finiscono in una posizione prevedibile
        os.chdir(_exe_dir())

        script_path = os.path.join(_bundle_base_path(), "app.py")
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Impossibile trovare 'app.py' nel bundle: {script_path}")

        port = _get_free_port(8501)

        # Disattiva il file watcher per performance in ambiente congelato.
        sys.argv = [
            "streamlit",
            "run",
            script_path,
            "--server.port",
            str(port),
            "--server.headless=false",
            "--server.fileWatcherType",
            "none",
            "--global.developmentMode=false",
            "--browser.gatherUsageStats",
            "false",
        ]
        stcli.main()
    except Exception as e:
        tb = traceback.format_exc()
        log_path = os.path.join(_exe_dir(), "streamlit_wrapper_error.log")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
        _message_box("GeneraOrarioGUI - Errore", f"Errore di avvio:\n{e}\n\nDettagli salvati in:\n{log_path}")


if __name__ == "__main__":
    main()
