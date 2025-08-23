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
* [ ANGELINI, DOCENTE1, DOCENTE3, SABATELLI, SCHIAVONE, CICCIMARRA, MARANGI, SIMEONE, PEPE, PALMISANO ] : fanno almeno un ora al giorno in entrambe le classi a loro assegnate
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

```
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
    "ZIZZI": {"5A": 11},
    "MOTORIA": {"5A": 2, "4A": 2, "4B":2, "5B":2 },
    "DOCENTE2": {"5A": 3, "4A": 4, "4B":4},
    "LEO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":2, "3B":2, "4A":2, "4B":2, "5A":2},
    "SAVINO": {"1A":2, "1B":2, "2A":2, "2B":2, "3A":2, "3B":2, "4A":2, "4B":2},
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

```


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

* Modello CP-SAT (OR-Tools) che rappresenta le ore in unità da 0.5h e mappa gli slot orari per ogni classe.
* Variabili binarie per ogni (classe, giorno, slot, docente) e per le coperture.
* Vincoli implementati e verificati:
  * ogni slot di ogni classe è assegnato a esattamente un docente autorizzato;
  * le ore settimanali di ogni classe corrispondono a `ORE_SETTIMANALI_CLASSI`;
  * ogni docente rispetta le ore totali settimanali massime (inclusa copertura);
  * vincoli specifici del README: MOTORIA/SAVINO ≤1h/giorno per classe; MOTORIA solo MAR/GIO/VEN; il gruppo di docenti indicato fa almeno 1h/giorno in entrambe le loro classi; SCHIAVONE (nome nel README trattato come `SCHIAVONE`) inizia alle 9 tre volte a settimana; ZIZZI e PEPE terminano il mercoledì alle 10; le ore giornaliere di uno stesso docente sono consecutive; coperture ripartite su slot disponibili;
  * un docente non può essere asseganto contemporaneamente in più classi o coperture nello stesso orario.
* Soluzione: il solver cerca una soluzione fattibile/ottima entro un timeout (configurato nello script). Se trova una soluzione, popola due DataFrame (`Classi`, `Docenti`), individua i "buco" (ore vuote tra lezioni dello stesso docente nello stesso giorno) e salva il tutto in `orario_settimanale.xlsx` (colorazione per giorno).
* Verifica: dopo la risoluzione lo script stampa controlli che confermano (o segnalano violazioni di) tutti i vincoli principali del README.

Note e assunzioni

* La gestione delle coperture è discretizzata in unità da 0.5h e distribuita su giorni; lo script segnala eventuali vincoli impossibili.
* Timeout del solver breve per esecuzioni interattive; aumentare `solver.parameters.max_time_in_seconds` nello script se necessario.

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
