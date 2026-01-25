"""
Script para baixar os releases de resultados mais recentes de cada empresa da CVM.
Lê uma planilha Excel com os dados e baixa apenas o documento mais recente por empresa.

Uso: python src/scripts/download_releases_cvm.py
"""
import os
import re
import time
import urllib3
import pandas as pd
import requests
from pathlib import Path

# Desabilitar warnings de SSL (comum no site da CVM)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurações
PLANILHA_PATH = Path(__file__).parent.parent.parent / "Planilha sem título (1).xlsx"
PASTA_DESTINO = Path(__file__).parent.parent.parent / "docs" / "releases"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 60  # segundos
MAX_RETRIES = 3
DELAY_ENTRE_DOWNLOADS = 1  # segundos (evitar sobrecarga no servidor)


def carregar_planilha(caminho):
    """Carrega a planilha Excel e retorna um DataFrame."""
    print(f"📂 Carregando planilha: {caminho}")
    df = pd.read_excel(caminho)
    print(f"   {len(df)} documentos encontrados")
    return df


def filtrar_mais_recente_por_empresa(df):
    """
    Para cada empresa (Codigo_CVM), retorna apenas a linha 
    com a Data_Referencia mais recente.
    """
    print("🔍 Filtrando documento mais recente por empresa...")
    
    # Garantir que Data_Referencia é datetime
    df['Data_Referencia'] = pd.to_datetime(df['Data_Referencia'])
    
    # Ordenar por Data_Referencia decrescente
    df_sorted = df.sort_values('Data_Referencia', ascending=False)
    
    # Pegar apenas o primeiro (mais recente) de cada Codigo_CVM
    df_recentes = df_sorted.drop_duplicates(subset=['Codigo_CVM'], keep='first')
    
    print(f"   {len(df_recentes)} empresas únicas")
    return df_recentes


def sanitizar_nome(nome):
    """
    Remove caracteres especiais do nome para usar em nome de arquivo.
    """
    # Remover caracteres especiais
    nome_limpo = re.sub(r'[^\w\s-]', '', nome)
    # Substituir espaços por underscore
    nome_limpo = re.sub(r'\s+', '_', nome_limpo)
    # Limitar tamanho (evitar nomes muito longos)
    nome_limpo = nome_limpo[:50]
    # Remover underscores duplicados
    nome_limpo = re.sub(r'_+', '_', nome_limpo)
    # Remover underscore no final
    nome_limpo = nome_limpo.rstrip('_')
    return nome_limpo


def gerar_nome_arquivo(row):
    """
    Gera o nome do arquivo no formato:
    {Codigo_CVM}_{Data_Referencia}_{Nome_Companhia}.pdf
    """
    codigo_cvm = str(row['Codigo_CVM'])
    data_ref = row['Data_Referencia'].strftime('%Y-%m-%d')
    nome_empresa = sanitizar_nome(row['Nome_Companhia'])
    
    return f"{codigo_cvm}_{data_ref}_{nome_empresa}.pdf"


def baixar_pdf(url, caminho_destino, retries=MAX_RETRIES):
    """
    Baixa o PDF do URL e salva no caminho especificado.
    Retorna True se sucesso, False se falhou.
    """
    # Verificar se já existe
    if os.path.exists(caminho_destino):
        return True  # Já baixado
    
    headers = {"User-Agent": USER_AGENT}
    
    for tentativa in range(retries):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=TIMEOUT, 
                verify=False,  # SSL do site da CVM pode dar problema
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Salvar arquivo
            with open(caminho_destino, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except requests.exceptions.Timeout:
            print(f"      ⏱️ Timeout (tentativa {tentativa + 1}/{retries})")
        except requests.exceptions.RequestException as e:
            print(f"      ❌ Erro: {e} (tentativa {tentativa + 1}/{retries})")
        
        if tentativa < retries - 1:
            time.sleep(2)  # Esperar antes de retry
    
    return False


def main(limite=None):
    """
    Função principal.
    
    Args:
        limite: Se especificado, baixa apenas esse número de arquivos (para teste)
    """
    # Criar pasta de destino
    PASTA_DESTINO.mkdir(parents=True, exist_ok=True)
    
    # Carregar dados
    df = carregar_planilha(PLANILHA_PATH)
    
    # Filtrar mais recente por empresa
    df_recentes = filtrar_mais_recente_por_empresa(df)
    
    # Aplicar limite se especificado
    if limite:
        df_recentes = df_recentes.head(limite)
        print(f"🧪 Modo teste: baixando apenas {limite} arquivos")
    
    # Download dos arquivos
    print(f"\n📥 Iniciando download de {len(df_recentes)} arquivos...")
    print(f"   Destino: {PASTA_DESTINO}")
    print()
    
    sucesso = 0
    falha = 0
    ja_existente = 0
    
    for idx, (_, row) in enumerate(df_recentes.iterrows(), 1):
        nome_arquivo = gerar_nome_arquivo(row)
        caminho_completo = PASTA_DESTINO / nome_arquivo
        
        # Verificar se já existe
        if caminho_completo.exists():
            ja_existente += 1
            print(f"[{idx}/{len(df_recentes)}] ⏩ {nome_arquivo} (já existe)")
            continue
        
        print(f"[{idx}/{len(df_recentes)}] ⬇️ {nome_arquivo}...", end=" ", flush=True)
        
        if baixar_pdf(row['Link_Download'], caminho_completo):
            sucesso += 1
            print("✅")
        else:
            falha += 1
            print("❌")
        
        # Delay entre downloads (evitar sobrecarga)
        if idx < len(df_recentes):
            time.sleep(DELAY_ENTRE_DOWNLOADS)
    
    # Resumo final
    print()
    print("=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    print(f"   ✅ Baixados com sucesso: {sucesso}")
    print(f"   ⏩ Já existentes: {ja_existente}")
    print(f"   ❌ Falhas: {falha}")
    print(f"   📁 Total na pasta: {sucesso + ja_existente}")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    # Verificar se tem argumento de limite (para teste)
    limite = None
    if len(sys.argv) > 1:
        try:
            limite = int(sys.argv[1])
            print(f"🧪 Modo teste ativado: limite de {limite} arquivos")
        except ValueError:
            pass
    
    main(limite=limite)
