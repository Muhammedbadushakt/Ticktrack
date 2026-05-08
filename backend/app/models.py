from .extension import db
from datetime import datetime


# ─────────────────────────────────────────────
# Student
# ─────────────────────────────────────────────

class Student(db.Model):
    __tablename__ = "students"

    id                = db.Column(db.Integer,     primary_key=True)
    name              = db.Column(db.String(50),  nullable=True)
    student_id        = db.Column(db.Integer,     unique=True, nullable=False)
    department        = db.Column(db.String(100), nullable=True)
    dob               = db.Column(db.Date,        nullable=True)
    mobile            = db.Column(db.String(15),  unique=True, nullable=True)
    email             = db.Column(db.String(100), unique=True, nullable=True)
    year_of_admission = db.Column(db.Date,        nullable=True)
    class_roll_no     = db.Column(db.Integer,     nullable=True)
    address           = db.Column(db.Text,        nullable=True)

    users           = db.relationship("User",          backref="student", lazy=True)
    roles           = db.relationship("Role",          backref="student", lazy=True, cascade="all, delete-orphan")
    event_responses = db.relationship("EventResponse", backref="student", lazy=True, cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# User
# ─────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer,     primary_key=True)
    student_id    = db.Column(db.Integer,     db.ForeignKey("students.student_id", ondelete="CASCADE"), nullable=True)
    username      = db.Column(db.String(50),  nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    otp               = db.Column(db.String(6),nullable=True)
    otp_created_at    = db.Column(db.DateTime,nullable=True)

    created_events = db.relationship("EventDetail", backref="created_by_user", lazy=True, cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# Role
# ─────────────────────────────────────────────

class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = (
        db.UniqueConstraint("student_id", "name", name="uq_role_student_name"),
    )

    id         = db.Column(db.Integer,    primary_key=True)
    student_id = db.Column(db.Integer,    db.ForeignKey("students.student_id", ondelete="CASCADE"), nullable=True)
    name       = db.Column(db.String(50), nullable=True)


# ─────────────────────────────────────────────
# Event Detail
# ─────────────────────────────────────────────

class EventDetail(db.Model):
    __tablename__ = "event_details"

    id          = db.Column(db.Integer,     primary_key=True)
    title       = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text,        nullable=True)
    created_by  = db.Column(db.Integer,     db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    polls = db.relationship("Poll", backref="event", lazy=True, cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# Poll
# ─────────────────────────────────────────────

class Poll(db.Model):
    __tablename__ = "polls"

    id       = db.Column(db.Integer,    primary_key=True)
    event_id = db.Column(db.Integer,    db.ForeignKey("event_details.id", ondelete="CASCADE"), nullable=True)
    question = db.Column(db.Text,       nullable=True)
    type     = db.Column(db.String(50), nullable=True)

    responses = db.relationship("EventResponse", backref="poll", lazy=True, cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# Event Response
# ─────────────────────────────────────────────

class EventResponse(db.Model):
    __tablename__ = "event_responses"
    __table_args__ = (
        db.UniqueConstraint("poll_id", "student_id", name="uq_response_poll_student"),
    )

    id         = db.Column(db.Integer,     primary_key=True)
    poll_id    = db.Column(db.Integer,     db.ForeignKey("polls.id",            ondelete="CASCADE"), nullable=True)
    student_id = db.Column(db.Integer,     db.ForeignKey("students.student_id", ondelete="CASCADE"), nullable=True)
    answer     = db.Column(db.Text,        nullable=True)
    file       = db.Column(db.String(255), nullable=True)
    status     = db.Column(db.Boolean,     nullable=True)