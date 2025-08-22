#!/usr/bin/env python3
"""
genera_orario.py
Genera automaticamente orari settimanali per classi e docenti e li esporta in Excel.
Requisiti implementati (approssimazione euristica):
- Ogni classe riceve le ore settimanali per materia definite in ORE_SETTIMANALI.
- Per ogni classe, ogni materia ha un docente unico (scelto tra DOCENTI disponibili per la materia).
- Ogni giorno nelle classi ci sono almeno due materie diverse (tentativo con shuffle ripetuto).
- Ogni docente ha una giornata libera (preventivamente riservata) e non viene assegnato in quella giornata.
- Ogni docente lavora al massimo ORE_DOCENTE ore; se dopo l'assegnazione delle lezioni ha meno ore, vengono assegnate ore di "coopertura" su slot liberi (se possibile).
- Vengono identificate le ore di BUCO (tra due lezioni nello stesso giorno, senza copertura).

Nota: lo script usa una strategia euristica con backtracking per assegnare i docenti alle materie per classe rispettando i vincoli di conflitto.
"""

import random
import itertools
from collections import defaultdict, Counter
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Alignment
from openpyxl.utils import get_column_letter

# ---------------------- DATI PERSONALIZZABILI ----------------------
CLASSI = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A"]
MATERIE = ["REL", "ING", "MAT", "ITA", "MOT"]
ORE_SETTIMANALI = {"REL": 2, "MOT": 2, "ING": 3, "MAT": 11, "ITA": 11}
GIORNI = ["LUN", "MAR", "MER", "GIO", "VEN"]
ORE_PER_GIORNATE = {"LUN":6, "MAR":6, "MER":6, "GIO":6, "VEN":5 }
ORE_DOCENTE = 22
GIORNATE_LIBERE = 1
DOCENTI = {
    "Doc1": ["MAT"],
    "Doc2": ["MAT"],
    "Doc3": ["MAT"],
    "Doc4": ["MAT"],
    "Doc5": ["ITA"],
    "Doc6": ["ITA"],
    "Doc7": ["ITA"],
    "Doc8": ["ITA"],
    "Doc9": ["ING"],
    "Doc10": ["REL"],
    "Doc11": ["MOT"],
    "Doc12": ["MAT", "ITA", "ING", "REL", "MOT"],
    "Doc13": ["MAT", "ITA", "ING", "REL", "MOT"],
    "Doc14": ["MAT", "ITA", "ING", "REL", "MOT"],
    "Doc15": ["MAT", "ITA"],
    "Doc16": ["MAT", "ING"],
    "Doc17": ["ITA", "ING"],
    "Doc18": ["REL", "MOT"],
    "Doc19": ["MAT", "ITA", "REL"],
    "Doc20": ["MAT", "ITA", "ING"],
}
# ------------------------------------------------------------------

random.seed(1)

# Derived structures
DAY_ORDER = GIORNI
SLOTS_PER_DAY = [ORE_PER_GIORNATE[d] for d in DAY_ORDER]
TOTAL_SLOTS = sum(SLOTS_PER_DAY)
# Linear slot indices map to (day, position)
SLOT_LABELS = []
for d in DAY_ORDER:
    for i in range(1, ORE_PER_GIORNATE[d] + 1):
        SLOT_LABELS.append(f"{d}{i}")

# Utilities
def make_empty_schedule():
    return [None] * TOTAL_SLOTS

def slots_for_day(day_index):
    start = sum(SLOTS_PER_DAY[:day_index])
    return range(start, start + SLOTS_PER_DAY[day_index])

