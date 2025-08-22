# 📘 Generatore Orario Classi e Docenti

Genera automaticamente gli orari settimanali per un insieme di classi e li assegna a un gruppo di docenti, rispettando i vincoli:

* Slot orari delle classi sono variabili e devono sempre essere assegnati ad un docente.
* Ogni giorno nelle classi ci devono essere almeno due docenti diversi.
* Ogni giorno le ore di uno stesso docente sono consecutive.
* Ogni docente lavora un max di ore lavorative settimanali (lezioni in classe + coperture).
* Ogni docente ha le sue assegnazioni predefinite
* Identificazione delle ore di buco degli insegnanti (ore di non lezione e non copertura fra una lezione e l'altra).

Il risultato viene esportato in un file Excel (`.xlsx`) :

Foglio **Classi**

* **Colonne:** le classi (`1A, 1B, 2A, …, coopertura, buco` ).
* **Righe:** slot orari (`Lun1 … Ven5`) con un colore diverso per giorno della settimana.
* **Valori:** materia assegnata in quell’ora (es. `MAT (Doc1), ITA(Doc3), ...`).

Foglio **Docenti**

* **Colonne:** i docenti (`Doc1, Doc2, …`).
* **Righe:** slot orari (`Lun1 … Ven5`) con un colore diverso per giorno della settimana.
* **Valori:**
  * `MAT (1A)` → insegna matematica in 1A.
  * `buco` → ora vuota tra due lezioni nello stesso giorno.
  * `coopertura` → ora di copertura per completare le 22 ore.

# I dati personalizzabili:

CLASSI = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A"]

GIORNI = ["LUN", "MAR", "MER", "GIO", "VEN" ]

ORE_SETTIMANALI_DOCENTE = 22
ORE_SETTIMANALI_CLASSE = 27

DOCENTI = [ "ANGELINI", "DOCENTE1", "SABATELLI", "SCHIAVONE", “CICCIMARRA”, "MARANGI", "SIMEONE", 	"PEPE", "PALMISANO", "ZIZZI", "DOCENTE2", "MOTORIA”, "LEO", "SAVINO"]

SLOT_1 = {"8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00","13:00-13:30"}
SLOT_2 = {"8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00","13:00-13:30"}
SLOT_3 = {"8:00-9:00","9:00-10:00","10:00-11:00","11:00-12:00","12:00-13:00"}

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

ASSEGNAZIONE_DOCENTI = {
	"ANGELINI"= {"1A”: 11, "1B”:11},
	"DOCENTE1"= {"1A”: 11, "1B”:11},
	"SABATELLI"= {"2A”: 9, "2B”:9, “copertura”:4},
	"SCHIAVONE"= {"2A”: 11, "2B”:11},
	“CICCIMARRA”= {"2A”: 3, "2B”:3, “copertura”:6},
	"MARANGI"= {"3A”: 10, "3B”:10, “copertura”:2},
	"SIMEONE"= {"3A”: 11, "3B”:11},
	"PEPE"= {"4A”: 8, "4B”:8, “copertura”:6},
	"PALMISANO"= {"4A”: 10, "4B”:10, “copertura”:2},
	"ZIZZI"= {"5A”: 11, "5B”:11},
	"DOCENTE2"= {"5A”: 3, "5B”:3, "4A”: 4, "4B”:4},
	"MOTORIA”= {"5A”: 2, "5B”:2, "4A”: 2, "4B”:2},
	"LEO"= {"1A”: 2, "1B”:2, "2A”: 2, "2B”:2 "3A”: 2, "3B”:2, "4A”: 2 "4B”:2, "5A”: 2, "5B”:2},
	"SAVINO"= {"1A”: 2,  "1B”:2, "2A”: 2,  "2B”:2 "3A”: 2, "3B”:2, "4A”: 2, "4B”:2},
}

---

## 🚀 Installazione

Prerequisiti: `Python 3.8+` e `git`.

Clona il repository (o spostati nella cartella del progetto se l'hai già scaricato):

```bash
git clone https://github.com/tuo-utente/orario-scolastico.git
cd orario-scolastico
```

Se non vuoi usare un ambiente virtuale, installa le dipendenze globalmente o usando il flag `--user` (consigliato su macOS/Linux/Windows senza privilegi amministrativi).

Aggiorna pip e installa i pacchetti richiesti:

```bash
python -m pip install --upgrade pip
# installa dal requirements
python -m pip install -r requirements.txt
```

Note utili:

- Su Windows, se `python` non è nel PATH, prova `py -3 -m pip install pandas openpyxl`.
- Se preferisci, puoi installare singolarmente solo i pacchetti necessari: `pip install pandas openpyxl`.

---

## ▶️ Esecuzione

Esegui lo script principale dalla cartella del progetto:

```bash
python genera_orario.py
```

Su Windows, se `python` non è disponibile, puoi usare il launcher:

```bash
py -3 genera_orario.py
```

Al termine verrà generato il file `orario_settimanale.xlsx` nella cartella corrente. I fogli creati sono `Classi` e `Docenti`.

---

## 🛠️ Implementazione (sintesi)

Lo script principale è `genera_orario.py`. Di seguito una panoramica sintetica dell'implementazione e dei requisiti effettivamente soddisfatti.

- Approccio generale
  - I tempi sono gestiti in minuti (1h = 60 min, 0.5h = 30 min) per calcolare somme esatte anche con slot da 30 minuti.
  - Per ogni classe lo script costruisce la lista degli slot disponibili (in base a `ASSEGNAZIONE_SLOT`) e seleziona un sottoinsieme di slot la cui somma in minuti è pari al target settimanale (o, se non possibile, alla somma massima <= target) usando un semplice algoritmo di subset-sum.
  - L'assegnazione ai docenti utilizza un'euristica in più passate:
    1. Prima passata: tenta di soddisfare le quote esplicite in `ASSEGNAZIONE_DOCENTI` piazzando blocchi contigui.
    2. Seconda passata: riempie i blocchi liberi privilegiando la consecutività e i docenti con capacità residua.
    3. Terza passata: assegna singoli slot rimasti.
    4. Passata finale: tenta di ottenere (quando possibile) almeno 2 docenti distinti per classe per giornata tramite riassegnazioni (se compatibile con gli altri vincoli).
  - Uso di seed casuale (basato su os.urandom + timestamp) per garantire che ogni run produca un'orario diverso.

- Vincoli applicati e controlli
  - Conversione dei vincoli di ore in minuti per conti precisi (ore settimanali docente e classe).
  - Nessuna ora di lezione rimane non assegnata: tutti gli slot scelti per la classe vengono assegnati a un docente.
  - Nessun blocco continuo di lezioni per lo stesso docente supera 4 ore consecutive (vincolo verificato prima di ogni assegnazione; lo script tenta riassegnazioni per rispettarlo).
  - Il totale ore settimanali per docente è rispettato ove possibile; eventuali superamenti sono segnalati nel report.
  - Le ore di "copertura" (quando un docente insegna in una classe non prevista nella sua mappa) sono segnate e riportate nel foglio `Classi` (colonna `coopertura`).
  - I "buchi" per docente (slot mancanti tra prima e ultima lezione dello stesso giorno) sono identificati e riportati:
    - nel foglio `Docenti` tramite la stringa `buco` sulle celle corrispondenti;
    - nel foglio `Classi` nella colonna `buco` viene elencato il/i docente/i che hanno un buco su quello slot.

- Output
  - Excel `orario_settimanale.xlsx` con due fogli:
    - `Classi`: colonne per ciascuna classe e colonne aggiuntive `coopertura` e `buco`.
    - `Docenti`: colonne per ciascun docente; le celle contengono la classe insegnata o `buco` quando presente.
  - Report stampato in console che:
    - mostra per ogni classe i minuti assegnati e il delta rispetto al target (in minuti e ore);
    - mostra per ogni docente i minuti assegnati, il delta rispetto al limite settimanale;
    - elenca i buchi identificati (non considerati violazioni automatiche);
    - riepiloga le violazioni di somma (solo mismatch totali e docenti oltre il limite).

- Requisiti soddisfatti
  - Gestione di slot variabili (30/60 min) e calcolo preciso delle ore in minuti.
  - Esportazione in Excel con fogli `Classi` e `Docenti` e colonne `coopertura`/`buco` richieste.
  - Ogni run genera un'assegnazione differente (seed casuale).
  - Identificazione e marcatura dei buchi degli insegnanti.
  - Tentativo di garantire almeno due docenti diversi per classe al giorno (quando possibile).
  - Rispetto del limite di 4 ore consecutive per docente.

- Limitazioni note
  - L'algoritmo è euristico: in scenari molto vincolati (poche risorse o conflitti) lo script può non riuscire a soddisfare simultaneamente tutti i vincoli; i mismatch totali vengono segnalati nel report.
  - La definizione di "copertura" è approssimativa e derivata dalla mappa `ASSEGNAZIONE_DOCENTI` (se il docente svolge ora in una classe non prevista nella sua mappa, quella ora è marcata come copertura).
  - La garanzia che ogni classe abbia esattamente le ore target è tentata tramite subset-sum; se non è possibile con gli slot disponibili viene scelta la migliore combinazione <= target e la discrepanza è segnalata.

- Esecuzione
  - Installare dipendenze: `python -m pip install -r requirements.txt` (pandas, openpyxl, ortools opzionale)
  - Eseguire: `python genera_orario.py` (il report verrà stampato in console; l'excel verrà salvato in `orario_settimanale.xlsx`).

---

### 📊 Foglio Classi (estratto)

| Ora  | 1A        | 1B        | 2A        | … |
| ---- | --------- | --------- | --------- | -- |
| Lun1 | MAT(DOC1) | ITA(DOC") | ING(DOC3) | … |
| Lun2 | ING(DOC3) | REL(DOC4) | MAT(DOC1) | … |

### 📊 Foglio Docenti (estratto)

| Ora  | Doc1     | Doc2     | Doc3     | … |
| ---- | -------- | -------- | -------- | -- |
| Lun1 | MAT (1A) | ITA (1B) | ING (2A) | … |
| Lun2 | BUCO     | COP      | ING (3B) | … |
