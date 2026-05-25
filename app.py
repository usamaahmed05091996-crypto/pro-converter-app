import os
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from models import db, User, FileHistory
from utils import (convert_pdf_to_excel, convert_pdf_to_word, merge_pdfs, 
                   convert_video_to_audio, convert_image_to_pdf, protect_pdf)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = "pro_converter_secret_2026"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = os.path.join('temp', 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join('temp', 'outputs')

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# --- HELPERS ---
def save_history(file_name, operation, path):
    new_record = FileHistory(user_id=current_user.id, file_name=file_name, operation_type=operation, file_path=path)
    db.session.add(new_record)
    db.session.commit()

def process_file(req, func, ext, operation_name, extra_args=None):
    file = req.files.get('file')
    if not file or file.filename == '':
        flash("No file selected!", "danger")
        return redirect(url_for('dashboard'))
    
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{file.filename}")
    output_filename = f"{unique_id}.{ext}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    file.save(input_path)
    try:
        if extra_args: func(input_path, output_path, *extra_args)
        else: func(input_path, output_path)
        
        save_history(file.filename, operation_name, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('dashboard'))
    finally:
        if os.path.exists(input_path): os.remove(input_path)

# --- ROUTES ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid Credentials!", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_user = User(username=request.form.get('username'), email=request.form.get('email'))
        new_user.set_password(request.form.get('password'))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('login.html', is_register=True)

@app.route('/dashboard')
@login_required
def dashboard():
    # History filter logic: Sirf last 1 hour ka record
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    history = FileHistory.query.filter_by(user_id=current_user.id)\
        .filter(FileHistory.timestamp >= one_hour_ago)\
        .order_by(FileHistory.timestamp.desc()).all()
    return render_template('dashboard.html', history=history)

# Conversions (Routes continue...)
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
    return process_file(request, protect_pdf, "pdf", "PROTECT_PDF", extra_args=[request.form.get('password')])

@app.route('/merge-pdfs', methods=['POST'])
@login_required
def h_merge():
    files = request.files.getlist('files')
    unique_id = str(uuid.uuid4())
    paths = []
    for f in files:
        p = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{f.filename}")
        f.save(p)
        paths.append(p)
    out = os.path.join(app.config['OUTPUT_FOLDER'], f"{unique_id}_merged.pdf")
    merge_pdfs(paths, out)
    save_history("Merged_Document.pdf", "MERGE_PDFS", out)
    return send_file(out, as_attachment=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)