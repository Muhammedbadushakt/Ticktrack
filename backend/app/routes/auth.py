import random, string, uuid
from datetime import datetime, timedelta
from flask import Blueprint ,request,redirect,url_for,render_template,session
from app.extension import db
from pwdlib import PasswordHash
from app.models import Student as S,User,Role
from app.utils import encode_username,decode_username
from app.services.mail_service import send_otp_email

OTP_EXPIRES     = timedelta(minutes=10)

auth_bp = Blueprint("auth", __name__, url_prefix="/login")


p = PasswordHash.recommended() 
def _gen_otp(length=6) -> str:
    return "".join(random.choices(string.digits, k=length))


@auth_bp.route("/register",methods=["POST","GET"])
def register():
    usernames = [u[0] for u in db.session.query(User.username).all()]
    if request.method == 'POST':
        
        Student = {
            "name" : '',
            "username" : '',
            "password": '',
            "student_id": '',
            "department": '',
            "dob" :'',
            "number" : '',
            "email":'',
            "Yoa" :'',
            "RollNo" :'',
            "address" : ''
        }
        Student['name'] = request.form.get('name')
        Student['username'] = request.form.get('username')
        Student['password'] = request.form.get('password')    
        Student['student_id']  = request.form.get('Student-id')
        Student['department']  = request.form.get('department')
        Student['dob']         = request.form.get('dob')
        Student['number']      = request.form.get('number')
        Student['email']       = request.form.get('email')
        Student['Yoa']         = request.form.get('Yoa')
        Student['RollNo']      = request.form.get('Roll-no')
        Student['address']     = request.form.get('address')
        if all(Student.values()):
            hashed = p.hash(Student['password'])
            try:
                s = S( 
                        name = Student['name'],
                        student_id = int(Student['student_id']), 
                        department = Student['department'],
                        dob     =  Student['dob'],            
                        mobile  =  Student['number'],      
                        email   =  Student['email'],       
                        year_of_admission =Student['Yoa'],         
                        class_roll_no =   int(Student['RollNo']),      
                        address      =   Student['address']  
                    )
                db.session.add(s)
                user =    User(
                            student_id = Student['student_id'],
                            username   = Student['username'],
                            password_hash = hashed
                        )
                db.session.add(user)
                role =    Role(
                            student_id = Student['student_id'],
                            name    = 'st'
                        )
                db.session.add(role)
                db.session.commit()
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                return f"Error: {e}"
        return "All fields are required"
    return render_template('Regist.html' ,username=usernames)

@auth_bp.route('/',methods=['POST','GET'])
def login():
    msg = ''
    if request.method =='POST':
        Username  = request.form.get('Username')
        Password  = request.form.get('password')
        role      = request.form.get('Role')
        check = User.query.filter_by(username=Username).first()
        if not role:
            msg = "Please select a role"
            return render_template('user.html', msg=msg)
        if check and p.verify(Password,check.password_hash):
            matched_role = Role.query.filter_by(
                student_id = check.student_id,
                name       = role.lower()
            ).first()
            if matched_role:
                session['Username'] = Username
                encode = encode_username(Username)

                if matched_role.name == 'st':
                    return redirect(url_for('student.student', user=encode))
                elif matched_role.name == 'cr':
                    return redirect(url_for('classrep.classrep', user=encode))
                elif matched_role.name == 'admin':
                    return redirect(
                        url_for(
                            'admin.dashboard',
                            user=encode
                        )
                    )
            else:
                msg = "ERROR: Role not found for this account!"
        else:
            msg = "Invalid username or password!"

    return render_template('user.html', msg=msg)

@auth_bp.route("/forgot_password", methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get('Username')
        email    = request.form.get('Email')

        user = User.query.filter_by(username=username).first()

        if not user:
            return render_template("frgtpass.html", msg="User not found")

        otp = _gen_otp()

        # store OTP
        user.otp = otp
        user.otp_created_at = datetime.utcnow()
        db.session.commit()
        try:
            send_otp_email(email, otp)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"OTP email failed: {e}")
            return render_template("frgtpass.html", msg="Failed to send OTP")

        return redirect(url_for('auth.verify_otp', email=email ,username=username))

    return render_template("frgtpass.html")
@auth_bp.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():

    email = request.args.get("email")
    username = request.args.get("username")

    if request.method == "POST":

        entered_otp = request.form.get("otp")

        user = User.query.filter_by(username=username).first()

        if not user or not user.otp:
            return "Invalid request"

        # OTP Expiry
        if datetime.utcnow() > user.otp_created_at + OTP_EXPIRES:
            return render_template(
                "verify_otp.html",
                msg="OTP expired",
                email=email,
                username=username
            )

        # Wrong OTP
        if user.otp != entered_otp:
            return render_template(
                "verify_otp.html",
                msg="Invalid OTP",
                email=email,
                username=username
            )

        # OTP Success
        user.otp = None
        user.otp_created_at = None

        db.session.commit()

        return redirect(
            url_for(
                'auth.reset_password',
                username=username
            )
        )

    return render_template(
        "verify_otp.html",
        email=email,
        username=username
    )

@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():

    username = request.args.get("username")

    user = User.query.filter_by(username=username).first()

    if not user:
        return redirect(url_for('auth.login'))

    if request.method == "POST":

        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if password != confirm:

            return render_template(
                "reset_password.html",
                msg="Passwords do not match",
                username=username
            )

        hashed = p.hash(password)

        user.password_hash = hashed

        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template(
        "reset_password.html",
        username=username
    )
@auth_bp.route("/make_admin", methods=["GET", "POST"])
def make_admin():
    admin_role = Role(                
        student_id=25022700,          
        name="admin"        
    )
    db.session.add(admin_role)
    db.session.commit()