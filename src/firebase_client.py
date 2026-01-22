"""
Cliente para integração com Firebase Firestore.
"""
import json
import os
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
