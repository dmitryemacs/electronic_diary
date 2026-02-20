from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'assignments')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    role = db.Column(db.String(20), nullable=False)  # 'organizer' or 'participant'
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    # Relationships
    organized_programs = db.relationship('Program', backref='organizer', lazy=True)
    program_enrollments = db.relationship('Enrollment', backref='participant', lazy=True)
    grades = db.relationship('Grade', backref='participant', lazy=True, foreign_keys='Grade.participant_id')
    created_tasks = db.relationship('Task', backref='organizer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='program', lazy=True)
    tasks = db.relationship('Task', backref='program', lazy=True)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    category = db.Column(db.String(50), default='homework')  # homework, test, project, quiz, exam
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    submissions = db.relationship('TaskSubmission', backref='task', lazy=True, cascade='all, delete-orphan')
    feedback_list = db.relationship('TaskFeedback', backref='task', lazy=True, cascade='all, delete-orphan')

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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

class TaskSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(500))  # Path to uploaded file
    submission_text = db.Column(db.Text)  # Text submission
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_submitted = db.Column(db.Boolean, default=False)
    is_late = db.Column(db.Boolean, default=False)
    
    # Relationships
    participant = db.relationship('User', backref='task_submissions')
    
class TaskFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedback_text = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 star rating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participant = db.relationship('User', foreign_keys=[participant_id], backref='received_task_feedback')
    organizer = db.relationship('User', foreign_keys=[organizer_id], backref='given_task_feedback')

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
    role = SelectField('Роль', choices=[('organizer', 'Организатор'), ('participant', 'Участник')], validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

class TaskForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание')
    category = SelectField('Категория', choices=[
        ('homework', 'Домашнее задание'),
        ('test', 'Тест'),
        ('project', 'Проект'),
        ('quiz', 'Викторина'),
        ('exam', 'Экзамен')
    ])
    due_date = StringField('Срок выполнения (ГГГГ-ММ-ДД)')
    submit = SubmitField('Создать задачу')

class TaskSubmissionForm(FlaskForm):
    submission_text = TextAreaField('Текст ответа')
    submission_file = FileField('Загрузить файл', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'png', 'zip'], 'Допустимые форматы: PDF, DOC, DOCX, TXT, JPG, PNG, ZIP')
    ])
    submit = SubmitField('Отправить')

class TaskFeedbackForm(FlaskForm):
    feedback_text = TextAreaField('Комментарий обратной связи', validators=[DataRequired()])
    rating = IntegerField('Оценка (1-5)', validators=[DataRequired()])
    submit = SubmitField('Оставить отзыв')

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
            if user.role == 'organizer':
                return redirect(url_for('organizer_dashboard'))
            else:
                return redirect(url_for('participant_dashboard'))
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

@app.route('/organizer')
@login_required
def organizer_dashboard():
    if current_user.role != 'organizer':
        return redirect(url_for('home'))

    programs = Program.query.filter_by(organizer_id=current_user.id).all()
    return render_template('organizer_dashboard.html', programs=programs)

@app.route('/participant')
@login_required
def participant_dashboard():
    if current_user.role != 'participant':
        return redirect(url_for('home'))

    # Get all programs the participant is enrolled in
    enrollments = Enrollment.query.filter_by(participant_id=current_user.id).all()
    program_ids = [e.program_id for e in enrollments]
    programs = Program.query.filter(Program.id.in_(program_ids)).all()

    # Get all grades for the participant
    grades = Grade.query.filter_by(participant_id=current_user.id).all()

    return render_template('participant_dashboard.html', programs=programs, grades=grades)

@app.route('/create_program', methods=['GET', 'POST'])
@login_required
def create_program():
    if current_user.role != 'organizer':
        return redirect(url_for('home'))

    if request.method == 'POST':
        program_name = request.form['program_name']
        subject = request.form['subject']

        new_program = Program(
            name=program_name,
            subject=subject,
            organizer_id=current_user.id
        )
        db.session.add(new_program)
        db.session.commit()
        flash('Программа успешно создана!')
        return redirect(url_for('organizer_dashboard'))

    return render_template('create_program.html')

@app.route('/program/<int:program_id>')
@login_required
def view_program(program_id):
    program = Program.query.get_or_404(program_id)

    # Check if user has access to this program
    if current_user.role == 'organizer':
        if program.organizer_id != current_user.id:
            return redirect(url_for('home'))
    else:  # participant
        enrollment = Enrollment.query.filter_by(
            participant_id=current_user.id,
            program_id=program_id
        ).first()
        if not enrollment:
            return redirect(url_for('home'))

    tasks = Task.query.filter_by(program_id=program_id).all()
    return render_template('view_program.html', program=program, tasks=tasks)

