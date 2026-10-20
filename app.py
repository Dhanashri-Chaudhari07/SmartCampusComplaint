
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "smart-campus-demo-key"

def get_db_connection():
    conn = sqlite3.connect("complaints.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            department TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()

create_table()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/complaint", methods=["GET", "POST"])
def complaint():
    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()
        department = request.form.get("department", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()

        if not all([student_name, department, category, description]):
            return "Please fill all fields.", 400

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO complaints
            (student_name, department, category, description)
            VALUES (?, ?, ?, ?)
        """, (student_name, department, category, description))
        conn.commit()
        complaint_id = conn.execute(
            "SELECT last_insert_rowid()"
            ).fetchone()[0]
        conn.close()
        return render_template(
            "success.html",
            complaint_id=complaint_id
        )

    return render_template("complaint.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid username or password!"

    return render_template("admin_login.html", error=error)



@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()

    complaints = conn.execute(
        "SELECT * FROM complaints ORDER BY id DESC"
    ).fetchall()

    total_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    pending_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Pending'"
    ).fetchone()[0]

    in_progress_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'"
    ).fetchone()[0]

    resolved_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        complaints=complaints,
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        in_progress_complaints=in_progress_complaints,
        resolved_complaints=resolved_complaints
    )



@app.route("/update-status/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    status = request.form.get("status", "")
    allowed_statuses = ["Pending", "In Progress", "Resolved"]

    if status not in allowed_statuses:
        return "Invalid status", 400

    conn = get_db_connection()
    conn.execute(
        "UPDATE complaints SET status = ? WHERE id = ?",
        (status, complaint_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))



@app.route("/success")
def success():
    conn = get_db_connection()
    complaint = conn.execute(
        "SELECT id FROM complaints ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    complaint_id = complaint["id"] if complaint else None

    return render_template(
        "success.html",
        complaint_id=complaint_id
    )


@app.route("/track", methods=["GET", "POST"])
def track_complaint():
    complaint = None
    error = ""

    if request.method == "POST":
        complaint_id = request.form.get("complaint_id", "").strip()

        if complaint_id.isdigit():
            conn = get_db_connection()
            complaint = conn.execute(
                "SELECT id, category, description, status "
                "FROM complaints WHERE id = ?",
                (int(complaint_id),)
            ).fetchone()
            conn.close()

        if complaint is None:
            error = "Complaint not found. Please check your ID."

    return render_template(
        "track.html",
        complaint=complaint,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)