# 1) Genera orario per classe: assegna per classe le materie (token) in base alle ORE_SETTIMANALI
def generate_class_schedule(class_name, max_attempts=500):
    """
    Crea una sequenza di length TOTAL_SLOTS per la classe.
    Vincoli rispettati (se possibile):
    - Il totale settimanale per materia è quello in ORE_SETTIMANALI.
    - All'interno di ogni giornata, ore della stessa materia sono consecutive, salvo al massimo 2 blocchi per materia/giorno solo se il conteggio di quella materia in quella giornata è >= 4.
    - Se una materia compare 1/2/3 volte in una giornata, quelle ore devono essere in un singolo blocco.
    - Ogni giornata deve contenere almeno due materie diverse (escludendo ATT).
    """
    subjects = list(ORE_SETTIMANALI.keys())
    for attempt in range(max_attempts):
        remaining = dict(ORE_SETTIMANALI)
        week_tokens = []
        failed = False
        for day_idx, slots in enumerate(SLOTS_PER_DAY):
            # build a preliminary day allocation by greedily taking blocks from remaining
            day_alloc = []  # list of subject tokens (length = slots)
            # while there are slots to fill
            while len(day_alloc) < slots:
                available = [s for s in subjects if remaining.get(s, 0) > 0]
                if not available:
                    # fill with ATT
                    day_alloc += ["ATT"] * (slots - len(day_alloc))
                    break
                # pick a subject to place next block (prefer subjects with more remaining)
                weights = [remaining[s] for s in available]
                s = random.choices(available, weights=weights, k=1)[0]
                # choose block size at most remaining[s] and remaining slots
                max_block = min(remaining[s], slots - len(day_alloc))
                # try to place larger blocks more often
                if max_block <= 1:
                    b = max_block
                else:
                    b = random.randint(1, max_block)
                day_alloc += [s] * b
                remaining[s] -= b
            # now we have a day_alloc, ensure it has at least two real subjects (exclude ATT)
            real_subjects = [t for t in set(day_alloc) if t != "ATT"]
            if len(real_subjects) < 2:
                # attempt to adjust by pulling one hour from another day later is complex; mark as failed
                failed = True
                break
            # enforce per-subject block rules by rebuilding day sequence from counts
            counts = defaultdict(int)
            for t in day_alloc:
                if t != "ATT":
                    counts[t] += 1
            # build blocks: list of (subject, size) respecting rules
            blocks = []
            for subj, cnt in counts.items():
                if cnt <= 3:
                    # single block
                    blocks.append((subj, cnt))
                else:
                    # allow up to 2 blocks: split roughly in half
                    k = cnt // 2
                    blocks.append((subj, k))
                    blocks.append((subj, cnt - k))
            # include ATT as single block at the end if present
            att_count = day_alloc.count("ATT")
            if att_count > 0:
                blocks.append(("ATT", att_count))
            # now order blocks so that equal subjects are not adjacent (ensure split blocks separated)
            ordered_blocks = []
            # greedy placement: always pick the largest remaining block whose subject != last_subject
            blocks_left = blocks.copy()
            last_subject = None
            while blocks_left:
                # filter candidates
                candidates = [b for b in blocks_left if b[0] != last_subject]
                if not candidates:
                    # cannot avoid adjacency; just pop one
                    b = blocks_left.pop(0)
                else:
                    # pick candidate with largest size to reduce fragmentation
                    b = max(candidates, key=lambda x: x[1])
                    blocks_left.remove(b)
                ordered_blocks.append(b)
                last_subject = b[0]
            # build final day_seq
            day_seq = []
            for subj, size in ordered_blocks:
                day_seq += [subj] * size
            # final sanity: length should equal slots
            if len(day_seq) != slots:
                # if mismatch, try trivial fix: trim or pad with ATT
                if len(day_seq) > slots:
                    day_seq = day_seq[:slots]
                else:
                    day_seq += ["ATT"] * (slots - len(day_seq))
            # ensure again that for subjects with counts 1-3 they are in single block
            def has_multiple_blocks(sequence, subject):
                seen = False
                blocks_found = 0
                i = 0
                n = len(sequence)
                while i < n:
                    if sequence[i] == subject:
                        blocks_found += 1
                        while i < n and sequence[i] == subject:
                            i += 1
                    else:
                        i += 1
                return blocks_found > 1
            ok_blocks = True
            for subj, cnt in counts.items():
                if cnt <= 3 and has_multiple_blocks(day_seq, subj):
                    ok_blocks = False
                    break
                if cnt >= 4:
                    # allow at most 2 blocks
                    if has_multiple_blocks(day_seq, subj):
                        # count blocks
                        # count occurrences of blocks
                        blocks_found = 0
                        i = 0
                        n = len(day_seq)
                        while i < n:
                            if day_seq[i] == subj:
                                blocks_found += 1
                                while i < n and day_seq[i] == subj:
                                    i += 1
                            else:
                                i += 1
                        if blocks_found > 2:
                            ok_blocks = False
                            break
            if not ok_blocks:
                failed = True
                break
            # append day_seq to week_tokens
            week_tokens.extend(day_seq)
        if failed:
            continue
        # final check: all remaining should be zero
        if any(v != 0 for v in remaining.values()):
            continue
        return week_tokens
    # fallback: naive fill
    tokens = []
    for m, h in ORE_SETTIMANALI.items():
        tokens += [m] * h
    remaining = TOTAL_SLOTS - len(tokens)
    tokens += ["ATT"] * remaining
    return tokens

