# Database Design

The database has **five tables**: `user`, `group`, `user_group` (association), `study_preference`, and `post`.

## Tables

### 1. `user`

Stores account info. Email is unique. Passwords are hashed.

| Column         | Type    | Notes                      |
|----------------|---------|----------------------------|
| `user_id`      | INTEGER | **Primary key**, autoincrement |
| `name`         | TEXT    | not null                   |
| `email`        | TEXT    | **unique**, not null       |
| `password_hash`| TEXT    | not null                   |

### 2. `group`

A study group (e.g. *Database Systems*).

| Column       | Type    | Notes                      |
|--------------|---------|----------------------------|
| `group_id`   | INTEGER | **Primary key**            |
| `name`       | TEXT    | not null                   |
| `description`| TEXT    |                            |

### 3. `user_group` (association / join table)

Connects users and groups in a **many-to-many** relationship. A user can join many groups; a group can have many members.

| Column     | Type    | Notes                                    |
|------------|---------|------------------------------------------|
| `user_id`  | INTEGER | FK → `user.user_id`, part of composite PK |
| `group_id` | INTEGER | FK → `group.group_id`, part of composite PK |

> **Why an association table?** Relational databases cannot store a list directly inside a row. To model "a user has many groups AND a group has many users", we use a third table where each row is one membership.

### 4. `study_preference`

One row per user (kept simple; not enforced as one-to-one in SQL). Lets each student describe what kind of study setup they want.

| Column        | Type    | Notes                              |
|---------------|---------|------------------------------------|
| `pref_id`     | INTEGER | **Primary key**                    |
| `user_id`     | INTEGER | FK → `user.user_id`, not null      |
| `group_size`  | TEXT    | `small` / `medium` / `large`       |
| `study_time`  | TEXT    | `morning` / `afternoon` / `evening`|
| `noise_level` | TEXT    | `quiet` / `moderate` / `loud`      |

### 5. `post`

A message in a group.

| Column      | Type     | Notes                          |
|-------------|----------|--------------------------------|
| `post_id`   | INTEGER  | **Primary key**                |
| `user_id`   | INTEGER  | FK → `user.user_id`            |
| `group_id`  | INTEGER  | FK → `group.group_id`          |
| `content`   | TEXT     | not null                       |
| `created_at`| DATETIME | default = current UTC time     |

## Relationships

**One-to-many**

- `user` → `post` (one user writes many posts)
- `group` → `post` (one group contains many posts)
- `user` → `study_preference` (one user has their preferences)

**Many-to-many**

- `user` ↔ `group` via `user_group` (a user joins many groups, a group has many users)

```
        (1)            (N)
  user  ───────────── post ──────────── group
   │          (1)                (1)      │
   │                                      │
   │              (M:N via user_group)    │
   └──────────────────────────────────────┘
   │
   │ (1:1-ish)
   ▼
 study_preference
```

## SQLAlchemy Models (backend/models.py)

```python
user_group = db.Table(
    "user_group",
    db.Column("user_id", db.Integer, db.ForeignKey("user.user_id"), primary_key=True),
    db.Column("group_id", db.Integer, db.ForeignKey("group.group_id"), primary_key=True),
)

class User(db.Model):
    user_id       = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(80), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    groups      = db.relationship("Group", secondary=user_group, back_populates="members")
    posts       = db.relationship("Post", backref="author", lazy=True)
    preferences = db.relationship("StudyPreference", backref="user", lazy=True)

class Group(db.Model):
    group_id    = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255))
    members     = db.relationship("User", secondary=user_group, back_populates="groups")
    posts       = db.relationship("Post", backref="group", lazy=True)

class StudyPreference(db.Model):
    pref_id     = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    group_size  = db.Column(db.String(20))
    study_time  = db.Column(db.String(20))
    noise_level = db.Column(db.String(20))

class Post(db.Model):
    post_id    = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    group_id   = db.Column(db.Integer, db.ForeignKey("group.group_id"), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## Equivalent Raw SQL Schema

```sql
CREATE TABLE user (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE "group" (
    group_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT
);

CREATE TABLE user_group (
    user_id  INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id)  REFERENCES user(user_id),
    FOREIGN KEY (group_id) REFERENCES "group"(group_id)
);

CREATE TABLE study_preference (
    pref_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    group_size  TEXT,
    study_time  TEXT,
    noise_level TEXT,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE post (
    post_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    group_id   INTEGER NOT NULL,
    content    TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)  REFERENCES user(user_id),
    FOREIGN KEY (group_id) REFERENCES "group"(group_id)
);
```

> Note: `group` is a reserved word in SQL, so it is quoted with double quotes in raw SQL. SQLAlchemy handles the quoting automatically.

## Four Demo SQL Queries

### 1. All groups a specific user belongs to

```sql
SELECT g.group_id, g.name
FROM "group" g
JOIN user_group ug ON g.group_id = ug.group_id
WHERE ug.user_id = 1;
```

### 2. All posts (with author) inside a given group

```sql
SELECT u.name AS author, p.content, p.created_at
FROM post p
JOIN user u ON u.user_id = p.user_id
WHERE p.group_id = 1
ORDER BY p.created_at DESC;
```

### 3. Users who share the same study-time preference

```sql
SELECT u1.name AS user_a, u2.name AS user_b, s1.study_time
FROM study_preference s1
JOIN study_preference s2
  ON s1.study_time = s2.study_time
 AND s1.user_id   <  s2.user_id
JOIN user u1 ON u1.user_id = s1.user_id
JOIN user u2 ON u2.user_id = s2.user_id;
```

### 4. Count members per group

```sql
SELECT g.name, COUNT(ug.user_id) AS members
FROM "group" g
LEFT JOIN user_group ug ON g.group_id = ug.group_id
GROUP BY g.group_id
ORDER BY members DESC;
```
