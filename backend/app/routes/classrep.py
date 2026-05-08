from flask import Blueprint, redirect, url_for, session, render_template, request, flash, send_file
from app.utils import decode_username, encode_username
from app.models import Student as S, User, EventDetail as E, Poll, EventResponse as Er
from app.extension import db
from app.config import Config
import os, csv, io
import zipfile
import tempfile
classrep_bp = Blueprint("classrep", __name__, url_prefix="/ClassRepresentative")


def get_cr_user():
    return User.query.filter_by(username=session['Username']).first()


# ── Dashboard ──────────────────────────────────────────────
@classrep_bp.route('/<user>')
def classrep(user):
    if 'Username' not in session or decode_username(user) != session['Username']:
        return redirect(url_for('auth.login'))

    events         = E.query.all()
    total_students = S.query.count()
    slide = request.args.get('slide', '0')
    # ── Responses slide data ──
    sheet_event_id    = request.args.get('sheet_event')
    selected_event_id = None
    sheet_polls       = []
    rows              = []

    if sheet_event_id:
        selected_event_id = int(sheet_event_id)
        sheet_polls = Poll.query.filter_by(event_id=sheet_event_id).all()

        for student in S.query.all():
            row = {
                'name':       student.name,
                'student_id': student.student_id,
                'responses':  []
            }
            for poll in sheet_polls:
                resp = Er.query.filter_by(
                    poll_id=poll.id,
                    student_id=student.student_id
                ).first()
                if resp:
                    row['responses'].append(resp.answer or resp.file or '—')
                else:
                    row['responses'].append('No response')
            rows.append(row)

    # ── Edit slide data ──
    edit_event_id       = request.args.get('edit_event')
    selected_edit_event = None
    edit_polls          = []

    if edit_event_id:
        selected_edit_event = E.query.get(edit_event_id)
        edit_polls = Poll.query.filter_by(event_id=edit_event_id).all()

    return render_template(
        'classrep.html',
        events=events,
        total_students=total_students,
        current_username=session['Username'],
        user=user,
        slide=slide,
        selected_event_id=selected_event_id,
        sheet_polls=sheet_polls,
        rows=rows,
        selected_edit_event=selected_edit_event,
        edit_polls=edit_polls,
    )


# ── Add Event + Polls ──────────────────────────────────────
@classrep_bp.route('/Eventadd', methods=['GET', 'POST'])
def eventadd():
    if 'Username' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title       = request.form.get('title')
        description = request.form.get('description')
        questions   = request.form.getlist('question[]')
        types       = request.form.getlist('type[]')

        if not title:
            flash("Event title is required", "danger")
            return redirect(url_for(
                'classrep.classrep',
                user=encode_username(session['Username']),
                slide=1
            ))

        cr_user = get_cr_user()

        try:
            event = E(
                title=title,
                description=description,
                created_by=cr_user.id
            )
            db.session.add(event)
            db.session.flush()  # get event.id before commit

            for q, t in zip(questions, types):
                if q.strip():
                    poll = Poll(
                        event_id=event.id,
                        question=q.strip(),
                        type=t
                    )
                    db.session.add(poll)

            db.session.commit()
            flash("Event created successfully", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating event: {e}", "danger")

    return redirect(url_for(
        'classrep.classrep',
        user=encode_username(session['Username'])
    ))


# ── Data Edit — edit/delete events and polls ──────────────
@classrep_bp.route('/dataedit', methods=['POST'])
def dataedit():
    if 'Username' not in session:
        return redirect(url_for('auth.login'))

    action   = request.form.get('action')
    event_id = request.form.get('event_id')

    # ── Update event title/description ──
    if action == 'update_event':
        ev = E.query.get(event_id)
        if ev:
            ev.title       = request.form.get('title')
            ev.description = request.form.get('description')
            db.session.commit()
            flash("Event updated successfully", "success")

    # ── Delete event ──
    elif action == 'delete_event':
        ev = E.query.get(event_id)
        if ev:
            db.session.delete(ev)
            db.session.commit()
            flash("Event deleted successfully", "success")
            return redirect(url_for(
                'classrep.classrep',
                user=encode_username(session['Username']),
                slide=0
            ))

    # ── Update poll question/type ──
    elif action == 'update_poll':
        poll = Poll.query.get(request.form.get('poll_id'))
        if poll:
            poll.question = request.form.get('question')
            poll.type     = request.form.get('type')
            db.session.commit()
            flash("Poll updated successfully", "success")

    # ── Delete poll ──
    elif action == 'delete_poll':
        poll = Poll.query.get(request.form.get('poll_id'))
        if poll:
            db.session.delete(poll)
            db.session.commit()
            flash("Poll deleted successfully", "success")

    # ── Add new poll to event ──
    elif action == 'add_poll':
        question = request.form.get('question')
        ptype    = request.form.get('type')
        if question and event_id:
            poll = Poll(
                event_id=event_id,
                question=question,
                type=ptype
            )
            db.session.add(poll)
            db.session.commit()
            flash("Poll added successfully", "success")

    return redirect(url_for(
        'classrep.classrep',
        user=encode_username(session['Username']),
        edit_event=event_id,
        slide = 3
    ) + '#edit')


# ── Data Export — download CSV ─────────────────────────────
@classrep_bp.route('/dataexport')
def dataexport():
    if 'Username' not in session:
        return redirect(url_for('auth.login'))

    event_id = request.args.get('event_id')

    if not event_id:
        return redirect(url_for(
            'classrep.classrep',
            user=encode_username(session['Username']),
            slide=4
        ))

    event = E.query.get(event_id)
    polls = Poll.query.filter_by(event_id=event_id).all()
    students = S.query.all()

    if not event:
        flash("Event not found", "danger")
        return redirect(url_for(
            'classrep.classrep',
            user=encode_username(session['Username']),
            slide=4
        ))

    # ─────────────────────────────────────────
    # CREATE CSV IN MEMORY
    # ─────────────────────────────────────────
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)

    header = ['Student Name', 'Student ID'] + [p.question for p in polls]
    writer.writerow(header)

    uploaded_files = []

    for student in students:
        row = [student.name, student.student_id]

        for poll in polls:
            resp = Er.query.filter_by(
                poll_id=poll.id,
                student_id=student.student_id
            ).first()

            if resp and resp.answer:
                row.append(resp.answer)

            elif resp and resp.file:

                # Store filename in CSV
                row.append(resp.file)

                # Save full file path for ZIP
                file_path = os.path.join(
                    Config.UPLOAD_FOLDER,
                    resp.file
                )

                if os.path.exists(file_path):
                    uploaded_files.append(file_path)

            else:
                row.append('No response')

        writer.writerow(row)

    csv_output.seek(0)

    # ─────────────────────────────────────────
    # CREATE ZIP
    # ─────────────────────────────────────────
    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:

        # Add CSV
        zf.writestr(
            'responses.csv',
            csv_output.getvalue()
        )

        # Add uploaded files
        for file_path in uploaded_files:

            filename = os.path.basename(file_path)

            zf.write(
                file_path,
                arcname=f'uploads/{filename}'
            )

    memory_file.seek(0)

    zip_filename = f"{event.title.replace(' ', '_')}_Export.zip"

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )
# ── Logout ─────────────────────────────────────────────────
@classrep_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))