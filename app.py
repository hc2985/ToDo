from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from supabase import create_client, Client
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key")  # Required for sessions
supabaseUrl = os.environ.get("SUPABASE_URL")
supabaseKey = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabaseUrl, supabaseKey)

@app.route("/")
def landing():
    #Landing page route
    return render_template("landing.html")

@app.route("/home")
def index():
    #show to-dos from the database + basic functionalities
    user = session.get('user_id', None)
    print(f"Session contents: {dict(session)}")  # Add this line
    print(f"User value: {user}")  # Add this line
    if not user:
        return redirect(url_for("landing"))

    todo_list = supabase.table("todos").select("*").eq("user_id", user).order("id").execute()
    return render_template("home.html", todo_list=todo_list.data)

@app.route("/add", methods=["POST"])
def add():
    #add new to-do to the database
    user = session.get('user_id', None)
    if not user:
        return redirect(url_for("landing"))
    
    title = request.form.get("title")
    supabase.table("todos").insert({"title": title, "complete": False, "user_id": user}).execute()
    return redirect(url_for("index"))

@app.route("/update/<int:todo_id>")
def update(todo_id):
    #update to-do in the database

    user = session.get('user_id', None)
    if not user:
        return redirect(url_for("landing"))

    supabase.rpc('completion_toggle', {'todo_id': todo_id, "u_id": user}).execute()
    return redirect(url_for("index"))

@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    #delete to-do from the database
    
    supabase.table("todos").delete().eq("id", todo_id).execute()
    return redirect(url_for("index"))

@app.route("/auth", methods=["POST"])
def auth():
    action = request.form.get("action")
    if action == "login":
        return login()
    if action == "signup":
        return signup()

@app.route("/login", methods=["POST"])
def login():
    #handle user login with email/password through supabase
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })

        session['user_id'] = response.user.id
        session['user_email'] = response.user.email

        return redirect(url_for("index"))

    except Exception as e:
        print(f"Error logging in: {e}")
        return render_template("landing.html", error="Invalid credentials")

@app.route("/signup")
def signup():
    #handle user login with email/password through supabase
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        response = supabase.auth.sign_up({
            'email': email,
            'password': password,
        })

        session['user_id'] = response.user.id
        session['user_email'] = response.user.email

        return redirect(url_for("landing"))
    
    except Exception as e:
        print(f"Error signing up: {e}")
    return render_template("landing.html", error="Invalid credentials")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    supabase.auth.sign_out()
    return redirect(url_for("landing"))

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
