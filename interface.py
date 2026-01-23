import customtkinter as ctk
import threading
import sys
from extrator_ergon import realizar_login_automatico, buscar_dados_servidor
from preencher import gerar_dtc

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PrintRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", text)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema Ergon - Automação")
        self.geometry("600x600")
        self.resizable(False, False)

        self.label_titulo = ctk.CTkLabel(self, text="Acesso Ergon", font=("Roboto", 24, "bold"))
        self.label_titulo.pack(pady=20)

        # --- FRAME DE LOGIN ---
        self.frame_login = ctk.CTkFrame(self)
        self.frame_login.pack(pady=20)

        self.input_user = ctk.CTkEntry(self.frame_login, placeholder_text="Usuário de Rede", width=250)
        self.input_user.pack(pady=5)

        self.input_pass = ctk.CTkEntry(self.frame_login, placeholder_text="Senha", show="*", width=250)
        self.input_pass.pack(pady=5)

        self.btn_entrar = ctk.CTkButton(self.frame_login, text="Conectar ao Sistema", command=self.acao_login)
        self.btn_entrar.pack(pady=10)

        # --- FRAME DE BUSCA (Começa invisível) ---
        self.frame_busca = ctk.CTkFrame(self)
        # Não damos .pack() aqui ainda, só quando logar

        self.input_cpf = ctk.CTkEntry(self.frame_busca, placeholder_text="Digite Matrícula/CPF", width=300)
        self.input_cpf.pack(side="left", padx=10)
        
        self.btn_gerar = ctk.CTkButton(self.frame_busca, text="Gerar DTC", command=self.acao_gerar, fg_color="green")
        self.btn_gerar.pack(side="left")

        # --- LOG ---
        self.label_status = ctk.CTkLabel(self, text="Status:", anchor="w")
        self.label_status.pack(fill="x", padx=20, pady=(20, 0))

        self.textbox_log = ctk.CTkTextbox(self, width=560, height=200)
        self.textbox_log.pack(pady=10)
        self.textbox_log.configure(state="disabled")

    def acao_login(self):
        user = self.input_user.get()
        senha = self.input_pass.get()
        
        if not user or not senha:
            return

        self.btn_entrar.configure(state="disabled", text="Conectando...")
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", ">> Iniciando navegador oculto e logando...\n")
        self.textbox_log.configure(state="disabled")

        threading.Thread(target=self.thread_login, args=(user, senha)).start()

    def thread_login(self, user, senha):
        sucesso = realizar_login_automatico(user, senha)
        
        # Volta para a thread principal para atualizar a tela
        self.after(0, lambda: self.pos_login(sucesso))

    def pos_login(self, sucesso):
        if sucesso:
            # Esconde login e mostra busca
            self.frame_login.pack_forget()
            self.frame_busca.pack(pady=20)
            self.label_titulo.configure(text="Gerador de DTC")
            self.input_cpf.focus()
            
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", ">> ✅ Login realizado com sucesso! Pode começar.\n")
            self.textbox_log.configure(state="disabled")
        else:
            self.btn_entrar.configure(state="normal", text="Conectar ao Sistema")
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert("end", ">> ❌ Falha no login. Verifique senha ou rede.\n")
            self.textbox_log.configure(state="disabled")

    def acao_gerar(self):
        cpf = self.input_cpf.get()
        if not cpf: return
        
        self.btn_gerar.configure(state="disabled", text="Aguarde...")
        threading.Thread(target=self.thread_gerar, args=(cpf,)).start()

    def thread_gerar(self, cpf):
        old_stdout = sys.stdout
        sys.stdout = PrintRedirector(self.textbox_log)
        
        print(f"\n--- Processando: {cpf} ---")
        try:
            dados = buscar_dados_servidor(cpf)
            if dados:
                gerar_dtc(dados)
                print("✅ Finalizado.")
                sucesso = True
            else:
                print("❌ Não encontrado.")
                sucesso = False
        except Exception as e:
            print(f"Erro: {e}")
            sucesso = False
        finally:
            sys.stdout = old_stdout
            self.after(0, lambda: self.reset_busca(sucesso))

    def reset_busca(self, sucesso):
        self.btn_gerar.configure(state="normal", text="Gerar DTC")
        if sucesso:
            self.input_cpf.delete(0, 'end')
            self.input_cpf.focus()

if __name__ == "__main__":
    app = App()
    app.mainloop()