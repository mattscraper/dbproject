# API & Demo Guide

## Running the project

```bash
# backend (terminal 1)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py            # creates database.db with demo data
python app.py             # starts API at http://localhost:5001

# frontend (terminal 2)
cd frontend/my-app
npm install
npm run dev               # UI at http://localhost:5173
```

Seed users all share the password **`password`**. Primary demo login:

- `alice@school.edu` / `password`

## API Endpoints

| Method | Endpoint                          | Description                                   |
|--------|-----------------------------------|-----------------------------------------------|
| POST   | `/api/register`                   | Create account `{name, email, password}`      |
| POST   | `/api/login`                      | Returns user `{email, password}`              |
| GET    | `/api/groups`                     | List all groups (with member counts)          |
| POST   | `/api/groups`                     | Create group `{name, description}`            |
| POST   | `/api/groups/<id>/join`           | Join group `{user_id}`                        |
| GET    | `/api/posts?group_id=<id>`        | Posts in a group (newest first)               |
| POST   | `/api/posts`                      | Create post `{user_id, group_id, content}`    |
| GET    | `/api/preferences/<user_id>`      | Get user's preferences                        |
| POST   | `/api/preferences`                | Create or update `{user_id, group_size, study_time, noise_level}` |
| POST   | `/api/query`                      | **Raw SQL** — body `{query: "SELECT …"}`      |

All responses are JSON. Errors return `{"error": "..."}` with a non-200 status.

## The `/api/query` feature

This is the centerpiece of the demo. It lets the user send any `SELECT` statement and get the result back as JSON:

```json
POST /api/query
{
  "query": "SELECT name, email FROM user LIMIT 3;"
}

→

{
  "columns": ["name", "email"],
  "rows": [
    ["Alice Anderson", "alice@school.edu"],
    ["Bob Baker",      "bob@school.edu"],
    ["Carol Chen",     "carol@school.edu"]
  ]
}
```

**Safety rules** (see [backend/app.py](../backend/app.py)):

1. The query must start with `SELECT` (case-insensitive).
2. Only **one** statement per request — any `;` inside the body is rejected, so no stacked queries like `SELECT 1; DROP TABLE user`.
3. Errors from SQLite (e.g. bad column name) are caught and returned as `{"error": "..."}`.

Write access (`INSERT`, `UPDATE`, `DELETE`) is intentionally left to the normal API routes that use SQLAlchemy, so the demo shows *both* access patterns over the same schema.

## Terminal SQL (no browser)

You can also hit the database directly:

```bash
cd backend
sqlite3 database.db
sqlite> .tables
sqlite> .schema user
sqlite> SELECT * FROM "group";
sqlite> SELECT g.name, COUNT(ug.user_id) AS members
   ...> FROM "group" g
   ...> LEFT JOIN user_group ug ON g.group_id = ug.group_id
   ...> GROUP BY g.group_id;
sqlite> .quit
```

This is the fastest way to verify that the ORM-written data is really sitting in a normal relational database.

## Demo Script

A ~5 minute walkthrough:

1. **Login** as `alice@school.edu` / `password`.
2. **View groups** — the Dashboard lists all 5 seeded groups with member counts.
3. **Join a group** — click *Join* on, say, *Operating Systems*. The member count goes up.
4. **Open a group** and **post a message** — shows the post appearing instantly, ordered newest-first.
5. **Preferences page** — set group size / study time / noise level, hit Save.
6. **SQL page** — the highlight:
   - Run `SELECT * FROM user;` to show the users table.
   - Run the *members per group* query to show a JOIN + GROUP BY.
   - Run the *users with same study_time* query to show a self-join.
   - Try a bad query (e.g. `SELECT * FROM nope;`) to show the clean error.
   - Try `DELETE FROM user;` to show the write-protection.
7. **(Optional) Terminal** — open `sqlite3 database.db` and run the same query to show the data lives in a real file.

## Concepts to Explain

- **Primary key** — Unique identifier for each row. `user.user_id`, `group.group_id`, etc. SQLite auto-assigns it.
- **Foreign key** — Column that references a primary key in another table. `post.user_id → user.user_id` is what ties a post to its author.
- **Join table** — A third table used to model many-to-many. `user_group` has `(user_id, group_id)` with both as foreign keys. Each row is one membership.
- **ORM vs. raw SQL** —
  - *ORM (SQLAlchemy)*: `User.query.filter_by(email=…).first()`. Python-object friendly, prevents injection, handles relationships.
  - *Raw SQL*: `SELECT * FROM user WHERE email = ?`. Total control, sometimes faster, but you write the SQL yourself. This app uses both: SQLAlchemy for CRUD, raw SQL via `/api/query` for the SQL page and demos.
- **Why hash passwords?** `werkzeug.security.generate_password_hash` so the DB never stores plaintext passwords.

## Sample Professor Q&A

**Q: Why did you make `user_group` a separate table instead of putting a group list on the user?**
A: Relational databases store one value per column. To represent "a user belongs to many groups and a group has many users", we need a separate row per membership. That third table is a standard way to model many-to-many.

**Q: What is the primary key of `user_group`?**
A: The composite key `(user_id, group_id)`. A user can't join the same group twice, so that pair is unique.

**Q: Show me that `/api/query` is safe against modifications.**
A: It rejects anything that doesn't start with `SELECT`, and it refuses queries containing `;` to stop stacked statements. Try `DELETE FROM user;` — you'll see the "only SELECT statements are allowed" error.

**Q: How does SQLAlchemy know that `user.groups` should go through `user_group`?**
A: The `db.relationship("Group", secondary=user_group, back_populates="members")` line — `secondary` is the association table, `back_populates` links the reverse side on `Group`.

**Q: Why SQLite?**
A: Zero-config — one file, one library, comes with Python. It fully supports the SQL we need (joins, group by, foreign keys). For a class demo, it keeps setup to `pip install` and `python seed.py`.

**Q: If two users try to join the same group at once, what happens?**
A: SQLAlchemy checks `if group not in user.groups` before appending. If both slipped through, the composite primary key `(user_id, group_id)` on `user_group` would still reject the duplicate at the DB level.

**Q: What would you change for a real production version?**
A: Real auth (JWT / sessions), pagination on `/api/posts`, stricter input validation, and Postgres instead of SQLite so it handles concurrent writes well. But the schema itself would stay essentially the same.
