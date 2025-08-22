#!/usr/bin/env python3
"""
Generatore di orario settimanale per classi e docenti.
- Esporta `orario_settimanale.xlsx` con fogli `Classi` e `Docenti`.
- Produce un report testuale in `reports/report_YYYYMMDD_HHMMSS.txt` con vincoli verificati e violazioni.
- Ogni esecuzione produce un'assegnazione diversa (seed casuale legato al tempo).

Nota: questo script implementa una euristica che tenta di rispettare i vincoli del README.
"""

import os
import random
import datetime
from collections import defaultdict
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# -----------------------------
# Parametri e dati (da README)
# -----------------------------
CLASSI = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A"]
GIORNI = ["LUN", "MAR", "MER", "GIO", "VEN"]
ORE_SETTIMANALI_DOCENTE = 22
ORE_SETTIMANALI_CLASSE = 27
# converti in minuti per conti precisi (60 min = 1h, 30 min = 0.5h)
ORE_SETTIMANALI_DOCENTE_MIN = ORE_SETTIMANALI_DOCENTE * 60
ORE_SETTIMANALI_CLASSE_MIN = ORE_SETTIMANALI_CLASSE * 60

# slot template (ordine matters)
SLOT_1 = ["8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00","13:00-13:30"]
SLOT_2 = ["8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00","13:00-13:30"]
SLOT_3 = ["8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00"]

ASSEGNAZIONE_SLOT = {
    "1A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" },
    "1B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" },
    "2A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" },
    "2B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" },
    "3A": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" },
    "3B": { "LUN":"SLOT_1", "MAR":"SLOT_1", "MER":"SLOT_1", "GIO":"SLOT_1", "VEN":"SLOT_3" },
    "4A":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" },
    "4B":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" },
    "5A":{ "LUN":"SLOT_2", "MAR":"SLOT_2", "MER":"SLOT_2", "GIO":"SLOT_2", "VEN":"SLOT_3" },
}

# assegnazioni docenti: mappa doc -> {classe:ore, ..., 'copertura':ore}
ASSEGNAZIONE_DOCENTI = {
    "ANGELINI": {"1A": 11, "1B":11},
    "DOCENTE1": {"1A": 11, "1B":11},
    "SABATELLI": {"2A": 9, "2B":9, "copertura":4},
    "SCHIAVONE": {"2A": 11, "2B":11},
    "CICCIMARRA": {"2A": 3, "2B":3, "copertura":6},
    "MARANGI": {"3A": 10, "3B":10, "copertura":2},
    "SIMEONE": {"3A": 11, "3B":11},
    "PEPE": {"4A": 8, "4B":8, "copertura":6},
    "PALMISANO": {"4A": 10, "4B":10, "copertura":2},
    "ZIZZI": {"5A": 11},
    "DOCENTE2": {"5A": 3, "4A": 4, "4B":4},
    "MOTORIA": {"5A": 2, "4A": 2, "4B":2},
    "LEO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":2, "3B":2, "4A":2, "4B":2, "5A":2},
    "SAVINO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":2, "3B":2, "4A":2, "4B":2},
}

# utility per mappare nome slot
SLOT_MAP = {"SLOT_1": SLOT_1, "SLOT_2": SLOT_2, "SLOT_3": SLOT_3}

# Colori per i giorni (openpyxl RGB)
DAY_COLORS = {
    "LUN": "FFF2CC",
    "MAR": "DDEBF7",
    "MER": "E2EFDA",
    "GIO": "FCE4D6",
    "VEN": "E6E6FA",
}

# -----------------------------
# Help functions
# -----------------------------

def seed_random():
    # random seed basato su tempo e fonte os.urandom per variabilità
    seed = int.from_bytes(os.urandom(4), "big") ^ int(datetime.datetime.utcnow().timestamp())
    random.seed(seed)
    return seed


