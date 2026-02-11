from docxtpl import DocxTemplate
from datetime import datetime
import os
import locale

# Tenta configurar o sistema para Português
try: 
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except: 
    pass

def gerar_dtc(dados_recebidos):
    pasta_destino = "Documentos_Gerados"
    modelo_docx = "modelo_dtc_template.docx"

    # --- LÓGICA HÍBRIDA (Aceita Lista ou Dicionário) ---
    if isinstance(dados_recebidos, list):
        if not dados_recebidos:
            print("❌ Lista vazia.")
            return
        # Se for lista, pega os dados pessoais do primeiro vínculo
        dados_final = dados_recebidos[0].copy()
        lista_para_tabela = dados_recebidos
    else:
        # Se for dicionário (legado), transforma em lista
        dados_final = dados_recebidos.copy()
        lista_para_tabela = [dados_recebidos]

    print(f"Iniciando doc para: {dados_final.get('nome_servidor')}")

    # --- MONTA A LISTA PARA A TABELA DO WORD ---
    tabela_word = []
    for i, item in enumerate(lista_para_tabela):
        linha = {
            'seq': i + 1,
            'data_admissao': item.get('data_admissao', '-----'),
            # Aqui 'ativo' recebe a Data de Desligamento ou "ATIVA" vindo do extrator
            'ativo': item.get('ativo', '-----'),
            'portaria_nomeacao': item.get('portaria_nomeacao', '-----')
        }
        tabela_word.append(linha)
    
    # Adiciona a lista formatada ao contexto principal
    dados_final['lista_tabela'] = tabela_word
    
    # --- DATAS ---
    # 1. Data curta (ex: 29/01/2025)
    dados_final['data_hoje'] = datetime.now().strftime("%d/%m/%Y")
    
    # 2. Data por extenso (ex: Brasília/DF, 29 de Janeiro de 2025.)
    try:
        hj = datetime.now()
        meses = {
            1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 
            7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'
        }
        dados_final['data_extenso'] = f"Brasília/DF, {hj.day} de {meses[hj.month]} de {hj.year}."
    except: 
        # Fallback simples caso dê erro no dicionário de meses
        dados_final['data_extenso'] = datetime.now().strftime("Brasília/DF, %d de %B de %Y.")

    # --- VERIFICAÇÕES E SALVAMENTO ---
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    if not os.path.exists(modelo_docx):
        print(f"❌ MODELO NÃO ENCONTRADO: {modelo_docx}")
        return

    try:
        doc = DocxTemplate(modelo_docx)
        doc.render(dados_final)
        
        nome = dados_final.get('nome_servidor', 'Servidor')
        mat = dados_final.get('matricula', '0000')
        nome_limpo = "".join([c for c in nome if c.isalnum() or c in (' ', '_')]).strip()
        
        caminho = os.path.join(pasta_destino, f"DTC_Completa_{nome_limpo}_{mat}.docx")
        
        doc.save(caminho)
        print(f"✅ Arquivo salvo: {caminho}")
        
    except Exception as e:
        print(f"ERRO Word: {e}")

# ==============================================================================
# NOVA FUNÇÃO: DECLARAÇÃO FUNCIONAL
# ==============================================================================
def gerar_declaracao_funcional(dados_recebidos):
    pasta_destino = "Documentos_Gerados"
    modelo_docx = "modelo_declaracao_funcional.docx"

    # Tratamento de lista (igual ao da DTC)
    if isinstance(dados_recebidos, list):
        if not dados_recebidos:
            return
        dados_base = dados_recebidos[0] # Pega os dados do primeiro vínculo
    else:
        dados_base = dados_recebidos

    print(f"Gerando Declaração Funcional para: {dados_base.get('nome_servidor')}")

    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    if not os.path.exists(modelo_docx):
        print(f"❌ MODELO NOVO NÃO ENCONTRADO: {modelo_docx}")
        return

    try:
        # Como as variáveis do seu arquivo novo ({{nome_servidor}}, {{cpf}}, etc)
        # são iguais às do extrator, podemos passar 'dados_base' direto.
        doc = DocxTemplate(modelo_docx)
        doc.render(dados_base)
        
        nome = dados_base.get('nome_servidor', 'Servidor')
        nome_limpo = "".join([c for c in nome if c.isalnum() or c in (' ', '_')]).strip()
        
        caminho = os.path.join(pasta_destino, f"Declaracao_Funcional_{nome_limpo}.docx")
        
        doc.save(caminho)
        print(f"✅ Declaração Funcional salva: {caminho}")
        
    except Exception as e:
        print(f"ERRO Word Funcional: {e}")