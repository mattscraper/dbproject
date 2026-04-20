# System Overview

## Purpose

A small, demo-ready web application for managing **study groups** on a college campus. Built as a database course project to show a clear relational schema, an ORM layer (SQLAlchemy), and raw SQL access over the same database.

## Problem Solved

Students often want to study together but have trouble finding groups that match their subject, schedule, and study style. This app lets them:

- Register an account
- Browse existing study groups
- Join groups they are interested in
- Post messages to group members
- Save study preferences (group size, preferred time, noise level)

It also doubles as a **live SQL playground** so we can demonstrate the underlying database during the demo.

## Features

1. User registration and login (password hashed with `werkzeug.security`).
2. Create, list, and join study groups.
3. Post messages inside a group.
4. Save per-user study preferences.
5. **SQL query page** — runs raw `SELECT` statements against the SQLite database and renders the result as a table.

## Tech Stack

| Layer       | Tool                         |
|-------------|------------------------------|
| Frontend    | React + Vite                 |
| Backend     | Flask (Python)               |
| ORM         | SQLAlchemy                   |
| Database    | SQLite3 (`database.db`)      |
| Auth        | `werkzeug.security` password hashing |
| CORS        | `flask-cors`                 |

## Architecture

```
┌──────────────┐     HTTP/JSON     ┌──────────────┐    SQLAlchemy    ┌──────────────┐
│   React UI   │  ───────────────> │  Flask API   │ ───────────────> │  SQLite DB   │
│  (Vite :5173)│  <─────────────── │  (:5001)     │ <─────────────── │ database.db  │
└──────────────┘                   └──────────────┘                  └──────────────┘
                                         │                                 ▲
                                         │  raw SQL via /api/query         │
                                         └─────────────────────────────────┘
```

- The React frontend is a single-page app. It calls the Flask API with `fetch`.
- Flask uses SQLAlchemy for all normal CRUD. One special endpoint, `/api/query`, executes raw SQL via `db.session.execute(text(sql))` so the demo can show both access styles against the same schema.
- SQLite keeps everything in a single file (`backend/database.db`), which is easy to inspect from a terminal with `sqlite3 database.db`.

## Demo Flow (short)

1. `python seed.py` seeds the DB with 10 users, 5 groups, memberships, posts, preferences.
2. `python app.py` starts the API at `http://localhost:5001`.
3. `npm run dev` inside `frontend/my-app` starts the UI at `http://localhost:5173`.
4. Log in as `alice@school.edu` / `password`.
5. Join a group, post a message, set preferences.
6. Open the **SQL** page and run a live `SELECT` to show the same data from the database directly.
