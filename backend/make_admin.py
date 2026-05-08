from backend.app import create_app, db
from backend.app.models import User

app = create_app()

student_id=25022700  # change this

with app.app_context():
    user = User.query.filter_by(student_id=student_id).first()

    if not user:
        print("User not found")
    else:
        user.role = "admin"   # OR user.is_admin = True (based on your model)
        db.session.commit()
        print("Admin role assigned successfully")