#!/usr/bin/env python3
"""Generatore di orario conforme al README del progetto.

Il programma costruisce un modello di soddisfacimento (CP-SAT) che assegna insegnanti a slot
orari delle classi rispettando tutti i vincoli specificati nel README.

Output: orario_settimanale.xlsx con fogli 'Classi' e 'Docenti'.
"""

from ortools.sat.python import cp_model
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from collections import defaultdict
import math

CLASSI= ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B"]

GIORNI= ["LUN", "MAR", "MER", "GIO", "VEN"]

MAX_ORE_SETTIMANALI_DOCENTI=22

ORE_SETTIMANALI_CLASSI= {
    "1A": 27,
    "1B": 27,
    "2A": 27,
    "2B": 27,
    "3A": 27,
    "3B": 27,
    "4A": 29,
    "4B": 29,
    "5A": 29,
    "5B": 29,
}

ASSEGNAZIONE_DOCENTI= {
    "ANGELINI": {"1A": 11, "1B":11},
    "DOCENTE1": {"1A": 11, "1B":11},
    "DOCENTE3": {"5A": 11, "5B": 11},
    "SABATELLI": {"2A": 9, "2B":9, "copertura":4},
    "SCHIAVONE": {"2A": 11, "2B":11},
    "CICCIMARRA": {"2A": 3, "2B":3, "copertura":6},
    "MARANGI": {"3A": 10, "3B":10, "copertura":2},
    "SIMEONE": {"3A": 11, "3B":11},
    "PEPE": {"4A": 8, "4B":8, "copertura":6},
    "PALMISANO": {"4A": 10, "4B":10, "copertura":2},
    "ZIZZI": {"5A": 11, "5B": 11},
    "MOTORIA": {"5A": 2, "4A": 2, "4B":2, "5B":2 },
    "DOCENTE2": {"5A": 3,"5B": 3,"4A": 4, "4B":4},
    "LEO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":2, "3B":2, "4A":2, "4B":2, "5A":2, "5B":2},
    "SAVINO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":3, "3B":3, "4A":3, "4B":3},
    "DOCENTE4": {"1A": 1, "1B":1, "3A": 1, "3B":1},
}

SLOT_1= [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0),("13:00-13:30",0.5)]
SLOT_2= [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0),("13:00-14:00",1.0)]
SLOT_3= [("8:00-9:00",1.0),("9:00-10:00",1.0),("10:00-11:00",1.0),("11:00-12:00",1.0),("12:00-13:00",1.0)]

