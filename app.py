import os
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import func
from models import db, User, FileHistory, Feedback
from utils import (convert_pdf_to_excel, convert_pdf_to_word, merge_pdfs, 
                    convert_video_to_audio, convert_image_to_pdf, protect_pdf)

app = Flask(__name__)

# --- Configurations ---
app.secret_key = os.environ.get('SECRET_KEY', 'pro_converter_secret_2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('temp', 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join('temp', 'outputs')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 
app.config.update(SESSION_COOKIE_HTTPONLY=True, PERMANENT_SESSION_LIFETIME=timedelta(days=7))

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Create folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# --- UTILS ---
def cleanup_temp_files():
    folders = [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]
    cutoff = datetime.utcnow() - timedelta(hours=1)
    for folder in folders:
        for filename in os.listdir(folder):
            path = os.path.join(folder, filename)
            try:
                if datetime.utcfromtimestamp(os.path.getmtime(path)) < cutoff:
                    if os.path.isfile(path): os.remove(path)
            except: continue

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'mp4', 'jpg', 'png', 'xlsx', 'mp3'}

def save_history(file_name, operation, path):
    db.session.add(FileHistory(user_id=current_user.id, file_name=file_name, operation_type=operation, file_path=path))
    db.session.commit()

def process_file(req, func, ext, operation_name, extra_args=None):
    file = req.files.get('file')
    if not file or file.filename == '' or not allowed_file(file.filename):
        flash("Invalid or missing file!", "danger")
        return redirect(url_for('dashboard'))
    
    unique_id = str(uuid.uuid4())
    in_p = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{file.filename}")
    out_p = os.path.join(app.config['OUTPUT_FOLDER'], f"{unique_id}.{ext}")
    
    file.save(in_p)
    try:
        if extra_args: func(in_p, out_p, *extra_args)
        else: func(in_p, out_p)
        save_history(file.filename, operation_name, out_p)
        return send_file(out_p, as_attachment=True)
    except Exception as e:
        flash(f"Conversion failed: {str(e)}", "danger")
        return redirect(url_for('dashboard'))
    finally:
        if os.path.exists(in_p): os.remove(in_p)

# --- ROUTES ---
@app.route('/')
def index():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    feedbacks = Feedback.query.order_by(Feedback.id.desc()).limit(6).all()
    avg_rating = db.session.query(func.avg(Feedback.rating)).scalar() or 0
    return render_template('index.html', feedbacks=feedbacks, avg_rating=round(avg_rating, 1))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        flash("Invalid credentials!", "danger")
    return render_template('login.html', is_register=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash("Username taken!", "danger")
        else:
            new_user = User(username=request.form.get('username'), email=request.form.get('email'))
            new_user.set_password(request.form.get('password'))
            db.session.add(new_user); db.session.commit()
            return redirect(url_for('login'))
    return render_template('login.html', is_register=True)

@app.route('/dashboard')
@login_required
def dashboard():
    cleanup_temp_files()
    history = FileHistory.query.filter_by(user_id=current_user.id).order_by(FileHistory.timestamp.desc()).limit(10).all()
    avg_rating = db.session.query(func.avg(Feedback.rating)).scalar() or 0
    total_feedbacks = Feedback.query.count()
    return render_template('dashboard.html', history=history, avg_rating=round(avg_rating, 1), total_feedbacks=total_feedbacks)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- CONVERSION ROUTES ---
@app.route('/convert-pdf-to-excel', methods=['POST'])
@login_required
def h_excel(): return process_file(request, convert_pdf_to_excel, "xlsx", "PDF_TO_EXCEL")

@app.route('/convert-pdf-to-word', methods=['POST'])
@login_required
def h_word(): return process_file(request, convert_pdf_to_word, "docx", "PDF_TO_WORD")

@app.route('/video-to-audio', methods=['POST'])
@login_required
def h_video(): return process_file(request, convert_video_to_audio, "mp3", "VIDEO_TO_AUDIO")

@app.route('/image-to-pdf', methods=['POST'])
@login_required
def h_img(): return process_file(request, convert_image_to_pdf, "pdf", "IMAGE_TO_PDF")

@app.route('/protect-pdf', methods=['POST'])
@login_required
def h_protect():
    pwd = request.form.get('password')
    if not pwd: flash("Password required!", "warning"); return redirect(url_for('dashboard'))
    return process_file(request, protect_pdf, "pdf", "PROTECT_PDF", extra_args=[pwd])

@app.route('/merge-pdfs', methods=['POST'])
@login_required
def h_merge():
    files = request.files.getlist('files')
    if not files or files[0].filename == '': return redirect(url_for('dashboard'))
    unique_id = str(uuid.uuid4())
    paths = []
    for f in files:
        p = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{f.filename}")
        f.save(p); paths.append(p)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{unique_id}_merged.pdf")
    try:
        merge_pdfs(paths, out)
        save_history("Merged_Document.pdf", "MERGE_PDFS", out)
        return send_file(out, as_attachment=True)
    finally:
        for p in paths:
            if os.path.exists(p): os.remove(p)

@app.route('/submit-feedback', methods=['POST'])
@login_required
def submit_feedback():
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    if rating and comment:
        db.session.add(Feedback(user_id=current_user.id, rating=int(rating), comment=comment))
        db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)