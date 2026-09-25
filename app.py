from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import re
from services.railway_provider import get_provider
from services.commercial_service import CommercialBookingService

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///smart_tatkal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    berth = db.Column(db.String(30), default="No Preference")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    source = db.Column(db.String(80), nullable=False)
    destination = db.Column(db.String(80), nullable=False)
    journey_date = db.Column(db.String(20), nullable=False)
    quota = db.Column(db.String(30), default="Tatkal")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PNR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    pnr = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(100), default="Demo status — connect an authorized PNR API")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


TRAINS = [
    {"number": "12555", "name": "Gorakhpur - Mumbai Express", "from": "Gorakhpur",
     "to": "Mumbai", "classes": {"SL": 14, "3A": 6, "2A": 2}, "duration": "28h 20m"},
    {"number": "12565", "name": "Bihar Sampark Kranti", "from": "Darbhanga",
     "to": "New Delhi", "classes": {"SL": 21, "3A": 8, "2A": 3}, "duration": "17h 45m"},
    {"number": "12423", "name": "Dibrugarh Rajdhani", "from": "Dibrugarh",
     "to": "New Delhi", "classes": {"3A": 5, "2A": 1}, "duration": "24h 10m"},
    {"number": "12309", "name": "Rajendra Nagar Rajdhani", "from": "Patna",
     "to": "New Delhi", "classes": {"3A": 7, "2A": 2}, "duration": "11h 35m"},
    {"number": "12176", "name": "Chambal Express", "from": "Gwalior",
     "to": "Prayagraj", "classes": {"SL": 19, "3A": 9}, "duration": "8h 30m"},
]


def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/")
def index():
    return render_template("index.html", trains=TRAINS)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 6:
            flash("Name, valid email and password of at least 6 characters are required.", "danger")
            return redirect(url_for("register"))

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash("Enter a valid email address.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "warning")
            return redirect(url_for("login"))

        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        flash("Account created successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    passengers = Passenger.query.filter_by(user_id=user.id).order_by(Passenger.created_at.desc()).all()
    searches = Search.query.filter_by(user_id=user.id).order_by(Search.created_at.desc()).limit(10).all()
    pnrs = PNR.query.filter_by(user_id=user.id).order_by(PNR.updated_at.desc()).all()
    return render_template("dashboard.html", passengers=passengers, searches=searches, pnrs=pnrs)


@app.route("/passengers/add", methods=["POST"])
def add_passenger():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    age = request.form.get("age", type=int)
    gender = request.form.get("gender", "Other")
    berth = request.form.get("berth", "No Preference")

    if not name or not age or age < 0 or age > 125:
        flash("Enter valid passenger details.", "danger")
        return redirect(url_for("dashboard"))

    db.session.add(Passenger(
        user_id=user.id, name=name, age=age, gender=gender, berth=berth
    ))
    db.session.commit()
    flash("Passenger saved.", "success")
    return redirect(url_for("dashboard"))


@app.route("/passengers/delete/<int:pid>", methods=["POST"])
def delete_passenger(pid):
    user = current_user()
    passenger = Passenger.query.filter_by(id=pid, user_id=user.id).first() if user else None
    if passenger:
        db.session.delete(passenger)
        db.session.commit()
    return redirect(url_for("dashboard"))


@app.route("/search", methods=["POST"])
def search():
    user = current_user()
    source = request.form.get("source", "").strip()
    destination = request.form.get("destination", "").strip()
    journey_date = request.form.get("journey_date", "").strip()

    if not source or not destination or not journey_date:
        flash("Enter source, destination and journey date.", "danger")
        return redirect(url_for("index"))

    if user:
        db.session.add(Search(
            user_id=user.id, source=source, destination=destination,
            journey_date=journey_date, quota="Tatkal"
        ))
        db.session.commit()

    source_l = source.lower()
    destination_l = destination.lower()
    try:
        provider = get_provider(TRAINS)
        payload = provider.search_trains(source, destination, journey_date, "Tatkal")
        matches = payload.get("trains", [])
        provider_name = payload.get("provider", "authorized")
        if not matches:
            matches = []
    except Exception as exc:
        flash(f"Railway API error: {exc}", "danger")
        matches = []
        provider_name = "error"

    return render_template(
        "results.html", trains=matches, source=source,
        destination=destination, journey_date=journey_date,
        provider_name=provider_name
    )


@app.route("/api/trains")
def api_trains():
    return jsonify(TRAINS)


@app.route("/pnr", methods=["POST"])
def add_pnr():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    pnr = request.form.get("pnr", "").strip()
    if not re.fullmatch(r"\d{10}", pnr):
        flash("PNR must contain exactly 10 digits.", "danger")
        return redirect(url_for("dashboard"))

    status = "Saved"
    try:
        provider = get_provider(TRAINS)
        data = provider.get_pnr_status(pnr)
        status = data.get("status", data.get("message", "Status received"))
    except Exception as exc:
        status = f"API not available: {exc}"

    db.session.add(PNR(user_id=user.id, pnr=pnr, status=status))
    db.session.commit()
    flash("PNR saved and checked through the configured provider.", "info")
    return redirect(url_for("dashboard"))


@app.route("/tatkal")
def tatkal():
    return render_template("tatkal.html")


@app.route("/commercial")
def commercial():
    return render_template("compliance.html")


@app.route("/booking-plan")
def booking_plan():
    if not current_user():
        return redirect(url_for("login"))
    passengers = Passenger.query.filter_by(user_id=current_user().id).all()
    return render_template("booking_plan.html", passengers=passengers)


@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