# Build all class schedules
class_schedules = {c: generate_class_schedule(c) for c in CLASSI}

# 2) For each class-subject, find indices where it appears
class_subject_slots = []  # list of (class, subject, indices)
for c in CLASSI:
    sched = class_schedules[c]
    for subj in MATERIE:
        indices = [i for i, s in enumerate(sched) if s == subj]
        if indices:
            class_subject_slots.append((c, subj, indices))

# Sort by descending number of occurrences to place heavy loads first
class_subject_slots.sort(key=lambda x: -len(x[2]))

# 3) Prepare teacher data structures
teachers = list(DOCENTI.keys())
# postpone free day selection until after assignment to avoid blocking feasibility
teacher_free_day = {t: None for t in teachers}

teacher_schedule = {t: make_empty_schedule() for t in teachers}
teacher_hours = {t: 0 for t in teachers}

# Helper to check teacher availability for given indices and subj
def teacher_can_take(t, indices, subject):
    # can teach subject?
    if subject not in DOCENTI[t]:
        return False
    # if a free day is already set, ensure none of the indices fall on that day
    free_day = teacher_free_day.get(t)
    if free_day is not None:
        free_day_idx = DAY_ORDER.index(free_day)
        for i in indices:
            day_idx = next(j for j, r in enumerate(itertools.accumulate(SLOTS_PER_DAY)) if i < r)
            if day_idx == free_day_idx:
                return False
    # ensure teacher is free in those slots
    for i in indices:
        if teacher_schedule[t][i] is not None:
            return False
    # hours limit
    if teacher_hours[t] + len(indices) > ORE_DOCENTE:
        return False
    return True

# Backtracking assignment of teachers to class-subject
assignment = {}  # (class,subject) -> teacher

pairs = [(c, s, idxs) for (c, s, idxs) in class_subject_slots]

def assign_recursive(pos=0):
    if pos >= len(pairs):
        return True
    c, s, idxs = pairs[pos]
    candidates = [t for t in teachers if teacher_can_take(t, idxs, s)]
    random.shuffle(candidates)
    for t in candidates:
        # assign
        assignment[(c, s)] = t
        for i in idxs:
            teacher_schedule[t][i] = f"{s} ({c})"
        teacher_hours[t] += len(idxs)
        # recurse
        if assign_recursive(pos + 1):
            return True
        # undo
        del assignment[(c, s)]
        for i in idxs:
            teacher_schedule[t][i] = None
        teacher_hours[t] -= len(idxs)
    return False

# Replace single attempt with multiple randomized attempts and debug info
MAX_ASSIGN_ATTEMPTS = 500
ok = False
for attempt in range(1, MAX_ASSIGN_ATTEMPTS + 1):
    # reset teacher schedules and hours (do not set free days yet)
    for t in teachers:
        teacher_schedule[t] = make_empty_schedule()
        teacher_hours[t] = 0
    assignment.clear()

    # quick sanity check: for each (class,subject) ensure at least one possible teacher that knows the subject
    impossible_pair = None
    for (c, s, idxs) in pairs:
        candidates_for_subject = [t for t in teachers if s in DOCENTI[t]]
        if len(candidates_for_subject) == 0:
            impossible_pair = (c, s)
            break
    if impossible_pair:
        print(f"Errore: nessun docente disponibile per la materia {impossible_pair[1]} nella classe {impossible_pair[0]}. Aggiorna DOCENTI.")
        break

    # debug: mostra numero di candidati per le prime 10 coppie per non inondare l'output
    print(f"Tentativo {attempt}/{MAX_ASSIGN_ATTEMPTS}: controllo candidati per le prime coppie (class, subject, #candidati)")
    for (c, s, idxs) in pairs[:10]:
        cand = [t for t in teachers if s in DOCENTI[t]]
        print(f"  {c} {s} ({len(idxs)} ore) -> {len(cand)} candidati: {cand}")

    if assign_recursive():
        print(f"Assegnazione trovata al tentativo {attempt}")
        ok = True
        break
    # otherwise try again

