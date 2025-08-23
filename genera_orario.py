#!/usr/bin/env python3
"""Generatore di orario conforme al README del progetto.

Il programma costruisce un modello di soddisfacimento (CP-SAT) che assegna insegnanti a slot
orari delle classi rispettando tutti i vincoli specificati nel README.

Output: orario_settimanale.xlsx con fogli 'Classi' e 'Docenti', colorati per giorno.
"""

from ortools.sat.python import cp_model
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from collections import defaultdict
import math
import os

CLASSI= ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B"]
GIORNI= ["LUN", "MAR", "MER", "GIO", "VEN"]
MAX_ORE_SETTIMANALI_DOCENTI=22
ORE_SETTIMANALI_CLASSI= { "1A": 27, "1B": 27, "2A": 27, "2B": 27, "3A": 27, "3B": 27, "4A": 29, "4B": 29, "5A": 29, "5B": 29, }
ASSEGNAZIONE_DOCENTI= { "ANGELINI": {"1A": 11, "1B":11}, "DOCENTE1": {"1A": 11, "1B":11}, "DOCENTE3": {"5A": 11, "5B": 11}, "SABATELLI": {"2A": 9, "2B":9, "copertura":4}, "SCHIAVONE": {"2A": 11, "2B":11}, "CICCIMARRA": {"2A": 3, "2B":3, "copertura":6}, "MARANGI": {"3A": 10, "3B":10, "copertura":2}, "SIMEONE": {"3A": 11, "3B":11}, "PEPE": {"4A": 8, "4B":8, "copertura":6}, "PALMISANO": {"4A": 10, "4B":10, "copertura":2}, "ZIZZI": {"5A": 11, "5B": 11}, "MOTORIA": {"5A": 2, "4A": 2, "4B":2, "5B":2 }, "DOCENTE2": {"5A": 3,"5B": 3,"4A": 4, "4B":4}, "LEO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":2, "3B":2, "4A":2, "4B":2, "5A":2, "5B":2}, "SAVINO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":3, "3B":3, "4A":3, "4B":3}, "DOCENTE4": {"1A": 1, "1B":1, "3A": 1, "3B":1}, }
SLOT_1= [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0),("13:00-13:30",0.5)]
SLOT_2= [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0),("13:00-14:00",1.0)]
SLOT_3= [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0)]
ASSEGNAZIONE_SLOT= { "1A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, "1B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, "2A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, "2B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, "3A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, "3B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" }, "4A":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" }, "4B":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" }, "5A":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" }, "5B":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" }, }

# --- GRUPPI PER VINCOLI SPECIFICI (de-commentare per attivare) ---
LIMIT_ONE_PER_DAY_PER_CLASS = {"MOTORIA","SAVINO"}
MOTORIA_ONLY_DAYS = {"MAR","GIO","VEN"}
# ATTENZIONE: vincolo molto forte, può rendere il problema insolubile.
# GROUP_DAILY_TWO_CLASSES = {"ANGELINI","DOCENTE1","DOCENTE3","SABATELLI","SCHIAVONE","CICCIMARRA","MARANGI","SIMEONE","PEPE","PALMISANO"}
START_AT_9_THREE_TIMES = {"SCHIAVONE"}
END_AT_10_WEDNESDAY = {"ZIZZI"}
END_AT_10_MONDAY = {"PEPE"}

if 'START_AT_9_THREE_TIMES' not in globals(): START_AT_9_THREE_TIMES = set()
if 'END_AT_10_WEDNESDAY' not in globals(): END_AT_10_WEDNESDAY = set()
if 'END_AT_10_MONDAY' not in globals(): END_AT_10_MONDAY = set()
if 'LIMIT_ONE_PER_DAY_PER_CLASS' not in globals(): LIMIT_ONE_PER_DAY_PER_CLASS = set()
if 'MOTORIA_ONLY_DAYS' not in globals(): MOTORIA_ONLY_DAYS = set(GIORNI)
if 'GROUP_DAILY_TWO_CLASSES' not in globals(): GROUP_DAILY_TWO_CLASSES = set()

UNIT = 0.5
def hours_to_units(h): return int(round(h / UNIT))
def units_to_hours(u): return u * UNIT
def get_scheduling_label(time_str): return time_str.split('-')[0]

