# --- START OF FILE utils.py ---

import json
import sys

def load_config(config_path='config.json'):
    """Carica e processa la configurazione da un file JSON."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Garantisce che solo le flag per i vincoli GENERICI esistano,
        # con default True. I vincoli specifici sono attivati dalla loro stessa presenza.
        generic_constraint_flags = [
            'USE_MAX_DAILY_HOURS_PER_CLASS',
            'USE_CONSECUTIVE_BLOCKS',
            'USE_MAX_ONE_HOLE'
        ]
        for flag in generic_constraint_flags:
            config.setdefault(flag, True)

        # Riconverte le liste in set dove necessario
        if 'GROUP_DAILY_TWO_CLASSES' in config:
            config['GROUP_DAILY_TWO_CLASSES'] = set(config['GROUP_DAILY_TWO_CLASSES'])
        if 'LIMIT_ONE_PER_DAY_PER_CLASS' in config:
            config['LIMIT_ONE_PER_DAY_PER_CLASS'] = set(config['LIMIT_ONE_PER_DAY_PER_CLASS'])
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
        print("Assicurati che 'config.json' sia nella stessa cartella dell'eseguibile.")
        sys.exit(1) # Esce con un codice di errore
    except json.JSONDecodeError:
        print(f"ERRORE: Il file di configurazione '{config_path}' non è un JSON valido.")
        sys.exit(1) # Esce con un codice di errore