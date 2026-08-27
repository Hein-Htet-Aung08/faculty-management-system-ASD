import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
DB_FILE = os.path.join(DATA_DIR, "student4.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def row_to_dict(row):
    return dict(row) if row else None

#all crud operations below:
#ResearchProjects CRUD
@app.route('/projects', methods=['GET'])
def get_projects():
    department = request.args.get('department')
    status = request.args.get('status')

    query = "SELECT * FROM ResearchProjects WHERE 1=1"
    params = []

    if department:
        query += " AND department = ?"
        params.append(department)
    if status:
        query += " AND status = ?"
        params.append(status)
    
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([row_to_dict(row) for row in rows]), 200~
#Grant CRUD

# Publications CRUD

# ProjectStaff CRUD

# GrantAlerts CRUD

#ResearchAIAnalysis CRUD