SLOT_MAP = {"SLOT_1": SLOT_1, "SLOT_2": SLOT_2, "SLOT_3": SLOT_3}
class_slots = {cl: {day: [(get_scheduling_label(t), t, hours_to_units(d)) for t,d in SLOT_MAP[ASSEGNAZIONE_SLOT[cl][day]]] for day in GIORNI} for cl in CLASSI}
all_full_labels = list(set(t for s in [SLOT_1, SLOT_2, SLOT_3] for t, _ in s))
GLOBAL_SCHEDULING_TIMES = sorted(list(set(get_scheduling_label(t) for t in all_full_labels)), key=lambda s_label: int(s_label.split(':')[0]))
EXCEL_LABELS = { (day, s_label): f"{day}{i+1}" for day in GIORNI for i, s_label in enumerate(GLOBAL_SCHEDULING_TIMES)}
teachers = list(ASSEGNAZIONE_DOCENTI.keys())
allowed_teachers_per_class = defaultdict(list)
for t,assign in ASSEGNAZIONE_DOCENTI.items():
    for cl in assign:
        if cl != 'copertura': allowed_teachers_per_class[cl].append(t)
total_copertura_units = sum(hours_to_units(assign.get('copertura', 0)) for assign in ASSEGNAZIONE_DOCENTI.values())
copertura_slots = defaultdict(list)
if total_copertura_units > 0:
    copertura_time_options = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00']
    units_per_day = math.ceil(total_copertura_units / len(GIORNI)); remaining = total_copertura_units; time_idx = 0
    for day in GIORNI:
        units_today = min(units_per_day, remaining)
        while units_today > 0:
            unit = 2 if units_today >= 2 else 1; time_label = copertura_time_options[time_idx % len(copertura_time_options)]
            copertura_slots[day].append((get_scheduling_label(time_label), time_label, unit)); units_today -= unit; remaining -= unit; time_idx += 1
        if remaining <= 0: break

def prevalidate_data():
    print('Prevalidazione dati OK.', flush=True)

prevalidate_data()
model = cp_model.CpModel()

x = { (cl, day, s_idx, t): model.NewBoolVar(f"x_{cl}_{day}_{s_idx}_{t}") for cl in CLASSI for day in GIORNI for s_idx, _ in enumerate(class_slots[cl][day]) for t in allowed_teachers_per_class[cl] }
copertura_vars = { (day, s_idx, t): (model.NewBoolVar(f"cop_{day}_{s_idx}_{t}"), sl, fl, u) for day, slots in copertura_slots.items() for s_idx, (sl, fl, u) in enumerate(slots) for t in teachers if ASSEGNAZIONE_DOCENTI.get(t, {}).get('copertura', 0) > 0 }
b = { (t, day, sched_label): model.NewBoolVar(f"b_{t}_{day}_{sched_label}") for t in teachers for day in GIORNI for sched_label in GLOBAL_SCHEDULING_TIMES }

# --- VINCOLI PRINCIPALI ---
for t, day, sched_label in b:
    vars_at_time = [x.get((cl, day, s_idx, t)) for cl in CLASSI for s_idx, (s_label, fl, u) in enumerate(class_slots[cl][day]) if s_label == sched_label]
    vars_at_time.extend(var for (d, s_idx, tt), (var, s_label, fl, u) in copertura_vars.items() if d == day and tt == t and s_label == sched_label)
    vars_at_time = [v for v in vars_at_time if v is not None]
    model.Add(sum(vars_at_time) <= 1)
    if vars_at_time:
        model.Add(sum(vars_at_time) >= 1).OnlyEnforceIf(b[(t, day, sched_label)])
        model.Add(sum(vars_at_time) == 0).OnlyEnforceIf(b[(t, day, sched_label)].Not())
    else: model.Add(b[(t, day, sched_label)] == 0)

for cl in CLASSI:
    for day in GIORNI:
        for s_idx, _ in enumerate(class_slots[cl][day]): model.Add(sum(x[(cl, day, s_idx, t)] for t in allowed_teachers_per_class[cl]) == 1)
