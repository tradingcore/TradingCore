"""
Cliente para integração com Firebase Firestore.
"""
import json
import os
from datetime import datetime, timezone, timedelta
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from .config import FIREBASE_SERVICE_ACCOUNT, FIREBASE_SERVICE_ACCOUNT_JSON

# Timezone de São Paulo (UTC-3)
SP_TZ = timezone(timedelta(hours=-3))


def _init_firestore():
    if firebase_admin._apps:
        return firestore.client()

    if FIREBASE_SERVICE_ACCOUNT_JSON:
        info = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(info)
    else:
        if not FIREBASE_SERVICE_ACCOUNT:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT não configurado.")
        if not os.path.exists(FIREBASE_SERVICE_ACCOUNT):
            raise ValueError("Arquivo de service account não encontrado.")
        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)

    firebase_admin.initialize_app(cred)
    return firestore.client()


def carregar_usuarios_firestore():
    """
    Carrega dados dos usuários do Firestore e retorna um DataFrame
    com os mesmos nomes de colunas usados pelo pipeline atual.
    """
    try:
        db = _init_firestore()
        rows = []

        for doc in db.collection("users").stream():
            data = doc.to_dict() or {}
            tickers = data.get("tickers", [])

            if isinstance(tickers, list):
                tickers_str = ", ".join(
                    [str(t).strip().upper() for t in tickers if str(t).strip()]
                )
            else:
                tickers_str = str(tickers or "")

            rows.append(
                {
                    "Qual seu nome completo?": data.get("name", ""),
                    "Qual seu e-mail?": data.get("email", ""),
                    "Ticker 1": tickers_str,
                    "Telefone com WhatsApp": data.get("phone", ""),
                    "Endereco": data.get("address", ""),
                    "Data de nascimento": data.get("birthdate", ""),
                }
            )

        df = pd.DataFrame(rows)
        print(f"✓ Carregados {len(df)} usuários do Firestore")
        return df
    except Exception as e:
        print(f"✗ Erro ao carregar Firestore: {e}")
        return pd.DataFrame()


def salvar_noticias_usuario(uid, resumos, consolidadas, precos, periodo_noticias=None, analises=None, sentimento_medio=None):
    """
    Salva as notícias processadas para um usuário no Firestore.
    
    Args:
        uid: ID do usuário no Firestore
        resumos: Dict {ticker: resumo_executivo}
        consolidadas: Dict {ticker: {'positivo': str, 'negativo': str}}
        precos: Dict {ticker: {preco_fechamento, variacao_percentual, sucesso, ...}}
        periodo_noticias: Tuple (data_inicio, data_fim) do período das notícias
        analises: Lista de análises para identificar o destaque
        sentimento_medio: Dict {ticker: sentimento_medio} para histórico
    """
    try:
        db = _init_firestore()
        
        # Data de hoje no formato YYYY-MM-DD (timezone São Paulo)
        hoje = datetime.now(SP_TZ).strftime("%Y-%m-%d")
        
        # Referência para o documento de notícias do dia
        news_ref = db.collection("users").document(uid).collection("news").document(hoje)
        
        # Preparar dados para salvar
        dados = {
            "resumos": resumos or {},
            "consolidadas": consolidadas or {},
            "precos": precos or {},
            "timestamp": firestore.SERVER_TIMESTAMP,
            "data": hoje
        }
        
        # Adicionar período das notícias se disponível
        if periodo_noticias:
            dados["periodo_noticias"] = {
                "de": periodo_noticias[0],
                "ate": periodo_noticias[1]
            }
        
        # Identificar destaque do dia (notícia mais relevante)
        if analises:
            destaque = _identificar_destaque(analises)
            if destaque:
                dados["destaque"] = destaque
        
        # Salvar sentimento médio por ticker para histórico
        if sentimento_medio:
            dados["sentimento_historico"] = sentimento_medio
        
        # Salvar no Firestore
        news_ref.set(dados, merge=True)
        
        print(f"  ✓ Notícias salvas no Firestore para usuário {uid[:8]}...")
        return True
        
    except Exception as e:
        print(f"  ✗ Erro ao salvar notícias no Firestore: {e}")
        return False


def _identificar_destaque(analises):
    """
    Identifica a notícia mais relevante para ser o destaque do dia.
    
    Args:
        analises: Lista de análises com relevancia_score e sentimento
        
    Returns:
        Dict com dados do destaque ou None
    """
    if not analises:
        return None
    
    # Filtrar apenas análises relevantes
    relevantes = [a for a in analises if a.get('relevante', False)]
    
    if not relevantes:
        return None
    
    # Ordenar por relevância (maior primeiro)
    ordenadas = sorted(relevantes, key=lambda x: x.get('relevancia_score', 0), reverse=True)
    
    # Pegar a mais relevante
    top = ordenadas[0]
    
    return {
        "ticker": top.get('ticker', ''),
        "titulo": top.get('titulo', ''),
        "resumo": top.get('resumo', ''),
        "relevancia_score": top.get('relevancia_score', 0),
        "sentimento": top.get('sentimento', 0)
    }


def buscar_uid_por_email(email):
    """
    Busca o UID de um usuário pelo email.
    
    Args:
        email: Email do usuário
        
    Returns:
        UID do usuário ou None se não encontrado
    """
    try:
        db = _init_firestore()
        
        # Buscar usuário pelo email
        docs = db.collection("users").where("email", "==", email).limit(1).stream()
        
        for doc in docs:
            return doc.id
            
        return None
        
    except Exception as e:
        print(f"  ✗ Erro ao buscar UID por email: {e}")
        return None