def build_class_slots():
    """Ritorna dict: classe -> list di slot disponibili con durata in minuti.
    Seleziona un sottoinsieme di slot la cui somma dei minuti è pari a ORE_SETTIMANALI_CLASSE_MIN (se possibile).
    """
    res = {}
    for cl in CLASSI:
        slots = []
        mapping = ASSEGNAZIONE_SLOT.get(cl)
        for g in GIORNI:
            slot_key = mapping[g]
            slot_template = SLOT_MAP[slot_key]
            for idx in range(len(slot_template)):
                time_label = slot_template[idx]
                # durata in minuti: se termina con 13:30 allora 30 altrimenti 60
                mins = 30 if time_label.endswith('13:30') else 60
                label = f"{g}{idx+1}"
                slots.append({"giorno": g, "idx": idx+1, "label": label, "time": time_label, "assigned": None, "mins": mins})
        total_available = sum(s['mins'] for s in slots)
        if total_available < ORE_SETTIMANALI_CLASSE_MIN:
            raise RuntimeError(f"Classe {cl} ha meno minuti disponibili ({total_available}) di ORE_SETTIMANALI_CLASSE_MIN ({ORE_SETTIMANALI_CLASSE_MIN})")
        # tentiamo di trovare una combinazione di slot con somma esatta usando DP (subset sum)
        # per variabilità mescoliamo l'ordine
        random.shuffle(slots)
        target = ORE_SETTIMANALI_CLASSE_MIN
        dp = {0: []}  # somma_min -> list of indices
        for i, s in enumerate(slots):
            dur = s['mins']
            # iterare sulle somme presenti in dp in ordine decrescente per evitare riuso nello stesso step
            for acc in sorted(list(dp.keys()), reverse=True):
                new_sum = acc + dur
                if new_sum > target:
                    continue
                if new_sum not in dp:
                    dp[new_sum] = dp[acc] + [i]
                if new_sum == target:
                    break
            if target in dp:
                break
        if target in dp:
            chosen_indices = dp[target]
        else:
            # se non trovi la somma esatta, scegli la somma massima <= target
            best = max(dp.keys())
            chosen_indices = dp[best]
        chosen = [slots[i] for i in chosen_indices]
        # ordina per giorno e idx per stabilità
        chosen.sort(key=lambda s: (GIORNI.index(s["giorno"]), s["idx"]))
        res[cl] = chosen
    return res


def contiguous_segments(day_slots):
    """Given sorted list of slots (by idx) returns list of (start_idx, length, slot_objs)
    day_slots must be sorted by idx
    """
    segs = []
    if not day_slots:
        return segs
    cur = [day_slots[0]]
    for s in day_slots[1:]:
        if s["idx"] == cur[-1]["idx"] + 1:
            cur.append(s)
        else:
            segs.append((cur[0]["idx"], len(cur), cur.copy()))
            cur = [s]
    segs.append((cur[0]["idx"], len(cur), cur.copy()))
    return segs

# -----------------------------
# Algoritmo di assegnazione
# -----------------------------

