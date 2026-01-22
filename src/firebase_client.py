"""
Cliente para integração com Firebase Firestore.
"""
import json
import os
from datetime import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from .config import FIREBASE_SERVICE_ACCOUNT, FIREBASE_SERVICE_ACCOUNT_JSON


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


def salvar_noticias_usuario(uid, resumos, consolidadas, precos):
    """
    Salva as notícias processadas para um usuário no Firestore.
    
    Args:
        uid: ID do usuário no Firestore
        resumos: Dict {ticker: resumo_executivo}
        consolidadas: Dict {ticker: {'positivo': str, 'negativo': str}}
        precos: Dict {ticker: {preco_fechamento, variacao_percentual, sucesso}}
    """
    try:
        db = _init_firestore()
        
        # Data de hoje no formato YYYY-MM-DD
        hoje = datetime.now().strftime("%Y-%m-%d")
        
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
        
        # Salvar no Firestore
        news_ref.set(dados, merge=True)
        
        print(f"  ✓ Notícias salvas no Firestore para usuário {uid[:8]}...")
        return True
        
    except Exception as e:
        print(f"  ✗ Erro ao salvar notícias no Firestore: {e}")
        return False


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
