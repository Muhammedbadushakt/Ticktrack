# admin.py

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
    flash,
    send_file
)

from app.models import (
    User,
    Student as S,
    Role,
    EventDetail as E,
    Poll,
    EventResponse as Er
)

from app.extension import db
from app.utils import encode_username
from app.config import Config

import os
import io
import csv
import zipfile


admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/Admin'
)


# ─────────────────────────────────────────────
# CHECK ADMIN
# ─────────────────────────────────────────────

def is_admin():

    if 'Username' not in session:
        return False

    user = User.query.filter_by(
        username=session['Username']
    ).first()

    if not user:
        return False

    role = Role.query.filter_by(
        student_id=user.student_id,
        name='admin'
    ).first()

    return bool(role)


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@admin_bp.route('/')
def dashboard():

    if not is_admin():
        return redirect(url_for('auth.login'))

    users = User.query.all()

    events = E.query.all()

    total_users = User.query.count()

    total_students = S.query.count()

    total_events = E.query.count()

    total_responses = Er.query.count()

    return render_template(
        'admin.html',
        users=users,
        events=events,
        total_users=total_users,
        total_students=total_students,
        total_events=total_events,
        total_responses=total_responses
    )


# ─────────────────────────────────────────────
# ASSIGN ROLE
# ─────────────────────────────────────────────

@admin_bp.route('/assign_role', methods=['POST'])
def assign_role():

    if not is_admin():
        return redirect(url_for('auth.login'))

    student_id = request.form.get('student_id')

    role_name = request.form.get('role')

    try:

        Role.query.filter_by(
            student_id=student_id
        ).delete()

        role = Role(
            student_id=student_id,
            name=role_name
        )

        db.session.add(role)

        db.session.commit()

        flash("Role updated successfully", "success")

    except Exception as e:

        db.session.rollback()

        print("ROLE ERROR:", e)

        flash("Role update failed", "danger")

    return redirect(url_for('admin.dashboard'))


# ─────────────────────────────────────────────
# DELETE USER
# ─────────────────────────────────────────────

@admin_bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):

    if not is_admin():
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)

    if not user:

        flash("User not found", "danger")

        return redirect(url_for('admin.dashboard'))

    try:

        db.session.delete(user)

        db.session.commit()

        flash("User deleted successfully", "success")

    except Exception as e:

        db.session.rollback()

        print("DELETE USER ERROR:", e)

        flash("Delete failed", "danger")

    return redirect(url_for('admin.dashboard'))


# ─────────────────────────────────────────────
# DELETE EVENT
# ─────────────────────────────────────────────

@admin_bp.route('/delete_event/<int:event_id>')
def delete_event(event_id):

    if not is_admin():
        return redirect(url_for('auth.login'))

    event = E.query.get(event_id)

    if not event:

        flash("Event not found", "danger")

        return redirect(url_for('admin.dashboard'))

    try:

        db.session.delete(event)

        db.session.commit()

        flash("Event deleted successfully", "success")

    except Exception as e:

        db.session.rollback()

        print("DELETE EVENT ERROR:", e)

        flash("Delete failed", "danger")

    return redirect(url_for('admin.dashboard'))


# ─────────────────────────────────────────────
# EXPORT EVENT RESPONSES
# ─────────────────────────────────────────────

@admin_bp.route('/export/<int:event_id>')
def export(event_id):

    if not is_admin():
        return redirect(url_for('auth.login'))

    event = E.query.get(event_id)

    polls = Poll.query.filter_by(
        event_id=event_id
    ).all()

    students = S.query.all()

    csv_output = io.StringIO()

    writer = csv.writer(csv_output)

    header = [
        'Student Name',
        'Student ID'
    ] + [poll.question for poll in polls]

    writer.writerow(header)

    uploaded_files = []

    for student in students:

        row = [
            student.name,
            student.student_id
        ]

        for poll in polls:

            response = Er.query.filter_by(
                poll_id=poll.id,
                student_id=student.student_id
            ).first()

            if response and response.answer:

                row.append(response.answer)

            elif response and response.file:

                row.append(response.file)

                file_path = os.path.join(
                    Config.UPLOAD_FOLDER,
                    response.file
                )

                if os.path.exists(file_path):

                    uploaded_files.append(file_path)

            else:

                row.append("No response")

        writer.writerow(row)

    csv_output.seek(0)

    memory_file = io.BytesIO()

    with zipfile.ZipFile(
        memory_file,
        'w',
        zipfile.ZIP_DEFLATED
    ) as zf:

        zf.writestr(
            'responses.csv',
            csv_output.getvalue()
        )

        for file_path in uploaded_files:

            zf.write(
                file_path,
                arcname=f'uploads/{os.path.basename(file_path)}'
            )

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{event.title}.zip"
    )


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────

@admin_bp.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('auth.login'))