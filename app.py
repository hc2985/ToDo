import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from supabase import create_client
import uvicorn

load_dotenv()

# App and API
app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SECRET_KEY", "fallback-secret-key")
)

templates = Jinja2Templates(directory="templates")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_user_id(request: Request):
    return request.session.get("user_id")


@app.get("/")
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/home")
def index(request: Request):
    user = get_user_id(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    todo_list = (
        supabase.table("todos")
        .select("*")
        .eq("user_id", user)
        .order("id")
        .execute()
    )

    return templates.TemplateResponse(
        "home.html", {"request": request, "todo_list": todo_list.data}
    )


@app.post("/add")
def add(request: Request, title: str = Form(...)):
    user = get_user_id(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    supabase.table("todos").insert(
        {"title": title, "complete": False, "user_id": user}
    ).execute()
    return RedirectResponse(url="/home", status_code=303)


@app.get("/update/{todo_id}")
def update(request: Request, todo_id: int):
    user = get_user_id(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    supabase.rpc("completion_toggle", {"todo_id": todo_id, "u_id": user}).execute()
    return RedirectResponse(url="/home", status_code=303)


@app.get("/delete/{todo_id}")
def delete(request: Request, todo_id: int):
    user = get_user_id(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    supabase.table("todos").delete().eq("id", todo_id).execute()
    return RedirectResponse(url="/home", status_code=303)


@app.post("/auth")
def auth(request: Request, action: str = Form(...), email: str = Form(""), password: str = Form("")):
    #use same form for sign up or log in
    if action == "login":
        return login(request=request, email=email, password=password)
    if action == "signup":
        return signup(request=request, email=email, password=password)
    return RedirectResponse(url="/", status_code=303)


@app.post("/login")
def login(
    request: Request = None,
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        request.session["user_id"] = response.user.id
        request.session["user_email"] = response.user.email
        return RedirectResponse(url="/home", status_code=303)
    except Exception as e:
        print(f"Error logging in: {e}")
        return templates.TemplateResponse(
            "landing.html",
            {"request": request, "error": "Incorrect Email/Password", "type": "login"},
            status_code=400,
        )


@app.post("/signup")
def signup(
    request: Request = None,
    email: str = Form(...),
    password: str = Form(...),
):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.session:
            return RedirectResponse(url="/", status_code=303)
        else:
            print("Existing Account: No session returned")
            return templates.TemplateResponse(
                "landing.html",
                {"request": request, "error": "Email already exists", "type": "existing"},
            )
    except Exception as e:
        print(f"Error signing up: {e}")
        return templates.TemplateResponse(
            "landing.html",
            {"request": request, "error": "Invalid Password/Email", "type": "signup"},
            status_code=400,
        )


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    try:
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Error signing out: {e}")
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