def assign_teachers(class_slots):
    # stato delle assegnazioni (in minuti)
    teacher_total = defaultdict(int)  # minuti assegnati per docente
    teacher_day_assigned = defaultdict(lambda: defaultdict(int))  # teacher -> giorno -> minuti
    teacher_day_slots = defaultdict(lambda: defaultdict(list))  # teacher->giorno->list of slot refs

    MAX_CONTIGUOUS_MIN = 4 * 60  # 4 ore in minuti

    def will_exceed_contiguous(teacher, giorno, added_slots):
        """Verifica se aggiungendo added_slots al teacher in quel giorno si formerebbe un blocco continuo > MAX_CONTIGUOUS_MIN."""
        # calcola tutti gli idx esistenti + quelli aggiunti
        existing = [s['idx'] for s in teacher_day_slots[teacher].get(giorno, [])]
        added = [s['idx'] for s in added_slots]
        combined_slots = existing + added
        if not combined_slots:
            return False
        # costruisci mappa idx -> mins per il giorno (considera anche eventuali duplicati)
        idx_to_mins = {}
        for s in teacher_day_slots[teacher].get(giorno, []):
            idx_to_mins[s['idx']] = idx_to_mins.get(s['idx'], 0) + s['mins']
        for s in added_slots:
            idx_to_mins[s['idx']] = idx_to_mins.get(s['idx'], 0) + s['mins']
        # trova segmenti contigui basandosi sugli idx presenti
        idxs = sorted(set(combined_slots))
        cur_sum = 0
        prev = None
        for idx in idxs:
            if prev is None or idx == prev + 1:
                cur_sum += idx_to_mins.get(idx, 0)
            else:
                # nuovo segmento
                if cur_sum > MAX_CONTIGUOUS_MIN:
                    return True
                cur_sum = idx_to_mins.get(idx, 0)
            prev = idx
        if cur_sum > MAX_CONTIGUOUS_MIN:
            return True
        return False

    # helper per provare assegnare un blocco contiguo di slot a un docente
    def try_assign_block(teacher, block_slots):
        giorno = block_slots[0]["giorno"]
        block_minutes = sum(s['mins'] for s in block_slots)
        # non permettere superamento ore settimanali
        if teacher_total[teacher] + block_minutes > ORE_SETTIMANALI_DOCENTE_MIN:
            return False
        # non permettere blocchi continui > MAX_CONTIGUOUS_MIN
        if will_exceed_contiguous(teacher, giorno, block_slots):
            return False
        # assegna
        for s in block_slots:
            s["assigned"] = teacher
            teacher_day_slots[teacher][giorno].append(s)
        teacher_day_assigned[teacher][giorno] += block_minutes
        teacher_total[teacher] += block_minutes
        return True

    # primo pass: soddisfare le quote esplicite in ASSEGNAZIONE_DOCENTI
    for teacher, quota_map in ASSEGNAZIONE_DOCENTI.items():
        quota_copy = dict(quota_map)
        copertura = quota_copy.pop('copertura', 0)
        if copertura:
            copertura = copertura * 60
        for cl, need in quota_copy.items():
            remain = need * 60
            slots = class_slots.get(cl, [])
            slots_by_day = defaultdict(list)
            for s in slots:
                if s["assigned"] is None:
                    slots_by_day[s["giorno"]].append(s)
            days = list(slots_by_day.keys())
            random.shuffle(days)
            for giorno in days:
                if remain <= 0:
                    break
                day_slots = sorted(slots_by_day[giorno], key=lambda x: x["idx"]) if slots_by_day[giorno] else []
                segs = contiguous_segments(day_slots)
                segs.sort(key=lambda x: -x[1])
                for start, length, seg_slots in segs:
                    if remain <= 0:
                        break
                    # proviamo lunghezze di blocco misurate in numero di slot ma calcoliamo i minuti effettivi
                    for block_slot_len in range(min(length, len(seg_slots)), 0, -1):
                        # seleziona posizione casuale
                        max_start = length - block_slot_len
                        pos = random.randint(0, max_start)
                        block = seg_slots[pos:pos+block_slot_len]
                        block_minutes = sum(s['mins'] for s in block)
                        if block_minutes > remain:
                            continue
                        if try_assign_block(teacher, block):
                            remain -= block_minutes
                            break
        if copertura:
            teacher_total[(teacher, 'desired_copertura')] = copertura

    # seconda pass: riempi i blocchi non assegnati cercando di mantenere consecutività
    unassigned = []
    for cl, slots in class_slots.items():
        for s in slots:
            if s["assigned"] is None:
                unassigned.append((cl, s))
    random.shuffle(unassigned)

    teachers = list(ASSEGNAZIONE_DOCENTI.keys())

    def choose_teacher_for_block(block_slots, giorno):
        block_minutes = sum(s['mins'] for s in block_slots)
        cand = [t for t in teachers if teacher_total[t] + block_minutes <= ORE_SETTIMANALI_DOCENTE_MIN and (teacher_day_assigned[t][giorno] == 0 or teacher_day_assigned[t][giorno] == block_minutes) and not will_exceed_contiguous(t, giorno, block_slots)]
        if not cand:
            # rilassiamo la condizione sulla consecutività ma manteniamo il vincolo del blocco contiguo
            cand = [t for t in teachers if teacher_total[t] + block_minutes <= ORE_SETTIMANALI_DOCENTE_MIN and not will_exceed_contiguous(t, giorno, block_slots)]
        if not cand:
            return None
        return random.choice(cand)

    # assegna segmenti contigui per classe/giorno
    for cl, slots in class_slots.items():
        by_day = defaultdict(list)
        for s in slots:
            if s["assigned"] is None:
                by_day[s["giorno"]].append(s)
        for giorno, day_slots in by_day.items():
            day_slots.sort(key=lambda x: x["idx"])
            segs = contiguous_segments(day_slots)
            for start, length, seg_slots in segs:
                i = 0
                while i < length:
                    max_block = length - i
                    block_slot_len = random.randint(1, max_block)
                    block = seg_slots[i:i+block_slot_len]
                    teacher = choose_teacher_for_block(block, giorno)
                    if teacher is None:
                        # non ci sono candidati, lasciamo per la pass finale
                        i += block_slot_len
                        continue
                    for s in block:
                        s["assigned"] = teacher
                    block_minutes = sum(s['mins'] for s in block)
                    teacher_day_slots[teacher][giorno].extend(block)
                    teacher_day_assigned[teacher][giorno] += block_minutes
                    teacher_total[teacher] += block_minutes
                    i += block_slot_len

    # TERZA PASSA: assegna qualsiasi slot ancora libero singolarmente cercando di evitare violazioni
    for cl, slots in class_slots.items():
        for s in slots:
            if s["assigned"] is None:
                giorno = s["giorno"]
                slot_min = s['mins']
                # preferisci docente che ha già ore consecutive in quel giorno
                candidates = []
                for t in teachers:
                    if teacher_total[t] + slot_min <= ORE_SETTIMANALI_DOCENTE_MIN and not will_exceed_contiguous(t, giorno, [s]):
                        # preferisci se t ha ore nello stesso giorno e vicine
                        if teacher_day_assigned[t][giorno] > 0:
                            candidates.insert(0, t)
                        else:
                            candidates.append(t)
                if not candidates:
                    # non ci sono docenti con capacità residua che rispettano il vincolo di 4h contigue
                    # cerchiamo candidati che potrebbero rispettare il vincolo se assegniamo comunque (ultima risorsa)
                    candidates = [t for t in teachers if teacher_total[t] + slot_min <= ORE_SETTIMANALI_DOCENTE_MIN]
                if not candidates:
                    # non ci sono candidati con capacità residua, scegline uno e forza (potrebbe superare il limite)
                    candidates = teachers[:]
                chosen = random.choice(candidates)
                s["assigned"] = chosen
                teacher_day_slots[chosen][giorno].append(s)
                teacher_day_assigned[chosen][giorno] += slot_min
                teacher_total[chosen] += slot_min

    # QUARTA PASSA: garantire almeno due docenti distinti per classe per giorno quando possibile
    for cl, slots in class_slots.items():
        # raggruppa per giorno
        by_day = defaultdict(list)
        for s in slots:
            by_day[s["giorno"]].append(s)
        for giorno, day_slots in by_day.items():
            assigned_teachers = defaultdict(list)
            for s in day_slots:
                if s["assigned"]:
                    assigned_teachers[s["assigned"]].append(s)
            teachers_present = list(assigned_teachers.keys())
            if len(teachers_present) >= 2:
                continue
            # se non ci sono assegnazioni (molto raro) o solo uno, proviamo a riassegnare
            free_slots = [s for s in day_slots]
            # se non ci sono almeno 2 slot fisici quel giorno non si può ottenere 2 docenti distinti
            if len(free_slots) < 2:
                # impossibile garantire 2 docenti per questo giorno — verrà segnalato nel report
                continue
            if len(teachers_present) == 0:
                # scegli due docenti differenti con capacità residua (in minuti)
                cand = [t for t in teachers if teacher_total[t] + 1 <= ORE_SETTIMANALI_DOCENTE_MIN and not will_exceed_contiguous(t, giorno, [free_slots[0]])]
                if len(cand) < 2:
                    cand = [t for t in teachers if not will_exceed_contiguous(t, giorno, [free_slots[0]])][:2]
                if len(cand) < 2:
                    cand = teachers[:2]
                chosen = random.sample(cand, 2) if len(cand) >= 2 else random.choices(teachers, k=2)
                # assegna a due slot distinti
                random.shuffle(free_slots)
                s1, s2 = free_slots[0], free_slots[1]
                # rimuovi assegnazioni pregresse se presenti
                if s1.get("assigned"):
                    prev = s1["assigned"]
                    teacher_day_assigned[prev][giorno] -= s1['mins']
                    teacher_total[prev] -= s1['mins']
                if s2.get("assigned"):
                    prev = s2["assigned"]
                    teacher_day_assigned[prev][giorno] -= s2['mins']
                    teacher_total[prev] -= s2['mins']
                # prima di assegnare verifica vincolo 4h
                if not will_exceed_contiguous(chosen[0], giorno, [s1]) and not will_exceed_contiguous(chosen[1], giorno, [s2]):
                    s1["assigned"] = chosen[0]
                    s2["assigned"] = chosen[1]
                    teacher_day_slots[chosen[0]][giorno].append(s1)
                    teacher_day_slots[chosen[1]][giorno].append(s2)
                    teacher_day_assigned[chosen[0]][giorno] += s1['mins']
                    teacher_day_assigned[chosen[1]][giorno] += s2['mins']
                    teacher_total[chosen[0]] += s1['mins']
                    teacher_total[chosen[1]] += s2['mins']
                else:
                    # se il vincolo non è rispettato per i chosen, proviamo a trovare altri target
                    alt_cand = [t for t in teachers if not will_exceed_contiguous(t, giorno, [s1]) and teacher_total[t] + s1['mins'] <= ORE_SETTIMANALI_DOCENTE_MIN]
                    if alt_cand:
                        t0 = random.choice(alt_cand)
                        s1["assigned"] = t0
                        teacher_day_slots[t0][giorno].append(s1)
                        teacher_day_assigned[t0][giorno] += s1['mins']
                        teacher_total[t0] += s1['mins']
                    # per s2
                    alt_cand2 = [t for t in teachers if not will_exceed_contiguous(t, giorno, [s2]) and teacher_total[t] + s2['mins'] <= ORE_SETTIMANALI_DOCENTE_MIN]
                    if alt_cand2:
                        t1 = random.choice(alt_cand2)
                        s2["assigned"] = t1
                        teacher_day_slots[t1][giorno].append(s2)
                        teacher_day_assigned[t1][giorno] += s2['mins']
                        teacher_total[t1] += s2['mins']
            elif len(teachers_present) == 1:
                sole = teachers_present[0]
                slots_of_sole = assigned_teachers[sole]
                # se il docente ha più di 1 ora quel giorno (in minuti), riassegna una di quelle ore a un altro docente
                if sum(x['mins'] for x in slots_of_sole) >= 2 * 60:
                    # trova candidato alternativo con capacità
                    alt = [t for t in teachers if t != sole and teacher_total[t] + 30 <= ORE_SETTIMANALI_DOCENTE_MIN and not will_exceed_contiguous(t, giorno, [max(slots_of_sole, key=lambda x: x['mins'])])]
                    if alt:
                        chosen_alt = random.choice(alt)
                        # prendi uno slot libero a caso tra quelli di sole
                        slot_to_reassign = random.choice(slots_of_sole)
                        # rimuovi assegnazione precedente
                        teacher_day_assigned[sole][giorno] -= slot_to_reassign['mins']
                        teacher_total[sole] -= slot_to_reassign['mins']
                        # assegna a docente alternativo
                        slot_to_reassign["assigned"] = chosen_alt
                        teacher_day_slots[chosen_alt][giorno].append(slot_to_reassign)
                        teacher_day_assigned[chosen_alt][giorno] += slot_to_reassign['mins']
                        teacher_total[chosen_alt] += slot_to_reassign['mins']

    return class_slots, teacher_total, teacher_day_slots

