# Guida Tecnica al Modello CP-SAT per la Generazione di Orari

## 1. Architettura Generale

Questo script utilizza il risolutore **CP-SAT (Constraint Programming - Satisfiability)** della libreria OR-Tools di Google. A differenza di approcci più tradizionali, CP-SAT è particolarmente efficace per problemi di scheduling perché esplora lo spazio delle possibili soluzioni in modo intelligente, guidato da vincoli e da una funzione obiettivo.

Il processo logico è il seguente:

1. **Definizione dei Dati**: I dati di input (classi, docenti, ore, ecc.) vengono letti e pre-elaborati.
2. **Creazione delle Variabili di Decisione**: Il modello crea un vasto insieme di variabili booleane che rappresentano ogni possibile assegnazione (es. `x[classe, giorno, ora, docente]`).
3. **Imposizione dei Vincoli**: Le regole dell'orario vengono tradotte in vincoli matematici che limitano i valori che le variabili di decisione possono assumere.
4. **Definizione dell'Obiettivo**: Viene definita una funzione numerica (la "penalità" per i buchi) che il solver deve minimizzare.
5. **Risoluzione**: Il solver esplora lo spazio delle soluzioni, cercando una combinazione di valori per le variabili che soddisfi **tutti** i vincoli e che abbia il valore più basso possibile per la funzione obiettivo.

## 2. Strutture Dati Chiave

La comprensione di queste strutture è fondamentale per modificare il modello.

- **`UNIT`**: L'unità di tempo atomica (30 minuti). Tutte le durate vengono convertite in multipli di questa unità. Modificarla richiede una revisione attenta dei vincoli.
- **`GLOBAL_SCHEDULING_TIMES`**: Una lista ordinata delle ore di *inizio* di ogni possibile slot (es. `['8:00', '9:00', '13:00']`). È la "griglia" temporale principale, usata per gestire le sovrapposizioni e la continuità. La logica `get_scheduling_label` è cruciale per unificare slot come `"13:00-13:30"` e `"13:00-14:00"` sotto la stessa etichetta di schedulazione `"13:00"`.
- **`class_slots`**: Un dizionario che mappa `(classe, giorno)` a una lista di tuple. Ogni tupla `(sched_label, full_label, units)` rappresenta uno slot di lezione disponibile, collegando l'etichetta di schedulazione alla sua durata e all'etichetta completa.
- **`x`**: Dizionario delle variabili di decisione principali. `x[c, d, s, t]` è `1` se il docente `t` è assegnato allo slot `s` della classe `c` nel giorno `d`, `0` altrimenti.
- **`b` (busy)**: Dizionario di variabili ausiliarie. `b[t, d, sl]` è `1` se il docente `t` è impegnato (insegnamento o copertura) nello slot che inizia all'ora `sl` del giorno `d`. Questa variabile semplifica enormemente la gestione delle sovrapposizioni e dei vincoli temporali.

## 3. Logica dei Vincoli Complessi

### 3.1. Continuità Oraria (Max 1 Buco)

Questo vincolo non impone semplicemente che le ore siano contigue. Invece, conta il numero di "inizi di blocco di lavoro" in un giorno.

- Se un docente non lavora, ha 0 blocchi.
- Se lavora in un blocco unico (es. 9-12), ha 1 inizio (alle 9) e quindi 1 blocco.
- Se ha un buco (es. lavora 8-10 e 12-13), ha 2 inizi (alle 8 e alle 12) e quindi 2 blocchi.
  Il vincolo `sum(starts) <= 2` permette quindi al massimo un buco.

### 3.2. Consecutività per Blocchi di 2/3 Ore

Questo vincolo è più specifico del precedente. Si applica a una singola `(docente, classe, giorno)`.

1. **Condizione di Attivazione**: Tramite variabili booleane ausiliarie, si determina se il totale di ore insegnate da `t` in `cl` nel giorno `d` è *esattamente* 2 o 3.
2. **Calcolo dei Blocchi Specifici**: Si calcola il numero di blocchi di insegnamento per quella specifica combinazione, ignorando le altre lezioni del docente.
3. **Implicazione**: Si impone la regola: **SE** la condizione di attivazione è vera, **ALLORA** il numero di blocchi specifici deve essere `1`.

### 3.3. `START_AT` e `END_AT` (Vincoli Forti)

La generalizzazione di questi vincoli è più potente di un semplice divieto. Per una regola come `START_AT = {"SCHIAVONE": {"LUN": 9}}`:

1. Viene creata una variabile `works_on_day` per determinare se Schiavone lavora o no il lunedì.
2. Viene imposto il divieto: le ore prima delle 9:00 devono essere `0`.
3. Viene imposto l'**obbligo condizionato**: `OnlyEnforceIf(works_on_day)`, l'ora delle 9:00 *deve* essere `1`.
   Questo garantisce che se il docente è di servizio quel giorno, il suo orario rispetterà la struttura desiderata.

## 4. Strategia di Ottimizzazione

L'obiettivo non è semplicemente trovare una soluzione, ma trovare quella "migliore". La funzione `model.Minimize()` guida il solver in questa ricerca.

1. **Identificazione dei Buchi**: Vengono create variabili booleane `h` (holes). Una variabile `h[t, d, sl]` è vera se:
   - Il docente `t` non lavora nell'ora `sl` del giorno `d`.
   - Esiste almeno un'ora di lavoro per `t` *prima* di `sl` in quel giorno.
   - Esiste almeno un'ora di lavoro per `t` *dopo* di `sl` in quel giorno.
2. **Sistema di Penalità**: Per ogni `(docente, giorno)`, viene calcolata una `daily_penalty`:
   - Se le ore di buco sono 0, la penalità è `0`.
   - Se le ore di buco sono 2, la penalità è `1` (un costo molto basso, per renderla una scelta accettabile).
   - In tutti gli altri casi, la penalità è `daily_hole_units * 10` (un costo molto alto per disincentivare fortemente buchi "scomodi").
3. **Minimizzazione**: Il solver riceve l'istruzione di minimizzare la somma di tutte le `daily_penalty`. Questo lo spinge a preferire soluzioni con zero buchi, poi quelle con buchi da 2 ore, e solo come ultima risorsa quelle con buchi di altre durate.
