#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generatore di orari scolastici "tipo Excel" per 9 classi, con regole:
- 5 giorni (Lun-Ven), 6 ore al giorno, ma Venerdì 5 ore.
- Materie: REL (2), EF (2), ING (3), MAT (10), ITA (10).
- 1 docente per tipologia per classe.
- Ogni docente ha almeno 1 giorno libero (nessuna ora quel giorno).
- Copertura di tutti gli slot: 29 a settimana per classe. Poiché le ore materia sono 27,
  il programma aggiunge 2 ore di STU (Studio) per coprire tutti gli slot.
- Output: 9 CSV (uno per classe), pronti per Excel/Google Sheets.

Uso:
    python3 genera_orario.py
"""

import os
import csv
from collections import Counter

# Parametri base
CLASSI = 9
GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven"]
ORE_PER_GIORNO = [6, 6, 6, 6, 5]  # Venerdì 5 ore
MATERIE = ["REL", "EF", "ING", "MAT", "ITA"]  # religione, educ. fisica, inglese, matematica, italiano
ORE_SETTIMANALI = {"REL": 2, "EF": 2, "ING": 3, "MAT": 10, "ITA": 10}
FILLER = "STU"  # Studio (copertura slot mancanti)
LEGENDA = {
    "REL": "Religione",
    "EF":  "Educazione fisica",
    "ING": "Inglese",
    "MAT": "Matematica",
    "ITA": "Italiano",
    "STU": "Studio"
}

TOT_SLOT = sum(ORE_PER_GIORNO)  # 29
TOT_MATERIE = sum(ORE_SETTIMANALI.values())  # 27
assert TOT_SLOT >= TOT_MATERIE, "Gli slot totali devono essere >= ore di materia totali"

def arrange_no_adjacent(items):
    """
    Riordina le ore della giornata cercando di evitare ripetizioni immediate della stessa materia.
    Strategia greedy: prende ogni volta la materia con maggior residuo diversa dall'ultima usata.
    """
    cnt = Counter(items)
    result = []
    last = None
    while cnt:
        # Ordina per conteggio decrescente
        choices = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
        pick = None
        for k, c in choices:
            if k != last:
                pick = k
                break
        if pick is None:
            pick = choices[0][0]  # non evitabile, prendi la più frequente
        result.append(pick)
        cnt[pick] -= 1
        if cnt[pick] == 0:
            del cnt[pick]
        last = pick
    return result

def distribuisci_ore_su_giorni(ore, giorno_libero, capacita_residua):
    """
    Distribuisce 'ore' di una materia sui 4 giorni disponibili (escludendo 'giorno_libero'),
    rispettando le capacità residue giornaliere.
    Greedy: ogni ora viene assegnata al giorno con maggiore spazio residuo.
    """
    per_giorno = [0]*5
    for _ in range(ore):
        candidati = [d for d in range(5) if d != giorno_libero and per_giorno[d] < capacita_residua[d]]
        if not candidati:
            # fallback (non dovrebbe capitare): permetti anche il giorno libero se proprio serve
            candidati = [d for d in range(5) if per_giorno[d] < capacita_residua[d]]
            if not candidati:
                raise RuntimeError("Capacità giornaliere esaurite: impossibile distribuire ore.")
        # scegli il giorno con più spazio residuo complessivo
        d = max(candidati, key=lambda x: capacita_residua[x] - per_giorno[x])
        per_giorno[d] += 1
    return per_giorno

def genera_orario_classe(idx_classe):
    """
    Genera l'orario per una singola classe (indice 1..9).
    Ritorna: lista di 5 liste (una per giorno) con le materie distribuite nell'ordine orario.
    """
    # Capacità residue per giorno
    cap = ORE_PER_GIORNO[:]
    # Slot per giorno: elenco materie (verrà poi ordinato per evitare ripetizioni)
    giorno_materie = [[] for _ in range(5)]

    # Ordine di posizionamento: prima le materie con più ore
    ordine_materie = sorted(MATERIE, key=lambda m: -ORE_SETTIMANALI[m])

    for m in ordine_materie:
        # Giorno libero docente per questa materia/classe: distribuito in modo deterministico
        # per non far capitare tutti i docenti liberi lo stesso giorno.
        giorno_libero = (idx_classe + ordine_materie.index(m)) % 5

        # Distribuisci le ore della materia sui giorni consentiti
        assegnazione = distribuisci_ore_su_giorni(ORE_SETTIMANALI[m], giorno_libero, cap)

        # Applica assegnazione
        for d in range(5):
            if assegnazione[d] > 0:
                giorno_materie[d].extend([m]*assegnazione[d])
                cap[d] -= assegnazione[d]

    # Riempie gli slot rimanenti con STU (Studio) per coprire tutti gli slot
    for d in range(5):
        if cap[d] > 0:
            giorno_materie[d].extend([FILLER]*cap[d])
            cap[d] = 0

    # Ordina le ore nella giornata per gradevolezza (evita ripetizioni immediate)
    for d in range(5):
        giorno_materie[d] = arrange_no_adjacent(giorno_materie[d])

    return giorno_materie

def valida_orario(orario):
    """
    Verifica i vincoli principali su un orario di classe.
    - Conteggio ore per materia
    - Venerdì a 5 ore
    - Ogni docente ha almeno 1 giorno con 0 ore (giorno libero)
    Ritorna (ok: bool, messaggi: list[str])
    """
    msgs = []
    ok = True

    # 1) Conteggio ore per materia
    flat = [m for day in orario for m in day]
    conta = Counter(flat)
    for m in MATERIE:
        if conta[m] != ORE_SETTIMANALI[m]:
            ok = False
            msgs.append(f"Ore {m}: attese {ORE_SETTIMANALI[m]}, trovate {conta[m]}")
    # STU deve essere 2
    if conta[FILLER] != (TOT_SLOT - TOT_MATERIE):
        ok = False
        msgs.append(f"Ore {FILLER}: attese {TOT_SLOT - TOT_MATERIE}, trovate {conta[FILLER]}")

    # 2) Venerdì 5 ore
    if len(orario[4]) != 5:
        ok = False
        msgs.append("Venerdì non ha 5 ore esatte.")

    # 3) Giorno libero per ogni docente (almeno un giorno con 0 ore di quella materia)
    for m in MATERIE:
        giorni_con_ore = sum(1 for d in range(5) if m in orario[d])
        if giorni_con_ore >= 5:
            ok = False
            msgs.append(f"Nessun giorno libero per docente {m}.")
    return ok, msgs

def scrivi_csv_orario(orario, idx_classe, outdir):
    """
    Scrive l'orario in CSV con intestazione Giorno,1..6 (la 6a ora di Ven resta vuota).
    """
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"orario_classe_{idx_classe}.csv")
    header = ["Giorno", "1", "2", "3", "4", "5", "6"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(header)
        for d, nome_giorno in enumerate(GIORNI):
            riga = [nome_giorno]
            celle = orario[d][:]
            # Pad a 6 colonne (Venerdì ha 5 ore -> aggiungi vuoto)
            while len(celle) < 6:
                celle.append("")
            riga.extend(celle[:6])
            w.writerow(riga)
    return path

def main():
    outdir = "orari_csv"
    print("Generazione orari...")
    print(f"- Classi: {CLASSI}")
    print(f"- Giorni: {', '.join(GIORNI)} (Ven a 5 ore)")
    print(f"- Materie e ore: {', '.join(f'{m}={ORE_SETTIMANALI[m]}' for m in MATERIE)}")
    print(f"- Slot totali/settimana: {TOT_SLOT}, ore materia: {TOT_MATERIE}, STU previsto: {TOT_SLOT - TOT_MATERIE}")
    print()

    tutti_ok = True
    for c in range(1, CLASSI+1):
        orario = genera_orario_classe(c)
        ok, msgs = valida_orario(orario)
        path = scrivi_csv_orario(orario, c, outdir)

        stato = "OK" if ok else "PROBLEMI"
        print(f"Classe {c}: {stato} -> {path}")
        if not ok:
            tutti_ok = False
            for m in msgs:
                print("  -", m)

    print("\nLegenda materie:")
    for k, v in LEGENDA.items():
        print(f"  {k} = {v}")

    if tutti_ok:
        print("\nTutti gli orari rispettano i vincoli.")

if __name__ == "__main__":
    main()
