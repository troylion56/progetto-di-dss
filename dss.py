import pulp

# --- 1. Dati del problema (Input interattivo) ---
T_grande = int(input("Inserisci l'orizzonte temporale massimo (es. 100): "))

# Input Macchinari
macchinari = {}
num_macchinari = int(input("Quanti macchinari ci sono? "))
for i in range(num_macchinari):
    nome_m = input(f"Nome del macchinario {i+1}: ")
    setup_m = float(input(f"Tempo di setup per {nome_m}: "))
    macchinari[nome_m] = setup_m

# Input Tasks
tasks = {}
lista_nomi_task = []
num_tasks = int(input("\nQuanti task (job) ci sono? "))
for i in range(num_tasks):
    print(f"\n--- Inserimento dati per il Task {i+1} ---")
    nome_t = input("Nome del task (es. T1): ")
    durata_t = float(input("Durata: "))
    deadline_t = float(input("Deadline: "))
    print("Macchinari disponibili:", list(macchinari.keys()))
    macchina_t = input("A quale macchinario è assegnato? ")
    
    # Controllo per assicurarsi che il macchinario esista
    while macchina_t not in macchinari:
        print("Errore: Macchinario non valido. Scegli tra quelli disponibili.")
        macchina_t = input("A quale macchinario è assegnato? ")

    tasks[nome_t] = {'durata': durata_t, 'deadline': deadline_t, 'macchina': macchina_t}
    lista_nomi_task.append(nome_t)

# --- Scelta della modalità (Ottimizzazione vs Ordine manuale) ---
print("\n--- MODALITÀ DI ESECUZIONE ---")
print("1. Trova l'ordine automatico migliore (Ottimizzazione)")
print("2. Voglio inserire io l'ordine GLOBALE manuale dei task")
scelta_modalita = input("Scegli la modalità (1/2): ")

ordine_globale = []
if scelta_modalita == '2':
    print(f"\nTask inseriti: {', '.join(lista_nomi_task)}")
    ordine_valido = False
    while not ordine_valido:
        ordine_str = input("Inserisci i nomi separati da spazio, nell'ordine GLOBALE desiderato (es. 1 3 2): ")
        ordine_globale = ordine_str.strip().split()
        if sorted(ordine_globale) == sorted(lista_nomi_task):
            ordine_valido = True
        else:
            print("Errore: devi inserire tutti i task una sola volta.")

# Big-M: Deve essere un numero sufficientemente grande
M_big = T_grande * 2 

# --- 2. Creazione del Modello ---
# Cerchiamo di minimizzare, quindi usiamo LpMinimize
modello = pulp.LpProblem("Minimizzazione_Tardiness_Scheduling", pulp.LpMinimize)

# --- 3. Variabili Decisionali ---
# C_i: Tempo di completamento del task i (variabile continua maggiore o uguale a 0)
C = pulp.LpVariable.dicts("Completamento", tasks.keys(), lowBound=0, upBound=T_grande, cat=pulp.LpContinuous)

# T_i: Tardiness del task i (variabile continua maggiore o uguale a 0)
Tard = pulp.LpVariable.dicts("Tardiness", tasks.keys(), lowBound=0, cat=pulp.LpContinuous)

# x_ij: Variabile binaria che vale 1 se il task i precede il task j
# Creiamo le possibili coppie di TUTTI i task (perché non si accavallano mai globalmente)
coppie_tutti_i_task = []
for i in range(len(lista_nomi_task)):
    for j in range(i + 1, len(lista_nomi_task)):
        coppie_tutti_i_task.append((lista_nomi_task[i], lista_nomi_task[j]))

x = pulp.LpVariable.dicts("Precedenza", coppie_tutti_i_task, cat=pulp.LpBinary)

# --- 4. Funzione Obiettivo ---
# Obiettivo: Minimizzare la sommatoria degli scarti in ritardo.
# Matematicamente: min sum(T_i) dove T_i = max(0, C_i - d_i)
modello += pulp.lpSum([Tard[i] for i in tasks.keys()]), "Somma_Tardiness"

