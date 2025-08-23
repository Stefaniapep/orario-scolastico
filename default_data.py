# File: default_data.py

def get_default_data():
    """Restituisce un dizionario con tutti i dati di configurazione di default."""
    
    data = {}
    
    data['CLASSI'] = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B"]
    data['GIORNI'] = ["LUN", "MAR", "MER", "GIO", "VEN"]
    data['SLOT_1'] = [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0),("13:00-13:30",0.5)]
    data['SLOT_2'] = [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0),("13:00-14:00",1.0)]
    data['SLOT_3'] = [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0)]
    data['ASSEGNAZIONE_SLOT'] = { 
        "1A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, 
        "1B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, 
        "2A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, 
        "2B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, 
        "3A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, 
        "3B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, 
        "4A":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" }, 
        "4B":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" }, 
        "5A":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" }, 
        "5B":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" }, 
    }
    data['ORE_SETTIMANALI_CLASSI'] = { "1A": 27, "1B": 27, "2A": 27, "2B": 27, "3A": 27, "3B": 27, "4A": 29, "4B": 29, "5A": 29, "5B": 29, }
    data['MAX_ORE_SETTIMANALI_DOCENTI'] = 22
    data['ASSEGNAZIONE_DOCENTI'] = { 
        "ANGELINI": {"1A": 11, "1B":11}, "DOCENTE1": {"1A": 11, "1B":11}, "DOCENTE3": {"5A": 11, "5B": 11}, 
        "SABATELLI": {"2A": 9, "2B":9, "copertura":4}, "SCHIAVONE": {"2A": 11, "2B":11}, 
        "MARANGI": {"3A": 10, "3B":10, "copertura":2}, "SIMEONE": {"3A": 11, "3B":11}, 
        "PEPE": {"4A": 8, "4B":8, "copertura":6}, "PALMISANO": {"4A": 10, "4B":10, "copertura":2}, 
        "ZIZZI": {"5A": 11, "5B": 11}, "CICCIMARRA": {"2A": 3, "2B":3, "copertura":6}, 
        "MOTORIA": {"5A": 2, "4A": 2, "4B":2, "5B":2 }, "DOCENTE2": {"5A": 3,"5B": 3,"4A": 4, "4B":4}, 
        "LEO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":2, "3B":2, "4A":2, "4B":2, "5A":2, "5B":2}, 
        "SAVINO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":3, "3B":3, "4A":3, "4B":3}, 
        "DOCENTE4": {"1A": 1, "1B":1, "3A": 1, "3B":1}, 
    }

    # Vincoli Specifici (con checkbox di attivazione)
    data['GROUP_DAILY_TWO_CLASSES'] = {"ANGELINI","DOCENTE1","DOCENTE3","SABATELLI","SCHIAVONE","MARANGI","SIMEONE","PEPE","PALMISANO","ZIZZI"}
    data['LIMIT_ONE_PER_DAY_PER_CLASS'] = {"MOTORIA","SAVINO"}
    data['ONLY_DAYS'] = { "MOTORIA": {"MAR", "GIO", "VEN"} }
    data['START_AT'] = { "SCHIAVONE": {"LUN": 9, "MAR": 9, "GIO": 9} }
    data['END_AT'] = { "ZIZZI": {"MER": 10}, "PEPE": {"LUN": 10} }

    # Vincoli Generici (nuovi)
    data['USE_MAX_DAILY_HOURS_PER_CLASS'] = True
    data['USE_CONSECUTIVE_BLOCKS'] = True
    data['USE_MAX_ONE_HOLE'] = True

    return data