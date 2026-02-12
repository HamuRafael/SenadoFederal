from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# --- NOVAS IMPORTAÇÕES (Para corrigir o erro do driver) ---
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Variável GLOBAL para segurar o navegador
driver = None

def iniciar_driver_debug():
    global driver
    print("--- Inicializando driver VISÍVEL ---")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--ignore-certificate-errors')
    
    # --- MUDANÇA AQUI: Usa o gerenciador para baixar/achar o driver ---
    try:
        servico = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=servico, options=options)
    except Exception as e:
        print(f"Erro no gerenciador: {e}")
        # Tenta o método antigo se o gerenciador falhar
        driver = webdriver.Chrome(options=options)

    return driver

def realizar_login_automatico(usuario, senha):
    global driver
    try:
        if driver is None:
            iniciar_driver_debug()
            
        url_alvo = "https://www26.senado.leg.br/senado/Ergon/Administracao/ERGadm00104.tp"
        driver.get(url_alvo)
        time.sleep(2) 
        
        try: driver.find_element(By.ID, "username").clear()
        except: pass
        driver.find_element(By.ID, "username").send_keys(usuario)
        
        try: driver.find_element(By.ID, "password").clear()
        except: pass
        driver.find_element(By.ID, "password").send_keys(senha)
        driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
        
        time.sleep(4)
        return True
    except Exception as e:
        print(f"Erro no login: {e}")
        return False

def buscar_dados_servidor(CPF_ALVO):
    global driver
    
    if driver is None:
        print("ERRO CRÍTICO: Navegador fechado.")
        return None

    try:
        dados_base = {} 
        lista_final_dados = [] 

        # =================================================================
        # ETAPA 1: DADOS PESSOAIS (Página 104)
        # =================================================================
        print(f"--- [ETAPA 1] Buscando dados pessoais: {CPF_ALVO} ---")
        driver.get("https://www26.senado.leg.br/senado/Ergon/Administracao/ERGadm00104.tp")
        time.sleep(2)
        
        campo_busca = None
        candidatos = driver.find_elements(By.CSS_SELECTOR, "input.searchbox")
        for input_teste in candidatos:
            if input_teste.is_displayed() and input_teste.is_enabled():
                campo_busca = input_teste
                break 
        if campo_busca is None:
            campo_busca = driver.switch_to.active_element

        campo_busca.click()
        try: campo_busca.clear()
        except: pass

        campo_busca.send_keys(CPF_ALVO)
        time.sleep(3)
        campo_busca.send_keys(Keys.RETURN)
        time.sleep(3) 

        def pegar_texto(id_elemento):
            try: return driver.find_element(By.ID, id_elemento).text
            except: return ""

        dados_base['nome_servidor'] = pegar_texto("txfNome")
        dados_base['cpf'] = pegar_texto("txfCpf")
        dados_base['matricula'] = pegar_texto("txfNumero")
        dados_base['data_nascimento'] = pegar_texto("txfDtnasc")
        dados_base['nome_pai'] = pegar_texto("txfPai")
        dados_base['nome_mae'] = pegar_texto("txfMae")
        dados_base['pis'] = pegar_texto("txfPispasep")
        dados_base['id'] = pegar_texto("txfNumrg")
        dados_base['ssp'] = pegar_texto("txfOrgaorg")
        dados_base['uf'] = pegar_texto("txfUfrg")

        if not dados_base['nome_servidor']:
            return []

        # =================================================================
        # ETAPA 2: VÍNCULOS (Página 156) - COM LÓGICA DE DATA FIM
        # =================================================================
        print(f"--- [ETAPA 2] Indo para página 156... ---")
        url_pag2 = "https://www26.senado.leg.br/senado/Ergon/Administracao/ERGadm00156.tp"
        driver.get(url_pag2)
        time.sleep(3)

        # 1. Digita para abrir a lista e contar
        try:
            campo_pag2 = driver.switch_to.active_element
            driver.execute_script("arguments[0].value = '';", campo_pag2)
            campo_pag2.send_keys(CPF_ALVO)
            print("Digitado para contagem. Aguardando lista (3s)...")
            time.sleep(2)
        except:
            return []

        # 2. Conta quantos itens tem na lista
        itens_lista = driver.find_elements(By.CLASS_NAME, "x-combo-list-item")
        qtd_vinculos = len(itens_lista)
        
        if qtd_vinculos == 0:
            qtd_vinculos = 1 

        print(f"--> Encontrados {qtd_vinculos} vínculo(s).")

        # 3. LOOP
        for i in range(qtd_vinculos):
            print(f"> Processando Vínculo {i+1} de {qtd_vinculos}...")
            
            if i > 0:
                driver.get(url_pag2)
                time.sleep(2)
            
            try:
                campo_pag2 = driver.switch_to.active_element
                driver.execute_script("arguments[0].value = '';", campo_pag2)
                time.sleep(0.5)
                campo_pag2.send_keys(CPF_ALVO)
                time.sleep(2) 
            except: pass

            if qtd_vinculos > 1 and i > 0:
                print(f"Descendo {i} vezes na lista...")
                for _ in range(i):
                    campo_pag2.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.3)
            
            campo_pag2.send_keys(Keys.RETURN)
            time.sleep(4) 

            # --- EXTRAÇÃO DESTE VÍNCULO ---
            dados_atual = dados_base.copy()
            
            # 1. DATA DE ADMISSÃO (Continua buscando no texto do cabeçalho por enquanto, ou se tiver ID pode trocar)
            try:
                elemento = driver.find_element(By.XPATH, "//div[@name='linha' and contains(text(), 'Tipo de Vínculo')]")
                texto = elemento.text
                if "Exercício:" in texto:
                    dados_atual['data_admissao'] = texto.split("Exercício:")[1].strip()[:10]
                else:
                    dados_atual['data_admissao'] = "-----"
            except:
                dados_atual['data_admissao'] = "-----"

            # 2. LÓGICA NOVA: DATA DE DESLIGAMENTO (ATIVO)
            # Procura pelo ID 'txfdtfim' que você encontrou
            try:
                elemento_fim = driver.find_element(By.ID, "txfdtfim")
                data_desligamento = elemento_fim.text.strip()
                
                if data_desligamento:
                    # Se tiver data, usa a data
                    dados_atual['ativo'] = data_desligamento
                else:
                    # Se estiver vazio, coloca "ATIVA"
                    dados_atual['ativo'] = "ATIVA"
            except:
                # Se der erro ou não achar o campo
                dados_atual['ativo'] = "ATIVA"

            dados_atual['portaria_nomeacao'] = "Informação não consta" 

            lista_final_dados.append(dados_atual)

        return lista_final_dados

    except Exception as e:
        print(f"ERRO: {e}")
        return []