from docxtpl import DocxTemplate
from datetime import datetime
import os

def gerar_dtc(dados_recebidos):
    # 1. Defina o nome da pasta onde quer salvar
    pasta_destino = "Documentos_Gerados"

    print(f"Iniciando preenchimento para: {dados_recebidos.get('nome_servidor', 'Desconhecido')}")

    # Verifica se o modelo existe
    if not os.path.exists("modelo_dtc_template.docx"):
        print("ERRO CRÍTICO: O arquivo 'modelo_dtc_template.docx' não foi encontrado!")
        return

    try:
        # 2. Cria a pasta automaticamente se ela não existir
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
            print(f"Pasta '{pasta_destino}' criada com sucesso.")

        # Carregar o modelo
        doc = DocxTemplate("modelo_dtc_template.docx")

        # Adiciona a data de hoje
        dados_recebidos['data_hoje'] = datetime.now().strftime("%d/%m/%Y")

        # Renderizar o documento
        doc.render(dados_recebidos)

        # Definir nome do arquivo
        nome_servidor = dados_recebidos.get('nome_servidor', 'Servidor')
        matricula = dados_recebidos.get('matricula', '000000')
        
        # Limpa caracteres estranhos do nome para não dar erro no Windows
        nome_limpo = "".join([c for c in nome_servidor if c.isalnum() or c in (' ', '_')]).strip()
        nome_arquivo = f"DTC_{nome_limpo}_{matricula}.docx"

        # 3. O SEGREDO: Junta o nome da pasta com o nome do arquivo
        # Isso gera algo como: "Documentos_Gerados\DTC_Fulano_12345.docx"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo)

        # Salvar no caminho completo
        doc.save(caminho_completo)

        print(f"--> Documento SALVO na pasta '{pasta_destino}': {nome_arquivo}")
        
    except Exception as e:
        print(f"ERRO ao preencher/salvar o Word: {e}")