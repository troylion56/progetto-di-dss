import tkinter as tk
from tkinter import ttk, messagebox
import pulp

class SchedulerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scheduling - Minimizzazione Tardiness")
        self.geometry("800x600")
        
        self.macchinari = {} # {nome: setup}
        self.tasks = {} # {nome: {durata, deadline, macchina}}
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame Principale
        main_frame = ttk.Notebook(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Immissione Dati
        tab_dati = ttk.Frame(main_frame)
        main_frame.add(tab_dati, text="1. Inserimento Dati")
        
        # --- Sezione Orizzonte Temporale ---
        frame_t = ttk.LabelFrame(tab_dati, text="Orizzonte Temporale")
        frame_t.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(frame_t, text="T Massimo:").pack(side=tk.LEFT, padx=5, pady=5)
        self.var_t = tk.IntVar(value=100)
        ttk.Entry(frame_t, textvariable=self.var_t, width=10).pack(side=tk.LEFT, padx=5)
        
        # --- Frame centrale diviso a metà ---
        frame_mid = ttk.Frame(tab_dati)
        frame_mid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Sezione Macchinari (Sinistra) ---
        frame_m = ttk.LabelFrame(frame_mid, text="2. Macchinari")
        frame_m.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(frame_m, text="Nome Macchina:").grid(row=0, column=0, padx=5, pady=5)
        self.var_m_nome = tk.StringVar()
        ttk.Entry(frame_m, textvariable=self.var_m_nome, width=10).grid(row=0, column=1)
        
        ttk.Label(frame_m, text="Tempo Setup:").grid(row=1, column=0, padx=5, pady=5)
        self.var_m_setup = tk.DoubleVar()
        ttk.Entry(frame_m, textvariable=self.var_m_setup, width=10).grid(row=1, column=1)
        
        ttk.Button(frame_m, text="Aggiungi Macchina", command=self.add_macchina).grid(row=2, column=0, columnspan=2, pady=10)
        
        self.list_m = tk.Listbox(frame_m, height=10)
        self.list_m.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # --- Sezione Tasks (Destra) ---
        frame_t = ttk.LabelFrame(frame_mid, text="3. Tasks (Job)")
        frame_t.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(frame_t, text="Nome Task:").grid(row=0, column=0, padx=5, pady=5)
        self.var_t_nome = tk.StringVar()
        ttk.Entry(frame_t, textvariable=self.var_t_nome, width=10).grid(row=0, column=1)
        
        ttk.Label(frame_t, text="Durata:").grid(row=1, column=0, padx=5, pady=5)
        self.var_t_durata = tk.DoubleVar()
        ttk.Entry(frame_t, textvariable=self.var_t_durata, width=10).grid(row=1, column=1)
        
        ttk.Label(frame_t, text="Deadline:").grid(row=2, column=0, padx=5, pady=5)
        self.var_t_deadline = tk.DoubleVar()
        ttk.Entry(frame_t, textvariable=self.var_t_deadline, width=10).grid(row=2, column=1)
        
        ttk.Label(frame_t, text="Macchina:").grid(row=3, column=0, padx=5, pady=5)
        self.cmb_t_macchina = ttk.Combobox(frame_t, state="readonly", width=8)
        self.cmb_t_macchina.grid(row=3, column=1)
        
        ttk.Button(frame_t, text="Aggiungi Task", command=self.add_task).grid(row=4, column=0, columnspan=2, pady=10)
        
        self.list_t = tk.Listbox(frame_t, height=10)
        self.list_t.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # --- Riepilogo / Esecuzione ---
        frame_bot = ttk.Frame(tab_dati)
        frame_bot.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(frame_bot, text="Scegli la modalità (Ottimizzazione o Ordine Manuale):").pack()
        self.var_modalita = tk.StringVar(value="1")
        ttk.Radiobutton(frame_bot, text="Ottimizzazione Automatica", variable=self.var_modalita, value="1").pack()
        ttk.Radiobutton(frame_bot, text="Ordine Manuale (scrivi l'ordine globale coi nomi divisi da spazio)", variable=self.var_modalita, value="2").pack()
        
        self.var_ordine = tk.StringVar()
        ttk.Entry(frame_bot, textvariable=self.var_ordine, width=40).pack(pady=5)
        
        ttk.Button(frame_bot, text="RISOLVI / CALCOLA TARDINESS", command=self.solve_model).pack(pady=10)
        
        # --- Tab 2: Risultati ---
        self.tab_risultati = ttk.Frame(main_frame)
        main_frame.add(self.tab_risultati, text="2. Risultati")
        
        self.txt_risultati = tk.Text(self.tab_risultati, font=("Courier", 10))
        self.txt_risultati.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def add_macchina(self):
        n = self.var_m_nome.get().strip()
        s = self.var_m_setup.get()
        if n:
            self.macchinari[n] = s
            self.list_m.insert(tk.END, f"{n} (Setup: {s})")
            self.var_m_nome.set("")
            self.var_m_setup.set(0.0)
            self.cmb_t_macchina['values'] = list(self.macchinari.keys())
            if not self.cmb_t_macchina.get() and self.macchinari:
                self.cmb_t_macchina.current(0)
                
    def add_task(self):
        n = self.var_t_nome.get().strip()
        d = self.var_t_durata.get()
        dl = self.var_t_deadline.get()
        m = self.cmb_t_macchina.get()
        
        if n and m in self.macchinari:
            self.tasks[n] = {'durata': d, 'deadline': dl, 'macchina': m}
            self.list_t.insert(tk.END, f"{n} (Macch: {m}, Dur: {d}, Dead: {dl})")
            self.var_t_nome.set("")
            self.var_t_durata.set(0.0)
            self.var_t_deadline.set(0.0)
            
    def solve_model(self):
        if not self.macchinari or not self.tasks:
            messagebox.showerror("Errore", "Inserisci almeno un macchinario e un task.")
            return
            
        T_grande = self.var_t.get()
        M_big = T_grande * 2
        modalita = self.var_modalita.get()
        lista_nomi_task = list(self.tasks.keys())
        ordine_globale = []
        
        if modalita == "2":
            ordine_str = self.var_ordine.get().strip().split()
            if sorted(ordine_str) != sorted(lista_nomi_task):
                messagebox.showerror("Errore", f"L'ordine manuale non è valido.\nI task sono: {', '.join(lista_nomi_task)}")
                return
            ordine_globale = ordine_str
            
        # Modello
        modello = pulp.LpProblem("Min_Tardiness", pulp.LpMinimize)
        C = pulp.LpVariable.dicts("Completamento", self.tasks.keys(), lowBound=0, upBound=T_grande, cat=pulp.LpContinuous)
        Tard = pulp.LpVariable.dicts("Tardiness", self.tasks.keys(), lowBound=0, cat=pulp.LpContinuous)
        
        coppie_tutti = []
        for i in range(len(lista_nomi_task)):
            for j in range(i + 1, len(lista_nomi_task)):
                coppie_tutti.append((lista_nomi_task[i], lista_nomi_task[j]))
                
        x = pulp.LpVariable.dicts("Prec", coppie_tutti, cat=pulp.LpBinary)
        
        modello += pulp.lpSum([Tard[i] for i in self.tasks.keys()]), "Somma_Tardiness"
        
        for i, data in self.tasks.items():
            modello += Tard[i] >= C[i] - data['deadline']
            modello += C[i] >= self.macchinari[data['macchina']] + data['durata']
            
        if modalita == '1':
            for (i, j) in coppie_tutti:
                p_i = self.tasks[i]['durata']
                p_j = self.tasks[j]['durata']
                s_j = self.macchinari[self.tasks[j]['macchina']] if self.tasks[i]['macchina'] != self.tasks[j]['macchina'] else 0
                s_i = self.macchinari[self.tasks[i]['macchina']] if self.tasks[i]['macchina'] != self.tasks[j]['macchina'] else 0
                
                modello += C[j] >= C[i] + p_j + s_j - M_big * (1 - x[(i, j)])
                modello += C[i] >= C[j] + p_i + s_i - M_big * x[(i, j)]
        else:
            for k in range(len(ordine_globale) - 1):
                i = ordine_globale[k]
                j = ordine_globale[k+1]
                p_j = self.tasks[j]['durata']
                s_j = self.macchinari[self.tasks[j]['macchina']] if self.tasks[i]['macchina'] != self.tasks[j]['macchina'] else 0
                modello += C[j] >= C[i] + p_j + s_j
                
        # Esecuzione
        modello.solve(pulp.PULP_CBC_CMD(msg=False))
        
        status = pulp.LpStatus[modello.status]
        obj = pulp.value(modello.objective)
        
        res = f"--- RISULTATI ---\n"
        res += f"Stato: {status}\n"
        res += f"TARDINESS TOTALE: {obj}\n\n"
        
        task_ordinati = sorted(self.tasks.keys(), key=lambda t: pulp.value(C[t]))
        
        for i in task_ordinati:
            completamento = pulp.value(C[i])
            inizio = completamento - self.tasks[i]['durata']
            tard = pulp.value(Tard[i])
            res += f"Task {i:<4} | Macchina: {self.tasks[i]['macchina']:<4} | Inizio: {inizio:>5.1f} | Fine: {completamento:>5.1f} | Deadline: {self.tasks[i]['deadline']:>5.1f} | Tardiness: {tard:>5.1f}\n"
            
        self.txt_risultati.delete(1.0, tk.END)
        self.txt_risultati.insert(tk.END, res)
        messagebox.showinfo("Successo", "Risolto! Vai alla scheda Risultati per vedere i dettagli.")

if __name__ == "__main__":
    app = SchedulerGUI()
    app.mainloop()