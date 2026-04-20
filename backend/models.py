"""SQLAlchemy models for the Study Group app.

Five tables:
- User              one user has many posts, many preferences (1 here), belongs to many groups
- Group             one group has many posts, many members
- UserGroup         association table connecting users <-> groups (many-to-many)
- StudyPreference   one-to-one-ish: a user can save preferences
- Post              belongs to one user and one group
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Association table for the many-to-many between User and Group.
# Kept as a plain Table (no extra columns) — simplest form.
user_group = db.Table(
    "user_group",
    db.Column("user_id", db.Integer, db.ForeignKey("user.user_id"), primary_key=True),
    db.Column("group_id", db.Integer, db.ForeignKey("group.group_id"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Relationships
    groups = db.relationship("Group", secondary=user_group, back_populates="members")
    posts = db.relationship("Post", backref="author", lazy=True)
    preferences = db.relationship("StudyPreference", backref="user", lazy=True)

    def to_dict(self):
        return {"user_id": self.user_id, "name": self.name, "email": self.email}


class Group(db.Model):
    __tablename__ = "group"

    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255))

    members = db.relationship("User", secondary=user_group, back_populates="groups")
    posts = db.relationship("Post", backref="group", lazy=True)

    def to_dict(self):
        return {
            "group_id": self.group_id,
            "name": self.name,
            "description": self.description,
            "member_count": len(self.members),
        }


class StudyPreference(db.Model):
    __tablename__ = "study_preference"

    pref_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    group_size = db.Column(db.String(20))       # e.g. "small", "medium", "large"
    study_time = db.Column(db.String(20))       # e.g. "morning", "afternoon", "evening"
    noise_level = db.Column(db.String(20))      # e.g. "quiet", "moderate", "loud"

    def to_dict(self):
        return {
            "pref_id": self.pref_id,
            "user_id": self.user_id,
            "group_size": self.group_size,
            "study_time": self.study_time,
            "noise_level": self.noise_level,
        }


class Post(db.Model):
    __tablename__ = "post"

    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("group.group_id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "post_id": self.post_id,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "author": self.author.name if self.author else None,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
