from fastapi import FastAPI, UploadFile, Form
from database import get_db, init_db
from auth import hash_pw, verify, reset_token, send_reset
import pandas as pd, hashlib

from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

templates = Jinja2Templates(directory="templates")


app = FastAPI()
init_db()

def make_hash(name, pin, state):
    raw = str(name)+str(pin)+str(state)
    return hashlib.sha256(raw.encode()).hexdigest()

@app.get("/")
def home():
    return {
        "title": "ReturnShield – Sellers Minimise Your Risk",
        "message": "Contribute your FK orders and returns to unlock risk insights."
    }

@app.post("/register")
def register(email: str = Form(), password: str = Form(), state: str = Form()):
    db = get_db()
    db.execute("INSERT INTO sellers(email,password,state) VALUES(?,?,?)",
               (email, hash_pw(password), state))
    db.commit()
    return {"status": "registered"}

@app.post("/upload-orders")
def upload_orders(file: UploadFile, seller_id: int = Form()):
    df = pd.read_csv(file.file, encoding="latin1")
    db = get_db()

    for _, r in df.iterrows():
        db.execute("""INSERT INTO orders VALUES(?,?,?,?,?)""",
                   (seller_id, r.get("Order Id"),
                    r.get("Buyer name"),
                    r.get("PIN Code"),
                    r.get("State")))
    db.commit()
    return {"status": "orders stored"}

@app.post("/upload-returns")
def upload_returns(file: UploadFile, seller_id: int = Form()):
    df = pd.read_csv(file.file, encoding="latin1")
    db = get_db()

    for _, r in df.iterrows():
        oid = r.get("Order ID")
        db.execute("INSERT INTO returns VALUES(?,?)",(seller_id, oid))

        # contribute to global network
        o = db.execute("SELECT name,pin,state FROM orders WHERE order_id=?",
                       (oid,)).fetchone()
        if o:
            h = make_hash(o["name"],o["pin"],o["state"])
            db.execute("INSERT INTO global_hash VALUES(?,1)",(h,))

    db.commit()
    return {"status": "returns processed"}

@app.post("/check-risk")
def check_risk(file: UploadFile):
    df = pd.read_csv(file.file, encoding="latin1")
    db = get_db()

    result = []
    for _, r in df.iterrows():
        h = make_hash(r.get("Buyer name"),
                      r.get("PIN Code"),
                      r.get("State"))

        score = len(db.execute(
            "SELECT * FROM global_hash WHERE hash=?",(h,)).fetchall()) * 20

        if score >= 40:
            result.append({
                "order": r.get("Order Id"),
                "risk": "HIGH",
                "message": "Suggested: High Risk Order",
                "action": "Prepaid Only – Mandatory + Packing Video – Mandatory"
            })
        else:
            result.append({
                "order": r.get("Order Id"),
                "risk": "LOW",
                "message": "OK",
                "action": "ALLOW COD"
            })

    return result

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard/{seller}")
def dash(request: Request, seller:int):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "seller": seller}
    )

@app.post("/web/check")
async def web_check(request: Request, file: UploadFile):
    r = await check_risk(file)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "result": r, "seller": 1}
    )