def analyze_and_report(class_slots, teacher_total, teacher_day_slots, seed):
    """Analizza l'orario generato e produce un report testuale sui vincoli verificati e violazioni.
    Restituisce (None, report_lines). Il report viene stampato in console.
    """
    report_lines = []
    try:
        report_lines.append(f"Report generato: {datetime.datetime.now().isoformat()}")
        report_lines.append(f"Random seed: {seed}")
        report_lines.append("")

        # VERIFICHE PER CLASSE: somma minuti assegnati
        report_lines.append("Verifiche per classe:")
        for cl, slots in class_slots.items():
            assigned = [s for s in slots if s.get("assigned")]
            total_min = sum(s['mins'] for s in assigned)
            delta = total_min - ORE_SETTIMANALI_CLASSE_MIN
            sign = "+" if delta > 0 else ("-" if delta < 0 else "")
            report_lines.append(f" - {cl}: assegnati {total_min} min ({total_min/60:.1f} h) | target {ORE_SETTIMANALI_CLASSE_MIN} min ({ORE_SETTIMANALI_CLASSE_MIN/60:.1f} h) | delta {sign}{abs(delta)} min ({sign}{abs(delta)/60:.1f} h)")

        report_lines.append("")

        # VERIFICA ORE SETTIMANALI DOCENTI: usa teacher_total (minuti) e calcola delta rispetto al limite
        report_lines.append("Verifica ore settimanali docenti:")
        for teacher in ASSEGNAZIONE_DOCENTI.keys():
            total = int(teacher_total.get(teacher, 0))
            delta = total - ORE_SETTIMANALI_DOCENTE_MIN
            sign = "+" if delta > 0 else ("-" if delta < 0 else "")
            report_lines.append(f" - {teacher}: assegnate={total} min ({total/60:.1f} h) | limite={ORE_SETTIMANALI_DOCENTE_MIN} min ({ORE_SETTIMANALI_DOCENTE_MIN/60:.1f} h) | delta {sign}{abs(delta)} min ({sign}{abs(delta)/60:.1f} h)")

        report_lines.append("")

        # IDENTIFICAZIONE BUCHI (non considerati violazioni): usa teacher_day_slots
        report_lines.append("Identificazione buco docenti per giorno:")
        any_buco = False
        for teacher, days in teacher_day_slots.items():
            for giorno, slots in days.items():
                if not slots:
                    continue
                idxs = sorted([s["idx"] for s in slots])
                if len(idxs) <= 1:
                    continue
                all_between = set(range(min(idxs), max(idxs)+1))
                missing = sorted(list(all_between - set(idxs)))
                if missing:
                    any_buco = True
                    report_lines.append(f" - {teacher} {giorno}: buco posizioni {missing}")
        if not any_buco:
            report_lines.append(" - Nessun buco identificato")

        report_lines.append("")

        # RIEPILOGO VIOLAZIONI: mismatch sulle somme totali e docenti oltre limite
        violations = []
        for cl, slots in class_slots.items():
            assigned = [s for s in slots if s.get("assigned")]
            total_min = sum(s['mins'] for s in assigned)
            if total_min != ORE_SETTIMANALI_CLASSE_MIN:
                violations.append(("ore_classe_mismatch", cl, total_min, ORE_SETTIMANALI_CLASSE_MIN))
        for teacher in ASSEGNAZIONE_DOCENTI.keys():
            total = int(teacher_total.get(teacher, 0))
            if total > ORE_SETTIMANALI_DOCENTE_MIN:
                violations.append(("ore_superiori", teacher, total))

        report_lines.append("Riepilogo violazioni:")
        if not violations:
            report_lines.append(" - Nessuna violazione rilevata sulle somme totali.")
        else:
            report_lines.append(f" - Totale violazioni: {len(violations)}")
            for v in violations:
                report_lines.append("   - " + str(v))

    except Exception as e:
        report_lines.append(f"Errore durante l'analisi del report: {e}")
        print(f"Errore durante l'analisi e reportistica: {e}", flush=True)

    # stampa il report in console
    print("\n" + "="*40 + " REPORT ORARIO " + "="*40 + "\n")
    for line in report_lines:
        print(line)
    print("\n" + "="*100 + "\n")

    return None, report_lines

