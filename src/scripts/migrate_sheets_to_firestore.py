import argparse
import pandas as pd
from firebase_admin import auth
from src.firebase_client import _init_firestore


def pick_column(df, candidates):
    for name in candidates:
        if name in df.columns:
            return name
    return None


def normalize_tickers(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [
        t.strip().upper()
        for t in str(value).split(",")
        if t and str(t).strip()
    ]


def safe_email_id(email):
    return email.replace("@", "_at_").replace(".", "_")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Caminho para CSV exportado do Sheets.")
    parser.add_argument(
        "--create-auth",
        action="store_true",
        help="Cria usuários no Firebase Auth e salva em users/{uid}.",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    name_col = pick_column(df, ["Qual seu nome completo?", "name", "Nome"])
    email_col = pick_column(df, ["Qual seu e-mail?", "email", "Email"])
    ticker_col = pick_column(df, ["Ticker", "Ticker 1", "Tickers"])
    phone_col = pick_column(df, ["Telefone com WhatsApp", "phone", "Telefone"])
    address_col = pick_column(df, ["Endereco", "Endereço", "address"])
    birthdate_col = pick_column(df, ["Data de nascimento", "birthdate", "Nascimento"])

    if not email_col:
        raise ValueError("Coluna de email não encontrada no CSV.")

    db = _init_firestore()
    migrated = 0

    for _, row in df.iterrows():
        email = str(row.get(email_col, "")).strip().lower()
        if not email:
            continue

        name = str(row.get(name_col, "")).strip() if name_col else ""
        tickers = normalize_tickers(row.get(ticker_col, "")) if ticker_col else []
        phone = str(row.get(phone_col, "")).strip() if phone_col else ""
        address = str(row.get(address_col, "")).strip() if address_col else ""
        birthdate = str(row.get(birthdate_col, "")).strip() if birthdate_col else ""

        payload = {
            "name": name,
            "email": email,
            "tickers": tickers,
            "phone": phone,
            "address": address,
            "birthdate": birthdate,
        }

        if args.create_auth:
            try:
                try:
                    user = auth.get_user_by_email(email)
                except auth.UserNotFoundError:
                    user = auth.create_user(email=email)

                db.collection("users").document(user.uid).set(payload, merge=True)
                link = auth.generate_password_reset_link(email)
                print(f"Reset link ({email}): {link}")
                migrated += 1
            except Exception as exc:
                print(f"Falha ao migrar {email}: {exc}")
        else:
            doc_id = safe_email_id(email)
            db.collection("users_by_email").document(doc_id).set(payload, merge=True)
            migrated += 1

    print(f"✓ Migração concluída: {migrated} registros.")


if __name__ == "__main__":
    main()
