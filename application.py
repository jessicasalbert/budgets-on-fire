import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, usd

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///budget.db")

#app.jinja_env.filters["usd"] = usd

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    else:
        user = request.form.get("username")
        password = request.form.get("password")
        if user == "" or password == "":
            return apology("Must enter username and password")
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")
        session["user_id"] = rows[0]["id"]
        return redirect("/")
        
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form.get("name")
        username = request.form.get("username")
        p1 = request.form.get("password")
        p2 = request.form.get("password2")
        if p1 != p2:
            return apology("Passwords don't match")
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if len(rows) == 1:
            return apology("Username taken")
        db.execute("INSERT INTO users (name, username, hash) VALUES (:name, :username, :pw)", name=name, username=username, pw=generate_password_hash(p1))
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        session["user_id"] = rows[0]["id"]
        return redirect("/")
        
@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
    
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    username = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])[0]["username"]
    name = db.execute("SELECT name FROM users WHERE id = :id", id = session["user_id"])[0]["name"]
    if request.method == "GET":
        return render_template("account.html", username=username, name=name)
    if request.method == "POST":
        if request.form.get("name") != "":
            db.execute("UPDATE users SET name=:name WHERE id=:id", name=request.form.get("name"), id=session["user_id"])
        if request.form.get("password") != "" and request.form.get("password") == request.form.get("password2"):
            db.execute("UPDATE users SET hash=:newpass WHERE id=:id", newpass=generate_password_hash(request.form.get("password")), id=session["user_id"])
    return redirect("/account")
    

@app.route("/money", methods=["GET", "POST"])
@login_required
def money():
    name = db.execute("SELECT name FROM users WHERE id = :id", id = session["user_id"])[0]["name"]
    balance = db.execute("SELECT balance FROM users WHERE id = :id", id = session["user_id"])[0]["balance"]
    date = f"{datetime.now().day}-{datetime.now().month}-{datetime.now().year}"
    categories = db.execute("SELECT DISTINCT category FROM transactions WHERE id=:id AND amount < 0", id=session["user_id"])
    data = db.execute("SELECT category, amount FROM transactions WHERE id=:id AND amount < 0", id=session["user_id"])
    counts = {}
    for x in categories:
        for y in data:
            if x["category"] == y["category"]:
                if x["category"] not in counts:
                    counts[x["category"]] = [-y["amount"]]
                else:
                    counts[x["category"]][0] = round(counts[x["category"]][0] - y["amount"], 2)
    totalExpense = 0
    for item in counts:
        totalExpense += counts[item][0]
    for item in counts:
        counts[item].append(round(100 * (counts[item][0] / totalExpense), 1))
    rows = db.execute("SELECT * FROM transactions WHERE id=:id", id=session["user_id"])
    if request.method == "GET":
        return render_template("money.html", name=name, date=date, balance=usd(balance), rows=rows, counts=counts)
        
@app.route("/transact", methods=["GET", "POST"])
@login_required
def transact():
    categories = db.execute("SELECT DISTINCT category FROM transactions WHERE id=:id", id=session["user_id"])
    if request.method == "GET":
        return render_template("transact.html", categories=categories)
    else:
        transact = request.form.get("type")
        amount = float(request.form.get("amount"))
        category = request.form.get("category")
        item = request.form.get("item")
        priorBalance = db.execute("SELECT balance FROM users WHERE id=:id", id=session["user_id"])[0]["balance"]
        if transact == "expense":
            amount = -amount
        newBalance = priorBalance + amount
        db.execute("INSERT INTO transactions (id, amount, item, category, time) VALUES (:id, :amount, :item, :category, :time)", id=session["user_id"], amount=amount, item=item, category=category, time=datetime.now())
        db.execute("UPDATE users SET balance=:balance WHERE id=:id", balance=newBalance, id=session["user_id"])
        return redirect("/money")
        
@app.route("/faq")
@login_required
def faq():
    return render_template("faq.html")