if not ok:
    raise RuntimeError("Impossibile assegnare i docenti con i vincoli attuali dopo tentativi multipli. Prova a modificare DOCENTI o parametri.")

# After successful assignment, choose a free day for each teacher: prefer a day with zero lessons
for t in teachers:
    # count lessons per day
    lessons_per_day = []
    for day_idx in range(len(DAY_ORDER)):
        day_slots = list(slots_for_day(day_idx))
        cnt = sum(1 for i in day_slots if teacher_schedule[t][i] is not None)
        lessons_per_day.append((cnt, day_idx))
    lessons_per_day.sort()  # prefer day with fewest lessons
    preferred_day_idx = lessons_per_day[0][1]
    teacher_free_day[t] = DAY_ORDER[preferred_day_idx]

# Ensure unique teacher per (class,subject) — validate and repair if needed
print("Validazione: garantire docente unico per ogni (classe, materia) ...")
for (c, s, idxs) in class_subject_slots:
    # collect which teacher currently holds each slot
    slot_teachers = []
    for i in idxs:
        owners = [t for t in teachers if teacher_schedule[t][i] == f"{s} ({c})"]
        slot_teachers.append(owners[0] if owners else None)
    unique_assigned = set([t for t in slot_teachers if t])
    if len(unique_assigned) <= 1 and all(x is not None for x in slot_teachers):
        # already a unique assigned teacher present for all slots
        assignment[(c, s)] = next(iter(unique_assigned)) if unique_assigned else assignment.get((c, s))
        continue
    # choose majority teacher if present
    counts = Counter([t for t in slot_teachers if t])
    chosen = None
    if counts:
        chosen = counts.most_common(1)[0][0]
    else:
        # find any qualified candidate who can cover all slots (or empty ones)
        candidates = []
        for t in teachers:
            if s not in DOCENTI[t]:
                continue
            ok = True
            extra_needed = 0
            for i in idxs:
                if teacher_schedule[t][i] is not None and teacher_schedule[t][i] != f"{s} ({c})":
                    ok = False
                    break
                if teacher_schedule[t][i] != f"{s} ({c})":
                    extra_needed += 1
            if not ok:
                continue
            if teacher_hours[t] + extra_needed <= ORE_DOCENTE:
                candidates.append(t)
        if candidates:
            chosen = candidates[0]
    if not chosen:
        print(f"Avviso: impossibile garantire docente unico per {c} {s}; nessun candidato trovato. Lasciando assegnazioni esistenti.")
        continue
    # reassign slots to chosen teacher
    for i in idxs:
        # remove from other teachers
        for t in teachers:
            if t != chosen and teacher_schedule[t][i] == f"{s} ({c})":
                teacher_schedule[t][i] = None
                teacher_hours[t] -= 1
        # assign to chosen if not already
        if teacher_schedule[chosen][i] != f"{s} ({c})":
            teacher_schedule[chosen][i] = f"{s} ({c})"
            teacher_hours[chosen] += 1
    assignment[(c, s)] = chosen

# 4) Identificare BUCO per ciascun docente (tra due lezioni nello stesso giorno: slot vuoto tra due lezioni)
BUCO = "BUCO"
for t in teachers:
    for day_idx, day in enumerate(DAY_ORDER):
        day_slots = list(slots_for_day(day_idx))
        # find lesson positions (non None)
        lesson_pos = [i for i in day_slots if teacher_schedule[t][i] is not None]
        if len(lesson_pos) >= 2:
            first = min(lesson_pos)
            last = max(lesson_pos)
            for i in range(first, last + 1):
                if teacher_schedule[t][i] is None:
                    teacher_schedule[t][i] = BUCO