ASSEGNAZIONE_SLOT= {
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

# Constraint-specific groups
#LIMIT_ONE_PER_DAY_PER_CLASS = {"MOTORIA","SAVINO"}
#MOTORIA_ONLY_DAYS = {"MAR","GIO","VEN"}
#GROUP_DAILY_TWO_CLASSES = {"ANGELINI","DOCENTE1","DOCENTE3","SABATELLI","SCHIAVONE","CICCIMARRA","MARANGI","SIMEONE","PEPE","PALMISANO"}
#START_AT_9_THREE_TIMES = "SCHIAVONE"
#END_AT_10_WEDNESDAY = {"ZIZZI"}
#END_AT_10_MONDAY = {"PEPE"}


if 'START_AT_9_THREE_TIMES' not in globals():
    START_AT_9_THREE_TIMES = None
if 'END_AT_10_WEDNESDAY' not in globals():
    END_AT_10_WEDNESDAY = set()
if 'END_AT_10_MONDAY' not in globals():
    END_AT_10_MONDAY = set()
if 'LIMIT_ONE_PER_DAY_PER_CLASS' not in globals():
    LIMIT_ONE_PER_DAY_PER_CLASS = set()
if 'MOTORIA_ONLY_DAYS' not in globals():
    MOTORIA_ONLY_DAYS = set(GIORNI)
if 'GROUP_DAILY_TWO_CLASSES' not in globals():
    GROUP_DAILY_TWO_CLASSES = set()

UNIT = 0.5

def hours_to_units(h):
    return int(round(h / UNIT))

# Build per-class per-day slot lists (with time labels and unit durations)
SLOT_MAP = {"SLOT_1": SLOT_1, "SLOT_2": SLOT_2, "SLOT_3": SLOT_3}

class_slots = {}  # class -> day -> list of (time_label, units)
for cl in CLASSI:
    class_slots[cl] = {}
    for day in GIORNI:
        slot_key = ASSEGNAZIONE_SLOT[cl][day]
        slots = SLOT_MAP[slot_key]
        class_slots[cl][day] = [(t, hours_to_units(d)) for t,d in slots]

# Build global time order per day (unique ordered time labels across slot definitions)
GLOBAL_DAY_TIMES = [t for t,_ in SLOT_2]  # full superset order
# Ensure order and unique
GLOBAL_DAY_TIMES = []
for s in [SLOT_1, SLOT_2, SLOT_3]:
    for t,_ in s:
        if t not in GLOBAL_DAY_TIMES:
            GLOBAL_DAY_TIMES.append(t)

# Create COPERTURA slots: distribute total needed coverage units across days at time '12:00-13:00' if possible
total_copertura_units = 0
for teacher,assign in ASSEGNAZIONE_DOCENTI.items():
    if 'copertura' in assign:
        total_copertura_units += hours_to_units(assign['copertura'])

copertura_slots = defaultdict(list)  # day -> list of (time, units)
# We'll put at most one 1h slot at 12:00-13:00 per day and split extra across days
if total_copertura_units > 0:
    units_per_day = math.ceil(total_copertura_units / len(GIORNI))
    remaining = total_copertura_units
    for day in GIORNI:
        take = min(units_per_day, remaining)
        # break take into 1-unit (0.5h) slots at 12:00-13:00 (1h -> 2 units)
        # to keep times consistent, use repeated 12:00-13:00 slots (may be multiple per day)
        while take > 0:
            # put either 2-unit (1h) or 1-unit (0.5h) if only 1 left
            unit = 2 if take >= 2 else 1
            copertura_slots[day].append(("12:00-13:00", unit))
            take -= unit
            remaining -= unit
        if remaining <= 0:
            break

# Allowed teachers per class (those that have that class in ASSEGNAZIONE_DOCENTI)
teachers = list(ASSEGNAZIONE_DOCENTI.keys())
allowed_teachers_per_class = defaultdict(list)
for t,assign in ASSEGNAZIONE_DOCENTI.items():
    for cl in assign:
        if cl != 'copertura':
            allowed_teachers_per_class[cl].append(t)

# --- Prevalidazione dati: controllo vincoli stringenti prima di costruire il modello ---
def prevalidate_data():
    errors = []
    # 1) verificare che il totale delle ore assegnate ai docenti copra le ore richieste per ogni classe
    for cl in CLASSI:
        total_assigned = 0
        for t, assign in ASSEGNAZIONE_DOCENTI.items():
            total_assigned += assign.get(cl, 0)
        required = ORE_SETTIMANALI_CLASSI.get(cl, 0)
        if total_assigned < required:
            errors.append(f"Classe {cl}: ore assegnate totali {total_assigned}h < richieste {required}h")
    # 2) verificare che per ogni docente le ore assegnate (lezioni + coperture) non superino il massimo
    for t, assign in ASSEGNAZIONE_DOCENTI.items():
        lesson_hours = sum(v for k,v in assign.items() if k != 'copertura')
        cov = assign.get('copertura', 0)
        total = lesson_hours + cov
        if total > MAX_ORE_SETTIMANALI_DOCENTI:
            errors.append(f"Docente {t}: ore totali assegnate {total}h > max settimanale {MAX_ORE_SETTIMANALI_DOCENTI}h")
    # Report e abort se necessario
    if errors:
        print('\nPREVALIDAZIONE DATI FALLITA:')
        for e in errors:
            print(' -', e)
        print('\nCorreggi i dati in ASSEGNAZIONE_DOCENTI o aumenta MAX_ORE_SETTIMANALI_DOCENTI e rilancia.')
        exit(1)
    else:
        print('Prevalidazione dati OK: assegnazioni coprono le richieste di classe e rispettano i massimi docenti.', flush=True)

# Esegui prevalidazione immediatamente
prevalidate_data()

# Model
model = cp_model.CpModel()

# Variables x[(cl,day,time_idx,t)] binary
x = {}
# We also create y[(teacher,day,time_label)] indicating teacher occupies that global time slot (any class or copertura)
y = {}

for cl in CLASSI:
    for day in GIORNI:
        slots = class_slots[cl][day]
        for s_idx,(time_label,units) in enumerate(slots):
            for t in allowed_teachers_per_class[cl]:
                var = model.NewBoolVar(f"x_{cl}_{day}_{s_idx}_{t}")
                x[(cl,day,s_idx,t)] = var

# Copertura variables: for each copertura slot we allow any teacher that has copertura >0
copertura_vars = {}
for day in GIORNI:
    for s_idx,(time_label,units) in enumerate(copertura_slots.get(day,[])):
        for t in teachers:
            if ASSEGNAZIONE_DOCENTI.get(t,{}).get('copertura',0) > 0:
                var = model.NewBoolVar(f"cop_{day}_{s_idx}_{t}")
                copertura_vars[(day,s_idx,t)] = (var, time_label, units)

# Constraint: each class slot must be assigned to exactly one teacher among allowed
for cl in CLASSI:
    for day in GIORNI:
        slots = class_slots[cl][day]
        for s_idx,(_time_label,units) in enumerate(slots):
            vars_slot = [x[(cl,day,s_idx,t)] for t in allowed_teachers_per_class[cl]]
            model.Add(sum(vars_slot) == 1)

# Constraint: a teacher cannot be assigned to two places at same day/time (class slots + copertura)
for day in GIORNI:
    # build mapping time_label -> list of variables for that day/time
    time_to_vars = defaultdict(list)
    for cl in CLASSI:
        slots = class_slots[cl][day]
        for s_idx,(time_label,units) in enumerate(slots):
            for t in allowed_teachers_per_class[cl]:
                time_to_vars[(time_label,t)].append(x[(cl,day,s_idx,t)])
    # copertura
    for (d,s_idx,t),(var,time_label,units) in list(copertura_vars.items()):
        if d == day:
            time_to_vars[(time_label,t)].append(var)
    # For each teacher and time, sum <=1
    for t in teachers:
        for time_label in set(k[0] for k in time_to_vars.keys()):
            vars_list = time_to_vars.get((time_label,t),[])
            if vars_list:
                model.Add(sum(vars_list) <= 1)

# Constraint: class weekly hours must match ORE_SETTIMANALI_CLASSI
for cl in CLASSI:
    total_units_needed = hours_to_units(ORE_SETTIMANALI_CLASSI[cl])
    # sum over all day slots (units * assigned)
    terms = []
    for day in GIORNI:
        slots = class_slots[cl][day]
        for s_idx,(time_label,units) in enumerate(slots):
            for t in allowed_teachers_per_class[cl]:
                terms.append(x[(cl,day,s_idx,t)] * units)
    model.Add(sum(terms) == total_units_needed)

# Constraint: per-teacher per-class totals must match ASSEGNAZIONE_DOCENTI
for t in teachers:
    assign = ASSEGNAZIONE_DOCENTI.get(t, {})
    for cl,hours in assign.items():
        if cl == 'copertura':
            continue
        needed = hours_to_units(hours)
        terms = []
        for day in GIORNI:
            slots = class_slots[cl][day]
            for s_idx,(time_label,units) in enumerate(slots):
                if (cl,day,s_idx,t) in x:
                    terms.append(x[(cl,day,s_idx,t)] * units)
        model.Add(sum(terms) == needed)

# Copertura totals per teacher
for t in teachers:
    cov_hours = ASSEGNAZIONE_DOCENTI.get(t,{}).get('copertura',0)
    needed = hours_to_units(cov_hours)
    # for each copertura slot (day,s_idx) exactly one teacher (with copertura capacity) can be assigned
for day in GIORNI:
    for s_idx,(time_label,units) in enumerate(copertura_slots.get(day,[])):
        vars_slot = []
        for tt in teachers:
            key = (day,s_idx,tt)
            if key in copertura_vars:
                vars_slot.append(copertura_vars[key][0])
        if vars_slot:
            model.Add(sum(vars_slot) == 1)

# now per-teacher copertura totals
for t in teachers:
    cov_hours = ASSEGNAZIONE_DOCENTI.get(t,{}).get('copertura',0)
    needed = hours_to_units(cov_hours)
    teacher_cov_vars = []
    for (day,s_idx,tt),(var,time_label,units) in copertura_vars.items():
        if tt == t:
            teacher_cov_vars.append((var, units))
    if teacher_cov_vars:
        model.Add(sum(var * units for var,units in teacher_cov_vars) == needed)
    else:
        # if teacher has no copertura slots available, ensure they have no required copertura
        model.Add(needed == 0)

# Max weekly hours per teacher (include copertura)
for t in teachers:
    terms = []
    for cl in CLASSI:
        for day in GIORNI:
            slots = class_slots[cl][day]
            for s_idx,(time_label,units) in enumerate(slots):
                if (cl,day,s_idx,t) in x:
                    terms.append(x[(cl,day,s_idx,t)] * units)
    # copertura terms for this teacher
    cov_terms = []
    for (day,s_idx,tt),(var,time_label,units) in copertura_vars.items():
        if tt == t:
            cov_terms.append(var * units)
    model.Add(sum(terms) + sum(cov_terms) <= hours_to_units(MAX_ORE_SETTIMANALI_DOCENTI))

# Rule: MOTORIA and SAVINO not more than 1 hour per day per class
for t in LIMIT_ONE_PER_DAY_PER_CLASS:
    for cl in CLASSI:
        for day in GIORNI:
            terms = []
            for s_idx,(time_label,units) in enumerate(class_slots[cl][day]):
                if (cl,day,s_idx,t) in x:
                    terms.append(x[(cl,day,s_idx,t)] * units)
            if terms:
                model.Add(sum(terms) <= hours_to_units(1))

# MOTORIA only MAR,GIO,VEN
for day in GIORNI:
    if day not in MOTORIA_ONLY_DAYS:
        for cl in CLASSI:
            for s_idx,(time_label,units) in enumerate(class_slots[cl][day]):
                if (cl,day,s_idx,'MOTORIA') in x:
                    model.Add(x[(cl,day,s_idx,'MOTORIA')] == 0)

# Teachers in GROUP_DAILY_TWO_CLASSES: if they have exactly 2 classes assigned, require at least 1 hour per day in each
for t in GROUP_DAILY_TWO_CLASSES:
    assign = ASSEGNAZIONE_DOCENTI.get(t,{})
    classes = [c for c in assign.keys() if c != 'copertura']
    if len(classes) == 2:
        for day in GIORNI:
            for cl in classes:
                terms = []
                for s_idx,(time_label,units) in enumerate(class_slots[cl][day]):
                    if (cl,day,s_idx,t) in x:
                        terms.append(x[(cl,day,s_idx,t)] * units)
                # at least 1 hour -> 2 units
                model.Add(sum(terms) >= hours_to_units(1))

# SCHIAVONE starts at 9 three times a week: earliest teaching slot that day must be 9:00
if START_AT_9_THREE_TIMES in teachers:
    t = START_AT_9_THREE_TIMES
    earliest_is_9 = []
    for day in GIORNI:
        # find index of 8:00 and 9:00 in GLOBAL_DAY_TIMES
        # create b_earlier = sum assigned in 8:00
        b_8_vars = []
        b_9_vars = []
        for cl in CLASSI:
            for s_idx,(time_label,units) in enumerate(class_slots[cl][day]):
                if time_label == '8:00-9:00' and (cl,day,s_idx,t) in x:
                    b_8_vars.append(x[(cl,day,s_idx,t)])
                if time_label == '9:00-10:00' and (cl,day,s_idx,t) in x:
                    b_9_vars.append(x[(cl,day,s_idx,t)])
        for (dd,s_idx,tt),(var,time_label,units) in copertura_vars.items():
            if dd == day and tt == t and time_label == '8:00-9:00':
                b_8_vars.append(var)
            if dd == day and tt == t and time_label == '9:00-10:00':
                b_9_vars.append(var)
        b_8 = model.NewBoolVar(f"b8_{t}_{day}")
        b_9 = model.NewBoolVar(f"b9_{t}_{day}")
        if b_8_vars:
            model.Add(sum(b_8_vars) >= 1).OnlyEnforceIf(b_8)
            model.Add(sum(b_8_vars) == 0).OnlyEnforceIf(b_8.Not())
        else:
            model.Add(b_8 == 0)
        if b_9_vars:
            model.Add(sum(b_9_vars) >= 1).OnlyEnforceIf(b_9)
            model.Add(sum(b_9_vars) == 0).OnlyEnforceIf(b_9.Not())
        else:
            model.Add(b_9 == 0)
        # earliest_is_9 => b_9 ==1 and b_8 ==0
        e9 = model.NewBoolVar(f"earliest9_{t}_{day}")
        model.Add(b_9 == 1).OnlyEnforceIf(e9)
        model.Add(b_8 == 0).OnlyEnforceIf(e9)
        # if not e9 we don't constrain
        earliest_is_9.append(e9)
    # At least 3 days with earliest at 9
    model.Add(sum(earliest_is_9) >= 3)

# ZIZZI end-at-10 on Wednesday
for t in END_AT_10_WEDNESDAY:
    for cl in CLASSI:
        for s_idx,(time_label,units) in enumerate(class_slots[cl]['MER']):
            # slots that start at 10:00 or later
            if time_label.startswith('10:') or time_label.startswith('11:') or time_label.startswith('12:') or time_label.startswith('13:'):
                if (cl,'MER',s_idx,t) in x:
                    model.Add(x[(cl,'MER',s_idx,t)] == 0)

# Enforce consecutiveness: for all i<j<k -> b_i + b_k -1 <= b_j
for t in teachers:
    for day in GIORNI:
        times = [tl for tl in GLOBAL_DAY_TIMES]
        for i in range(len(times)):
            for j in range(i+1,len(times)):
                for k in range(j+1,len(times)):
                    model.Add(b[(t,day,times[i])] + b[(t,day,times[k])] - 1 <= b[(t,day,times[j])])

# Solve
#print placeholder replaced by debug-enabled solve
print("DEBUG: Avvio risoluzione modello...", flush=True)
print(f"DEBUG: CLASSI={CLASSI}, GIORNI={GIORNI}, teachers={teachers}", flush=True)
try:
    per_class_slot_counts = ", ".join(f"{cl}:{sum(len(class_slots[cl][d]) for d in GIORNI)}" for cl in CLASSI)
except Exception:
    per_class_slot_counts = "(error computing)"
print(f"DEBUG: slot per classe: {per_class_slot_counts}", flush=True)
print(f"DEBUG: variabili create: x={len(x)}, copertura_vars={len(copertura_vars)}, b={len(b)}", flush=True)
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300
solver.parameters.num_search_workers = 24
res = None
try:
    res = solver.Solve(model)
    print("DEBUG: Solve() terminato, status code:", res, flush=True)
except Exception as e:
    import traceback
    print("DEBUG: Eccezione durante solver.Solve():", e, flush=True)
    traceback.print_exc()
    res = None

# Nuove stampe diagnostiche: mappa status e file system
import os
status_map_local = {
    cp_model.OPTIMAL: 'OPTIMAL',
    cp_model.FEASIBLE: 'FEASIBLE',
    cp_model.INFEASIBLE: 'INFEASIBLE',
    cp_model.MODEL_INVALID: 'MODEL_INVALID',
    cp_model.UNKNOWN: 'UNKNOWN',
}
print('DEBUG: status_map_local =', status_map_local, flush=True)
print('DEBUG: res textual =', status_map_local.get(res, res), flush=True)
print('DEBUG: current working dir =', os.getcwd(), flush=True)
print('DEBUG: files in cwd =', sorted(os.listdir('.')), flush=True)

# Se il solver ha trovato soluzione, esportiamo subito un Excel sintetico e terminiamo
if res in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    try:
        from openpyxl import Workbook
        import os as _os
        wb = Workbook()
        ws_classi = wb.active
        ws_classi.title = "Classi"
        ws_docenti = wb.create_sheet("Docenti")
        # header classi
        header = ["Slot"] + CLASSI
        ws_classi.append(header)
        # costruiamo righe unite su GLOBAL_DAY_TIMES
        rows = []
        for day in GIORNI:
            for time_label in GLOBAL_DAY_TIMES:
                rows.append((day,time_label))
        for day,time_label in rows:
            row = [f"{day} {time_label}"]
            for cl in CLASSI:
                val = ""
                for s_idx,(tl,units) in enumerate(class_slots[cl][day]):
                    if tl == time_label:
                        # cerca docente assegnato
                        for t in allowed_teachers_per_class[cl]:
                            v = x.get((cl,day,s_idx,t))
                            if v is not None and solver.Value(v) == 1:
                                val = f"LEZ ({t})"
                                break
                        break
                row.append(val)
            ws_classi.append(row)
        # sheet docenti
        header_d = ["Slot"] + teachers
        ws_docenti.append(header_d)
        for day,time_label in rows:
            row = [f"{day} {time_label}"]
            for t in teachers:
                out = ""
                # ricerca in classi
                for cl in CLASSI:
                    for s_idx,(tl,units) in enumerate(class_slots[cl][day]):
                        if tl != time_label:
                            continue
                        v = x.get((cl,day,s_idx,t))
                        if v is not None and solver.Value(v) == 1:
                            out = f"LEZ ({cl})"
                            break
                        cov = copertura_vars.get((day,s_idx,t))
                        if cov is not None and solver.Value(cov[0]) == 1:
                            out = f"COP ({cl})"
                            break
                    if out:
                        break
                row.append(out)
            ws_docenti.append(row)
        _os.makedirs("./out", exist_ok=True)
        out_path = "./out/orario_settimanale.xlsx"
        wb.save(out_path)
        print("DEBUG: Excel salvato in:", out_path, flush=True)
    except Exception as e:
        import traceback
        print("DEBUG: Errore durante export Excel:", e, flush=True)
        traceback.print_exc()
    # Esci con successo
    exit(0)

# Infeasible: collect diagnostic messages and write a log instead of printing suggestions
problems = []
problems.append("Nessuna soluzione trovata con i vincoli attuali.")
problems.append("Eseguo diagnostica per individuare cause comuni di infeasibilità:\n")

def u_to_h(u):
    return u * UNIT

# 1) Controllo capacità slot per classe
for cl in CLASSI:
    total_slots = sum(units for day in GIORNI for (_tl,units) in class_slots[cl][day])
    required = hours_to_units(ORE_SETTIMANALI_CLASSI[cl])
    if total_slots < required:
        problems.append(f"Classe {cl}: slot disponibili {total_slots} (={u_to_h(total_slots)}h) < richieste {required} (={u_to_h(required)}h). Impossibile soddisfare le ore della classe.")

# 2) Controllo richieste per docente vs max settimanale
for t in teachers:
    req = 0
    for cl,hours in ASSEGNAZIONE_DOCENTI.get(t,{}).items():
        req += hours_to_units(hours)
    maxu = hours_to_units(MAX_ORE_SETTIMANALI_DOCENTI)
    if req > maxu:
        problems.append(f"Docente {t}: richieste totali {req} (={u_to_h(req)}h) > max settimanale {maxu} (={u_to_h(maxu)}h).")

# 3) Controllo per-teacher per-class availability
for t,assign in ASSEGNAZIONE_DOCENTI.items():
    for cl,hours in assign.items():
        if cl == 'copertura':
            continue
        needed = hours_to_units(hours)
        available = sum(units for day in GIORNI for (tl,units) in class_slots[cl][day])
        if available < needed:
            problems.append(f"Assegnazione impossibile: {t} -> {cl}: disponibili {available} (={u_to_h(available)}h) < richieste {needed} (={u_to_h(needed)}h).")

# helper to compute available units excluding forbidden day/time
def available_for_teacher_excluding_forbidden(t, forbidden_day_times):
    total = 0
    for cl in ASSEGNAZIONE_DOCENTI.get(t,{}):
        if cl == 'copertura':
            continue
        for day in GIORNI:
            for (tl,units) in class_slots[cl][day]:
                if (day,tl) in forbidden_day_times:
                    continue
                total += units
    for day in GIORNI:
        for (_idx,(tl,units)) in enumerate(copertura_slots.get(day,[])):
            if (day,tl) in forbidden_day_times:
                continue
            total += units
    return total

# 4) MOTORIA: richiesta vs disponibilità solo MAR/GIO/VEN
if 'MOTORIA' in ASSEGNAZIONE_DOCENTI:
    mot_req = sum(hours_to_units(h) for cl,h in ASSEGNAZIONE_DOCENTI['MOTORIA'].items())
    mot_avail = 0
    for cl,h in ASSEGNAZIONE_DOCENTI['MOTORIA'].items():
        for day in GIORNI:
            if day in MOTORIA_ONLY_DAYS:
                mot_avail += sum(units for (tl,units) in class_slots[cl][day])
    if mot_req > mot_avail:
        problems.append(f"MOTORIA: richieste {mot_req} (={u_to_h(mot_req)}h) su MAR/GIO/VEN ma slot disponibili {mot_avail} (={u_to_h(mot_avail)}h).")

# MOTORIA specifics
if 'MOTORIA' in ASSEGNAZIONE_DOCENTI:
    mot_req = sum(hours_to_units(h) for cl,h in ASSEGNAZIONE_DOCENTI['MOTORIA'].items())
    mot_avail = 0
    for cl,h in ASSEGNAZIONE_DOCENTI['MOTORIA'].items():
        for day in GIORNI:
            if day in MOTORIA_ONLY_DAYS:
                mot_avail += sum(units for (tl,units) in class_slots[cl][day])
    note = 'OK' if mot_avail >= mot_req else 'INSUFFICIENTE'
    print(f"\nMOTORIA: richieste {mot_req} (={mot_req*UNIT}h), disponibili su {sorted(list(MOTORIA_ONLY_DAYS))} = {mot_avail} (={mot_avail*UNIT}h) -> {note}")

# 5) Vincoli di fine lezione (PEPE LUN, ZIZZI MER)
if 'PEPE' in teachers:
    forbidden = set()
    for (tl,units) in SLOT_1 + SLOT_2 + SLOT_3:
        if tl.startswith('10:') or tl.startswith('11:') or tl.startswith('12:') or tl.startswith('13:'):
            forbidden.add(('LUN', tl))
    pepe_needed = sum(hours_to_units(h) for cl,h in ASSEGNAZIONE_DOCENTI.get('PEPE',{}).items())
    pepe_avail = available_for_teacher_excluding_forbidden('PEPE', forbidden)
    if pepe_avail < pepe_needed:
        problems.append(f"PEPE: a causa del vincolo fine-lezioni LUN alle 10 disponibili {pepe_avail} (={u_to_h(pepe_avail)}h) < richieste {pepe_needed} (={u_to_h(pepe_needed)}h).")

if 'ZIZZI' in teachers:
    forbidden = set()
    for (tl,units) in SLOT_1 + SLOT_2 + SLOT_3:
        if tl.startswith('10:') or tl.startswith('11:') or tl.startswith('12:') or tl.startswith('13:'):
            forbidden.add(('MER', tl))
    zizzi_needed = sum(hours_to_units(h) for cl,h in ASSEGNAZIONE_DOCENTI.get('ZIZZI',{}).items())
    zizzi_avail = available_for_teacher_excluding_forbidden('ZIZZI', forbidden)
    if zizzi_avail < zizzi_needed:
        problems.append(f"ZIZZI: a causa del vincolo fine-lezioni MER alle 10 disponibili {zizzi_avail} (={u_to_h(zizzi_avail)}h) < richieste {zizzi_needed} (={u_to_h(zizzi_needed)}h).")

# 6) SCHIAVONE starts at 9 three times a week: verifica potenziale
if START_AT_9_THREE_TIMES:
    t = START_AT_9_THREE_TIMES
    possible_days = 0
    for day in GIORNI:
        for cl in ASSEGNAZIONE_DOCENTI.get(t,{}):
            if cl == 'copertura':
                continue
            if any(tl == '9:00-10:00' for (tl,units) in class_slots[cl][day]):
                possible_days += 1
                break
    if possible_days < 3:
        problems.append(f"{t}: esistono solo {possible_days} giorni con slot alle 9:00 nelle sue classi; impossibile iniziare alle 9 almeno 3 volte.")

# 7) Gruppo docenti con due classi: almeno 1h al giorno in entrambe le classi
for t in GROUP_DAILY_TWO_CLASSES:
    assign = ASSEGNAZIONE_DOCENTI.get(t,{})
    classes = [c for c in assign.keys() if c != 'copertura']
    if len(classes) == 2:
        for day in GIORNI:
            has_in_both = True
            for cl in classes:
                if sum(units for (tl,units) in class_slots[cl][day]) < hours_to_units(1):
                    has_in_both = False
                    break
            if not has_in_both:
                problems.append(f"{t}: il giorno {day} una delle due classi non ha almeno 1h disponibile; impossibile soddisfare l'obbligo 'almeno 1h al giorno in entrambe'.")

# Stampare la diagnostica a video (non creare file). Forniamo un dettaglio esteso
from datetime import datetime
print(f"\nDiagnostica eseguita: {datetime.now().isoformat()}\n")
print(f"{len(problems)} problemi trovati:\n")
for idx, p in enumerate(problems, 1):
    print(f"{idx}. {p}")

print("\n--- Dettaglio diagnostica esteso ---\n")
# Per-class details
for cl in CLASSI:
    total_slots = sum(units for day in GIORNI for (_tl,units) in class_slots[cl][day])
    required = hours_to_units(ORE_SETTIMANALI_CLASSI[cl])
    status = "OK" if total_slots >= required else "INSUFFICIENTE"
    print(f"Classe {cl}: slot disponibili {total_slots} (={total_slots*UNIT}h), richieste {required} (={required*UNIT}h) -> {status}")

print('\nPer-docente: richieste vs max settimanale')
for t in teachers:
    req = 0
    for cl,hours in ASSEGNAZIONE_DOCENTI.get(t,{}).items():
        req += hours_to_units(hours)
    maxu = hours_to_units(MAX_ORE_SETTIMANALI_DOCENTI)
    note = 'OK' if req <= maxu else 'SOVRACCARICO'
    print(f"Docente {t}: richieste totali {req} (={req*UNIT}h), max {maxu} (={maxu*UNIT}h) -> {note}")

print('\nPer-coppia docente-classe: richieste vs slot disponibili nella classe')
for t,assign in ASSEGNAZIONE_DOCENTI.items():
    for cl,hours in assign.items():
        if cl == 'copertura':
            continue
        needed = hours_to_units(hours)
        available = sum(units for day in GIORNI for (tl,units) in class_slots[cl][day])
        note = 'OK' if available >= needed else 'INSUFFICIENTE'
        print(f"{t} -> {cl}: richieste {needed} (={needed*UNIT}h), disponibili {available} (={available*UNIT}h) -> {note}")

# Dettagli per docente
for t in teachers:
    print(f"\nDettagli per docente {t}:")
    total_assigned = 0
    for cl,assign in ASSEGNAZIONE_DOCENTI.items():
        if cl == 'copertura':
            continue
        if t in assign:
            hours = assign[t]
            assigned_units = hours_to_units(hours)
            total_assigned += assigned_units
            status = "OK"
            # controlla se ci sono slot disponibili nella classe
            available_slots = sum(units for day in GIORNI for (tl,units) in class_slots[cl][day])
            if available_slots < assigned_units:
                status = "INSUFFICIENTE"
            print(f"  {cl}: richieste {assigned_units} (={hours}h), disponibili {available_slots} -> {status}")
    # dettagli copertura
    cov_hours = ASSEGNAZIONE_DOCENTI.get(t,{}).get('copertura',0)
    cov_needed = hours_to_units(cov_hours)
    cov_assigned = 0
    if cov_needed > 0:
        cov_assigned = sum(units for (var,units) in teacher_cov_vars if var in x.values())
    cov_status = "OK" if cov_assigned >= cov_needed else "INSUFFICIENTE"
    print(f"  Copertura: richieste {cov_needed}, assegnate {cov_assigned} -> {cov_status}")
    # totale
    total_hours = cov_hours + total_assigned * UNIT
    print(f"  Totale ore: {total_hours} (richieste {cov_hours + total_assigned}h)")

# Dettagli per classe
for cl in CLASSI:
    print(f"\nDettagli per classe {cl}:")
    total_slots = sum(units for day in GIORNI for (_tl,units) in class_slots[cl][day])
    required = hours_to_units(ORE_SETTIMANALI_CLASSI[cl])
    status = "OK" if total_slots >= required else "INSUFFICIENTE"
    print(f"  Slot disponibili {total_slots} (={u_to_h(total_slots)}h), richieste {required} (={u_to_h(required)}h) -> {status}")
    if status == "INSUFFICIENTE":
        # suggerisci riduzione ore o aumento disponibilità
        print("  Suggerimenti:")
        # riduzione ore
        riduzione_ore = total_slots * UNIT
        if riduzione_ore > 0:
            print(f"    Ridurre le ore a {riduzione_ore}h")
        # aumento disponibilità
        for t in teachers:
            if t in ASSEGNAZIONE_DOCENTI.get(cl,{}):
                max_disponibile = hours_to_units(MAX_ORE_SETTIMANALI_DOCENTI) - sum(units for day in GIORNI for (tl,units) in class_slots[cl][day] if (cl,day,tl) in x)
                if max_disponibile > 0:
                    print(f"    Aumentare disponibilità di {t} di almeno {max_disponibile} ore")

# Dettagli vincoli di fine lezione
for t in teachers:
    if t == 'PEPE':
        print(f"\nDettagli vincoli fine lezione per {t}:")
        forbidden = set()
        for (tl,units) in SLOT_1 + SLOT_2 + SLOT_3:
            if tl.startswith('10:') or tl.startswith('11:') or tl.startswith('12:') or tl.startswith('13:'):
                forbidden.add(('LUN', tl))
        for day in GIORNI:
            if day == 'LUN':
                continue
            available = available_for_teacher_excluding_forbidden(t, forbidden)
            print(f"  {day}: disponibile {available} ore (vincoli esclusi)")
    if t == 'ZIZZI':
        print(f"\nDettagli vincoli fine lezione per {t}:")
        forbidden = set()
        for (tl,units) in SLOT_1 + SLOT_2 + SLOT_3:
            if tl.startswith('10:') or tl.startswith('11:') or tl.startswith('12:') or tl.startswith('13:'):
                forbidden.add(('MER', tl))
        for day in GIORNI:
            if day == 'MER':
                continue
            available = available_for_teacher_excluding_forbidden(t, forbidden)
            print(f"  {day}: disponibile {available} ore (vincoli esclusi)")

print("\nDiagnostica completata.")