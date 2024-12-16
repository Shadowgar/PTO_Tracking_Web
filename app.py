from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import calendar
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pto_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class WorkSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Integer, nullable=False)
    hours_worked = db.Column(db.Float, nullable=False)
    pto_used = db.Column(db.Float, nullable=False)

class PTOData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_accrued = db.Column(db.Float, nullable=False)
    accrual_rate = db.Column(db.Float, nullable=False)
    last_update_date = db.Column(db.String, nullable=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Handle form submission for PTO data
        pto_data = PTOData.query.first()
        if not pto_data:
            pto_data = PTOData(current_accrued=0, accrual_rate=0, last_update_date="")
            db.session.add(pto_data)
        
        pto_data.current_accrued = float(request.form.get("current_accrued", 0))
        pto_data.accrual_rate = float(request.form.get("accrual_rate", 0))
        pto_data.last_update_date = request.form.get("last_update_date") or "1970-01-01"

        # Save the daily schedule data
        month = int(request.form.get("month"))
        year = int(request.form.get("year"))
        days_data = request.form.getlist("day_data[]")

        # Clear existing data for the month
        WorkSchedule.query.filter_by(year=year, month=month).delete()

        # Process the days data and save to work_schedule
        for day_data in days_data:
            day_info = day_data.split(",")  # expecting 'date, hours_worked, pto_used'
            date = int(day_info[0])
            hours_worked = float(day_info[1])
            pto_used = float(day_info[2])

            work_schedule = WorkSchedule(year=year, month=month, date=date, hours_worked=hours_worked, pto_used=pto_used)
            db.session.add(work_schedule)

        db.session.commit()
        return redirect(url_for("index", year=year, month=month))

    current_year = int(request.args.get('year', datetime.datetime.now().year))
    current_month = int(request.args.get('month', datetime.datetime.now().month))

    # Set the first weekday to Monday
    calendar.setfirstweekday(calendar.MONDAY)

    # Get the calendar for the selected month
    month_calendar = calendar.monthcalendar(current_year, current_month)

    # Retrieve saved work schedule for the month
    saved_schedule = WorkSchedule.query.filter_by(year=current_year, month=current_month).all()

    # Retrieve PTO data
    pto_data = PTOData.query.first()
    if not pto_data:
        pto_data = PTOData(current_accrued=0, accrual_rate=0, last_update_date="")

    # Calculate PTO balance
    pto_balance = calculate_pto_balance(current_year, current_month)

    return render_template(
        "index.html",
        current_year=current_year,
        current_month=current_month,
        work_schedule=saved_schedule,
        pto_data=pto_data,
        calendar=calendar,
        month_calendar=month_calendar,
        pto_balance=pto_balance
    )

def calculate_pto_balance(year, month):
    total_pto_used = 0
    total_hours_worked = 0

    work_schedule = WorkSchedule.query.all()
    for day in work_schedule:
        total_hours_worked += day.hours_worked
        total_pto_used += day.pto_used

    pto_data = PTOData.query.first()
    if not pto_data:
        return 0

    # Calculate accrued PTO
    accrued_pto = total_hours_worked * pto_data.accrual_rate
    pto_balance = pto_data.current_accrued + accrued_pto - total_pto_used

    return pto_balance

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)