# --- 5. Vincoli ---

for i, data in tasks.items():
    m = data['macchina']
    setup = macchinari[m]
    p_i = data['durata']
    d_i = data['deadline']
    
    # 5.1 Definizione della Tardiness (Ti = max(0, Ci - di)):
    # Il vincolo sottostante costringe T_i ad assumere il valore (C_i - d_i). 
    # Essendo T_i inizializzato con lowBound=0, se (C_i - d_i) è negativo,
    # il solutore la forzerà al minimo consentito, ovvero 0. Questa combinazione
    # tra lowBound=0, questo vincolo e la funzione di minimizzazione, modella 
    # esattamente l'equazione T_i = max(0, C_i - d_i).
    modello += Tard[i] >= C[i] - d_i, f"Definizione_Tardiness_{i}"
    
    # 5.2 (Rimosso il vecchio vincolo di inizializzazione forzata per tutti)
    # Ora la logica di partenza/setup iniziale viene gestita in modo globale

# (Nuovo) Il primo task ad essere eseguito deve coprire il setup della sua macchina
for i in tasks.keys():
    modello += C[i] >= macchinari[tasks[i]['macchina']] + tasks[i]['durata'], f"Primo_Setup_{i}"

# 5.3 Vincoli temporali sequenziali GLOBALI (Ottimizzazione o Ordine Manuale)
if scelta_modalita == '1':
    # Modalità Ottimizzazione: Il solutore sceglie l'ordine globale
    for (i, j) in coppie_tutti_i_task:
        p_i = tasks[i]['durata']
        p_j = tasks[j]['durata']
        
        # Calcolo del setup incrociato: se passiamo ad un'altra macchina, si paga il setup della nuova
        setup_su_j = macchinari[tasks[j]['macchina']] if tasks[i]['macchina'] != tasks[j]['macchina'] else 0
        setup_su_i = macchinari[tasks[i]['macchina']] if tasks[i]['macchina'] != tasks[j]['macchina'] else 0
        
        modello += C[j] >= C[i] + p_j + setup_su_j - M_big * (1 - x[(i, j)]), f"Disgiuntivo_1_{i}_{j}"
        modello += C[i] >= C[j] + p_i + setup_su_i - M_big * x[(i, j)], f"Disgiuntivo_2_{i}_{j}"
elif scelta_modalita == '2':
    # Modalità Manuale: Fissiamo l'ordine GLOBALE indicato dall'utente
    for k in range(len(ordine_globale) - 1):
        i = ordine_globale[k]
        j = ordine_globale[k+1]
        p_j = tasks[j]['durata']
        
        # Se passiamo ad una macchina diversa, dobbiamo pagare il setup!
        setup_su_j = macchinari[tasks[j]['macchina']] if tasks[i]['macchina'] != tasks[j]['macchina'] else 0
        
        modello += C[j] >= C[i] + p_j + setup_su_j, f"Manuale_Ordine_{i}_precede_{j}"

# --- 6. Risoluzione ---
# Risolviamo il modello silenziando l'output del solutore (msg=False)
modello.solve(pulp.PULP_CBC_CMD(msg=False))

# --- 7. Stampa dei Risultati ---
print(f"Stato della risoluzione: {pulp.LpStatus[modello.status]}")
print(f"Obiettivo (Tardiness Totale): {pulp.value(modello.objective)}")

print("\n--- Dettagli per ogni Task ---")
# Li ordiniamo per tempo di completamento per maggiore chiarezza
task_ordinati = sorted(tasks.keys(), key=lambda t: pulp.value(C[t]))

for i in task_ordinati:
    inizio_stimato = pulp.value(C[i]) - tasks[i]['durata']
    completamento = pulp.value(C[i])
    tardiness = pulp.value(Tard[i])
    deadline = tasks[i]['deadline']
    macchina = tasks[i]['macchina']
    
    print(f"Task {i:<3} | Macchina: {macchina} | Inizio: {inizio_stimato:>5.1f} | Completamento: {completamento:>5.1f} | Deadline: {deadline:>4} | Tardiness: {tardiness:>4.1f}")