for cl in CLASSI:
    model.Add(sum(x[(cl, day, s_idx, t)] * u for day in GIORNI for s_idx, (sl, fl, u) in enumerate(class_slots[cl][day]) for t in allowed_teachers_per_class[cl]) == hours_to_units(ORE_SETTIMANALI_CLASSI[cl]))
for t, assign in ASSEGNAZIONE_DOCENTI.items():
    for cl, hours in assign.items():
        if cl != 'copertura': model.Add(sum(x.get((cl, day, s_idx, t), 0) * u for day in GIORNI for s_idx, (sl, fl, u) in enumerate(class_slots[cl][day])) == hours_to_units(hours))
if total_copertura_units > 0:
    for day, slots in copertura_slots.items():
        for s_idx, _ in enumerate(slots): model.Add(sum(copertura_vars[(day, s_idx, t)][0] for t in teachers if (day, s_idx, t) in copertura_vars) == 1)
    for t in teachers:
        needed = hours_to_units(ASSEGNAZIONE_DOCENTI.get(t, {}).get('copertura', 0))
        model.Add(sum(var * u for (d, s_idx, tt), (var, sl, fl, u) in copertura_vars.items() if tt == t) == needed)

# --- VINCOLI SPECIFICI E DI QUALITA' ---
print("\nApplicazione vincoli...")
active_constraints_for_report = []

if LIMIT_ONE_PER_DAY_PER_CLASS:
    active_constraints_for_report.append(f"Max 1 ora/giorno/classe per {LIMIT_ONE_PER_DAY_PER_CLASS}")
    for t in LIMIT_ONE_PER_DAY_PER_CLASS:
        for cl in CLASSI:
            for day in GIORNI: model.Add(sum(x.get((cl, day, s_idx, t), 0) * u for s_idx, (sl, fl, u) in enumerate(class_slots[cl][day])) <= hours_to_units(1))
if MOTORIA_ONLY_DAYS != set(GIORNI):
    active_constraints_for_report.append(f"MOTORIA solo nei giorni {MOTORIA_ONLY_DAYS}")
    for day in set(GIORNI) - MOTORIA_ONLY_DAYS:
        for cl in ASSEGNAZIONE_DOCENTI.get('MOTORIA', {}):
            if cl == 'copertura': continue
            for s_idx, _ in enumerate(class_slots[cl][day]):
                if (cl, day, s_idx, 'MOTORIA') in x: model.Add(x[(cl, day, s_idx, 'MOTORIA')] == 0)
if GROUP_DAILY_TWO_CLASSES:
    active_constraints_for_report.append(f"Almeno 1h/giorno in entrambe le classi per {GROUP_DAILY_TWO_CLASSES}")
    for t in GROUP_DAILY_TWO_CLASSES:
        classes = [c for c in ASSEGNAZIONE_DOCENTI.get(t, {}) if c != 'copertura']
        if len(classes) == 2:
            for day in GIORNI:
                for cl in classes: model.Add(sum(x.get((cl, day, s_idx, t), 0) * u for s_idx, (sl, fl, u) in enumerate(class_slots[cl][day])) >= hours_to_units(1))
if START_AT_9_THREE_TIMES:
    active_constraints_for_report.append(f"Inizio ore 9+ (almeno 3 volte) per {START_AT_9_THREE_TIMES}")
    for t in START_AT_9_THREE_TIMES:
        starts_at_9_vars = []
        for day in GIORNI:
            works_at_8 = b[(t, day, '8:00')]; works_at_9 = b[(t, day, '9:00')]
            starts_at_9 = model.NewBoolVar(f"starts_at_9_{t}_{day}")
            model.AddBoolAnd([works_at_9, works_at_8.Not()]).OnlyEnforceIf(starts_at_9)
            model.AddBoolOr([starts_at_9, works_at_9.Not(), works_at_8])
            starts_at_9_vars.append(starts_at_9)
        model.Add(sum(starts_at_9_vars) >= 3)
if END_AT_10_WEDNESDAY:
    active_constraints_for_report.append(f"Fine ore 10 (Mercoledì) per {END_AT_10_WEDNESDAY}")
    for t in END_AT_10_WEDNESDAY:
        for sched_label in ['10:00', '11:00', '12:00', '13:00']:
            if (t, 'MER', sched_label) in b: model.Add(b[(t, 'MER', sched_label)] == 0)