def export_excel(class_slots):
    """Esporta l'orario in un file Excel `orario_settimanale.xlsx` con fogli separati per classi e docenti.
    Costruisce i DataFrame in memoria e salva con openpyxl; aggiunge colonne `coopertura` e `buco` nel foglio Classi e segnala i buchi nel foglio Docenti.
    """
    out_path = os.path.join(os.path.dirname(__file__), 'orario_settimanale.xlsx')
    try:
        # costruisci row_labels (giorno+indice) basandoci sul massimo numero di slot giornalieri
        max_idx_per_day = max(len(SLOT_1), len(SLOT_2), len(SLOT_3))
        row_labels = [f"{g}{i}" for g in GIORNI for i in range(1, max_idx_per_day+1)]

        # calcola coopertura e buchi
        coop_map = defaultdict(list)  # label -> [teacher,...]
        teacher_day_idxs = defaultdict(lambda: defaultdict(list))  # teacher -> giorno -> [idx,...]

        for cl, slots in class_slots.items():
            for s in slots:
                label = f"{s['giorno']}{s['idx']}"
                teacher = s.get('assigned')
                if teacher:
                    prefs = ASSEGNAZIONE_DOCENTI.get(teacher, {})
                    if cl not in prefs:
                        coop_map[label].append(teacher)
                    teacher_day_idxs[teacher][s['giorno']].append(s['idx'])

        buco_label_map = defaultdict(list)
        for teacher, days in teacher_day_idxs.items():
            for giorno, idxs in days.items():
                if not idxs:
                    continue
                idxs_sorted = sorted(idxs)
                if len(idxs_sorted) <= 1:
                    continue
                all_between = set(range(min(idxs_sorted), max(idxs_sorted)+1))
                missing = sorted(list(all_between - set(idxs_sorted)))
                for m in missing:
                    buco_label_map[f"{giorno}{m}"].append(teacher)

        # DataFrame Classi
        extra_cols = ['coopertura', 'buco']
        df_classi = pd.DataFrame('', index=row_labels, columns=CLASSI + extra_cols)
        df_classi.index.name = 'Ora'
        for cl, slots in class_slots.items():
            slot_map = {f"{s['giorno']}{s['idx']}": s for s in slots}
            for rl in row_labels:
                s = slot_map.get(rl)
                if s and s.get('assigned'):
                    df_classi.at[rl, cl] = s['assigned']
        for rl in row_labels:
            coop_list = coop_map.get(rl, [])
            df_classi.at[rl, 'coopertura'] = ','.join(coop_list) if coop_list else ''
            buco_list = buco_label_map.get(rl, [])
            df_classi.at[rl, 'buco'] = ','.join(buco_list) if buco_list else ''

        # DataFrame Docenti
        teachers = list(ASSEGNAZIONE_DOCENTI.keys())
        df_doc = pd.DataFrame('', index=row_labels, columns=teachers)
        df_doc.index.name = 'Ora'
        for cl, slots in class_slots.items():
            for s in slots:
                label = f"{s['giorno']}{s['idx']}"
                teacher = s.get('assigned')
                if teacher:
                    df_doc.at[label, teacher] = cl
        # segna buco nel foglio docenti
        for label, tlist in buco_label_map.items():
            for t in tlist:
                df_doc.at[label, t] = 'buco'

        # salva in Excel
        with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
            df_classi.to_excel(writer, sheet_name='Classi')
            df_doc.to_excel(writer, sheet_name='Docenti')

        # colorazione righe per giorno
        wb = load_workbook(out_path)
        for sheet_name in ['Classi', 'Docenti']:
            if sheet_name not in wb.sheetnames:
                continue
            ws = wb[sheet_name]
            for ridx, rl in enumerate(row_labels, start=2):
                giorno = rl[:3]
                color = DAY_COLORS.get(giorno)
                if color:
                    fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
                    for cidx in range(1, ws.max_column+1):
                        cell = ws.cell(row=ridx, column=cidx)
                        cell.fill = fill
        wb.save(out_path)
        print(f"Excel salvato in: {out_path}", flush=True)
    except Exception as e:
        print(f"Errore durante l'esportazione in Excel: {e}", flush=True)
    return out_path

def main():
    print("[DEBUG] main() start", flush=True)
    seed = seed_random()
    print(f"[DEBUG] seed={seed}", flush=True)
    class_slots = build_class_slots()
    print("[DEBUG] build_class_slots completato", flush=True)
    class_slots, teacher_total, teacher_day_slots = assign_teachers(class_slots)
    print("[DEBUG] assign_teachers completato", flush=True)
    report_path, report_lines = analyze_and_report(class_slots, teacher_total, teacher_day_slots, seed)
    print("[DEBUG] analyze_and_report completato", flush=True)
    excel_path = export_excel(class_slots)
    print("[DEBUG] export_excel completato", flush=True)
    print("Fatto.")
    # stampa report su console
    try:
        for line in report_lines:
            print(line)
    except Exception as e:
        print(f"Errore durante la stampa del report: {e}", flush=True)

print("[DEBUG] genera_orario.py avviato", flush=True)
print(f"[DEBUG] cwd={os.getcwd()}", flush=True)

if __name__ == "__main__":
    main()