@app.route('/create_task/<int:program_id>', methods=['GET', 'POST'])
@login_required
def create_task(program_id):
    program = Program.query.get_or_404(program_id)

    if current_user.role != 'organizer' or program.organizer_id != current_user.id:
        return redirect(url_for('home'))

    form = TaskForm()
    if form.validate_on_submit():
        try:
            due_date = datetime.strptime(form.due_date.data, '%Y-%m-%d') if form.due_date.data else None
        except ValueError:
            due_date = None

        task = Task(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            due_date=due_date,
            program_id=program_id,
            organizer_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()

        # Notify all participants in the program about the new task
        enrollments = Enrollment.query.filter_by(program_id=program_id).all()
        for enrollment in enrollments:
            create_notification(
                enrollment.participant_id,
                f'Создана новая задача: {form.title.data}',
                'task',
                task.id
            )

        flash('Задача успешно создана!')
        return redirect(url_for('view_program', program_id=program_id))

    return render_template('create_task.html', form=form, program=program)

@app.route('/grade_participants/<int:task_id>', methods=['GET', 'POST'])
@login_required
def grade_participants(task_id):
    task = Task.query.get_or_404(task_id)

    if current_user.role != 'organizer' or task.organizer_id != current_user.id:
        return redirect(url_for('home'))

    # Get all participants in this program
    enrollments = Enrollment.query.filter_by(program_id=task.program_id).all()
    participants = [e.participant for e in enrollments]

    if request.method == 'POST':
        for participant in participants:
            grade_value = request.form.get(f'grade_{participant.id}')
            if grade_value:
                # Update or create grade
                grade = Grade.query.filter_by(
                    task_id=task_id,
                    participant_id=participant.id
                ).first()

                if grade:
                    grade.value = int(grade_value)
                else:
                    grade = Grade(
                        value=int(grade_value),
                        task_id=task_id,
                        participant_id=participant.id,
                        organizer_id=current_user.id
                    )
                    db.session.add(grade)

        db.session.commit()

        # Notify participants about their grades
        for participant in participants:
            grade_value = request.form.get(f'grade_{participant.id}')
            if grade_value:
                create_notification(
                    participant.id,
                    f'Ваша оценка для задачи "{task.title}" была обновлена на {grade_value}',
                    'grade',
                    task.id
                )

        flash('Оценки успешно обновлены!')
        return redirect(url_for('view_program', program_id=task.program_id))

    # Get existing grades
    grades = Grade.query.filter_by(task_id=task_id).all()
    grade_dict = {grade.participant_id: grade.value for grade in grades}

    return render_template('grade_participants.html',
                         task=task,
                         participants=participants,
                         grades=grade_dict)

@app.route('/enroll_participant/<int:program_id>', methods=['POST'])
@login_required
def enroll_participant(program_id):
    program = Program.query.get_or_404(program_id)

    if current_user.role != 'organizer' or program.organizer_id != current_user.id:
        return redirect(url_for('home'))

    participant_id = request.form.get('participant_id')
    if participant_id:
        # Check if participant exists and is not already enrolled
        participant = User.query.filter_by(id=participant_id, role='participant').first()
        if participant:
            existing_enrollment = Enrollment.query.filter_by(
                participant_id=participant_id,
                program_id=program_id
            ).first()

            if not existing_enrollment:
                enrollment = Enrollment(
                    participant_id=participant_id,
                    program_id=program_id
                )
                db.session.add(enrollment)
                db.session.commit()
                flash('Участник успешно зачислен!')
            else:
                flash('Участник уже записан в эту программу')
        else:
            flash('Участник не найден')

    return redirect(url_for('view_program', program_id=program_id))

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

# New routes for extended task system
@app.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    if current_user.role == 'organizer':
        if task.organizer_id != current_user.id:
            return redirect(url_for('home'))
    else:  # participant
        enrollment = Enrollment.query.filter_by(
            participant_id=current_user.id,
            program_id=task.program_id
        ).first()
        if not enrollment:
            return redirect(url_for('home'))
    
    # Get submission if participant
    submission = None
    if current_user.role == 'participant':
        submission = TaskSubmission.query.filter_by(
            task_id=task_id,
            participant_id=current_user.id
        ).first()
    
    # Get feedback
    feedback = None
    if current_user.role == 'participant':
        feedback = TaskFeedback.query.filter_by(
            task_id=task_id,
            participant_id=current_user.id
        ).first()
    
    form = TaskSubmissionForm()
    return render_template('task_detail.html', 
                         task=task, 
                         submission=submission,
                         feedback=feedback,
                         form=form)

@app.route('/task/<int:task_id>/submit', methods=['POST'])
@login_required
def submit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if current_user.role != 'participant':
        return redirect(url_for('home'))
    
    # Check if participant is enrolled in the program
    enrollment = Enrollment.query.filter_by(
        participant_id=current_user.id,
        program_id=task.program_id
    ).first()
    if not enrollment:
        return redirect(url_for('home'))
    
    # Check if already submitted
    existing_submission = TaskSubmission.query.filter_by(
        task_id=task_id,
        participant_id=current_user.id
    ).first()
    
    # Handle file upload
    file_path = None
    if 'submission_file' in request.files:
        file = request.files['submission_file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = f"uploads/assignments/{filename}"
    
    submission_text = request.form.get('submission_text', '')
    
    # Check if late
    is_late = False
    if task.due_date and datetime.utcnow() > task.due_date:
        is_late = True
    
    if existing_submission:
        existing_submission.submission_text = submission_text
        existing_submission.file_path = file_path or existing_submission.file_path
        existing_submission.is_submitted = True
        existing_submission.is_late = is_late
        existing_submission.submitted_at = datetime.utcnow()
    else:
        submission = TaskSubmission(
            task_id=task_id,
            participant_id=current_user.id,
            submission_text=submission_text,
            file_path=file_path,
            is_submitted=True,
            is_late=is_late
        )
        db.session.add(submission)
    
    db.session.commit()
    
    # Notify organizer
    create_notification(
        task.organizer_id,
        f'{current_user.first_name} {current_user.last_name} отправил ответ на задачу "{task.title}"',
        'submission',
        task_id
    )
    
    flash('Задача успешно отправлена!')
    return redirect(url_for('view_task', task_id=task_id))

@app.route('/task/<int:task_id>/submissions')
@login_required
def view_task_submissions(task_id):
    task = Task.query.get_or_404(task_id)
    
    if current_user.role != 'organizer' or task.organizer_id != current_user.id:
        return redirect(url_for('home'))
    
    # Get all submissions for this task
    submissions = TaskSubmission.query.filter_by(
        task_id=task_id
    ).all()
    
    # Get all participants in the program
    enrollments = Enrollment.query.filter_by(program_id=task.program_id).all()
    all_participants = {e.participant_id: e.participant for e in enrollments}
    
    return render_template('task_submissions.html',
                         task=task,
                         submissions=submissions,
                         all_participants=all_participants)

@app.route('/task_feedback/<int:task_id>/<int:participant_id>', methods=['GET', 'POST'])
@login_required
def add_task_feedback(task_id, participant_id):
    task = Task.query.get_or_404(task_id)
    participant = User.query.get_or_404(participant_id)
    
    if current_user.role != 'organizer' or task.organizer_id != current_user.id:
        return redirect(url_for('home'))
    
    # Get existing submission
    submission = TaskSubmission.query.filter_by(
        task_id=task_id,
        participant_id=participant_id
    ).first_or_404()
    
    # Get existing feedback or create new
    feedback = TaskFeedback.query.filter_by(
        task_id=task_id,
        participant_id=participant_id
    ).first()
    
    form = TaskFeedbackForm()
    
    if form.validate_on_submit():
        if feedback:
            feedback.feedback_text = form.feedback_text.data
            feedback.rating = form.rating.data
            feedback.updated_at = datetime.utcnow()
        else:
            feedback = TaskFeedback(
                task_id=task_id,
                participant_id=participant_id,
                organizer_id=current_user.id,
                feedback_text=form.feedback_text.data,
                rating=form.rating.data
            )
            db.session.add(feedback)
        
        db.session.commit()
        
        # Notify participant
        create_notification(
            participant_id,
            f'Организатор оставил отзыв на вашу задачу "{task.title}"',
            'feedback',
            task_id
        )
        
        flash('Отзыв успешно сохранен!')
        return redirect(url_for('view_task_submissions', task_id=task_id))
    
    if feedback:
        form.feedback_text.data = feedback.feedback_text
        form.rating.data = feedback.rating
    
    return render_template('add_task_feedback.html',
                         task=task,
                         participant=participant,
                         submission=submission,
                         form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True)