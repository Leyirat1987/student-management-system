from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for, session
import os
import json
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import pandas as pd
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'utis_pdf_system_secret_key_2024_azerbaijan'

# Admin credentials - Production-da dəyişdirin!
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'  # Production-da güçlü parol istifadə edin!

# Database configuration - Production vs Development
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Production - PostgreSQL
    import psycopg2
    import psycopg2.extras
    DATABASE = DATABASE_URL
else:
    # Development - SQLite
    DATABASE = 'students.db'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size for bulk uploads

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db_connection():
    """Get database connection - PostgreSQL or SQLite"""
    if DATABASE_URL:
        # PostgreSQL connection
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn, True  # Return connection and is_postgres flag
    else:
        # SQLite connection
        conn = sqlite3.connect(DATABASE)
        return conn, False

def is_admin_logged_in():
    """Check if admin is logged in"""
    return session.get('admin_logged_in', False)

def login_required(f):
    """Decorator to require admin login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin_logged_in():
            flash('Admin panelinə giriş üçün daxil olun!', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_excel_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXCEL_EXTENSIONS

def init_db():
    """Initialize database tables"""
    conn, is_postgres = get_db_connection()
    
    if is_postgres:
        c = conn.cursor()
        # PostgreSQL table creation
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                utis_code VARCHAR(20) UNIQUE NOT NULL,
                student_name VARCHAR(255) NOT NULL,
                fin_code VARCHAR(7) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS pdfs (
                id SERIAL PRIMARY KEY,
                utis_code VARCHAR(20) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255),
                file_path TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        c = conn.cursor()
        # SQLite table creation (existing code)
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                utis_code TEXT UNIQUE NOT NULL,
                student_name TEXT NOT NULL,
                fin_code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS pdfs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                utis_code TEXT NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT,
                file_path TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def get_student_by_utis(utis_code):
    """Get student information by UTIS code"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE utis_code = ?', (utis_code,))
    student = c.fetchone()
    conn.close()
    return student

