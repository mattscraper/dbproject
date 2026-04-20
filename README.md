# Study Group Management & Collaboration

A database-course demo: Flask + SQLAlchemy + SQLite + React, with a live SQL query page.

## Quick start

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py            # http://localhost:5001

# frontend (in another terminal)
cd frontend/my-app
npm install
npm run dev              # http://localhost:5173
```

Login: `alice@school.edu` / `password`

## Structure

```
backend/
  app.py          Flask API (+ /api/query for raw SQL)
  models.py       SQLAlchemy models
  seed.py         Seeds 10 users, 5 groups, posts, preferences
  requirements.txt
  database.db     (created by seed.py)

frontend/my-app/
  src/
    api.js        Thin fetch wrapper
    App.jsx       Top-level nav + page switcher
    pages/
      Login.jsx
      Dashboard.jsx
      GroupPage.jsx
      Preferences.jsx
      SqlPage.jsx

docs/
  system_overview.md
  database_design.md
  api_and_demo_guide.md
```

See [docs/](docs/) for full documentation and the demo script.

## Terminal SQL

```bash
cd backend
sqlite3 database.db
sqlite> SELECT name, email FROM user;
```
