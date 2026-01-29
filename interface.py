import customtkinter as ctk
import threading
import sys

# ==============================================================================
# CORREÇÃO PARA PYTHON 3.13 (FIX "BAD SCREEN DISTANCE")
# ==============================================================================
# O CustomTkinter ainda não foi atualizado oficialmente para o Python 3.13.
# Este bloco de código intercepta a criação dos widgets e força o tamanho
# a ser um número inteiro, evitando o erro 'bad screen distance "0.0"'.
from customtkinter.windows.widgets.core_rendering import CTkCanvas

_original_init = CTkCanvas.__init__

def _fixed_init(self, *args, **kwargs):
    if "width" in kwargs:
        kwargs["width"] = int(kwargs["width"])
    if "height" in kwargs:
        kwargs["height"] = int(kwargs["height"])
    _original_init(self, *args, **kwargs)

CTkCanvas.__init__ = _fixed_init
# ==============================================================================

# Importa o extrator
from extrator_ergon import realizar_login_automatico, buscar_dados_servidor
# Importa o gerador de DTC (agora com a lógica unificada)
from preencher import gerar_dtc

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PrintRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", text)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except:
            pass # Evita erro se a janela fechar no meio do print

    def flush(self):
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Automação - Senado Federal")
        self.geometry("700x600")
        self.resizable(False, False)
        
        # Variável para saber qual documento estamos gerando
        self.modo_atual = "" 

        # --- CABEÇALHO ---
        self.label_titulo = ctk.CTkLabel(self, text="Acesso Ergon", font=("Roboto", 24, "bold"))
        self.label_titulo.pack(pady=20)

        # ===================================================
        # FRAME 1: LOGIN (Visível no início)
        # ===================================================
        self.frame_login = ctk.CTkFrame(self)
        self.frame_login.pack(pady=20)

        self.input_user = ctk.CTkEntry(self.frame_login, placeholder_text="Usuário de Rede", width=250)
        self.input_user.pack(pady=10, padx=20)

        self.input_pass = ctk.CTkEntry(self.frame_login, placeholder_text="Senha", show="*", width=250)
        self.input_pass.pack(pady=10, padx=20)

        self.btn_entrar = ctk.CTkButton(self.frame_login, text="Conectar ao Sistema", command=self.acao_login, height=40)
        self.btn_entrar.pack(pady=20)

        # ===================================================
        # FRAME 2: MENU DE ESCOLHA (Invisível no início)
        # ===================================================
        self.frame_menu = ctk.CTkFrame(self, fg_color="transparent") 
        # Não damos pack() aqui ainda

        # Botão 1: DTC
        self.btn_opcao_dtc = ctk.CTkButton(self.frame_menu, text="Gerar DTC", 
                                           command=self.selecionar_dtc, 
                                           width=300, height=60, 
                                           font=("Arial", 16, "bold"))
        self.btn_opcao_dtc.pack(pady=15)

        # Botão 2: Nova Declaração (Exemplo)
        self.btn_opcao_nova = ctk.CTkButton(self.frame_menu, text="Gerar Declaração X (Novo)", 
                                            command=self.selecionar_nova, 
                                            width=300, height=60, 
                                            font=("Arial", 16, "bold"),
                                            fg_color="#D35400", hover_color="#A04000") 
        self.btn_opcao_nova.pack(pady=15)

        # ===================================================
        # FRAME 3: BUSCA E GERAÇÃO (Invisível no início)
        # ===================================================
        self.frame_input = ctk.CTkFrame(self)
        
        self.label_instrucao = ctk.CTkLabel(self.frame_input, text="Digite a Matrícula ou CPF:", font=("Arial", 14))
        self.label_instrucao.pack(pady=(20, 5))

        self.input_cpf = ctk.CTkEntry(self.frame_input, placeholder_text="...", width=300, font=("Arial", 14))
        self.input_cpf.pack(pady=5)
        
        self.btn_gerar = ctk.CTkButton(self.frame_input, text="Processar", command=self.acao_processar, 
                                       fg_color="green", height=40, font=("Arial", 14, "bold"))
        self.btn_gerar.pack(pady=20, fill="x", padx=30)

        # Botão de Voltar para o Menu
        self.btn_voltar = ctk.CTkButton(self.frame_input, text="Voltar ao Menu", command=self.voltar_menu, 
                                        fg_color="gray", width=100)
        self.btn_voltar.pack(pady=5)

        # ===================================================
        # LOG (Rodapé)
        # ===================================================
        self.label_status = ctk.CTkLabel(self, text="Status:", anchor="w")
        self.label_status.pack(fill="x", padx=20, pady=(10, 0))

        self.textbox_log = ctk.CTkTextbox(self, width=650, height=150)
        self.textbox_log.pack(pady=10)
        self.textbox_log.configure(state="disabled")

    # -----------------------------------------------
    # LÓGICA DE LOGIN
    # -----------------------------------------------
    def acao_login(self):
        user = self.input_user.get()
        senha = self.input_pass.get()
        
        if not user or not senha:
            return

        self.btn_entrar.configure(state="disabled", text="Conectando...")
        self.log_msg(">> Iniciando login...")
        
        # Roda em thread para não travar a tela
        threading.Thread(target=self.thread_login, args=(user, senha)).start()

    def thread_login(self, user, senha):
        sucesso = realizar_login_automatico(user, senha)
        self.after(0, lambda: self.pos_login(sucesso))

    def pos_login(self, sucesso):
        if sucesso:
            self.log_msg(">> ✅ Login realizado com sucesso!")
            # Esconde Login, Mostra Menu
            self.frame_login.pack_forget()
            self.label_titulo.configure(text="Selecione o Serviço")
            self.frame_menu.pack(pady=20)
        else:
            self.btn_entrar.configure(state="normal", text="Conectar ao Sistema")
            self.log_msg(">> ❌ Falha no login. Verifique suas credenciais.")

    # -----------------------------------------------
    # LÓGICA DO MENU
    # -----------------------------------------------
    def selecionar_dtc(self):
        self.modo_atual = "DTC"
        self.mostrar_tela_input("Gerar Documento DTC")

    def selecionar_nova(self):
        self.modo_atual = "NOVA"
        self.mostrar_tela_input("Gerar Nova Declaração")

    def mostrar_tela_input(self, titulo_janela):
        self.frame_menu.pack_forget()
        self.label_titulo.configure(text=titulo_janela)
        self.frame_input.pack(pady=20)
        self.input_cpf.focus()
        self.log_msg(f">> Modo selecionado: {self.modo_atual}")

    def voltar_menu(self):
        self.frame_input.pack_forget()
        self.label_titulo.configure(text="Selecione o Serviço")
        self.frame_menu.pack(pady=20)
        self.input_cpf.delete(0, 'end')

    # -----------------------------------------------
    # LÓGICA DE PROCESSAMENTO
    # -----------------------------------------------
    def acao_processar(self):
        cpf = self.input_cpf.get()
        if not cpf: return
        
        self.btn_gerar.configure(state="disabled", text="Processando...")
        threading.Thread(target=self.thread_gerar, args=(cpf,)).start()

    def thread_gerar(self, cpf):
        # Redireciona prints para o log da tela
        old_stdout = sys.stdout
        sys.stdout = PrintRedirector(self.textbox_log)
        
        print(f"\n--- Iniciando ({self.modo_atual}) para: {cpf} ---")
        sucesso = False
        
        try:
            # 1. Busca os dados
            dados = buscar_dados_servidor(cpf)
            
            if dados:
                # 2. Decide qual documento gerar
                if self.modo_atual == "DTC":
                    print("Gerando arquivo DTC...")
                    # A função gerar_dtc agora já lida com listas ou dicionários
                    gerar_dtc(dados)
                    print("✅ DTC Finalizado com sucesso.")
                    sucesso = True
                
                elif self.modo_atual == "NOVA":
                    print("⚠️ A função da Nova Declaração ainda será criada!")
                    # AQUI VAMOS COLOCAR A FUNÇÃO NOVA DEPOIS
                    sucesso = True
            else:
                print("❌ Dados não encontrados.")
        
        except Exception as e:
            print(f"Erro Crítico: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            sys.stdout = old_stdout
            self.after(0, lambda: self.reset_busca(sucesso))

    def reset_busca(self, sucesso):
        self.btn_gerar.configure(state="normal", text="Processar")
        if sucesso:
            self.input_cpf.delete(0, 'end')
            self.input_cpf.focus()

    def log_msg(self, texto):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", texto + "\n")


        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()