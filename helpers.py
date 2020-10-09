import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message):
    """Render message as an apology to user."""
    return render_template("apology.html", error=message)
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
    
    
def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"