def get_pdfs_by_utis(utis_code):
    """Get all PDFs for a UTIS code directly"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM pdfs WHERE utis_code = ?', (utis_code,))
    pdfs = c.fetchall()
    conn.close()
    return pdfs

def extract_utis_from_filename(filename):
    """Extract UTIS code from PDF filename"""
    # Fayl adından UTİS kodunu çıxarır
    # Məsələn: "UTIS123456.pdf" -> "UTIS123456"
    name_without_ext = os.path.splitext(filename)[0]
    # UTİS kodu adətən UTIS ilə başlayır
    if name_without_ext.upper().startswith('UTIS'):
        return name_without_ext.upper()
    return name_without_ext.upper()

@app.route('/')
def index():
    """Main page for FIN code input (first step)"""
    return render_template('index.html')

@app.route('/verify_fin', methods=['POST'])
def verify_fin():
    """Verify FIN code and proceed to UTIS input"""
    fin_code = request.form.get('fin_code', '').strip().upper()
    
    if not fin_code:
        flash('FİN kodunu daxil edin!', 'error')
        return redirect(url_for('index'))
    
    # Check if FIN code exists in database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE fin_code = ?', (fin_code,))
    student = c.fetchone()
    conn.close()
    
    if student:
        # Store FIN code in session for verification
        session['verified_fin'] = fin_code
        session['student_info'] = {
            'id': student[0],
            'utis_code': student[1],
            'name': student[2],
            'fin_code': student[3]
        }
        flash(f'Salam {student[2] or "Şagird"}! İndi UTİS kodunuzu daxil edin.', 'success')
        return redirect(url_for('enter_utis'))
    else:
        flash('Bu FİN kodu sistemdə qeydiyyatda deyil! Əlaqə saxlayın.', 'error')
        return redirect(url_for('index'))

@app.route('/enter_utis')
def enter_utis():
    """Page for UTIS code input (second step)"""
    if 'verified_fin' not in session:
        flash('Əvvəlcə FİN kodunu daxil edin!', 'error')
        return redirect(url_for('index'))
    
    student_info = session.get('student_info', {})
    return render_template('enter_utis.html', student_info=student_info)

@app.route('/search', methods=['POST'])
def search_student():
    """Search for PDFs by UTIS code (requires FIN verification)"""
    # Check if FIN is verified
    if 'verified_fin' not in session:
        flash('Əvvəlcə FİN kodunu daxil edin!', 'error')
        return redirect(url_for('index'))
    
    utis_code = request.form.get('utis_code', '').strip().upper()
    
    if not utis_code:
        flash('UTİS kodu daxil edin!', 'error')
        return redirect(url_for('enter_utis'))
    
    # Get student info from session
    student_info = session.get('student_info', {})
    
    # Additional security: Check if entered UTIS matches the student's UTIS
    if student_info.get('utis_code') != utis_code:
        flash('Daxil etdiyiniz UTİS kodu FİN kodunuzla uyğun gəlmir!', 'error')
        return redirect(url_for('enter_utis'))
    
    # PDF-ləri birbaşa UTİS kodu ilə tap
    pdfs = get_pdfs_by_utis(utis_code)
    
    if not pdfs:
        flash('Bu UTİS kodu üçün PDF fayl tapılmadı!', 'error')
        return redirect(url_for('enter_utis'))
    
    # Şagird məlumatlarını da əldə et
    student = get_student_by_utis(utis_code)
    
    return render_template('student_pdfs.html', 
                         student=student, 
                         pdfs=pdfs, 
                         utis_code=utis_code,
                         student_info=student_info)

@app.route('/logout_student')
def logout_student():
    """Logout student and clear session"""
    session.pop('verified_fin', None)
    session.pop('student_info', None)
    flash('Çıxış edildi!', 'info')
    return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Uğurla daxil oldunuz!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('İstifadəçi adı və ya parol səhvdir!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Sistemdən çıxış etdiniz!', 'info')
    return redirect(url_for('index'))

@app.route('/admin_panel_secret_2024')
def admin_secret():
    """Secret admin access route - redirects to login"""
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin():
    """Admin panel for managing students and PDFs"""
    conn, is_postgres = get_db_connection()
    c = conn.cursor()
    
    # Bütün şagirdləri al
    c.execute('SELECT * FROM students ORDER BY created_at DESC')
    students = c.fetchall()
    
    # PDF statistikası
    c.execute('SELECT COUNT(*) FROM pdfs')
    total_pdfs = c.fetchone()[0]
    
    # UTİS kodları olan PDF-lər
    c.execute('SELECT DISTINCT utis_code FROM pdfs')
    unique_utis_codes = c.fetchall()
    
    # Validation: Şagird və PDF sayı uyğunluğu
    student_count = len(students)
    pdf_count = total_pdfs
    unique_pdf_count = len(unique_utis_codes)
    
    # PDF olmayan şagirdlər
    c.execute('''
        SELECT s.utis_code, s.student_name 
        FROM students s 
        LEFT JOIN pdfs p ON s.utis_code = p.utis_code 
        WHERE p.utis_code IS NULL
    ''')
    students_without_pdfs = c.fetchall()
    
    # Şagirdi olmayan PDF-lər  
    c.execute('''
        SELECT p.utis_code, p.filename 
        FROM pdfs p 
        LEFT JOIN students s ON p.utis_code = s.utis_code 
        WHERE s.utis_code IS NULL
    ''')
    pdfs_without_students = c.fetchall()
    
    # PDF olmayan şagirdlərin ID-lərini al (rəngli göstərmək üçün)
    c.execute('''
        SELECT s.id 
        FROM students s 
        LEFT JOIN pdfs p ON s.utis_code = p.utis_code 
        WHERE p.utis_code IS NULL
    ''')
    students_without_pdfs_ids = [row[0] for row in c.fetchall()]
    
    # Şagirdi olmayan PDF-lərin ID-lərini al (rəngli göstərmək üçün)
    c.execute('''
        SELECT p.id 
        FROM pdfs p 
        LEFT JOIN students s ON p.utis_code = s.utis_code 
        WHERE s.utis_code IS NULL
    ''')
    pdfs_without_students_ids = [row[0] for row in c.fetchall()]
    
    # Validation mesajları
    validation_status = {
        'student_count': student_count,
        'pdf_count': pdf_count,
        'unique_pdf_count': unique_pdf_count,
        'students_without_pdfs': students_without_pdfs,
        'pdfs_without_students': pdfs_without_students,
        'students_without_pdfs_ids': students_without_pdfs_ids,
        'pdfs_without_students_ids': pdfs_without_students_ids,
        'is_balanced': student_count == unique_pdf_count,
        'coverage_percentage': round((unique_pdf_count / student_count * 100) if student_count > 0 else 0, 1)
    }
    
    # Bütün PDF faylları al (fayl həcmi ilə birlikdə)
    c.execute('SELECT * FROM pdfs ORDER BY upload_date DESC')
    pdf_files_raw = c.fetchall()
    
    # Fayl həcmini əlavə et
    pdf_files = []
    for pdf in pdf_files_raw:
        pdf_data = list(pdf)
        try:
            # Fayl həcmini hesabla
            file_path_index = 4 if not is_postgres else 4  # file_path column index
            if len(pdf) > file_path_index and pdf[file_path_index] and os.path.exists(pdf[file_path_index]):
                file_size = os.path.getsize(pdf[file_path_index])
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024*1024:
                    size_str = f"{file_size/1024:.1f} KB"
                else:
                    size_str = f"{file_size/(1024*1024):.1f} MB"
                pdf_data.append(size_str)
            else:
                pdf_data.append("Fayl tapılmadı")
        except:
            pdf_data.append("N/A")
        
        pdf_files.append(pdf_data)
    
    conn.close()
    return render_template('admin.html', 
                         students=students, 
                         total_pdfs=total_pdfs,
                         unique_utis_codes=len(unique_utis_codes),
                         pdf_files=pdf_files,
                         validation_status=validation_status)

@app.route('/bulk_upload_pdfs', methods=['POST'])
@login_required
def bulk_upload_pdfs():
    """Upload multiple PDFs at once"""
    if 'files' not in request.files:
        flash('Fayl seçilməyib!', 'error')
        return redirect(url_for('admin'))
    
    files = request.files.getlist('files')
    
    if not files or all(f.filename == '' for f in files):
        flash('PDF faylları seçin!', 'error')
        return redirect(url_for('admin'))
    
    uploaded_count = 0
    failed_count = 0
    
    for file in files:
        if file and allowed_file(file.filename):
            try:
                # Fayl adından UTİS kodunu çıxar
                utis_code = extract_utis_from_filename(file.filename)
                
                # Fayl adını təhlükəsiz et
                original_filename = file.filename
                filename = secure_filename(file.filename)
                
                # Unikal fayl adı yarat
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                new_filename = f"{utis_code}_{timestamp}_{filename}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                file.save(file_path)
                
                # Verilənlər bazasına əlavə et
                conn = sqlite3.connect(DATABASE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO pdfs (utis_code, filename, original_filename, file_path)
                    VALUES (?, ?, ?, ?)
                ''', (utis_code, new_filename, original_filename, file_path))
                conn.commit()
                conn.close()
                
                uploaded_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Fayl yükləmə səhvi: {file.filename} - {str(e)}")
        else:
            failed_count += 1
    
    if uploaded_count > 0:
        flash(f'{uploaded_count} PDF uğurla yükləndi!', 'success')
    if failed_count > 0:
        flash(f'{failed_count} PDF yüklənə bilmədi!', 'error')
    
    return redirect(url_for('admin'))

@app.route('/upload_excel_students', methods=['POST'])
@login_required
def upload_excel_students():
    """Upload students from Excel file"""
    if 'excel_file' not in request.files:
        flash('Excel fayl seçilməyib!', 'error')
        return redirect(url_for('admin'))
    
    file = request.files['excel_file']
    
    if file.filename == '':
        flash('Excel fayl seçin!', 'error')
        return redirect(url_for('admin'))
    
    if file and allowed_excel_file(file.filename):
        try:
            # Excel faylı oxu
            df = pd.read_excel(file)
            
            # Lazımi sütunları yoxla
            required_columns = ['utis_code', 'student_name', 'fin_code']
            if not all(col in df.columns for col in required_columns):
                flash('Excel faylında lazımi sütunlar yoxdur: utis_code, student_name, fin_code', 'error')
                return redirect(url_for('admin'))
            
            added_count = 0
            failed_count = 0
            
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            
            for _, row in df.iterrows():
                try:
                    utis_code = str(row['utis_code']).strip().upper()
                    student_name = str(row['student_name']).strip()
                    fin_code = str(row['fin_code']).strip()
                    
                    if utis_code and student_name and fin_code:
                        c.execute('''
                            INSERT OR REPLACE INTO students (utis_code, student_name, fin_code)
                            VALUES (?, ?, ?)
                        ''', (utis_code, student_name, fin_code))
                        added_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Şagird əlavə etmə səhvi: {str(e)}")
            
            conn.commit()
            conn.close()
            
            if added_count > 0:
                flash(f'{added_count} şagird uğurla əlavə edildi/yeniləndi!', 'success')
            if failed_count > 0:
                flash(f'{failed_count} şagird əlavə edilə bilmədi!', 'error')
                
        except Exception as e:
            flash(f'Excel fayl oxunmadı: {str(e)}', 'error')
    else:
        flash('Yalnız Excel faylları (.xlsx, .xls) qəbul edilir!', 'error')
    
    return redirect(url_for('admin'))

@app.route('/download/<int:pdf_id>')
def download_pdf(pdf_id):
    """Download a PDF file"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM pdfs WHERE id = ?', (pdf_id,))
    pdf = c.fetchone()
    conn.close()
    
    if pdf and os.path.exists(pdf[4]):  # pdf[4] is file_path
        return send_file(pdf[4], as_attachment=True, download_name=pdf[3])  # pdf[3] is original_filename
    else:
        flash('Fayl tapılmadı!', 'error')
        return redirect(url_for('index'))

