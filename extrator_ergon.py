from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Variável GLOBAL para segurar o navegador
driver = None

def iniciar_driver_debug():
    global driver
    print("--- Inicializando driver em modo HEADLESS (Invisível) ---")
    
    options = webdriver.ChromeOptions()

    options.add_argument('--headless') 
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--ignore-certificate-errors')
    
    driver = webdriver.Chrome(options=options)
    return driver

def realizar_login_automatico(usuario, senha):
    global driver
    
    try:
        if driver is None:
            iniciar_driver_debug()
            
        url_alvo = "https://www26.senado.leg.br/senado/Ergon/Administracao/ERGadm00104.tp"
        driver.get(url_alvo)
        
        print("Aguardando página de login...")
        time.sleep(3) 
        
        # --- LOGIN ---
        try:
            driver.find_element(By.ID, "username").clear()
        except: pass
        driver.find_element(By.ID, "username").send_keys(usuario)
        
        try:
            driver.find_element(By.ID, "password").clear()
        except: pass
        driver.find_element(By.ID, "password").send_keys(senha)
        driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        
        print("Login enviado. Esperando 5s para carregar sistema...")
        time.sleep(5)
        
        return True

    except Exception as e:
        print(f"Erro no login: {e}")
        return False

def buscar_dados_servidor(CPF_ALVO):
    global driver
    
    if driver is None:
        print("ERRO CRÍTICO: O navegador não foi detectado. Faça o login novamente.")
        return None

    try:
        print(f"--- Iniciando busca por: {CPF_ALVO} ---")
        
        # 1. ENCONTRAR O CAMPO CORRETO
        # O problema 'not interactable' acontece porque existem VÁRIOS inputs 'searchbox' escondidos.
        # Aqui pegamos todos e filtramos apenas o que está VISÍVEL.
        campo_busca = None
        
        # Procura todos os inputs com a classe 'searchbox'
        candidatos = driver.find_elements(By.CSS_SELECTOR, "input.searchbox")
        
        for input_teste in candidatos:
            if input_teste.is_displayed() and input_teste.is_enabled():
                campo_busca = input_teste
                break # Achamos o visível, pode parar de procurar
        
        # Se não achou nenhum visível pela classe, tenta pegar o elemento ativo (plano B)
        if campo_busca is None:
            print("Aviso: Searchbox visível não encontrada. Tentando usar o elemento focado.")
            campo_busca = driver.switch_to.active_element

        # 2. CLICAR E LIMPAR
        campo_busca.click()
        time.sleep(0.5)
        
        # Tenta limpar com clear, se falhar (erro de estado), ignora e digita por cima
        try:
            campo_busca.clear()
        except:
            pass

        # 3. DIGITAR
        print(f"Digitando CPF: {CPF_ALVO}")
        campo_busca.send_keys(CPF_ALVO)
        
        # 4. PAUSA OBRIGATÓRIA (Sua regra dos 5s)
        print("Aguardando 5 segundos (Regra do sistema)...")
        time.sleep(5)
        
        print("Enviando ENTER...")
        campo_busca.send_keys(Keys.RETURN)
        
        print("Aguardando 4 segundos para dados aparecerem...")
        time.sleep(4) 

        # 5. RASPAGEM
        dados = {}
        
        def pegar_texto(id_elemento):
            try:
                return driver.find_element(By.ID, id_elemento).text
            except:
                return ""

        dados['nome_servidor'] = pegar_texto("txfNome")
        dados['cpf'] = pegar_texto("txfCpf")
        dados['matricula'] = pegar_texto("txfNumero")
        
        dados['data_nascimento'] = pegar_texto("txfDtnasc")
        dados['nome_pai'] = pegar_texto("txfPai")
        dados['nome_mae'] = pegar_texto("txfMae")
        dados['pis'] = pegar_texto("txfPispasep")
        dados['id'] = pegar_texto("txfNumrg")
        dados['ssp'] = pegar_texto("txfOrgaorg")
        dados['uf'] = pegar_texto("txfUfrg")

        if not dados['nome_servidor']:
            print("Aviso: Nome não apareceu. A busca pode ter falhado.")
            return None

        return dados

    except Exception as e:
        print(f"ERRO DE EXECUÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return None