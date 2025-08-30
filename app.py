import streamlit as st
import pandas as pd
from io import BytesIO
import json
import ast
import os

# Importa il motore di calcolo e i dati di default
from engine import generate_schedule
from utils import load_config, save_config

# --- Funzioni di supporto per l'UI ---
def dataframe_to_excel_bytes(dfs):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name)
    processed_data = output.getvalue()
    return processed_data


def style_days(row):
    day_colors = {"LUN": "#FFFFCC", "MAR": "#CCFFCC", "MER": "#CCE5FF", "GIO": "#FFDDCC", "VEN": "#E5CCFF"}
    
    # Gestisci il caso in cui row.name potrebbe essere un numero o una stringa
    if isinstance(row.name, str) and len(row.name) >= 3:
        day = row.name[:3]
        color = day_colors.get(day, "")
        if color:
            style = f'background-color: {color}; color: black;'
            return [style] * len(row)
    
    return [''] * len(row)


# --- VALIDAZIONE CONFIG ---
def _is_half_hour_multiple(v):
    try:
        return abs((float(v) * 2) - round(float(v) * 2)) < 1e-6
    except Exception:
        return False


def validate_config(cfg: dict):
    """Valida la configurazione costruita via UI. Ritorna (ok, errors, warnings)."""
    errors = []
    warnings = []

    # Chiavi essenziali
    required_keys = [
        'GIORNI', 'CLASSI', 'SLOT_1', 'SLOT_2', 'SLOT_3',
        'ASSEGNAZIONE_SLOT', 'ORE_SETTIMANALI_CLASSI',
        'MAX_ORE_SETTIMANALI_DOCENTI', 'ASSEGNAZIONE_DOCENTI'
    ]
    for k in required_keys:
        if k not in cfg:
            errors.append(f"Chiave di configurazione mancante: {k}")

    if errors:
        return False, errors, warnings

    # GIORNI
    giorni = cfg['GIORNI']
    if not isinstance(giorni, (list, tuple)) or not giorni:
        errors.append("'GIORNI' deve essere una lista non vuota.")
    if len(set(giorni)) != len(giorni):
        warnings.append("'GIORNI' contiene duplicati. Verranno considerati una sola volta.")

    # SLOT
    for slot_name in ['SLOT_1', 'SLOT_2', 'SLOT_3']:
        slot = cfg.get(slot_name, [])
        if not isinstance(slot, (list, tuple)) or len(slot) == 0:
            errors.append(f"'{slot_name}' deve essere una lista non vuota di [fascia_oraria, durata].")
            continue
        for idx, item in enumerate(slot):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                errors.append(f"{slot_name}[{idx}] non è una coppia valida [fascia_oraria, durata].")
                continue
            fascia, durata = item
            if not isinstance(fascia, str) or '-' not in fascia:
                warnings.append(f"{slot_name}[{idx}] ha una fascia oraria non standard: '{fascia}'. Formato atteso 'H:MM-H:MM'.")
            try:
                d = float(durata)
                if d <= 0:
                    errors.append(f"{slot_name}[{idx}] ha una durata <= 0.")
                elif not _is_half_hour_multiple(d):
                    warnings.append(f"{slot_name}[{idx}] durata {d} non è multiplo di 0.5h: sarà arrotondata internamente.")
            except Exception:
                errors.append(f"{slot_name}[{idx}] durata non numerica: '{durata}'.")

    # CLASSI
    classi = cfg['CLASSI']
    if not isinstance(classi, (list, tuple)) or not classi:
        errors.append("'CLASSI' deve essere una lista non vuota.")

    # ORE_SETTIMANALI_CLASSI
    ore_cl = cfg['ORE_SETTIMANALI_CLASSI']
    for cl in classi:
        v = ore_cl.get(cl)
        if v is None:
            errors.append(f"Manca 'ORE_SETTIMANALI_CLASSI' per la classe {cl}.")
            continue
        try:
            vv = int(v)
            if vv <= 0:
                errors.append(f"Ore settimanali per {cl} devono essere > 0.")
        except Exception:
            errors.append(f"Ore settimanali per {cl} non numeriche: '{v}'.")

    # ASSEGNAZIONE_SLOT per ogni classe e giorno
    valid_slots = {"SLOT_1", "SLOT_2", "SLOT_3"}
    for cl in classi:
        per_class = cfg['ASSEGNAZIONE_SLOT'].get(cl)
        if per_class is None:
            errors.append(f"Manca 'ASSEGNAZIONE_SLOT' per la classe {cl}.")
            continue
        for day in giorni:
            slot_val = per_class.get(day)
            if slot_val not in valid_slots:
                errors.append(f"ASSEGNAZIONE_SLOT per {cl} nel giorno {day} non valido: {slot_val}.")

    # MAX_ORE_SETTIMANALI_DOCENTI
    try:
        max_ore_doc = int(cfg['MAX_ORE_SETTIMANALI_DOCENTI'])
        if max_ore_doc <= 0:
            errors.append("'MAX_ORE_SETTIMANALI_DOCENTI' deve essere > 0.")
    except Exception:
        errors.append("'MAX_ORE_SETTIMANALI_DOCENTI' non è numerico.")

    # ASSEGNAZIONE_DOCENTI
    per_classe_assegnate = {cl: 0 for cl in classi}
    for docente, assignments in cfg['ASSEGNAZIONE_DOCENTI'].items():
        if not isinstance(assignments, dict):
            errors.append(f"Assegnazioni del docente {docente} non valide.")
            continue
        total_doc_hours = 0
        for k, v in assignments.items():
            if k == 'copertura':
                try:
                    cov = int(v)
                    if cov < 0:
                        errors.append(f"Docente {docente}: ore di copertura negative.")
                    total_doc_hours += max(0, cov)
                except Exception:
                    errors.append(f"Docente {docente}: ore di copertura non numeriche: '{v}'.")
                continue
            if k not in classi:
                errors.append(f"Docente {docente}: classe '{k}' non esiste nella lista CLASSI.")
                continue
            try:
                hv = int(v)
                if hv <= 0:
                    errors.append(f"Docente {docente} in {k}: ore devono essere > 0.")
                else:
                    per_classe_assegnate[k] += hv
                    total_doc_hours += hv
            except Exception:
                errors.append(f"Docente {docente} in {k}: ore non numeriche: '{v}'.")
        if 'MAX_ORE_SETTIMANALI_DOCENTI' in cfg and total_doc_hours > cfg['MAX_ORE_SETTIMANALI_DOCENTI']:
            errors.append(f"Docente {docente}: ore totali assegnate {total_doc_hours} superano il massimo {cfg['MAX_ORE_SETTIMANALI_DOCENTI']}.")

    # Copertura ore richieste per classe
    for cl in classi:
        req = ore_cl.get(cl, 0)
        got = per_classe_assegnate.get(cl, 0)
        if got < req:
            errors.append(f"Classe {cl}: ore assegnate {got} < richieste {req}.")

    # VALIDAZIONE ASSEGNAZIONE_DOCENTI_SPECIFICHE
    if 'ASSEGNAZIONE_DOCENTI_SPECIFICHE' in cfg:
        specifiche = cfg['ASSEGNAZIONE_DOCENTI_SPECIFICHE']
        
        # Supporta sia il formato dict che il formato lista (interno)
        if isinstance(specifiche, dict):
            # Formato JSON: {docente: [classe, giorno, orario, durata]} o {docente: [[classe, giorno, orario, durata], ...]}
            for docente, assegnazioni in specifiche.items():
                # Verifica che il docente esista in ASSEGNAZIONE_DOCENTI
                if docente not in cfg['ASSEGNAZIONE_DOCENTI']:
                    errors.append(f"Docente {docente} in ASSEGNAZIONE_DOCENTI_SPECIFICHE non trovato in ASSEGNAZIONE_DOCENTI.")
                    continue
                
                # Gestisce sia formato singolo che multiplo
                assignments_to_check = []
                if isinstance(assegnazioni, list):
                    if len(assegnazioni) == 4 and isinstance(assegnazioni[0], str):
                        # Formato singolo: [classe, giorno, orario, durata]
                        assignments_to_check = [assegnazioni]
                    else:
                        # Formato multiplo: [[classe, giorno, orario, durata], ...]
                        assignments_to_check = assegnazioni
                
                for i, assegnazione in enumerate(assignments_to_check):
                    # Verifica formato dell'assegnazione: [classe, giorno, orario, durata]
                    if not isinstance(assegnazione, (list, tuple)) or len(assegnazione) != 4:
                        errors.append(f"Assegnazione {i+1} per docente {docente} deve essere [classe, giorno, orario, durata].")
                        continue
                        
                    classe, giorno, orario, durata = assegnazione
                    
                    # Verifica che la classe esista
                    if classe not in classi:
                        errors.append(f"Classe {classe} per {docente} in ASSEGNAZIONE_DOCENTI_SPECIFICHE non esiste.")
                        continue
                        
                    # Verifica che il docente sia assegnato a quella classe
                    if classe not in cfg['ASSEGNAZIONE_DOCENTI'][docente]:
                        errors.append(f"Docente {docente} ha assegnazione specifica per {classe} ma non è assegnato a quella classe.")
                        continue
                    
                    # Verifica formato giorno, orario, durata
                    if giorno not in cfg['GIORNI']:
                        errors.append(f"Giorno {giorno} per {docente}-{classe} non valido.")
                    
                    # Verifica che l'orario sia un orario di inizio valido dagli slot
                    valid_times = set()
                    for slot_name in ['SLOT_1', 'SLOT_2', 'SLOT_3']:
                        if slot_name in cfg:
                            for time_range, duration in cfg[slot_name]:
                                start_time = time_range.split('-')[0]
                                valid_times.add(start_time)
                    
                    if orario not in valid_times:
                        errors.append(f"Orario {orario} per {docente}-{classe} non valido. Orari disponibili: {sorted(valid_times)}.")
                    
                    try:
                        durata_num = float(durata)
                        if durata_num <= 0 or durata_num > 6:
                            errors.append(f"Durata {durata} per {docente}-{classe} deve essere tra 0 e 6 ore.")
                    except (ValueError, TypeError):
                        errors.append(f"Durata {durata} per {docente}-{classe} non è un numero valido.")
                        continue
                    
                    # --- VALIDAZIONI AVANZATE DI COMPATIBILITÀ ---
                    
                    # 1. Verifica compatibilità con ASSEGNAZIONE_SLOT
                    if 'ASSEGNAZIONE_SLOT' in cfg and classe in cfg['ASSEGNAZIONE_SLOT'] and giorno in cfg['ASSEGNAZIONE_SLOT'][classe]:
                        slot_type = cfg['ASSEGNAZIONE_SLOT'][classe][giorno]
                        if slot_type in cfg:
                            class_slots = cfg[slot_type]
                            # Verifica che l'orario sia disponibile per quella classe in quel giorno
                            available_for_class = [time_range.split('-')[0] for time_range, _ in class_slots]
                            if orario not in available_for_class:
                                errors.append(f"Orario {orario} non disponibile per classe {classe} il {giorno} (usa {slot_type}).")
                            
                            # Verifica che ci sia spazio sufficiente per la durata richiesta
                            try:
                                start_idx = available_for_class.index(orario)
                                total_duration_available = sum(dur for _, dur in class_slots[start_idx:])
                                if durata_num > total_duration_available:
                                    errors.append(f"Durata {durata}h per {docente}-{classe} alle {orario} di {giorno} eccede il tempo disponibile ({total_duration_available}h).")
                            except (ValueError, IndexError):
                                pass
                    
                    # 2. Verifica compatibilità con START_AT
                    if 'START_AT' in cfg and docente in cfg['START_AT'] and giorno in cfg['START_AT'][docente]:
                        min_start_hour = cfg['START_AT'][docente][giorno]
                        try:
                            orario_hour = float(orario.split(':')[0]) + float(orario.split(':')[1])/60
                            if orario_hour < min_start_hour:
                                errors.append(f"Orario {orario} per {docente} il {giorno} viola il vincolo START_AT (min {min_start_hour}).")
                        except (ValueError, IndexError):
                            pass
                    
                    # 3. Verifica compatibilità con END_AT
                    if 'END_AT' in cfg and docente in cfg['END_AT'] and giorno in cfg['END_AT'][docente]:
                        max_end_hour = cfg['END_AT'][docente][giorno]
                        try:
                            orario_hour = float(orario.split(':')[0]) + float(orario.split(':')[1])/60
                            end_hour = orario_hour + durata_num
                            if end_hour > max_end_hour:
                                errors.append(f"Orario {orario}+{durata}h per {docente} il {giorno} viola il vincolo END_AT (max {max_end_hour}).")
                        except (ValueError, IndexError, TypeError):
                            pass
                    
                    # 4. Verifica compatibilità con ONLY_DAYS
                    if 'ONLY_DAYS' in cfg and docente in cfg['ONLY_DAYS']:
                        allowed_days = cfg['ONLY_DAYS'][docente]
                        if isinstance(allowed_days, (list, set)) and giorno not in allowed_days:
                            errors.append(f"Giorno {giorno} per {docente} viola il vincolo ONLY_DAYS ({list(allowed_days)}).")
                    
                    # 5. Verifica compatibilità con MAX_DAILY_HOURS_PER_CLASS
                    if 'MAX_DAILY_HOURS_PER_CLASS' in cfg and 'USE_MAX_DAILY_HOURS_PER_CLASS' in cfg and cfg['USE_MAX_DAILY_HOURS_PER_CLASS']:
                        max_daily = cfg['MAX_DAILY_HOURS_PER_CLASS']
                        if durata_num > max_daily:
                            warnings.append(f"Durata {durata}h per {docente}-{classe} eccede MAX_DAILY_HOURS_PER_CLASS ({max_daily}h).")
                    
                    # 6. Verifica compatibilità con HOURS_PER_DAY_PER_CLASS
                    if 'HOURS_PER_DAY_PER_CLASS' in cfg and docente in cfg['HOURS_PER_DAY_PER_CLASS']:
                        exact_hours = cfg['HOURS_PER_DAY_PER_CLASS'][docente]
                        if durata_num != exact_hours:
                            errors.append(f"Durata {durata}h per {docente}-{classe} viola HOURS_PER_DAY_PER_CLASS (richieste esattamente {exact_hours}h).")
                    
                    # 7. Verifica compatibilità con ORE_SETTIMANALI_CLASSI
                    if 'ORE_SETTIMANALI_CLASSI' in cfg and classe in cfg['ORE_SETTIMANALI_CLASSI']:
                        if docente in cfg['ORE_SETTIMANALI_CLASSI'][classe]:
                            weekly_hours = cfg['ORE_SETTIMANALI_CLASSI'][classe][docente]
                            # Calcola le ore totali specifiche per questa combinazione docente-classe
                            total_specific_hours = 0
                            for spec_classe, spec_giorno, spec_orario, spec_durata in assignments_to_check:
                                if spec_classe == classe:
                                    try:
                                        total_specific_hours += float(spec_durata)
                                    except (ValueError, TypeError):
                                        pass
                            
                            if total_specific_hours > weekly_hours:
                                errors.append(f"Ore specifiche totali {total_specific_hours}h per {docente}-{classe} eccedono ORE_SETTIMANALI_CLASSI ({weekly_hours}h).")
                            elif total_specific_hours == weekly_hours:
                                warnings.append(f"Ore specifiche {total_specific_hours}h per {docente}-{classe} saturano completamente ORE_SETTIMANALI_CLASSI.")
        
        elif isinstance(specifiche, list):
            # Formato interno: [[docente, classe, giorno, orario, durata], ...]
            for i, assegnazione in enumerate(specifiche):
                if not isinstance(assegnazione, (list, tuple)) or len(assegnazione) != 5:
                    errors.append(f"Assegnazione specifica {i+1} deve essere [docente, classe, giorno, orario, durata].")
                    continue
                    
                docente, classe, giorno, orario, durata = assegnazione
                
                # Verifica che il docente esista
                if docente not in cfg['ASSEGNAZIONE_DOCENTI']:
                    errors.append(f"Docente {docente} in assegnazione specifica {i+1} non trovato in ASSEGNAZIONE_DOCENTI.")
                    continue
                    
                # Verifica che la classe esista
                if classe not in classi:
                    errors.append(f"Classe {classe} in assegnazione specifica {i+1} non esiste.")
                    continue
                    
                # Verifica che il docente sia assegnato a quella classe
                if classe not in cfg['ASSEGNAZIONE_DOCENTI'][docente]:
                    errors.append(f"Docente {docente} ha assegnazione specifica per {classe} ma non è assegnato a quella classe.")
                    continue

    return len(errors) == 0, errors, warnings


