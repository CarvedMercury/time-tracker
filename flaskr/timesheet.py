from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import datetime
bp = Blueprint('timesheet', __name__)

def ensure_rows_for_day(user_id, date):
    db = get_db()
    cur = db.cursor()

    # Check if rows exist for the current day and user
    cur.execute("SELECT COUNT(*) FROM activity_fact WHERE author_id = ? AND date(start_time) = ?", (user_id, date))
    count = cur.fetchone()[0]

    # If rows don't exist, insert them
    if count == 0:
        for hour in range(24):
            start_time = f"{date} {hour}:00:00"
            end_time = f"{date} {hour}:59:59"
            cur.execute("INSERT INTO activity_fact (author_id, start_time, end_time, activity_id) VALUES (?, ?, ?, ?)",
                        (user_id, start_time, end_time, 1))
        db.commit()

@bp.route('/')
@login_required
def index():
    date =datetime.today().date()
    ensure_rows_for_day(g.user["id"],date )
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT start_time, end_time, activity_id FROM activity_fact WHERE author_id = ? AND date(start_time) = ? ORDER BY start_time",
                (g.user["id"], date))
    rows = cur.fetchall()

    return render_template('blog/index.html', rows=rows)

@bp.route('/update_activity', methods=['PUT'])
@login_required
def update_activity():
    selected_rows = request.values.getlist('row_ids')
    activity = request.values.get('activity')
    db = get_db()
    cur = db.cursor()
    for row_time in selected_rows:
        cur.execute("UPDATE activity_fact SET activity_id = ? WHERE author_id = ? AND start_time LIKE ?",
                    (activity, g.user["id"], f"{row_time}%"))

    db.commit()

    cur.execute("SELECT start_time, end_time, activity_id FROM activity_fact WHERE author_id = ? AND date(start_time) = ? ORDER BY start_time",
                (g.user["id"],datetime.strptime(row_time, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")))
    rows = cur.fetchall()

    return render_template('blog/rows.html', rows=rows)

@bp.route('/change_day', methods=['POST'])
@login_required
def change_day():

    selected_day = request.form.get("selected_date")
    print(selected_day)
    db = get_db()
    cur = db.cursor()
    ensure_rows_for_day(g.user["id"], selected_day)
    cur.execute("SELECT start_time, end_time, activity_id FROM activity_fact WHERE author_id = ? AND date(start_time) = ? ORDER BY start_time",
                (g.user["id"], selected_day))
    rows = cur.fetchall()

    return render_template('blog/rows.html', rows=rows)