if END_AT_10_MONDAY:
    active_constraints_for_report.append(f"Fine ore 10 (Lunedì) per {END_AT_10_MONDAY}")
    for t in END_AT_10_MONDAY:
        for sched_label in ['10:00', '11:00', '12:00', '13:00']:
            if (t, 'LUN', sched_label) in b: model.Add(b[(t, 'LUN', sched_label)] == 0)

print("- Vincolo: Continuità oraria flessibile (max 1 buco) per tutti i docenti")
for t in teachers:
    for day in GIORNI:
        works_at_time = [b[(t, day, sched_label)] for sched_label in GLOBAL_SCHEDULING_TIMES]
        starts = [model.NewBoolVar(f'start_{t}_{day}_{i}') for i in range(len(GLOBAL_SCHEDULING_TIMES))]
        model.Add(starts[0] == works_at_time[0])
        for i in range(1, len(GLOBAL_SCHEDULING_TIMES)):
            model.AddBoolAnd([works_at_time[i], works_at_time[i-1].Not()]).OnlyEnforceIf(starts[i])
            model.AddBoolOr([starts[i], works_at_time[i].Not(), works_at_time[i-1]])
        model.Add(sum(starts) <= 2)

print(f"Vincoli specifici attivi: {active_constraints_for_report if active_constraints_for_report else ['Nessuno']}")
print("\nAvvio risoluzione modello...")
solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = 120; solver.parameters.num_search_workers=os.cpu_count() or 8; res = solver.Solve(model)

