# --- START OF FILE utils.py ---

import json
import sys
import os


def _bundle_base_path():
    """Return the base path where resources are located.
    - In PyInstaller onefile, it's sys._MEIPASS
    - Otherwise, it's the directory of this file
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def _writable_base_path():
    """Return a writable base path for saving files.
    - In PyInstaller onefile, use the directory of the executable
    - Otherwise, use the directory of this file
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def load_config(config_path='config.json'):
    """Carica e processa la configurazione da un file JSON.

    Cerca prima un override scrivibile accanto all'eseguibile/sorgente,
    poi fa fallback al file incluso nel bundle di PyInstaller.
    """
    try:
        final_path = config_path
        if not os.path.isabs(final_path):
            # 1) Override utente (scrivibile) accanto all'eseguibile/sorgente
            candidate = os.path.join(_writable_base_path(), final_path)
            if os.path.exists(candidate):
                final_path = candidate
            else:
                # 2) Fallback al bundle (read-only in onefile)
                final_path = os.path.join(_bundle_base_path(), final_path)

        with open(final_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Garantisce che solo le flag per i vincoli GENERICI esistano,
        # con default True. I vincoli specifici sono attivati dalla loro stessa presenza.
        generic_constraint_flags = [
            'USE_MAX_DAILY_HOURS_PER_CLASS',
            'USE_CONSECUTIVE_BLOCKS',
            'USE_MAX_ONE_HOLE',
            'USE_OPTIMIZE_HOLES'
        ]
        for flag in generic_constraint_flags:
            config.setdefault(flag, True)

        # Parametri numerici per i vincoli generici
        config.setdefault('MAX_DAILY_HOURS_PER_CLASS', 4.0)

        # Riconverte le liste in set dove necessario
        if 'GROUP_DAILY_TWO_CLASSES' in config:
            config['GROUP_DAILY_TWO_CLASSES'] = set(config['GROUP_DAILY_TWO_CLASSES'])
        if 'HOURS_PER_DAY_PER_CLASS' in config:
            # HOURS_PER_DAY_PER_CLASS è già un dizionario, non serve conversione
            pass
        if 'MIN_TWO_HOURS_IF_PRESENT_SPECIFIC' in config:
            config['MIN_TWO_HOURS_IF_PRESENT_SPECIFIC'] = set(config['MIN_TWO_HOURS_IF_PRESENT_SPECIFIC'])
        if 'ONLY_DAYS' in config:
            for teacher, days in config['ONLY_DAYS'].items():
                config['ONLY_DAYS'][teacher] = set(days)
        # Converte le liste di tuple per gli slot
        for key in ['SLOT_1', 'SLOT_2', 'SLOT_3']:
            if key in config:
                config[key] = [tuple(item) for item in config[key]]

        return config
    except FileNotFoundError:
        print(f"ERRORE: File di configurazione '{config_path}' non trovato!")
        print("Assicurati che 'config.json' sia nella stessa cartella dell'eseguibile o inclusa nel bundle.")
        sys.exit(1)  # Esce con un codice di errore
    except json.JSONDecodeError:
        print(f"ERRORE: Il file di configurazione '{config_path}' non è un JSON valido.")
        sys.exit(1)  # Esce con un codice di errore


def _to_jsonable(value):
    """Convert Python structures (set, tuple, nested dict/list) into JSON-serializable ones."""
    # Handle numpy scalars if present (avoid hard dependency)
    try:
        import numpy as _np  # type: ignore
        if isinstance(value, (_np.integer, _np.floating)):
            return value.item()
    except Exception:
        pass

    if isinstance(value, set):
        return sorted([_to_jsonable(v) for v in value])
    if isinstance(value, tuple):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


def save_config(config: dict, dest_path: str | None = None) -> str:
    """Salva la configurazione corrente in JSON, occupandosi delle conversioni necessarie.

    Ritorna il percorso del file salvato. Lancia eccezione in caso di errore.
    """
    # Serializza strutture non JSON (set, tuple, ecc.)
    data = dict(config)

    # Normalizza le chiavi note con set e tuple
    for key in ['GROUP_DAILY_TWO_CLASSES', 'MIN_TWO_HOURS_IF_PRESENT_SPECIFIC']:
        if key in data and isinstance(data[key], set):
            data[key] = sorted(list(data[key]))

    if 'ONLY_DAYS' in data and isinstance(data['ONLY_DAYS'], dict):
        data['ONLY_DAYS'] = {t: sorted(list(days)) for t, days in data['ONLY_DAYS'].items()}

    for key in ['SLOT_1', 'SLOT_2', 'SLOT_3']:
        if key in data:
            data[key] = [list(item) for item in data[key]]

    # Applica conversione ricorsiva come fallback generale
    data = _to_jsonable(data)

    # Determina path di destinazione
    if not dest_path:
        dest_path = os.path.join(_writable_base_path(), 'config.json')
    elif not os.path.isabs(dest_path):
        dest_path = os.path.join(_writable_base_path(), dest_path)

    # Scrive su disco
    with open(dest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return dest_path