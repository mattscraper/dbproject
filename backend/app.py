"""Flask API for the Study Group app.

Run:
    pip install -r requirements.txt
    python seed.py      # create and seed database.db
    python app.py       # start API on http://localhost:5001
"""

import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

from models import db, User, Group, StudyPreference, Post

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)
db.init_app(app)


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "name, email, password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 400

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify(user.to_dict())


# ---------------------------------------------------------------------------
# GROUPS
# ---------------------------------------------------------------------------

@app.route("/api/groups", methods=["GET"])
def list_groups():
    groups = Group.query.all()
    return jsonify([g.to_dict() for g in groups])


@app.route("/api/groups", methods=["POST"])
def create_group():
    data = request.get_json() or {}
    name = data.get("name")
    description = data.get("description", "")
    if not name:
        return jsonify({"error": "name required"}), 400

    group = Group(name=name, description=description)
    db.session.add(group)
    db.session.commit()
    return jsonify(group.to_dict()), 201


@app.route("/api/groups/<int:group_id>/join", methods=["POST"])
def join_group(group_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    user = User.query.get(user_id)
    group = Group.query.get(group_id)
    if not user or not group:
        return jsonify({"error": "user or group not found"}), 404

    if group not in user.groups:
        user.groups.append(group)
        db.session.commit()

    return jsonify({"message": f"{user.name} joined {group.name}"})


# ---------------------------------------------------------------------------
# POSTS
# ---------------------------------------------------------------------------

@app.route("/api/posts", methods=["GET"])
def list_posts():
    group_id = request.args.get("group_id", type=int)
    query = Post.query
    if group_id is not None:
        query = query.filter_by(group_id=group_id)
    posts = query.order_by(Post.created_at.desc()).all()
    return jsonify([p.to_dict() for p in posts])


@app.route("/api/posts", methods=["POST"])
def create_post():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    group_id = data.get("group_id")
    content = data.get("content")
    if not user_id or not group_id or not content:
        return jsonify({"error": "user_id, group_id, content required"}), 400

    post = Post(user_id=user_id, group_id=group_id, content=content)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201


# ---------------------------------------------------------------------------
# PREFERENCES
# ---------------------------------------------------------------------------

@app.route("/api/preferences/<int:user_id>", methods=["GET"])
def get_preferences(user_id):
    pref = StudyPreference.query.filter_by(user_id=user_id).first()
    if not pref:
        return jsonify(None)
    return jsonify(pref.to_dict())


@app.route("/api/preferences", methods=["POST"])
def save_preferences():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    pref = StudyPreference.query.filter_by(user_id=user_id).first()
    if pref:
        pref.group_size = data.get("group_size", pref.group_size)
        pref.study_time = data.get("study_time", pref.study_time)
        pref.noise_level = data.get("noise_level", pref.noise_level)
    else:
        pref = StudyPreference(
            user_id=user_id,
            group_size=data.get("group_size"),
            study_time=data.get("study_time"),
            noise_level=data.get("noise_level"),
        )
        db.session.add(pref)

    db.session.commit()
    return jsonify(pref.to_dict())


# ---------------------------------------------------------------------------
# MATCHING — simple +1 per matching preference field (0..3)
# ---------------------------------------------------------------------------

@app.route("/api/matches/<int:user_id>", methods=["GET"])
def get_matches(user_id):
    me = StudyPreference.query.filter_by(user_id=user_id).first()
    if not me:
        return jsonify([])

    others = (
        db.session.query(StudyPreference, User)
        .join(User, User.user_id == StudyPreference.user_id)
        .filter(StudyPreference.user_id != user_id)
        .all()
    )

    results = []
    for pref, user in others:
        score = (
            (1 if pref.group_size  == me.group_size  else 0)
            + (1 if pref.study_time  == me.study_time  else 0)
            + (1 if pref.noise_level == me.noise_level else 0)
        )
        results.append({
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "score": score,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return jsonify(results[:5])


# ---------------------------------------------------------------------------
# RAW SQL QUERY (SELECT only, for the database demo)
# ---------------------------------------------------------------------------

@app.route("/api/query", methods=["POST"])
def run_query():
    data = request.get_json() or {}
    sql = (data.get("query") or "").strip().rstrip(";")

    if not sql:
        return jsonify({"error": "query required"}), 400

    # Only allow a single SELECT statement.
    if ";" in sql:
        return jsonify({"error": "only a single statement is allowed"}), 400
    if not re.match(r"^\s*select\b", sql, re.IGNORECASE):
        return jsonify({"error": "only SELECT statements are allowed"}), 400

    try:
        result = db.session.execute(text(sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        return jsonify({"columns": columns, "rows": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001, debug=True)
