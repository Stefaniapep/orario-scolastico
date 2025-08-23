# 📘 Generatore Orario Classi e Docenti

Genera automaticamente gli orari settimanali per un insieme di classi e li assegna a un gruppo di docenti, rispettando vincoli generici:

* Slot orari delle classi sono variabili e devono sempre essere assegnati ad un docente.
* Ogni giorno nelle classi ci devono essere almeno due docenti diversi.
* Ogni giorno le ore di uno stesso docente sono consecutive.
* Ogni docente lavora un max di ore lavorative settimanali (lezioni in classe + coperture).
* Ogni docente ha le sue assegnazioni predefinite
* Identificazione delle ore di buco degli insegnanti (ore di non lezione e non copertura fra una lezione e l'altra).

E vincoli specifici:

* [ MOTORIA, SAVINO ] : non fanno mai più di un ora al giorno per classe.
* [ MOTORIA ] : lezione solo MAR, GIO, VEN.
* [ ANGELINI, DOCENTE1, DOCENTE3, SABATELLI, SCHIAVONE, MARANGI, SIMEONE, PEPE, PALMISANO ] : fanno almeno un ora al giorno in entrambe le classi a loro assegnate
* [ SHIAVONE ] : inizia le lezioni alle 9 tre volte a settimana
* [ ZIZZI ] : termina le lezioni alle ore 10 MER
* [ PEPE ] : termina le lezioni alle ore 10 LUN

Il risultato viene esportato in un file Excel (`.xlsx`) :

Foglio **Classi**

* **Colonne:** le classi (`1A, 1B, 2A, …, coopertura, buco`).
* **Righe:** slot orari (`Lun1 … Ven5`) con un colore diverso per giorno della settimana.
* **Valori:** materia assegnata in quell’ora (es. `MAT (Doc1), ITA(Doc3), ...`).

Foglio **Docenti**

* **Colonne:** i docenti (`Doc1, Doc2, …`).
* **Righe:** slot orari (`Lun1 … Ven5`) con un colore diverso per giorno della settimana.
* **Valori:**
  * `MAT (1A)` → insegna matematica in 1A.
  * `buco` → ora vuota tra due lezioni nello stesso giorno.
  * `coopertura` → ora di copertura assegnate.

# I dati personalizzabili:

CLASSI = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B"]

GIORNI = ["LUN", "MAR", "MER", "GIO", "VEN" ]

DOCENTI = [ "ANGELINI", "DOCENTE1", "SABATELLI", "SCHIAVONE", “CICCIMARRA”, "MARANGI", "SIMEONE", "PEPE", "PALMISANO", "ZIZZI", "DOCENTE2", "MOTORIA”, "LEO", "SAVINO"]

MAX_ORE_SETTIMANALI_DOCENTI = 22
ORE_SETTIMANALI_CLASSI : {
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
# installa dal requirements
python -m pip install -r requirements.txt
```

Note utili:

- Su Windows, se `python` non è nel PATH, prova `py -3 -m pip install pandas openpyxl`.

---

## ▶️ Esecuzione

Esegui lo script principale dalla cartella del progetto:

```bash
streamlit run app.py
```

Su Windows, se `python` non è disponibile, puoi usare il launcher:

```bash
py -3 genera_orario.py
```

Al termine verrà generato il file `orario_settimanale.xlsx` nella cartella corrente. I fogli creati sono `Classi` e `Docenti`.

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