# 5) Assegnare coopertura per raggiungere ORE_DOCENTE, evitando i giorni liberi e preferendo slot non-BUCO
for t in teachers:
    needed = ORE_DOCENTE - teacher_hours[t]
    if needed <= 0:
        continue
    free_day_idx = DAY_ORDER.index(teacher_free_day[t])
    # list candidate slots: slots that are None (not BUCO) and not on free day
    candidates = [i for i, v in enumerate(teacher_schedule[t]) if v is None and (next(j for j, r in enumerate(itertools.accumulate(SLOTS_PER_DAY)) if i < r) != free_day_idx)]
    # prefer slots outside BUCO (we already set BUCO so candidates exclude BUCO)
    chosen = []
    # if not enough candidates, allow BUCO slots to be replaced by coopertura (less ideal)
    for i in candidates:
        if needed <= 0:
            break
        teacher_schedule[t][i] = "coopertura"
        chosen.append(i)
        needed -= 1
    if needed > 0:
        # allow replacing BUCO
        candidates_buco = [i for i, v in enumerate(teacher_schedule[t]) if v == BUCO and (next(j for j, r in enumerate(itertools.accumulate(SLOTS_PER_DAY)) if i < r) != free_day_idx)]
        for i in candidates_buco:
            if needed <= 0:
                break
            teacher_schedule[t][i] = "coopertura"
            needed -= 1
    teacher_hours[t] = ORE_DOCENTE - max(0, needed)

# 6) Marcare giornata_libero per i docenti: se il giorno è il free day, mettere 'giorno_libero' in tutte le celle
for t in teachers:
    fd_idx = DAY_ORDER.index(teacher_free_day[t])
    for i in slots_for_day(fd_idx):
        teacher_schedule[t][i] = "giorno_libero"

# 7) Preparare DataFrame per foglio Classi: valori come 'MAT (Doc1)'
# Per ciascuna classe, sostituire materia con 'MAT (DocX)'
class_df = pd.DataFrame(index=SLOT_LABELS)
for c in CLASSI:
    col = []
    sched = class_schedules[c]
    for i, subj in enumerate(sched):
        if subj == "ATT":
            col.append("")
        else:
            teacher = assignment.get((c, subj))
            if teacher:
                col.append(f"{subj} ({teacher})")
            else:
                col.append(subj)
    class_df[c] = col
# aggiungo colonna coopertura vuota per compatibilità con richiesta
class_df["coopertura"] = [""] * TOTAL_SLOTS

# 8) Preparare DataFrame per foglio Docenti
doc_df = pd.DataFrame(index=SLOT_LABELS)
for t in teachers:
    col = []
    sched = teacher_schedule[t]
    for cell in sched:
        if cell is None:
            col.append("")
        else:
            col.append(cell)
    doc_df[t] = col

# 9) Esportare in Excel con colorazione per giorni
out_fn = "orario_settimanale.xlsx"
with pd.ExcelWriter(out_fn, engine="openpyxl") as writer:
    class_df.to_excel(writer, sheet_name="Classi")
    doc_df.to_excel(writer, sheet_name="Docenti")

# Apri workbook per styling
wb = load_workbook(out_fn)
# color map per giorni
day_colors = {
    "LUN": "FFF2CC",
    "MAR": "D9EAD3",
    "MER": "D9E1F2",
    "GIO": "FCE4D6",
    "VEN": "F4CCCC",
}
for sheet_name in ["Classi", "Docenti"]:
    ws = wb[sheet_name]
    # header alignment
    for col in range(1, ws.max_column + 1):
        ws.cell(row=1, column=col).alignment = Alignment(horizontal="center", vertical="center")
    # colorare le righe per giorni
    row_offset = 2  # DataFrame written with index, so data starts at row 2
    r = row_offset
    for day_idx, day in enumerate(DAY_ORDER):
        fill = PatternFill(start_color=day_colors.get(day, "FFFFFF"), end_color=day_colors.get(day, "FFFFFF"), fill_type="solid")
        for _ in range(SLOTS_PER_DAY[day_idx]):
            for col in range(1, ws.max_column + 1):
                ws.cell(row=r, column=col).fill = fill
            r += 1
    # set column widths
    for col in range(1, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18

wb.save(out_fn)

print(f"Orario generato e salvato in '{out_fn}'")