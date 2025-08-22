# 📘 Generatore Orario Classi e Docenti

Genera automaticamente gli orari settimanali per un insieme di classi e li assegna a un gruppo di docenti, rispettando i vincoli di:

* Materie da insegnare e numero di ore settimanali per materia.
* Ogni classe ha assegnato sempre lo stesso docente per materia.
* Ogni giorno nelle classi ci devono essere almeno due materie diverse.
* Ogni giorno le ore di una stessa materia sono consecutive.
* Ogni docente lavora un max di ore lavorative settimanali (lezioni in classe + coperture generiche).
* Ogni docente ha almeno una giornata libera (nessuna lezione e nessuna copertura).
* Ogni docente può insegnare un diverso insieme di materie
* Identificazione delle ore di **BUCO** degli insegnanti (ore di non lezione e non copertura fra una lezione e l'altra).

Il risultato viene esportato in un file Excel (`.xlsx`) :

Foglio **Classi**

* **Colonne:** le classi (`1A, 1B, 2A, …, coopertura`).
* **Righe:** slot orari (`Lun1 … Ven5`) con un colore diverso per giorno della settimana.
* **Valori:** materia assegnata in quell’ora (es. `MAT (Doc1), ITA(Doc3), ...`).

Foglio **Docenti**

* **Colonne:** i docenti (`Doc1, Doc2, …`).
* **Righe:** slot orari (`Lun1 … Ven5`) con un colore diverso per giorno della settimana.
* **Valori:**
  * `MAT (1A)` → insegna matematica in 1A.
  * `BUCO` → ora vuota tra due lezioni nello stesso giorno.
  * `coopertura` → ora di copertura per completare le 22 ore.
  * `giorno_libero` → giorno libero o nessuna attività in quell’ora.

# I dati personalizzabili:

CLASSI = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A"]
MATERIE = ["REL", "ING", "MAT", "ITA", "MOT"]
ORE_SETTIMANALI = {"REL": 2, "MOT": 2, "ING": 3, "MAT": 10, "ITA": 10}
GIORNI = {"LUN", "MAR", "MER", "GIO", "VEN" }
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
    "Doc9": ["ING"],
    "Doc10": ["REL"],
    "Doc11": ["MOT"],
    "Doc12": ["MAT", "ITA", "ING", "REL", "MOT"],
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

## ✅ Esempio di output

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
