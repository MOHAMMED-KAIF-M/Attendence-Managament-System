from flask import Flask, render_template, request, redirect, session
from models import db, Student, Attendance
from auth import auth_bp
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'attendance_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# -------------------------
# Dashboard: show students
# -------------------------
@app.route('/')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    students = Student.query.all()
    return render_template('dashboard.html', students=students)

# -------------------------
# Register new student
# -------------------------
@app.route('/register_student', methods=['POST'])
def register_student():
    if 'user' not in session:
        return redirect('/login')

    name = request.form.get('name')
    usn = request.form.get('usn')
    branch = request.form.get('branch')

    if not name or not usn or not branch:
        return "All fields are required"

    # Check for duplicate USN
    if Student.query.filter_by(usn=usn).first():
        return "Student with this USN already exists"

    student = Student(name=name, usn=usn, branch=branch)
    db.session.add(student)
    db.session.commit()

    return redirect('/')

# -------------------------
# Mark attendance
# -------------------------
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user' not in session:
        return redirect('/login')

    today = date.today().strftime("%Y-%m-%d")

    for student_id, status in request.form.items():
        try:
            attendance = Attendance(
                student_id=int(student_id),
                date=today,
                status=status
            )
            db.session.add(attendance)
        except ValueError:
            continue  # skip invalid IDs

    db.session.commit()
    return redirect('/')

# -------------------------
# View attendance records
# -------------------------
@app.route('/attendance_records')
def attendance_records():
    if 'user' not in session:
        return redirect('/login')

    records = db.session.query(
        Attendance.id,  # Include ID for deletion
        Attendance.date,
        Attendance.status,
        Student.name,
        Student.usn,
        Student.branch
    ).join(Student, Attendance.student_id == Student.id).all()

    return render_template('attendance_records.html', records=records)

# -------------------------
# Delete student and related attendance
# -------------------------
@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'user' not in session:
        return redirect('/login')

    student = Student.query.get(student_id)
    if student:
        # Delete all attendance records for this student
        Attendance.query.filter_by(student_id=student.id).delete()
        db.session.delete(student)
        db.session.commit()

    return redirect('/')

# -------------------------
# Delete individual attendance record (optional)
# -------------------------
@app.route('/delete_attendance/<int:attendance_id>', methods=['POST'])
def delete_attendance(attendance_id):
    if 'user' not in session:
        return redirect('/login')

    record = Attendance.query.get(attendance_id)
    if record:
        db.session.delete(record)
        db.session.commit()

    return redirect('/attendance_records')

# -------------------------
# Run the app
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