@app.route('/preview/<int:pdf_id>')
def preview_pdf(pdf_id):
    """Stream PDF file for preview"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM pdfs WHERE id = ?', (pdf_id,))
    pdf = c.fetchone()
    conn.close()
    
    if pdf and os.path.exists(pdf[4]):  # pdf[4] is file_path
        # PDF-i önizləmə üçün inline göstər
        return send_file(pdf[4], 
                        mimetype='application/pdf',
                        as_attachment=False,
                        download_name=pdf[3])
    else:
        return "PDF fayl tapılmadı", 404

@app.route('/delete_pdf/<int:pdf_id>')
@login_required
def delete_pdf(pdf_id):
    """Delete a PDF file"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM pdfs WHERE id = ?', (pdf_id,))
    pdf = c.fetchone()
    
    if pdf:
        # Delete file from disk
        if os.path.exists(pdf[4]):
            os.remove(pdf[4])
        
        # Delete from database
        c.execute('DELETE FROM pdfs WHERE id = ?', (pdf_id,))
        conn.commit()
        flash('PDF silindi!', 'success')
    
    conn.close()
    return redirect(url_for('admin'))

@app.route('/bulk_delete_pdfs', methods=['POST'])
@login_required
def bulk_delete_pdfs():
    """Delete multiple PDF files at once"""
    pdf_ids = request.form.getlist('pdf_ids')
    
    if not pdf_ids:
        flash('Silinəcək PDF seçin!', 'error')
        return redirect(url_for('admin'))
    
    deleted_count = 0
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    for pdf_id in pdf_ids:
        try:
            c.execute('SELECT * FROM pdfs WHERE id = ?', (pdf_id,))
            pdf = c.fetchone()
            
            if pdf:
                # Delete file from disk
                if os.path.exists(pdf[4]):
                    os.remove(pdf[4])
                
                # Delete from database
                c.execute('DELETE FROM pdfs WHERE id = ?', (pdf_id,))
                deleted_count += 1
        except Exception as e:
            print(f"PDF silmə səhvi {pdf_id}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        flash(f'{deleted_count} PDF uğurla silindi!', 'success')
    else:
        flash('Heç bir PDF silinə bilmədi!', 'error')
    
    return redirect(url_for('admin'))

@app.route('/delete_student/<int:student_id>')
@login_required
def delete_student(student_id):
    """Delete a student"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Get student info first
    c.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = c.fetchone()
    
    if student:
        # Delete student from database
        c.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        flash(f'Şagird {student[1]} silindi!', 'success')
    else:
        flash('Şagird tapılmadı!', 'error')
    
    conn.close()
    return redirect(url_for('admin'))

@app.route('/bulk_delete_students', methods=['POST'])
@login_required
def bulk_delete_students():
    """Delete multiple students at once"""
    student_ids = request.form.getlist('student_ids')
    
    if not student_ids:
        flash('Silinəcək şagird seçin!', 'error')
        return redirect(url_for('admin'))
    
    deleted_count = 0
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    for student_id in student_ids:
        try:
            c.execute('DELETE FROM students WHERE id = ?', (student_id,))
            deleted_count += 1
        except Exception as e:
            print(f"Şagird silmə səhvi {student_id}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        flash(f'{deleted_count} şagird uğurla silindi!', 'success')
    else:
        flash('Heç bir şagird silinə bilmədi!', 'error')
    
    return redirect(url_for('admin'))

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    """Edit student information"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if request.method == 'POST':
        utis_code = request.form['utis_code'].strip()
        student_name = request.form['student_name'].strip()
        fin_code = request.form['fin_code'].strip().upper()
        
        # Unikal UTIS yoxlaması (özü istisna olmaqla)
        c.execute('SELECT id FROM students WHERE utis_code = ? AND id != ?', (utis_code, student_id))
        existing = c.fetchone()
        
        if existing:
            flash('Bu UTIS kodu artıq mövcuddur!', 'error')
        else:
            try:
                c.execute('''
                    UPDATE students 
                    SET utis_code = ?, student_name = ?, fin_code = ? 
                    WHERE id = ?
                ''', (utis_code, student_name, fin_code, student_id))
                conn.commit()
                flash('Şagird məlumatları yeniləndi!', 'success')
                conn.close()
                return redirect(url_for('admin'))
            except Exception as e:
                flash(f'Xəta: {str(e)}', 'error')
    
    # Şagird məlumatlarını əldə et
    c.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = c.fetchone()
    conn.close()
    
    if not student:
        flash('Şagird tapılmadı!', 'error')
        return redirect(url_for('admin'))
    
    return render_template('edit_student.html', student=student)

@app.route('/edit_pdf/<int:pdf_id>', methods=['GET', 'POST'])
@login_required
def edit_pdf(pdf_id):
    """Edit PDF filename"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if request.method == 'POST':
        new_filename = request.form['filename'].strip()
        
        # .pdf uzantısını əlavə et əgər yoxdursa
        if not new_filename.lower().endswith('.pdf'):
            new_filename += '.pdf'
        
        # Fayl adında qadağan olunmuş simvolları təmizlə
        import re
        new_filename = re.sub(r'[<>:"/\\|?*]', '_', new_filename)
        
        try:
            # Köhnə PDF məlumatlarını əldə et
            c.execute('SELECT * FROM pdfs WHERE id = ?', (pdf_id,))
            pdf = c.fetchone()
            
            if pdf:
                old_filepath = pdf[4]  # Köhnə fayl yolu
                
                # Yeni fayl yolunu hazırla
                upload_dir = os.path.dirname(old_filepath)
                new_filepath = os.path.join(upload_dir, new_filename)
                
                # Faylın mövcudluğunu yoxla və adını dəyiş
                if os.path.exists(old_filepath):
                    os.rename(old_filepath, new_filepath)
                
                # Verilənlər bazasında yenilə
                c.execute('''
                    UPDATE pdfs 
                    SET filename = ?, filepath = ? 
                    WHERE id = ?
                ''', (new_filename, new_filepath, pdf_id))
                conn.commit()
                flash('PDF adı yeniləndi!', 'success')
            else:
                flash('PDF tapılmadı!', 'error')
                
        except Exception as e:
            flash(f'Xəta: {str(e)}', 'error')
        
        conn.close()
        return redirect(url_for('admin'))
    
    # PDF məlumatlarını əldə et
    c.execute('SELECT * FROM pdfs WHERE id = ?', (pdf_id,))
    pdf = c.fetchone()
    conn.close()
    
    if not pdf:
        flash('PDF tapılmadı!', 'error')
        return redirect(url_for('admin'))
    
    return render_template('edit_pdf.html', pdf=pdf)

@app.route('/get_validation_status')
@login_required 
def get_validation_status():
    """Get validation status for color coding"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # PDF olmayan şagirdlər
    c.execute('''
        SELECT s.id, s.utis_code 
        FROM students s 
        LEFT JOIN pdfs p ON s.utis_code = p.utis_code 
        WHERE p.utis_code IS NULL
    ''')
    students_without_pdfs = {row[0]: row[1] for row in c.fetchall()}
    
    # Şagirdi olmayan PDF-lər  
    c.execute('''
        SELECT p.id, p.utis_code 
        FROM pdfs p 
        LEFT JOIN students s ON p.utis_code = s.utis_code 
        WHERE s.utis_code IS NULL
    ''')
    pdfs_without_students = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    
    return jsonify({
        'students_without_pdfs': students_without_pdfs,
        'pdfs_without_students': pdfs_without_students
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 