"""Seed script — creates database.db and populates demo data.

Run once before starting the app:
    python seed.py
"""

import os
from werkzeug.security import generate_password_hash

from app import app
from models import db, User, Group, StudyPreference, Post


USERS = [
    ("Alice Anderson",   "alice@school.edu"),
    ("Bob Baker",        "bob@school.edu"),
    ("Carol Chen",       "carol@school.edu"),
    ("David Diaz",       "david@school.edu"),
    ("Emma Evans",       "emma@school.edu"),
    ("Frank Ford",       "frank@school.edu"),
    ("Grace Gupta",      "grace@school.edu"),
    ("Henry Hill",       "henry@school.edu"),
    ("Ivy Iverson",      "ivy@school.edu"),
    ("Jake Johnson",     "jake@school.edu"),
]

GROUPS = [
    ("Database Systems",     "CS 4800 study group — covers SQL, ER models, normalization."),
    ("Algorithms",           "Weekly algorithms practice and problem solving."),
    ("Linear Algebra",       "Matrices, vector spaces, eigenvalues."),
    ("Operating Systems",    "Processes, memory, file systems."),
    ("Intro to AI",          "Search, logic, basic ML concepts."),
]

# (user_index, group_index) pairs — membership map
MEMBERSHIPS = [
    (0, 0), (0, 1),
    (1, 0), (1, 2),
    (2, 0), (2, 3), (2, 4),
    (3, 1), (3, 2),
    (4, 0), (4, 4),
    (5, 3),
    (6, 0), (6, 1), (6, 4),
    (7, 2), (7, 3),
    (8, 1), (8, 4),
    (9, 0), (9, 3),
]

PREFS = [
    # user_index, group_size, study_time, noise_level
    (0, "small",  "evening",   "quiet"),
    (1, "medium", "morning",   "moderate"),
    (2, "small",  "evening",   "quiet"),
    (3, "large",  "afternoon", "moderate"),
    (4, "medium", "evening",   "quiet"),
    (5, "small",  "morning",   "quiet"),
    (6, "large",  "afternoon", "loud"),
    (7, "medium", "evening",   "moderate"),
    (8, "small",  "morning",   "quiet"),
    (9, "medium", "afternoon", "moderate"),
]

POSTS = [
    (0, 0, "Anyone want to review JOINs tonight?"),
    (1, 0, "Sharing my normalization notes — DM me."),
    (2, 0, "Quiz next week — who's hosting study session?"),
    (3, 1, "Dijkstra vs. A* — pros and cons?"),
    (0, 1, "Meeting at the library at 7pm."),
    (2, 3, "Finished process scheduling homework, happy to compare."),
    (4, 4, "AI project idea: recommend study groups based on preferences."),
    (6, 0, "ER diagram for the final project is due Friday."),
    (8, 4, "Anyone want to pair on the search algorithms worksheet?"),
    (9, 3, "Good video on virtual memory: youtu.be/..."),
]


def seed():
    with app.app_context():
        db_file = os.path.join(os.path.dirname(__file__), "database.db")
        if os.path.exists(db_file):
            os.remove(db_file)
        db.create_all()

        users = [
            User(name=n, email=e, password_hash=generate_password_hash("password"))
            for n, e in USERS
        ]
        db.session.add_all(users)

        groups = [Group(name=n, description=d) for n, d in GROUPS]
        db.session.add_all(groups)
        db.session.commit()

        for ui, gi in MEMBERSHIPS:
            users[ui].groups.append(groups[gi])

        for ui, size, when, noise in PREFS:
            db.session.add(StudyPreference(
                user_id=users[ui].user_id,
                group_size=size,
                study_time=when,
                noise_level=noise,
            ))

        for ui, gi, content in POSTS:
            db.session.add(Post(
                user_id=users[ui].user_id,
                group_id=groups[gi].group_id,
                content=content,
            ))

        db.session.commit()
        print(f"Seeded {len(users)} users, {len(groups)} groups, "
              f"{len(POSTS)} posts, {len(PREFS)} preferences.")
        print("Login with any email above, password: 'password'")


if __name__ == "__main__":
    seed()
