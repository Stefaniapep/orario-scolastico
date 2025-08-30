# 📘 Generatore Orario Classi e Docenti

Genera automaticamente l'orario settimanale per un insieme di classi e docenti, rispettando vincoli generici e specifici configurabili tramite file `config.json` o tramite GUI (Streamlit).

Caratteristiche principali dell'engine:

- Slot orari configurabili per giorno e classe (fino a 3 insiemi di slot: `SLOT_1`, `SLOT_2`, `SLOT_3`).
- Assegnazione docenti per classe e ore settimanali, con eventuali ore di copertura.
- Obiettivo: minimizzazione dei buchi orari dei docenti (0 o 2 ore preferibili).
- Vincoli generici (attivabili/disattivabili con flag booleani nel config):

  -`USE_MAX_DAILY_HOURS_PER_CLASS` (default: true): massimo 4 ore/giorno per docente nella stessa classe.

  -`USE_CONSECUTIVE_BLOCKS` (default: true): se un docente fa 2 o 3 ore nella stessa classe in un giorno, devono essere consecutive.

  -`USE_MAX_ONE_HOLE` (default: true): al massimo un buco orario al giorno per docente.
- Vincoli specifici (attivati dalla presenza dei dati):

  -`LIMIT_ONE_PER_DAY_PER_CLASS`: insieme di docenti per cui vale max 1 ora/giorno nella stessa classe.

  -`ONLY_DAYS`: giorni consentiti per docente (per giorno della settimana).

  -`GROUP_DAILY_TWO_CLASSES`: docenti che, avendo 2 classi, devono fare almeno 1h/giorno in entrambe.

  -`START_AT`: orario minimo di inizio per docente e giorno.

  -`END_AT`: orario massimo di fine per docente e giorno.

  -`MIN_TWO_HOURS_IF_PRESENT_SPECIFIC`: docenti per i quali, se presenti in un giorno, devono fare almeno 2 ore complessive.

Output su Excel (`orario_settimanale.xlsx`):

- Foglio "Classi"

  - Colonne: `Slot`, poi tutte le classi, e una colonna finale `Copertura`.
  - Righe: slot giornalieri ordinati per giorno e orario (colorati per giorno).
  - Valori: nelle colonne delle classi compare il docente assegnato; nella colonna `Copertura` compaiono i docenti in copertura, se presenti.
- Foglio "Docenti"

  - Colonne: `Slot`, poi tutti i docenti.
  - Righe: slot giornalieri colorati per giorno.
  - Valori: nome classe assegnata (es. `1A`), oppure `COPERTURA`, oppure `BUCO` per indicare un buco orario.

Nota: La GUI valida e salva automaticamente la configurazione in `config.json` quando si preme "GENERA ORARIO". Il salvataggio avviene accanto all'eseguibile (se in versione compilata) o accanto ai sorgenti (in sviluppo). In lettura, se esistono sia un `config.json` esterno sia quello nel bundle PyInstaller, ha priorità quello esterno.

---

## 🔧 Dati personalizzabili

Esempio di campi principali del `config.json`:

-`CLASSI`: lista di classi (es. `["1A", "1B", "2A", ...]`).

-`GIORNI`: lista dei giorni (es. `["LUN", "MAR", "MER", "GIO", "VEN"]`).

-`SLOT_1`/`SLOT_2`/`SLOT_3`: liste di coppie `["H:MM-H:MM", durata_ore]` (la durata può essere anche 0.5).

-`ASSEGNAZIONE_SLOT`: per ogni classe e giorno, quale insieme slot usare (`SLOT_1`/`SLOT_2`/`SLOT_3`).

-`ORE_SETTIMANALI_CLASSI`: ore richieste per ogni classe.

-`MAX_ORE_SETTIMANALI_DOCENTI`: limite ore totali per docente (lezioni + copertura).

-`ASSEGNAZIONE_DOCENTI`: ore per docente su ciascuna classe, e opzionale `copertura`.

- Vincoli specifici/generici come descritti sopra.

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
pip install ortools openpyxl streamlit pandas
```

Oppure installa dal requirements in virtualenv:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## ▶️ Esecuzione ()

Esegui lo script principale dalla cartella del progetto:

```bash
#(usa config.json nella cartella corrente)
python engine.py

#oppure specificando il file di configurazione
python engine.py -c ./config.json
```

Oppure avvia l'applicazione completa di interfaccia grafica:

```bash
streamlit run app.py
```

Il file `orario_settimanale.xlsx` verrà salvato nella cartella corrente. La GUI effettua la validazione dei dati e salva `config.json` alla pressione del tasto "GENERA ORARIO".

---

## 📦 Build eseguibili (Windows)

- Solo motore (CLI):

```bash
pyinstaller --clean --name "GeneraOrarioEngine" --onefile --console --add-data "config.json;." --add-data "utils.py;." --collect-all ortools engine.py
```

- GUI Streamlit con wrapper dedicato:

```bash
pyinstaller --clean --name "GeneraOrarioApp" --onefile --console --add-data "app.py;." --add-data "config.json;." --collect-all streamlit --collect-all ortools --noconfirm streamlit_wrapper.py
```

Il tuo file eseguibile si trova all'interno della cartella dist

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
