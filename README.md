Prerequisiti

Avere Python 3 installato (già presente sulla maggior parte dei PC/Mac/Linux).

Salva il file

Copia il codice in un file chiamato genera_orario.py.

Esegui il programma

Da terminale/cmd, vai nella cartella dove hai salvato il file e lancia:

python3 genera_orario.py


(su Windows può essere python genera_orario.py)

Risultato

Verrà creata la cartella orari_csv/ con 9 file CSV, uno per classe:

orario_classe_1.csv, orario_classe_2.csv, …, orario_classe_9.csv

Apri i CSV con Excel o Google Sheets: le colonne sono “1..6” (ore della giornata), le righe sono i giorni (Lun–Ven).

Il venerdì ha 5 celle piene e una vuota (6ª), come richiesto.

Le sigle sono: REL (Religione), EF (Educazione Fisica), ING (Inglese), MAT (Matematica), ITA (Italiano), STU (Studio).

Cosa garantisce il programma

Ore settimanali per materia rispettate (REL 2, EF 2, ING 3, MAT 10, ITA 10).

Almeno un giorno libero per ogni docente (per materia e per classe).

Copertura di tutti gli slot: aggiunge 2 ore di STU per classe (necessario perché 29 slot > 27 ore di materia).

Venerdì a 5 ore.

Come personalizzare (facoltativo)

Modifica in testa al file:

CLASSI per cambiare il numero di classi.

MATERIE e ORE_SETTIMANALI per aggiungere/togliere materie o cambiare le ore.

ORE_PER_GIORNO per cambiare il numero di ore/giorno (ad esempio se il venerdì ha 4 ore).

La costante FILLER se vuoi nominare diversamente le ore di riempimento (es. “LAB”).

Se vuoi, posso estendere lo script per esportare direttamente un file .xlsx multipagina (uno per classe) o per imporre regole aggiuntive (es. “max 2 MAT di fila”, “ING solo al mattino”, ecc.).
