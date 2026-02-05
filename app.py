from fastapi import FastAPI, UploadFile, Form
import pandas as pd
import hashlib

app = FastAPI()

DB = {
    "orders": {},
    "returns": {},
    "global": {}
}

def make_hash(name, pin, state):
    raw = str(name).strip() + str(pin).strip() + str(state).strip()
    return hashlib.sha256(raw.encode()).hexdigest()

@app.get("/")
def home():
    return {
        "title": "ReturnShield – Sellers Minimise Your Risk",
        "message": "Contribute your FK orders and returns to unlock risk insights."
    }

@app.post("/upload-orders")
def upload_orders(file: UploadFile):
    df = pd.read_csv(file.file, encoding="latin1")

    for _, r in df.iterrows():
        oid = str(r.get("Order Id"))
        DB["orders"][oid] = {
            "name": r.get("Buyer name"),
            "pin": r.get("PIN Code"),
            "state": r.get("State")
        }

    return {"status": "orders stored", "count": len(DB["orders"])}


@app.post("/upload-returns")
def upload_returns(file: UploadFile):
    df = pd.read_csv(file.file, encoding="latin1")

    for _, r in df.iterrows():
        oid = str(r.get("Order ID"))

        if oid in DB["orders"]:
            o = DB["orders"][oid]
            hid = make_hash(o["name"], o["pin"], o["state"])

            DB["global"][hid] = DB["global"].get(hid, 0) + 1

    return {"status": "returns processed", "customers": len(DB["global"])}


@app.post("/check-risk")
def check_risk(file: UploadFile):
    df = pd.read_csv(file.file, encoding="latin1")

    result = []

    for _, r in df.iterrows():
        oid = str(r.get("Order Id"))
        name = r.get("Buyer name")
        pin = r.get("PIN Code")
        state = r.get("State")

        hid = make_hash(name, pin, state)

        score = DB["global"].get(hid, 0) * 20

        risk = "LOW"
        action = "ALLOW COD"

        if score >= 40:
            risk = "HIGH"
            action = "Prepaid Only – Mandatory + Packing Video – Mandatory"

        result.append({
            "order": oid,
            "risk": risk,
            "message": "Suggested: High Risk Order" if risk=="HIGH" else "OK",
            "action": action
        })

    return result
