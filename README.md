# Scheduling con minimizzazione della Tardiness

Sistema di supporto alle decisioni (DSS) per la pianificazione di una sequenza di task (job) su più macchinari con tempi di setup, con l'obiettivo di **minimizzare la tardiness totale** (somma dei ritardi rispetto alle deadline).

Il problema è formulato come modello di **Programmazione Lineare Intera Mista (MILP)** e risolto con [PuLP](https://coin-or.github.io/pulp/) e il solutore CBC incluso.

Il progetto offre due interfacce con la stessa logica:

| File | Interfaccia |
|------|-------------|
| [dss.py](dss.py) | Riga di comando (input interattivo da terminale) |
| [dss_gui.py](dss_gui.py) | Interfaccia grafica (Tkinter) |

## Il problema

- Ci sono **N task**, ognuno con una durata, una deadline e un macchinario assegnato.
- Ogni **macchinario** ha un tempo di setup.
- I task vengono eseguiti **uno alla volta su un'unica linea temporale globale**: due task non si sovrappongono mai, anche se assegnati a macchinari diversi.
- Il setup si paga **all'inizio** (per il primo task eseguito) e **ogni volta che si cambia macchinario** tra due task consecutivi. Due task consecutivi sulla stessa macchina non richiedono setup.
- Un task è in ritardo se termina dopo la sua deadline; la sua tardiness è `max(0, completamento − deadline)`.

Sono disponibili due modalità:

1. **Ottimizzazione automatica**: il solutore sceglie l'ordine globale dei task che minimizza la tardiness totale.
2. **Ordine manuale**: l'utente fissa l'ordine globale dei task e il programma calcola tempi e tardiness risultanti. Utile per valutare una sequenza proposta e confrontarla con l'ottimo.

## Modello matematico

**Parametri**

- $J$: insieme dei task; $p_j$ durata, $d_j$ deadline, $m(j)$ macchinario del task $j$
- $s_m$: tempo di setup del macchinario $m$
- $T_{\max}$: orizzonte temporale massimo
- $M = 2\,T_{\max}$: costante Big-M
- $\sigma_{ij} = s_{m(j)}$ se $m(i) \neq m(j)$, altrimenti $0$ (setup da pagare passando da $i$ a $j$)

**Variabili**

- $C_j \in [0, T_{\max}]$: tempo di completamento del task $j$
- $T_j \ge 0$: tardiness del task $j$
- $x_{ij} \in \{0,1\}$, per ogni coppia $i < j$: vale 1 se $i$ precede $j$

**Funzione obiettivo**

$$\min \sum_{j \in J} T_j$$

**Vincoli**

$$T_j \ge C_j - d_j \qquad \forall j$$

$$C_j \ge s_{m(j)} + p_j \qquad \forall j \quad \text{(setup iniziale)}$$

Modalità ottimizzazione (vincoli disgiuntivi Big-M, per ogni coppia $i < j$):

$$C_j \ge C_i + p_j + \sigma_{ij} - M\,(1 - x_{ij})$$

$$C_i \ge C_j + p_i + \sigma_{ji} - M\,x_{ij}$$

Modalità manuale (per ogni coppia consecutiva $(i, j)$ dell'ordine scelto):

$$C_j \ge C_i + p_j + \sigma_{ij}$$

Il vincolo $T_j \ge C_j - d_j$ insieme a $T_j \ge 0$ e alla minimizzazione modella esattamente $T_j = \max(0,\, C_j - d_j)$.

## Requisiti

- Python 3 (testato con Python 3.14 e PuLP 3.3.0)
- [PuLP](https://pypi.org/project/PuLP/), che include già il solutore CBC
- Tkinter (solo per la GUI; incluso in Python su Windows e macOS, su Linux potrebbe servire il pacchetto `python3-tk`)

Installazione delle dipendenze:

```bash
pip install pulp
```

## Utilizzo

### Riga di comando

```bash
python dss.py
```

Il programma chiede, in ordine:

1. l'orizzonte temporale massimo;
2. il numero di macchinari e, per ognuno, nome e tempo di setup;
3. il numero di task e, per ognuno, nome, durata, deadline e macchinario assegnato;
4. la modalità (`1` = ottimizzazione, `2` = ordine manuale). In modalità manuale si inseriscono i nomi dei task separati da spazio, ad esempio `T2 T1 T3`.

### Interfaccia grafica

```bash
python dss_gui.py
```

Nella scheda **1. Inserimento Dati**:

1. imposta il **T Massimo** (default 100);
2. aggiungi i macchinari con nome e tempo di setup;
3. aggiungi i task con nome, durata, deadline e macchina (scelta dal menu a tendina);
4. scegli la modalità; per l'ordine manuale scrivi i nomi dei task separati da spazio nel campo di testo;
5. premi **RISOLVI / CALCOLA TARDINESS**.

I risultati compaiono nella scheda **2. Risultati**.

## Esempio

Dati in ingresso (orizzonte 100):

| Macchinario | Setup |
|-------------|-------|
| M1 | 2 |
| M2 | 3 |

| Task | Durata | Deadline | Macchinario |
|------|--------|----------|-------------|
| T1 | 4 | 6 | M1 |
| T2 | 3 | 12 | M2 |
| T3 | 2 | 8 | M1 |

**Ottimizzazione automatica**: tardiness totale 2.

```
Stato della risoluzione: Optimal
Obiettivo (Tardiness Totale): 2.0

--- Dettagli per ogni Task ---
Task T1  | Macchina: M1 | Inizio:   2.0 | Completamento:   6.0 | Deadline:  6.0 | Tardiness:  0.0
Task T3  | Macchina: M1 | Inizio:   6.0 | Completamento:   8.0 | Deadline:  8.0 | Tardiness:  0.0
Task T2  | Macchina: M2 | Inizio:  11.0 | Completamento:  14.0 | Deadline: 12.0 | Tardiness:  2.0
```

Il solutore raggruppa i due task di M1 (un solo setup iniziale) e paga il setup di M2 solo una volta, alla fine.

**Ordine manuale `T2 T1 T3`**: tardiness totale 12.

```
Task T2  | Macchina: M2 | Inizio:   3.0 | Completamento:   6.0 | Deadline: 12.0 | Tardiness:  0.0
Task T1  | Macchina: M1 | Inizio:   8.0 | Completamento:  12.0 | Deadline:  6.0 | Tardiness:  6.0
Task T3  | Macchina: M1 | Inizio:  12.0 | Completamento:  14.0 | Deadline:  8.0 | Tardiness:  6.0
```

## Note

- **Inizio** è calcolato come `completamento − durata`, quindi non comprende il tempo di setup che lo precede.
- I nomi dei task devono essere **univoci e senza spazi**, perché l'ordine manuale viene letto separando i nomi con lo spazio.
- Se l'orizzonte temporale è troppo piccolo per eseguire tutti i task, il modello risulta `Infeasible`: in quel caso aumenta il T massimo.
- L'obiettivo considera solo la tardiness: a parità di tardiness totale, il solutore può restituire tempi di completamento non compattati (con tempi morti) per i task che sono comunque in orario.