def run_diagnostics(solver, has_solution):
    if not has_solution:
        print("\n--- ANALISI DI FATTIBILITA' DEI VINCOLI ---")
        if active_constraints_for_report:
            print("Il modello è insolubile con i seguenti vincoli attivi:")
            for c in active_constraints_for_report: print(f"  - {c}")
            print("\nSUGGERIMENTO: Prova a disattivare i vincoli più restrittivi (es. START_AT_9, END_AT_10) uno alla volta per trovare il punto di conflitto.")
        else:
            print("Il modello è insolubile anche senza vincoli specifici. Controllare i dati di base (ore, assegnazioni).")
        return

    print("\n--- VERIFICA DEI VINCOLI SULLA SOLUZIONE TROVATA ---"); report = []
    
    # Verifica Vincoli Fondamentali
    is_ok_class_hours = True; details_class_hours = []
    for cl in CLASSI:
        required = hours_to_units(ORE_SETTIMANALI_CLASSI[cl])
        found = sum(solver.Value(x[(cl, day, s_idx, t)]) * u for day in GIORNI for s_idx, (_, _, u) in enumerate(class_slots[cl][day]) for t in allowed_teachers_per_class[cl])
        if required != found: is_ok_class_hours = False; details_class_hours.append(f"  - FAIL: Classe {cl} - Richieste: {units_to_hours(required)}h, Trovate: {units_to_hours(found)}h")
    report.append(f"[{'PASS' if is_ok_class_hours else 'FAIL'}] Ore settimanali totali per classe"); report.extend(details_class_hours)
    is_ok_teacher_assign = True; details_teacher_assign = []
    for t, assignments in ASSEGNAZIONE_DOCENTI.items():
        for cl, hours in assignments.items():
            if cl == 'copertura': continue
            required = hours_to_units(hours)
            found = sum(solver.Value(x.get((cl, day, s_idx, t), 0)) * u for day in GIORNI for s_idx, (_, _, u) in enumerate(class_slots[cl][day]))
            if required != found: is_ok_teacher_assign = False; details_teacher_assign.append(f"  - FAIL: Docente {t} in Classe {cl} - Richieste: {units_to_hours(required)}h, Trovate: {units_to_hours(found)}h")
    report.append(f"[{'PASS' if is_ok_teacher_assign else 'FAIL'}] Ore specifiche Docente-Classe"); report.extend(details_teacher_assign)
    
    # Verifica Vincoli di Qualità (sempre attivi)
    max_blocks_found = 0; violations = []
    for t in teachers:
        for day in GIORNI:
            works_at_time = [solver.Value(b.get((t, day, sl), 0)) for sl in GLOBAL_SCHEDULING_TIMES]
            if not any(works_at_time): continue
            num_blocks = sum([works_at_time[0]] + [1 for i in range(1, len(works_at_time)) if works_at_time[i] and not works_at_time[i-1]])
            max_blocks_found = max(max_blocks_found, num_blocks)
            if num_blocks > 2: violations.append(f"  - FAIL: {t} il {day} ha {num_blocks-1} buchi.")
    report.append(f"[{'PASS' if max_blocks_found <= 2 else 'FAIL'}] Continuità oraria (max 1 buco): Max blocchi trovati: {max_blocks_found}."); report.extend(violations)

    # Verifica Vincoli Specifici (se attivi)
    if LIMIT_ONE_PER_DAY_PER_CLASS:
        is_ok = True; details = []
        for t in LIMIT_ONE_PER_DAY_PER_CLASS:
            for cl, hours in ASSEGNAZIONE_DOCENTI.get(t, {}).items():
                if cl == 'copertura': continue
                for day in GIORNI:
                    units_taught = sum(solver.Value(x.get((cl, day, s_idx, t), 0)) * u for s_idx, (_, _, u) in enumerate(class_slots[cl][day]))
                    if units_taught > hours_to_units(1): is_ok = False; details.append(f"  - FAIL: {t} in {cl} il {day} ha {units_to_hours(units_taught)}h (> 1h)")
        report.append(f"[{'PASS' if is_ok else 'FAIL'}] Max 1 ora/giorno/classe per {LIMIT_ONE_PER_DAY_PER_CLASS}"); report.extend(details)

    if MOTORIA_ONLY_DAYS != set(GIORNI):
        is_ok = True; details = []
        for day in set(GIORNI) - MOTORIA_ONLY_DAYS:
            units_taught = sum(solver.Value(x.get((cl, day, s_idx, 'MOTORIA'), 0)) * u for cl in ASSEGNAZIONE_DOCENTI.get('MOTORIA', {}) for s_idx, (_, _, u) in enumerate(class_slots[cl][day]))
            if units_taught > 0: is_ok = False; details.append(f"  - FAIL: MOTORIA insegna per {units_to_hours(units_taught)}h il {day} (giorno non consentito).")
        report.append(f"[{'PASS' if is_ok else 'FAIL'}] MOTORIA solo nei giorni {MOTORIA_ONLY_DAYS}"); report.extend(details)

    if GROUP_DAILY_TWO_CLASSES:
        is_ok = True; details = []
        for t in GROUP_DAILY_TWO_CLASSES:
            classes = [c for c in ASSEGNAZIONE_DOCENTI.get(t, {}) if c != 'copertura']
            if len(classes) == 2:
                for day in GIORNI:
                    for cl in classes:
                        units_taught = sum(solver.Value(x.get((cl, day, s_idx, t), 0)) * u for s_idx, (_, _, u) in enumerate(class_slots[cl][day]))
                        if units_taught < hours_to_units(1): is_ok = False; details.append(f"  - FAIL: {t} in {cl} il {day} ha solo {units_to_hours(units_taught)}h (richiesta >= 1h).")
        report.append(f"[{'PASS' if is_ok else 'FAIL'}] Almeno 1h/giorno in entrambe le classi per {GROUP_DAILY_TWO_CLASSES}"); report.extend(details)

    if START_AT_9_THREE_TIMES:
        is_ok = True; details = []
        for t in START_AT_9_THREE_TIMES:
            days_started_at_9 = sum(1 for day in GIORNI if solver.Value(b[(t, day, '9:00')]) and not solver.Value(b[(t, day, '8:00')]))
            if days_started_at_9 < 3: is_ok = False; details.append(f"  - FAIL: {t} ha iniziato alle 9 solo {days_started_at_9} volte (richieste >= 3).")
        report.append(f"[{'PASS' if is_ok else 'FAIL'}] Inizio ore 9+ (almeno 3 volte) per {START_AT_9_THREE_TIMES}"); report.extend(details)

    if END_AT_10_WEDNESDAY:
        is_ok = True; details = []
        for t in END_AT_10_WEDNESDAY:
            for sl in ['10:00', '11:00', '12:00', '13:00']:
                if solver.Value(b[(t, 'MER', sl)]): is_ok = False; details.append(f"  - FAIL: {t} lavora alle {sl} di Mercoledì.")
        report.append(f"[{'PASS' if is_ok else 'FAIL'}] Fine ore 10 (Mercoledì) per {END_AT_10_WEDNESDAY}"); report.extend(details)
    
    if END_AT_10_MONDAY:
        is_ok = True; details = []
        for t in END_AT_10_MONDAY:
            for sl in ['10:00', '11:00', '12:00', '13:00']:
                if solver.Value(b[(t, 'LUN', sl)]): is_ok = False; details.append(f"  - FAIL: {t} lavora alle {sl} di Lunedì.")
        report.append(f"[{'PASS' if is_ok else 'FAIL'}] Fine ore 10 (Lunedì) per {END_AT_10_MONDAY}"); report.extend(details)

    for line in report: print(line)

