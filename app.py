from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    # Relationships
    teacher_classes = db.relationship('Class', backref='teacher', lazy=True)
    student_classes = db.relationship('StudentClass', backref='student', lazy=True)
    grades = db.relationship('Grade', backref='student', lazy=True, foreign_keys='Grade.student_id')
    assignments = db.relationship('Assignment', backref='teacher', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    students = db.relationship('StudentClass', backref='class_obj', lazy=True)
    assignments = db.relationship('Assignment', backref='class_obj', lazy=True)

class StudentClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_type = db.Column(db.String(50), nullable=False)  # e.g., 'assignment', 'grade', 'system'
    reference_id = db.Column(db.Integer)  # ID of related object (assignment_id, grade_id, etc.)

    # Relationship
    user = db.relationship('User', backref='notifications')

# Forms
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    role = SelectField('Роль', choices=[('teacher', 'Учитель'), ('student', 'Студент')], validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

class AssignmentForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = StringField('Описание')
    due_date = StringField('Срок выполнения (ГГГГ-ММ-ДД)')
    submit = SubmitField('Создать задание')

class GradeForm(FlaskForm):
    value = StringField('Оценка', validators=[DataRequired()])
    submit = SubmitField('Сохранить')

# Helper function to create notifications
def create_notification(user_id, message, notification_type, reference_id=None):
    notification = Notification(
        user_id=user_id,
        message=message,
        notification_type=notification_type,
        reference_id=reference_id
    )
    db.session.add(notification)
    db.session.commit()

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Имя пользователя уже существует. Пожалуйста, выберите другое имя пользователя.')
            return render_template('register.html', form=form)

        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email уже существует. Пожалуйста, используйте другой адрес email.')
            return render_template('register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Пожалуйста, войдите в систему.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/teacher')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        return redirect(url_for('home'))

    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher_dashboard.html', classes=classes)

@app.route('/student')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get all classes the student is enrolled in
    student_classes = StudentClass.query.filter_by(student_id=current_user.id).all()
    class_ids = [sc.class_id for sc in student_classes]
    classes = Class.query.filter(Class.id.in_(class_ids)).all()

    # Get all grades for the student
    grades = Grade.query.filter_by(student_id=current_user.id).all()

    return render_template('student_dashboard.html', classes=classes, grades=grades)

@app.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_class():
    if current_user.role != 'teacher':
        return redirect(url_for('home'))

    if request.method == 'POST':
        class_name = request.form['class_name']
        subject = request.form['subject']

        new_class = Class(
            name=class_name,
            subject=subject,
            teacher_id=current_user.id
        )
        db.session.add(new_class)
        db.session.commit()
        flash('Класс успешно создан!')
        return redirect(url_for('teacher_dashboard'))

    return render_template('create_class.html')

@app.route('/class/<int:class_id>')
@login_required
def view_class(class_id):
    class_obj = Class.query.get_or_404(class_id)

    # Check if user has access to this class
    if current_user.role == 'teacher':
        if class_obj.teacher_id != current_user.id:
            return redirect(url_for('home'))
    else:  # student
        student_class = StudentClass.query.filter_by(
            student_id=current_user.id,
            class_id=class_id
        ).first()
        if not student_class:
            return redirect(url_for('home'))

    assignments = Assignment.query.filter_by(class_id=class_id).all()
    return render_template('view_class.html', class_obj=class_obj, assignments=assignments)

@app.route('/create_assignment/<int:class_id>', methods=['GET', 'POST'])
@login_required
def create_assignment(class_id):
    class_obj = Class.query.get_or_404(class_id)

    if current_user.role != 'teacher' or class_obj.teacher_id != current_user.id:
        return redirect(url_for('home'))

    form = AssignmentForm()
    if form.validate_on_submit():
        try:
            due_date = datetime.strptime(form.due_date.data, '%Y-%m-%d') if form.due_date.data else None
        except ValueError:
            due_date = None

        assignment = Assignment(
            title=form.title.data,
            description=form.description.data,
            due_date=due_date,
            class_id=class_id,
            teacher_id=current_user.id
        )
        db.session.add(assignment)
        db.session.commit()

        # Notify all students in the class about the new assignment
        student_classes = StudentClass.query.filter_by(class_id=class_id).all()
        for student_class in student_classes:
            create_notification(
                student_class.student_id,
                f'Создано новое задание: {form.title.data}',
                'assignment',
                assignment.id
            )

        flash('Задание успешно создано!')
        return redirect(url_for('view_class', class_id=class_id))

    return render_template('create_assignment.html', form=form, class_obj=class_obj)

@app.route('/grade_students/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def grade_students(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    if current_user.role != 'teacher' or assignment.teacher_id != current_user.id:
        return redirect(url_for('home'))

    # Get all students in this class
    student_classes = StudentClass.query.filter_by(class_id=assignment.class_id).all()
    students = [sc.student for sc in student_classes]

    if request.method == 'POST':
        for student in students:
            grade_value = request.form.get(f'grade_{student.id}')
            if grade_value:
                # Update or create grade
                grade = Grade.query.filter_by(
                    assignment_id=assignment_id,
                    student_id=student.id
                ).first()

                if grade:
                    grade.value = int(grade_value)
                else:
                    grade = Grade(
                        value=int(grade_value),
                        assignment_id=assignment_id,
                        student_id=student.id,
                        teacher_id=current_user.id
                    )
                    db.session.add(grade)

        db.session.commit()

        # Notify students about their grades
        for student in students:
            grade_value = request.form.get(f'grade_{student.id}')
            if grade_value:
                create_notification(
                    student.id,
                    f'Ваша оценка для задания "{assignment.title}" была обновлена на {grade_value}',
                    'grade',
                    assignment.id
                )

        flash('Оценки успешно обновлены!')
        return redirect(url_for('view_class', class_id=assignment.class_id))

    # Get existing grades
    grades = Grade.query.filter_by(assignment_id=assignment_id).all()
    grade_dict = {grade.student_id: grade.value for grade in grades}

    return render_template('grade_students.html',
                         assignment=assignment,
                         students=students,
                         grades=grade_dict)

@app.route('/enroll_student/<int:class_id>', methods=['POST'])
@login_required
def enroll_student(class_id):
    class_obj = Class.query.get_or_404(class_id)

    if current_user.role != 'teacher' or class_obj.teacher_id != current_user.id:
        return redirect(url_for('home'))

    student_id = request.form.get('student_id')
    if student_id:
        # Check if student exists and is not already enrolled
        student = User.query.filter_by(id=student_id, role='student').first()
        if student:
            existing_enrollment = StudentClass.query.filter_by(
                student_id=student_id,
                class_id=class_id
            ).first()

            if not existing_enrollment:
                enrollment = StudentClass(
                    student_id=student_id,
                    class_id=class_id
                )
                db.session.add(enrollment)
                db.session.commit()
                flash('Студент успешно зачислен!')
            else:
                flash('Студент уже записан в этот класс')
        else:
            flash('Студент не найден')

    return redirect(url_for('view_class', class_id=class_id))

@app.route('/notifications')
@login_required
def view_notifications():
    # Get all notifications for current user, ordered by created_at descending
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()

    # Mark notifications as read when viewed
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in unread_notifications:
        notification.is_read = True
    db.session.commit()

    return render_template('notifications.html', notifications=notifications)

@app.route('/notifications/unread_count')
@login_required
def get_unread_notification_count():
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return {'unread_count': unread_count}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)