# --- INIZIALIZZAZIONE DELLO STATO ---
if 'config' not in st.session_state:
    config_data = load_config()
    if config_data:
        st.session_state.config = config_data
    else:
        # Se load_config fallisce, stampa l'errore nell'interfaccia
        # e ferma l'esecuzione dello script Streamlit.
        st.error("Caricamento della configurazione fallito. Controlla il file config.json.")
        st.stop()

# --- INTERFACCIA UTENTE ---
st.set_page_config(layout="wide", page_title="Generatore Orario Scolastico")
st.title("Generatore Orario Scolastico Interattivo")
st.caption("Un'applicazione per configurare e generare l'orario scolastico in modo semplice e intuitivo.")

# --- UI DI CONFIGURAZIONE IN UN ACCORDION ---
with st.expander("⚙️ **Apri per configurare Dati e Vincoli**", expanded=False):
    
    tab_classi, tab_docenti, tab_vincoli_spec, tab_vincoli_gen = st.tabs([
        "**1. Classi e Orari**", 
        "**2. Docenti e Assegnazioni**", 
        "**3. Vincoli Specifici**", 
        "**4. Vincoli Generici**"
    ])

    # --- Scheda Classi e Orari ---
    with tab_classi:
        st.subheader("Impostazioni Generali")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.config['GIORNI'] = ast.literal_eval(st.text_input("Giorni della settimana", value=str(st.session_state.config['GIORNI'])))
        with c2:
            st.session_state.config['MAX_ORE_SETTIMANALI_DOCENTI'] = st.number_input("Max Ore Settimanali per Docente", min_value=1, value=st.session_state.config['MAX_ORE_SETTIMANALI_DOCENTI'])

        st.subheader("Definizione Interattiva degli Slot Orari")
        c1, c2, c3 = st.columns(3)
        slot_names = ["SLOT_1", "SLOT_2", "SLOT_3"]
        for col, slot_name in zip([c1, c2, c3], slot_names):
            with col:
                st.markdown(f"**{slot_name}**")
                # Converti la lista di tuple in DataFrame per l'editor
                slot_df = pd.DataFrame(st.session_state.config[slot_name], columns=["Fascia Oraria", "Durata (ore)"])
                edited_slot_df = st.data_editor(slot_df, num_rows="dynamic", key=f"editor_{slot_name}", hide_index=True)
                # Riconverti il DataFrame modificato in lista di tuple
                st.session_state.config[slot_name] = [tuple(row) for row in edited_slot_df.itertuples(index=False)]
        
        st.divider()

        st.subheader("Griglia Classi: Ore e Assegnazione Slot")
        classi_str = st.text_input("Aggiungi o rimuovi classi (separate da virgola)", value=", ".join(st.session_state.config['CLASSI']))
        st.session_state.config['CLASSI'] = [c.strip() for c in classi_str.split(',') if c.strip()]
        
        class_data = []
        for cl in st.session_state.config['CLASSI']:
            class_info = {'Classe': cl, 'Ore Settimanali': st.session_state.config['ORE_SETTIMANALI_CLASSI'].get(cl, 27)}
            for day in st.session_state.config['GIORNI']:
                class_info[day] = st.session_state.config['ASSEGNAZIONE_SLOT'].get(cl, {}).get(day, "SLOT_1")
            class_data.append(class_info)
        
        edited_df = st.data_editor(pd.DataFrame(class_data), hide_index=True, use_container_width=True,
            column_config={
                "Classe": st.column_config.TextColumn("Classe", disabled=True),
                "Ore Settimanali": st.column_config.NumberColumn("Ore Sett.", required=True, min_value=10, max_value=40),
                **{day: st.column_config.SelectboxColumn(day, options=slot_names, required=True) for day in st.session_state.config['GIORNI']}
            })
        for _, row in edited_df.iterrows():
            cl = row['Classe']
            st.session_state.config['ORE_SETTIMANALI_CLASSI'][cl] = row['Ore Settimanali']
            if cl not in st.session_state.config['ASSEGNAZIONE_SLOT']: st.session_state.config['ASSEGNAZIONE_SLOT'][cl] = {}
            for day in st.session_state.config['GIORNI']: st.session_state.config['ASSEGNAZIONE_SLOT'][cl][day] = row[day]

    # --- Scheda Docenti (con UI assegnazioni migliorata) ---
    with tab_docenti:
        c1, c2 = st.columns([3, 1])
        with c1: new_teacher_name = st.text_input("Nome del nuovo docente", key="new_teacher_name")
        with c2:
            if st.button("Aggiungi Docente", use_container_width=True, key="add_teacher_btn"):
                if new_teacher_name and new_teacher_name not in st.session_state.config['ASSEGNAZIONE_DOCENTI']:
                    st.session_state.config['ASSEGNAZIONE_DOCENTI'][new_teacher_name] = {}; st.rerun()
                else: st.warning("Nome docente non valido o già esistente.")
        st.divider()
        st.subheader("Gestione Assegnazioni Docenti")
        
        for teacher in list(st.session_state.config['ASSEGNAZIONE_DOCENTI'].keys()):
            with st.expander(f"👨‍🏫 **{teacher}**"):
                assignments = st.session_state.config['ASSEGNAZIONE_DOCENTI'][teacher]
                
                copertura_hours = assignments.get('copertura', 0)
                class_hours = sum(h for c, h in assignments.items() if c != 'copertura')
                total_hours = class_hours + copertura_hours
                max_hours = st.session_state.config['MAX_ORE_SETTIMANALI_DOCENTI']
                
                c1, c2 = st.columns(2)
                with c1:
                    st.metric(label="Totale Ore Assegnate", value=f"{total_hours}h", delta=f"{total_hours - max_hours}h vs Max", delta_color="inverse")
                    if total_hours > max_hours: st.error(f"Attenzione: Superato il massimo di {max_hours} ore settimanali!")
                with c2:
                    new_copertura = st.number_input("Ore di Copertura", value=copertura_hours, min_value=0, step=1, key=f"copertura_{teacher}")
                    if new_copertura > 0: assignments['copertura'] = new_copertura
                    elif 'copertura' in assignments: del assignments['copertura']

                st.markdown("**Assegnazioni Classi:**")
                assign_data = [{"Classe": cl, "Ore": h} for cl, h in assignments.items() if cl != 'copertura']
                edited_assign_df = st.data_editor(pd.DataFrame(assign_data), num_rows="dynamic", use_container_width=True, key=f"assign_editor_{teacher}",
                    column_config={
                        "Classe": st.column_config.SelectboxColumn("Classe", options=st.session_state.config['CLASSI'], required=True),
                        "Ore": st.column_config.NumberColumn("Ore", min_value=1, max_value=max_hours, required=True)
                    })
                
                for cl in list(assignments.keys()):
                    if cl != 'copertura': del assignments[cl]
                for _, row in edited_assign_df.iterrows():
                    assignments[row["Classe"]] = row["Ore"]
                
                if st.button("❌ Rimuovi Docente", key=f"remove_teacher_{teacher}", use_container_width=True, type="secondary"):
                    del st.session_state.config['ASSEGNAZIONE_DOCENTI'][teacher]; st.rerun()

        with tab_vincoli_spec:
            st.subheader("Personalizzazione dei Vincoli Specifici")
            all_teachers = list(st.session_state.config['ASSEGNAZIONE_DOCENTI'].keys())
                        
            with st.container(border=True):
                use_constraint = st.checkbox("**Minimo 2 ore/giorno di servizio se presente (per docenti specifici)**", 
                                            value='MIN_TWO_HOURS_IF_PRESENT_SPECIFIC' in st.session_state.config)
                if use_constraint:
                    st.session_state.config.setdefault('MIN_TWO_HOURS_IF_PRESENT_SPECIFIC', set())
                    selected = st.multiselect("Seleziona i docenti a cui applicare questo vincolo:", all_teachers, 
                                            default=list(st.session_state.config['MIN_TWO_HOURS_IF_PRESENT_SPECIFIC']),
                                            key="min_two_hours_multiselect")
                    st.session_state.config['MIN_TWO_HOURS_IF_PRESENT_SPECIFIC'] = set(selected)
                elif 'MIN_TWO_HOURS_IF_PRESENT_SPECIFIC' in st.session_state.config:
                    del st.session_state.config['MIN_TWO_HOURS_IF_PRESENT_SPECIFIC']

            with st.container(border=True):
                use_constraint = st.checkbox("**Min 1h/giorno in ENTRAMBE le classi assegnate**", 
                                            value='GROUP_DAILY_TWO_CLASSES' in st.session_state.config)
                if use_constraint:
                    st.session_state.config.setdefault('GROUP_DAILY_TWO_CLASSES', set())
                    selected = st.multiselect("Seleziona i docenti a cui applicare questo vincolo (solitamente chi ha 2 classi):", all_teachers, 
                                            default=list(st.session_state.config['GROUP_DAILY_TWO_CLASSES']),
                                            key="group_daily_multiselect")
                    st.session_state.config['GROUP_DAILY_TWO_CLASSES'] = set(selected)
                elif 'GROUP_DAILY_TWO_CLASSES' in st.session_state.config:
                    del st.session_state.config['GROUP_DAILY_TWO_CLASSES']

            with st.container(border=True):
                use_constraint = st.checkbox("**Durata lezione per giorno per classe**", 
                                            value='HOURS_PER_DAY_PER_CLASS' in st.session_state.config)
                if use_constraint:
                    st.session_state.config.setdefault('HOURS_PER_DAY_PER_CLASS', {})
                    st.caption("Specifica il numero di ore che ogni docente deve insegnare quando presente in una classe (0 ore = non presente, altrimenti possibilmente il numero specificato):")
                    hours_rules = [{"Docente": teacher, "Ore/Giorno": hours} 
                                  for teacher, hours in st.session_state.config['HOURS_PER_DAY_PER_CLASS'].items()]
                    edited_hours_df = st.data_editor(pd.DataFrame(hours_rules), num_rows="dynamic", use_container_width=True,
                        column_config={
                            "Docente": st.column_config.SelectboxColumn("Docente", options=all_teachers, required=True), 
                            "Ore/Giorno": st.column_config.NumberColumn("Ore/Giorno", min_value=0.5, max_value=8.0, step=0.5, required=True, help="Numero di ore quando il docente è presente nella classe")
                        })
                    new_hours_per_day = {}
                    for _, row in edited_hours_df.iterrows():
                        if row["Docente"] and row["Ore/Giorno"]:
                            new_hours_per_day[row["Docente"]] = row["Ore/Giorno"]
                    st.session_state.config['HOURS_PER_DAY_PER_CLASS'] = new_hours_per_day
                elif 'HOURS_PER_DAY_PER_CLASS' in st.session_state.config:
                    del st.session_state.config['HOURS_PER_DAY_PER_CLASS']

            with st.container(border=True):
                use_constraint = st.checkbox("**Giorni di lezione specifici**", 
                                            value='ONLY_DAYS' in st.session_state.config)
                if use_constraint:
                    st.session_state.config.setdefault('ONLY_DAYS', {})
                    only_days_rules = [{"Docente": teacher, "Giorni Consentiti": ", ".join(sorted(list(days)))} 
                                    for teacher, days in st.session_state.config['ONLY_DAYS'].items()]
                    edited_only_days_df = st.data_editor(pd.DataFrame(only_days_rules), num_rows="dynamic", use_container_width=True,
                        column_config={"Docente": st.column_config.SelectboxColumn("Docente", options=all_teachers, required=True), "Giorni Consentiti": st.column_config.TextColumn("Giorni (es: MAR, GIO, VEN)", required=True)})
                    new_only_days = {}
                    for _, row in edited_only_days_df.iterrows():
                        if row["Docente"] and row["Giorni Consentiti"]:
                            new_only_days[row["Docente"]] = {day.strip().upper() for day in row["Giorni Consentiti"].split(',') if day.strip()}
                    st.session_state.config['ONLY_DAYS'] = new_only_days
                elif 'ONLY_DAYS' in st.session_state.config:
                    del st.session_state.config['ONLY_DAYS']

            with st.container(border=True):
                use_constraint = st.checkbox("**Assegnazioni specifiche docenti**", 
                                            value='ASSEGNAZIONE_DOCENTI_SPECIFICHE' in st.session_state.config)
                if use_constraint:
                    st.session_state.config.setdefault('ASSEGNAZIONE_DOCENTI_SPECIFICHE', [])
                    
                    # Converti formato interno (lista) a formato UI se necessario
                    if isinstance(st.session_state.config['ASSEGNAZIONE_DOCENTI_SPECIFICHE'], dict):
                        temp_list = []
                        for docente, assignments in st.session_state.config['ASSEGNAZIONE_DOCENTI_SPECIFICHE'].items():
                            # Gestisce sia formato singolo che multiplo
                            if isinstance(assignments[0], str):  # Formato singolo: [classe, giorno, orario, durata]
                                classe, giorno, orario, durata = assignments
                                temp_list.append([docente, classe, giorno, orario, durata])
                            else:  # Formato multiplo: [[classe, giorno, orario, durata], ...]
                                for assignment in assignments:
                                    classe, giorno, orario, durata = assignment
                                    temp_list.append([docente, classe, giorno, orario, durata])
                        st.session_state.config['ASSEGNAZIONE_DOCENTI_SPECIFICHE'] = temp_list
                    
                    # Prepara i dati per il data_editor dal formato interno
                    assignments_data = []
                    if st.session_state.config['ASSEGNAZIONE_DOCENTI_SPECIFICHE']:
                        for assignment in st.session_state.config['ASSEGNAZIONE_DOCENTI_SPECIFICHE']:
                            if len(assignment) >= 5:
                                docente, classe, giorno, orario, durata = assignment
                                assignments_data.append({
                                    "Docente": docente,
                                    "Classe": classe,
                                    "Giorno": giorno,
                                    "Orario": orario,
                                    "Durata": durata
                                })
                    
                    # Se non ci sono assegnazioni, mostra un editor vuoto
                    if not assignments_data:
                        assignments_data = [{"Docente": "", "Classe": "", "Giorno": "", "Orario": "", "Durata": 1}]
                    
                    # Estrai tutti gli orari di inizio disponibili dagli slot
                    available_times = set()
                    for slot_name in ['SLOT_1', 'SLOT_2', 'SLOT_3']:
                        if slot_name in st.session_state.config:
                            for time_range, duration in st.session_state.config[slot_name]:
                                start_time = time_range.split('-')[0]
                                available_times.add(start_time)
                    available_times = sorted(list(available_times))
                    
                    edited_assignments_df = st.data_editor(
                        pd.DataFrame(assignments_data), 
                        num_rows="dynamic", 
                        use_container_width=True,
                        key="assegnazioni_specifiche_editor",
                        column_config={
                            "Docente": st.column_config.SelectboxColumn("Docente", options=all_teachers, required=True),
                            "Classe": st.column_config.SelectboxColumn("Classe", options=st.session_state.config['CLASSI'], required=True),
                            "Giorno": st.column_config.SelectboxColumn("Giorno", options=st.session_state.config['GIORNI'], required=True),
                            "Orario": st.column_config.SelectboxColumn("Orario", options=available_times, required=True),
                            "Durata": st.column_config.NumberColumn("Durata (ore)", min_value=0.5, max_value=6, step=0.5, required=True)
                        }
                    )
                    
                    # Aggiorna le assegnazioni specifiche nel formato interno
                    new_assignments = []
                    for _, row in edited_assignments_df.iterrows():
                        if row["Docente"] and row["Classe"] and row["Giorno"] and row["Orario"] and row["Durata"]:
                            assignment = [row["Docente"], row["Classe"], row["Giorno"], row["Orario"], float(row["Durata"])]
                            new_assignments.append(assignment)
                    
                    st.session_state.config['ASSEGNAZIONE_DOCENTI_SPECIFICHE'] = new_assignments
                    
                    st.caption("💡 Assegna docenti a specifiche classi, giorni e orari. Puoi aggiungere multiple assegnazioni per lo stesso docente.")
                    
                elif 'ASSEGNAZIONE_DOCENTI_SPECIFICHE' in st.session_state.config:
                    del st.session_state.config['ASSEGNAZIONE_DOCENTI_SPECIFICHE']

            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    use_constraint = st.checkbox("**Orario di inizio specifico**", 
                                                value='START_AT' in st.session_state.config)
                    if use_constraint:
                        st.session_state.config.setdefault('START_AT', {})
                        start_rules = [{"Docente": t, "Giorno": d, "Inizia non prima delle": h} for t, r in st.session_state.config['START_AT'].items() for d, h in r.items()]
                        edited_start_rules = st.data_editor(pd.DataFrame(start_rules), num_rows="dynamic", use_container_width=True,
                            column_config={"Docente": st.column_config.SelectboxColumn("Docente", options=all_teachers, required=True),"Giorno": st.column_config.SelectboxColumn("Giorno", options=st.session_state.config['GIORNI'], required=True),"Inizia non prima delle": st.column_config.NumberColumn("Ora", min_value=8, max_value=13, required=True)})
                        new_start_at = {}
                        for _, row in edited_start_rules.iterrows():
                            t, d, h = row["Docente"], row["Giorno"], row["Inizia non prima delle"]
                            if t not in new_start_at: new_start_at[t] = {}
                            new_start_at[t][d] = h
                        st.session_state.config['START_AT'] = new_start_at
                    elif 'START_AT' in st.session_state.config:
                        del st.session_state.config['START_AT']
            with c2:
                with st.container(border=True):
                    use_constraint = st.checkbox("**Orario di fine specifico**", 
                                                value='END_AT' in st.session_state.config)
                    if use_constraint:
                        st.session_state.config.setdefault('END_AT', {})
                        end_rules = [{"Docente": t, "Giorno": d, "Finisce entro le": h} for t, r in st.session_state.config['END_AT'].items() for d, h in r.items()]
                        edited_end_rules = st.data_editor(pd.DataFrame(end_rules), num_rows="dynamic", use_container_width=True,
                            column_config={"Docente": st.column_config.SelectboxColumn("Docente", options=all_teachers, required=True),"Giorno": st.column_config.SelectboxColumn("Giorno", options=st.session_state.config['GIORNI'], required=True),"Finisce entro le": st.column_config.NumberColumn("Ora", min_value=9, max_value=14, required=True)})
                        new_end_at = {}
                        for _, row in edited_end_rules.iterrows():
                            t, d, h = row["Docente"], row["Giorno"], row["Finisce entro le"]
                            if t not in new_end_at: new_end_at[t] = {}
                            new_end_at[t][d] = h
                        st.session_state.config['END_AT'] = new_end_at
                    elif 'END_AT' in st.session_state.config:
                        del st.session_state.config['END_AT']
            

            
    # --- Scheda Vincoli Generici ---
    with tab_vincoli_gen:
            st.subheader("Attivazione dei Vincoli Strutturali Generici")
            st.caption("Questi vincoli definiscono la qualità base dell'orario. Disattivali solo per esperimenti o se il modello fatica a trovare soluzioni.")
            with st.container(border=True):
                st.session_state.config['USE_OPTIMIZE_HOLES'] = st.checkbox(
                    "**Ottimizzazione minimizzazione buchi orari**",
                    value=st.session_state.config.get('USE_OPTIMIZE_HOLES', True),
                    help="Se attivo, il solver ottimizza l'orario per minimizzare i buchi orari. Se disattivo, trova semplicemente una soluzione valida diversa ogni volta."
                )

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.session_state.config['USE_MAX_DAILY_HOURS_PER_CLASS'] = st.checkbox(
                        "**Massimo ore/giorno per docente nella stessa classe**",
                        value=st.session_state.config.get('USE_MAX_DAILY_HOURS_PER_CLASS', True),
                        help="Impedisce che un docente tenga più del numero specificato di ore di lezione nella stessa classe in un singolo giorno."
                    )
                with col2:
                    if st.session_state.config.get('USE_MAX_DAILY_HOURS_PER_CLASS', True):
                        st.session_state.config['MAX_DAILY_HOURS_PER_CLASS'] = st.number_input(
                            "Max ore",
                            min_value=1.0,
                            max_value=8.0,
                            value=st.session_state.config.get('MAX_DAILY_HOURS_PER_CLASS', 4.0),
                            step=0.5,
                            help="Numero massimo di ore che un docente può insegnare nella stessa classe in un giorno"
                        )
                    else:
                        # Se il vincolo è disattivato, rimuovi la configurazione o imposta un default
                        st.session_state.config['MAX_DAILY_HOURS_PER_CLASS'] = st.session_state.config.get('MAX_DAILY_HOURS_PER_CLASS', 4.0)

            with st.container(border=True):
                st.session_state.config['USE_CONSECUTIVE_BLOCKS'] = st.checkbox(
                    "**I blocchi di 2 o 3 ore devono essere consecutivi**",
                    value=st.session_state.config.get('USE_CONSECUTIVE_BLOCKS', True),
                    help="Se un docente ha 2 o 3 ore nella stessa classe in un giorno, queste ore devono essere in slot adiacenti (es. 9-10 e 10-11)."
                )

            with st.container(border=True):
                st.session_state.config['USE_MAX_ONE_HOLE'] = st.checkbox(
                    "**Massimo un buco orario al giorno per docente**",
                    value=st.session_state.config.get('USE_MAX_ONE_HOLE', True),
                    help="Ogni docente può avere al massimo un'ora di buco tra due lezioni nello stesso giorno. Questo vincolo forza la compattezza dell'orario."
                )

