# Advanced Feature — Study Preference Matching

## 1. What it does

Each student can save their study preferences — *group size*, *study time*, and *noise level*. The **Matches** page then shows the top 5 other students whose preferences overlap with theirs most, ranked by how many of the three fields line up.

Endpoint:

```
GET /api/matches/<user_id>
```

Response:

```json
[
  { "user_id": 3, "name": "Carol Chen", "score": 3 },
  { "user_id": 5, "name": "Emma Evans", "score": 2 },
  ...
]
```

## 2. Why predefined values?

Each preference field is restricted to a small fixed set of strings:

| Field         | Allowed values                          |
|---------------|-----------------------------------------|
| `group_size`  | `small`, `medium`, `large`              |
| `study_time`  | `morning`, `afternoon`, `night`         |
| `noise_level` | `silent`, `moderate`, `loud`            |

The frontend enforces this with pill buttons — there is no free-text input. This matters for matching:

- **Comparability** — matching is a simple string equality check. "morning" matches "morning", but would never match "mornings" or "AM" or "早上".
- **Data quality** — fixed options keep the database tidy. Without enums, users would enter slightly different variants and fewer real matches would be found.
- **Easy to explain** — the scoring rule is a literal `=` comparison, not fuzzy matching.

## 3. The scoring system (0–3)

For every other user with saved preferences, we compute a score by comparing each of the three fields:

```
score = (same group_size ? 1 : 0)
      + (same study_time ? 1 : 0)
      + (same noise_level ? 1 : 0)
```

| Score | Meaning        |
|-------|----------------|
| 3     | Perfect match  |
| 2     | Strong match   |
| 1     | Weak match     |
| 0     | No match       |

Matches are sorted by `score DESC` and the **top 5** are returned.

## 4. Worked example — Alice vs. others

Alice's preferences (after re-seeding):

| Field         | Alice    |
|---------------|----------|
| `group_size`  | small    |
| `study_time`  | night    |
| `noise_level` | silent   |

Compare against three other seeded users:

| User   | group_size | study_time | noise_level | +1 per match       | Score |
|--------|------------|------------|-------------|--------------------|-------|
| Carol  | small      | night      | silent      | 1 + 1 + 1          | **3** |
| Emma   | medium     | night      | silent      | 0 + 1 + 1          | **2** |
| Frank  | small      | morning    | silent      | 1 + 0 + 1          | **2** |
| Bob    | medium     | morning    | moderate    | 0 + 0 + 0          | **0** |

Carol is a perfect match; Emma and Frank are strong matches; Bob has nothing in common.

## 5. SQL version of the matching query

The same logic expressed as a single SQL statement using `CASE`. It is pasteable straight into the in-app SQL page (`/api/query`) — replace `sp1.user_id = 1` with any user ID:

```sql
SELECT
  u.user_id,
  u.name,
  (
    (CASE WHEN sp1.group_size  = sp2.group_size  THEN 1 ELSE 0 END) +
    (CASE WHEN sp1.study_time  = sp2.study_time  THEN 1 ELSE 0 END) +
    (CASE WHEN sp1.noise_level = sp2.noise_level THEN 1 ELSE 0 END)
  ) AS score
FROM study_preference sp1
JOIN study_preference sp2 ON sp1.user_id != sp2.user_id
JOIN user u             ON u.user_id = sp2.user_id
WHERE sp1.user_id = 1
ORDER BY score DESC
LIMIT 5
```

> The `/api/query` endpoint requires a single SELECT and rejects `;`, so run this query **without a trailing semicolon**.

### How the SQL works, in plain English

1. `sp1` is a copy of the `study_preference` table aliased to "me" — filtered by `WHERE sp1.user_id = 1`.
2. `sp2` is the same table aliased to "every other user" — filtered by `sp1.user_id != sp2.user_id`.
3. The `user` table is joined so we can show names, not just IDs.
4. Each `CASE WHEN` turns a matching column into `1`, a non-match into `0`. We add the three together to get the score.
5. `ORDER BY score DESC LIMIT 5` picks the top 5 matches.

## 6. Database concepts demonstrated

| Concept          | Where it shows up in this feature |
|------------------|-----------------------------------|
| **Filtering**    | `WHERE sp1.user_id = 1` selects "me". `sp1.user_id != sp2.user_id` filters out self-matching. |
| **Self-join**    | `study_preference` is joined *to itself* (`sp1 JOIN sp2`) — a classic pattern for "compare each row to every other row". |
| **Inner joins**  | We also join the `user` table to resolve user IDs into display names. |
| **Column-wise comparison** | The three `CASE WHEN` expressions compute per-field equality; this is a one-line scoring function in SQL. |
| **ORDER BY + LIMIT** | Ranking logic lives in the database — the app doesn't have to sort in Python. |

This single query showcases the three most common "real" SQL patterns students learn: **filtering**, **joining** (especially a self-join), and **aggregating** a score out of row-level comparisons.

## 7. Demo — step-by-step

The whole feature takes ~90 seconds to show:

1. **Start the backend** (venv, `python seed.py`, `python app.py`). The seed now uses the new enum values (`night`, `silent`, …) so matches will be meaningful.
2. **Log in** as `alice@school.edu` / `password`.
3. **Open the Preferences page**. Show that every input is a pill button — no free text possible. Tweak one pill if desired; save.
4. **Open the Matches page**. Point out:
   - Users are ranked top-to-bottom by score.
   - Each card shows a 3-bar indicator plus a `score/3` number.
   - Colours change by score (amber = weak, indigo = strong, green = perfect).
5. **Open the SQL page**. Click the last example (the `CASE WHEN` matching query). Press **Run query**. The same ranking appears as a raw table — proof that the ORM and raw-SQL paths compute the same result.
6. *(Optional)* Open `sqlite3 backend/database.db` in a terminal and paste the same SQL to show it runs identically outside the app.

Talking points during the demo:

- Predefined options make `=` comparisons reliable.
- The Python endpoint (`/api/matches/<user_id>`) is just a `for`-loop with the same three comparisons — it's the simplest possible algorithm, intentionally.
- The SQL version is arguably *simpler* than the Python one: three `CASE` expressions, one `ORDER BY LIMIT`. This is where relational databases shine.
