from flask import Blueprint, session, render_template, redirect, url_for, request, flash, jsonify
from app.utils import decode_username, encode_username
from app.models import Student as S, User, EventDetail as E, Poll, EventResponse as Er
from app.extension import db, p
from werkzeug.utils import secure_filename
from app.config import Config
import os
from app.services.aichat import ai_chat

student_bp = Blueprint("student", __name__, url_prefix="/Student")


# ─────────────────────────────────────────────
# STUDENT DASHBOARD
# ─────────────────────────────────────────────

@student_bp.route('/<user>')
def student(user):

    if 'Username' not in session or decode_username(user) != session['Username']:
        return redirect(url_for('auth.login'))

    event_id = request.args.get('event_id')

    current_user = User.query.filter_by(
        username=session['Username']
    ).first()

    student = S.query.filter_by(
        student_id=current_user.student_id
    ).first()

    events = E.query.all()

    usernames = [i.username for i in User.query.all()]

    polls = []

    if event_id:
        polls = Poll.query.filter_by(event_id=event_id).all()

    return render_template(
        'student.html',
        Student=student,
        events=events,
        polls=polls,
        event_id=event_id,
        username=usernames,
        current_username=session['Username']
    )


# ─────────────────────────────────────────────
# GET POLL
# ─────────────────────────────────────────────

@student_bp.route('/get_poll', methods=['POST'])
def get_poll():

    if 'Username' not in session:
        return redirect(url_for('auth.login'))

    event_id = request.form.get('event_id')

    return redirect(
        url_for(
            'student.student',
            user=encode_username(session['Username']),
            event_id=event_id
        )
    )


# ─────────────────────────────────────────────
# SUBMIT POLL
# ─────────────────────────────────────────────

@student_bp.route('/submit', methods=['POST'])
def submit():

    if 'Username' not in session:
        return redirect(url_for('auth.login'))

    event_id = request.form.get('event_id')

    if not event_id:
        flash("Event ID missing", "danger")

        return redirect(
            url_for(
                'student.student',
                user=encode_username(session['Username'])
            )
        )

    polls = Poll.query.filter_by(event_id=event_id).all()

    student_id = User.query.filter_by(
        username=session['Username']
    ).first().student_id

    try:

        for poll in polls:

            poll_name = f"q{poll.id}"

            existing = Er.query.filter_by(
                poll_id=poll.id,
                student_id=student_id
            ).first()

            if existing:
                    # RADIO/TEXT UPDATE
                if poll.type in ['radio', 'text']:

                    existing.answer = request.form.get(poll_name)

                # FILE UPDATE
                elif poll.type == 'file':

                    file = request.files.get(poll_name)

                    if file and file.filename != '':

                        filename = secure_filename(file.filename)

                        unique_name = f"{student_id}_{poll.id}_{filename}"

                        file_path = os.path.join(
                            Config.UPLOAD_FOLDER,
                            unique_name
                        )

                        file.save(file_path)

                        existing.file = unique_name

                continue

            # RADIO / TEXT
            if poll.type in ['radio', 'text']:

                response = request.form.get(poll_name)

                er = Er(
                    poll_id=poll.id,
                    student_id=student_id,
                    answer=response
                )

                db.session.add(er)

            # FILE
            elif poll.type == 'file':

                file = request.files.get(poll_name)

                if not file or file.filename == '':
                    continue

                filename = secure_filename(file.filename)

                unique_name = f"{student_id}_{poll.id}_{filename}"

                file_path = os.path.join(
                    Config.UPLOAD_FOLDER,
                    unique_name
                )
                print("SAVING TO:", file_path)

                file.save(file_path)

                print("FILE SAVED")

                er = Er(
                    poll_id=poll.id,
                    student_id=student_id,
                    file=unique_name
                )

                db.session.add(er)

        db.session.commit()

        flash("Response submitted successfully", "success")

    except Exception as e:

        db.session.rollback()

        print("SUBMIT ERROR:", e)

        flash("Error submitting response", "danger")

    return redirect(
        url_for(
            'student.student',
            user=encode_username(session['Username'])
        )
    )


# ─────────────────────────────────────────────
# UPDATE PROFILE
# ─────────────────────────────────────────────

@student_bp.route('/update', methods=['POST'])
def update():

    if 'Username' not in session:
        return redirect(url_for('auth.login'))

    field = request.form.get('field')

    value = request.form.get(field)

    student_id = User.query.filter_by(
        username=session['Username']
    ).first().student_id

    update_user = User.query.filter_by(
        student_id=student_id
    ).first()

    update_student = S.query.filter_by(
        student_id=student_id
    ).first()

    allowed = {
        "name",
        "department",
        "dob",
        "mobile",
        "email",
        "year_of_admission",
        "class_roll_no",
        "address"
    }

    if not field:
        return redirect(
            url_for(
                'student.student',
                user=encode_username(session['Username'])
            )
        )

    try:

        # PASSWORD
        if field == "password":

            confirm = request.form.get("confirm")

            if value != confirm:

                flash("Passwords do not match", "danger")

                return redirect(
                    url_for(
                        'student.student',
                        user=encode_username(session['Username'])
                    )
                )

            update_user.password_hash = p.hash(value)

            db.session.commit()

            flash("Password updated successfully", "success")

        # USERNAME
        elif field == "username":

            existing = User.query.filter_by(
                username=value
            ).first()

            if existing:

                flash("Username already exists", "danger")

                return redirect(
                    url_for(
                        'student.student',
                        user=encode_username(session['Username'])
                    )
                )

            update_user.username = value

            session['Username'] = value

            db.session.commit()

            flash("Username updated successfully", "success")

        # STUDENT FIELDS
        elif field in allowed:

            setattr(update_student, field, value)

            db.session.commit()

            flash("Profile updated successfully", "success")

    except Exception as e:

        db.session.rollback()

        print("UPDATE ERROR:", e)

        flash("Update failed", "danger")

    return redirect(
        url_for(
            'student.student',
            user=encode_username(session['Username'])
        )
    )


# ─────────────────────────────────────────────
# CHATBOT
# ─────────────────────────────────────────────

@student_bp.route('/chatbot', methods=['POST'])
def chatbot():

    if 'Username' not in session:
        return jsonify({
            "reply": "Please login first"
        })

    try:

        data = request.get_json()

        message = data.get("message")

        if not message:
            return jsonify({
                "reply": "Empty message"
            })

        reply = ai_chat(message)

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print("CHATBOT ERROR:", e)

        return jsonify({
            "reply": "AI is currently unavailable"
        })


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────

@student_bp.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('auth.login'))