# --- Pulsante di Generazione e Area Risultati ---
st.divider()
if st.button("🚀 **GENERA ORARIO**", use_container_width=True, type="primary"):
    # Valida e salva il config prima di generare
    ok, errs, warns = validate_config(st.session_state.config)
    if warns:
        for w in warns:
            st.warning(w)
    if not ok:
        for e in errs:
            st.error(e)
        st.stop()
    # Salvataggio su config.json (accanto all'eseguibile o alla sorgente)
    try:
        saved_path = save_config(st.session_state.config)
        st.success(f"Configurazione salvata in: `{saved_path}`")
    except Exception as e:
        st.error(f"Errore nel salvataggio della configurazione: {e}")
        st.stop()

    with st.spinner("Elaborazione in corso... Potrebbe richiedere fino a 5 minuti."):
        df_classi, df_docenti, log_output, diagnostics_output = generate_schedule(st.session_state.config)
    if df_classi is not None and df_docenti is not None:
        st.success("🎉 Orario generato con successo!")
        st.info(f"Il file 'orario_settimanale.xlsx' è stato salvato automaticamente nella cartella: `{os.getcwd()}`")
        excel_data = dataframe_to_excel_bytes({"Classi": df_classi, "Docenti": df_docenti})
        st.download_button(label="📥 Scarica una Copia dell'Orario (Excel)", data=excel_data, file_name="orario_generato.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.subheader("🗓️ Anteprima Orario - Vista per Classi")
        st.dataframe(df_classi.style.apply(style_days, axis=1), use_container_width=True)
        st.subheader("👨‍🏫 Anteprima Orario - Vista per Docenti")
        st.dataframe(df_docenti.style.apply(style_days, axis=1), use_container_width=True)
    else:
        st.error("❌ Impossibile trovare una soluzione con i vincoli e i dati forniti. Controlla il log e la diagnostica qui sotto per dettagli.")
    with st.expander("📝 Mostra Log dell'elaborazione"):
        st.code(log_output)
    with st.expander("🔍 Mostra Diagnostica e Verifica Vincoli"):
        st.code(diagnostics_output)
else:
    st.info("Controlla la configurazione nell'area espandibile qui sopra, poi clicca su 'GENERA ORARIO'.")