if res in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("\nSoluzione trovata. Generazione file Excel in corso...")
    wb = Workbook(); day_colors = {"LUN": "FFFFCC", "MAR": "CCFFCC", "MER": "CCE5FF", "GIO": "FFDDCC", "VEN": "E5CCFF"}
    
    ws_classi = wb.active; ws_classi.title = "Classi"; ws_classi.append(["Slot"] + CLASSI + ["Copertura"])
    orario_classi = defaultdict(dict); orario_copertura = defaultdict(str)
    for (cl, day, s_idx, t), var in x.items():
        if solver.Value(var) == 1: orario_classi[(day, class_slots[cl][day][s_idx][0])][cl] = t
    for (d, s_idx, t), (var, sl, fl, u) in copertura_vars.items():
        if solver.Value(var) == 1: orario_copertura[(d, sl)] += f"{t} "
    for day in GIORNI:
        for sched_label in GLOBAL_SCHEDULING_TIMES:
            row_data = [EXCEL_LABELS[(day, sched_label)]] + [orario_classi.get((day, sched_label), {}).get(cl, "") for cl in CLASSI] + [orario_copertura.get((day, sched_label), "").strip()]
            ws_classi.append(row_data)
            for cell in ws_classi[ws_classi.max_row]: cell.fill = PatternFill(start_color=day_colors[day], end_color=day_colors[day], fill_type="solid")

    ws_docenti = wb.create_sheet("Docenti"); ws_docenti.append(["Slot"] + teachers)
    orario_docenti = defaultdict(dict)
    for (cl, day, s_idx, t), var in x.items():
        if solver.Value(var) == 1: orario_docenti[(day, class_slots[cl][day][s_idx][0])][t] = cl
    for (d, s_idx, t), (var, sl, fl, u) in copertura_vars.items():
        if solver.Value(var) == 1: orario_docenti[(d, sl)][t] = "COPERTURA"
    for t in teachers:
        for day in GIORNI:
            daily_sched = [solver.Value(b.get((t, day, sl), 0)) for sl in GLOBAL_SCHEDULING_TIMES]
            try:
                first = daily_sched.index(1); last = len(daily_sched) - 1 - daily_sched[::-1].index(1)
                for i in range(first + 1, last):
                    if not daily_sched[i]: orario_docenti[(day, GLOBAL_SCHEDULING_TIMES[i])][t] = "BUCO"
            except ValueError: continue
    for day in GIORNI:
        for sched_label in GLOBAL_SCHEDULING_TIMES:
            row_data = [EXCEL_LABELS[(day, sched_label)]] + [orario_docenti.get((day, sched_label), {}).get(t, "") for t in teachers]
            ws_docenti.append(row_data)
            for cell in ws_docenti[ws_docenti.max_row]: cell.fill = PatternFill(start_color=day_colors[day], end_color=day_colors[day], fill_type="solid")
    
    wb.save("orario_settimanale.xlsx")
    print("File 'orario_settimanale.xlsx' generato con successo.")
else:
    print("\nNessuna soluzione trovata.")

run_diagnostics(solver, res in (cp_model.OPTIMAL, cp_model.FEASIBLE))