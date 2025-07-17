import requests
import time
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GATE_API_KEY")
API_SECRET = os.getenv("GATE_API_SECRET")

def sign_request(method, url, query='', body=''):
    t = str(int(time.time()))
    payload = f"{t}\n{method.upper()}\n{url}\n{query}\n{body}"
    sign = hmac.new(API_SECRET.encode(), payload.encode(), hashlib.sha512).hexdigest()
    return t, sign

def get_ledger_entries(limit=50):
    path = "/api/v4/wallet/ledger"
    query = f"limit={limit}"
    t, signature = sign_request("GET", path, query)
    headers = {
        "KEY": API_KEY,
        "Timestamp": t,
        "SIGN": signature
    }
    r = requests.get(f"https://api.gate.io{path}?{query}", headers=headers)
    r.raise_for_status()
    return r.json()

def get_total_balance():
    path = "/api/v4/wallet/total_balance"
    t, signature = sign_request("GET", path)
    headers = {
        "KEY": API_KEY,
        "Timestamp": t,
        "SIGN": signature
    }
    r = requests.get(f"https://api.gate.io{path}", headers=headers)
    r.raise_for_status()
    data = r.json().get("assets", {})
    return {k: float(v) for k, v in data.items() if float(v) > 0}
