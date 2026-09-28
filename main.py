from fastapi import FastAPI, Request, Form, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import User, History
from .auth import hash_password, verify_password
from .gemini_utils import *
from PIL import Image
import io

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PocketSmart AI")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

current_user_store = {"user": None}

@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"user": current_user_store["user"]})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Invalid credentials"})
    current_user_store["user"] = user
    return RedirectResponse("/", status_code=302)

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={})

@app.post("/register")
def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "User already exists"})
    new_user = User(username=username, email=email, hashed_password=hash_password(password))
    db.add(new_user); db.commit()
    return RedirectResponse("/login", status_code=302)

@app.get("/logout")
def logout():
    current_user_store["user"] = None
    return RedirectResponse("/login", status_code=302)

@app.get("/home-planner")
def home_planner(request: Request):
    return templates.TemplateResponse(request=request, name="home_planner.html", context={})

@app.get("/party-planner")
def party_planner(request: Request):
    return templates.TemplateResponse(request=request, name="party_planner.html", context={})

@app.get("/jewelry-planner")
def jewelry_planner(request: Request):
    return templates.TemplateResponse(request=request, name="jewelry_planner.html", context={})

@app.post("/generate-home")
async def gen_home(request: Request, budget: int = Form(...), room_type: str = Form(...), style: str = Form(...), db: Session = Depends(get_db)):
    result = get_home_recommendations(budget, room_type, style)
    if current_user_store["user"]:
        h = History(user_id=current_user_store["user"].id, category="home", budget=budget, query=f"{room_type} {style}", result=result)
        db.add(h); db.commit()
    return templates.TemplateResponse(request=request, name="home_planner.html", context={"result": result, "budget": budget})

@app.post("/generate-party")
async def gen_party(request: Request, budget: int = Form(...), event_type: str = Form(...), guests: int = Form(...), db: Session = Depends(get_db)):
    result = get_party_recommendations(budget, event_type, guests)
    if current_user_store["user"]:
        h = History(user_id=current_user_store["user"].id, category="party", budget=budget, query=f"{event_type} {guests}", result=result)
        db.add(h); db.commit()
    return templates.TemplateResponse(request=request, name="party_planner.html", context={"result": result})

@app.post("/generate-jewelry")
async def gen_jewelry(request: Request, budget: int = Form(...), occasion: str = Form(...), outfit: str = Form(...), image: UploadFile = File(None), db: Session = Depends(get_db)):
    pil_image = None
    if image and image.filename:
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents))
    result = get_jewelry_recommendations(budget, occasion, outfit, pil_image)
    if current_user_store["user"]:
        h = History(user_id=current_user_store["user"].id, category="jewelry", budget=budget, query=f"{occasion} {outfit}", result=result)
        db.add(h); db.commit()
    return templates.TemplateResponse(request=request, name="jewelry_planner.html", context={"result": result})

@app.get("/history")
def history_page(request: Request, db: Session = Depends(get_db)):
    if not current_user_store["user"]:
        return RedirectResponse("/login", status_code=302)
    histories = db.query(History).filter(History.user_id == current_user_store["user"].id).order_by(History.id.desc()).all()
    return templates.TemplateResponse(request=request, name="history.html", context={"histories": histories})

@app.get("/health")
def health():
    return {"status": "ok"}