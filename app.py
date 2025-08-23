import streamlit as st
import pandas as pd
from io import BytesIO
import json
import ast
import os

# Importa il motore di calcolo e i dati di default
from genera_orario_engine import generate_schedule
from default_data import get_default_data 

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
    day = row.name[:3]
    color = day_colors.get(day, "")
    if color:
        style = f'background-color: {color}; color: black;'
        return [style] * len(row)
    return [''] * len(row)

# --- INIZIALIZZAZIONE DELLO STATO ---
if 'config' not in st.session_state:
    st.session_state.config = get_default_data()

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
        "**4. Vincoli Generici**"  # NUOVA SCHEDA
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
                
                # Calcolo e visualizzazione del totale ore
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
                # Griglia interattiva per le assegnazioni
                assign_data = [{"Classe": cl, "Ore": h} for cl, h in assignments.items() if cl != 'copertura']
                edited_assign_df = st.data_editor(pd.DataFrame(assign_data), num_rows="dynamic", use_container_width=True, key=f"assign_editor_{teacher}",
                    column_config={
                        "Classe": st.column_config.SelectboxColumn("Classe", options=st.session_state.config['CLASSI'], required=True),
                        "Ore": st.column_config.NumberColumn("Ore", min_value=1, max_value=max_hours, required=True)
                    })
                
                # Aggiorna lo stato dalle modifiche della griglia
                # Rimuove prima le vecchie assegnazioni (tranne copertura) per gestire le cancellazioni
                for cl in list(assignments.keys()):
                    if cl != 'copertura': del assignments[cl]
                # Aggiunge le assegnazioni nuove/modificate
                for _, row in edited_assign_df.iterrows():
                    assignments[row["Classe"]] = row["Ore"]
                
                if st.button("❌ Rimuovi Docente", key=f"remove_teacher_{teacher}", use_container_width=True, type="secondary"):
                    del st.session_state.config['ASSEGNAZIONE_DOCENTI'][teacher]; st.rerun()

        # --- Scheda Vincoli Specifici ---
    with tab_vincoli_spec:
    # ... (Questa sezione è corretta e rimane invariata)
        st.subheader("Personalizzazione dei Vincoli Specifici")
        all_teachers = list(st.session_state.config['ASSEGNAZIONE_DOCENTI'].keys())
        with st.container(border=True):
            st.session_state.config['USE_LIMIT_ONE_PER_DAY'] = st.checkbox("**Limite 1 ora/giorno per classe**", value=st.session_state.config.get('USE_LIMIT_ONE_PER_DAY', True))
            if st.session_state.config['USE_LIMIT_ONE_PER_DAY']:
                selected = st.multiselect("Seleziona i docenti a cui applicare questo vincolo:", all_teachers, default=list(st.session_state.config.get('LIMIT_ONE_PER_DAY_PER_CLASS', [])))
                st.session_state.config['LIMIT_ONE_PER_DAY_PER_CLASS'] = set(selected)
        with st.container(border=True):
            st.session_state.config['USE_GROUP_DAILY_TWO_CLASSES'] = st.checkbox("**Min 1h/giorno in entrambe le classi assegnate**", value=st.session_state.config.get('USE_GROUP_DAILY_TWO_CLASSES', True))
            if st.session_state.config['USE_GROUP_DAILY_TWO_CLASSES']:
                selected = st.multiselect("Seleziona i docenti a cui applicare questo vincolo (solitamente chi ha 2 classi):", all_teachers, default=list(st.session_state.config.get('GROUP_DAILY_TWO_CLASSES', [])))
                st.session_state.config['GROUP_DAILY_TWO_CLASSES'] = set(selected)
        with st.container(border=True):
            st.session_state.config['USE_ONLY_DAYS'] = st.checkbox("**Giorni di lezione specifici**", value=st.session_state.config.get('USE_ONLY_DAYS', True))
            if st.session_state.config['USE_ONLY_DAYS']:
                only_days_rules = [{"Docente": teacher, "Giorni Consentiti": ", ".join(sorted(list(days)))} for teacher, days in st.session_state.config['ONLY_DAYS'].items()]
                edited_only_days_df = st.data_editor(pd.DataFrame(only_days_rules), num_rows="dynamic", use_container_width=True,
                    column_config={"Docente": st.column_config.SelectboxColumn("Docente", options=all_teachers, required=True), "Giorni Consentiti": st.column_config.TextColumn("Giorni (es: MAR, GIO, VEN)", required=True)})
                new_only_days = {}
                for _, row in edited_only_days_df.iterrows():
                    if row["Docente"] and row["Giorni Consentiti"]:
                        new_only_days[row["Docente"]] = {day.strip().upper() for day in row["Giorni Consentiti"].split(',') if day.strip()}
                st.session_state.config['ONLY_DAYS'] = new_only_days
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.session_state.config['USE_START_AT'] = st.checkbox("**Orario di inizio specifico**", value=st.session_state.config.get('USE_START_AT', True))
                if st.session_state.config['USE_START_AT']:
                    start_rules = [{"Docente": t, "Giorno": d, "Inizia non prima delle": h} for t, r in st.session_state.config['START_AT'].items() for d, h in r.items()]
                    edited_start_rules = st.data_editor(pd.DataFrame(start_rules), num_rows="dynamic", use_container_width=True,
                        column_config={"Docente": st.column_config.SelectboxColumn("Docente", options=all_teachers, required=True),"Giorno": st.column_config.SelectboxColumn("Giorno", options=st.session_state.config['GIORNI'], required=True),"Inizia non prima delle": st.column_config.NumberColumn("Ora", min_value=8, max_value=13, required=True)})
                    new_start_at = {}
                    for _, row in edited_start_rules.iterrows():
                        t, d, h = row["Docente"], row["Giorno"], row["Inizia non prima delle"]
                        if t not in new_start_at: new_start_at[t] = {}
                        new_start_at[t][d] = h
                    st.session_state.config['START_AT'] = new_start_at
        with c2:
            with st.container(border=True):
                st.session_state.config['USE_END_AT'] = st.checkbox("**Orario di fine specifico**", value=st.session_state.config.get('USE_END_AT', True))
                if st.session_state.config['USE_END_AT']:
                    end_rules = [{"Docente": t, "Giorno": d, "Finisce entro le": h} for t, r in st.session_state.config['END_AT'].items() for d, h in r.items()]
                    edited_end_rules = st.data_editor(pd.DataFrame(end_rules), num_rows="dynamic", use_container_width=True,
                        column_config={"Docente": st.column_config.SelectboxColumn("Docente", options=all_teachers, required=True),"Giorno": st.column_config.SelectboxColumn("Giorno", options=st.session_state.config['GIORNI'], required=True),"Finisce entro le": st.column_config.NumberColumn("Ora", min_value=9, max_value=14, required=True)})
                    new_end_at = {}
                    for _, row in edited_end_rules.iterrows():
                        t, d, h = row["Docente"], row["Giorno"], row["Finisce entro le"]
                        if t not in new_end_at: new_end_at[t] = {}
                        new_end_at[t][d] = h
                    st.session_state.config['END_AT'] = new_end_at

            
        # --- NUOVA SCHEDA: Vincoli Generici ---
    with tab_vincoli_gen:
            st.subheader("Attivazione dei Vincoli Strutturali Generici")
            st.caption("Questi vincoli definiscono la qualità base dell'orario. Disattivali solo per esperimenti o se il modello fatica a trovare soluzioni.")
            
            with st.container(border=True):
                st.session_state.config['USE_MAX_DAILY_HOURS_PER_CLASS'] = st.checkbox(
                    "**Massimo 4 ore/giorno per docente nella stessa classe**",
                    value=st.session_state.config.get('USE_MAX_DAILY_HOURS_PER_CLASS', True),
                    help="Impedisce che un docente tenga più di 4 ore di lezione nella stessa classe in un singolo giorno."
                )

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
    # ... (Questa sezione è corretta e rimane invariata)
    with st.spinner("Elaborazione in corso... Potrebbe richiedere fino a 2 minuti."):
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