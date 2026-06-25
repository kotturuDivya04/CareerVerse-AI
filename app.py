# =============================================================================
# app.py  —  CareerVerse AI
# =============================================================================

import os
import uuid
import json
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory, abort
)
from werkzeug.utils import secure_filename

from database.models import (
    db, User, Report, PlagiarismReport,
    ResumeReport, JobRecommendation,
    InterviewReport, ActivityLog
)
from modules.auth.auth import hash_password, verify_password, login_required
from modules.plagiarism.reader import extract_text
from modules.plagiarism.plagiarism_engine import analyze_plagiarism
from modules.plagiarism.report_generator import generate_plagiarism_pdf
from modules.resume.reader import extract_resume_text
from modules.resume.resume_engine import analyze_resume
from modules.resume.resume_report import generate_resume_pdf
#from modules.job_recommender.recommender_engine import recommend_roles
#from modules.job_recommender.recommender_report import generate_recommender_pdf
from modules.interview.question_generator import generate_interview_questions
from modules.interview.interview_report import generate_interview_pdf


# =============================================================================
# APP FACTORY
# =============================================================================

def create_app():
    app = Flask(__name__)

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_FOLDER = os.path.join(BASE_DIR, "database")
    DB_PATH = os.path.join(DB_FOLDER, "careerverse.db")

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'careerverse-secret-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
    app.config['REPORTS_FOLDER'] = os.path.join(BASE_DIR, 'reports')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024   # 10 MB

    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    os.makedirs(DB_FOLDER, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def save_upload(file_obj):
        original    = secure_filename(file_obj.filename)
        unique_name = f"{uuid.uuid4().hex}_{original}"
        filepath    = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file_obj.save(filepath)
        return unique_name, filepath

    def delete_upload(filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass

    def log_activity(user_id, action, detail, report_type=None,
                     report_id=None, status_label=None):
        entry = ActivityLog(
            user_id      = user_id,
            action       = action,
            detail       = detail,
            report_type  = report_type,
            report_id    = report_id,
            created_at   = datetime.utcnow()
        )
        db.session.add(entry)
        db.session.commit()

    def get_dashboard_donut(user_id):
        """
        Returns (plag_pct, resume_pct, plag_dash, resume_dash, resume_offset)
        for the two-segment donut SVG on dashboard.html.
        Circumference of r=52 circle = 2 * pi * 52 ≈ 327
        """
        circumference = 327
        p = PlagiarismReport.query.filter_by(user_id=user_id).count()
        r = ResumeReport.query.filter_by(user_id=user_id).count()
        total = p + r or 1
        plag_pct   = round(p / total * 100)
        resume_pct = 100 - plag_pct
        plag_dash   = f"{round(plag_pct / 100 * circumference)} {circumference}"
        resume_dash = f"{round(resume_pct / 100 * circumference)} {circumference}"
        resume_offset = f"-{round(plag_pct / 100 * circumference)}"
        return plag_pct, resume_pct, plag_dash, resume_dash, resume_offset

    def get_weekly_chart_data(user_id):
        from sqlalchemy import func
        from datetime import timedelta
        today  = datetime.utcnow().date()
        result = []
        for i in range(6, -1, -1):
            day   = today - timedelta(days=i)
            count = (Report.query
                     .filter(Report.user_id == user_id,
                             func.date(Report.created_at) == str(day))
                     .count())
            result.append({'day': day.strftime('%a'), 'count': count})
        return result

    # =========================================================================
    # AUTH ROUTES
    # =========================================================================

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            email    = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            if not email or not password:
                flash('Email and password are required.', 'error')
                return render_template('login.html')
            user = User.query.filter_by(email=email).first()
            if user and verify_password(password, user.password_hash):
                session.permanent    = True
                session['user_id']   = user.id
                session['user_name'] = user.name
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid email or password.', 'error')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            name     = request.form.get('name', '').strip()
            email    = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm  = request.form.get('confirm_password', '')
            if not all([name, email, password, confirm]):
                flash('All fields are required.', 'error')
                return render_template('register.html')
            if password != confirm:
                flash('Passwords do not match.', 'error')
                return render_template('register.html')
            if len(password) < 8:
                flash('Password must be at least 8 characters.', 'error')
                return render_template('register.html')
            if User.query.filter_by(email=email).first():
                flash('An account with this email already exists.', 'error')
                return render_template('register.html')
            new_user = User(
                name          = name,
                email         = email,
                password_hash = hash_password(password),
                created_at    = datetime.utcnow()
            )
            db.session.add(new_user)
            db.session.commit()
            session['user_id']   = new_user.id
            session['user_name'] = new_user.name
            flash(f'Account created! Welcome, {name}!', 'success')
            return redirect(url_for('dashboard'))
        return render_template('register.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    # =========================================================================
    # DASHBOARD
    # =========================================================================

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_id = session['user_id']

        total_analyses    = Report.query.filter_by(user_id=user_id).count()
        plagiarism_count  = PlagiarismReport.query.filter_by(user_id=user_id).count()
        resume_count      = ResumeReport.query.filter_by(user_id=user_id).count()
        reports_generated = Report.query.filter(
            Report.user_id == user_id,
            Report.pdf_filename.isnot(None)
        ).count()

        recent_activity = (ActivityLog.query
                           .filter_by(user_id=user_id)
                           .order_by(ActivityLog.created_at.desc())
                           .limit(6).all())

        recent_reports = (Report.query
                          .filter_by(user_id=user_id)
                          .order_by(Report.created_at.desc())
                          .limit(4).all())

        chart_data = get_weekly_chart_data(user_id)

        plag_pct, resume_pct, plag_dash, resume_dash, resume_offset = \
            get_dashboard_donut(user_id)

        return render_template(
            'dashboard.html',
            active_page        = 'dashboard',
            user_name          = session['user_name'],
            total_analyses     = total_analyses,
            plagiarism_count   = plagiarism_count,
            resume_count       = resume_count,
            reports_generated  = reports_generated,
            recent_activity    = recent_activity,
            recent_reports     = recent_reports,
            chart_data         = json.dumps(chart_data),
            plag_pct           = plag_pct,
            resume_pct         = resume_pct,
            plag_dash          = plag_dash,
            resume_dash        = resume_dash,
            resume_offset      = resume_offset,
        )

    @app.route('/api/dashboard/stats')
    @login_required
    def api_dashboard_stats():
        user_id = session['user_id']
        return jsonify({
            'total_analyses':   Report.query.filter_by(user_id=user_id).count(),
            'plagiarism_count': PlagiarismReport.query.filter_by(user_id=user_id).count(),
            'resume_count':     ResumeReport.query.filter_by(user_id=user_id).count(),
            'reports_generated': Report.query.filter(
                Report.user_id == user_id,
                Report.pdf_filename.isnot(None)
            ).count(),
        })
    # =========================================================================
    # PLAGIARISM DETECTOR
    # =========================================================================

    @app.route('/plagiarism')
    @login_required
    def plagiarism():
        return render_template(
            'plagiarism.html',
            active_page='plagiarism',
            user_name=session['user_name']
        )


    @app.route('/api/plagiarism/analyze', methods=['POST'])
    @login_required
    def api_plagiarism_analyze():
        user_id = session['user_id']

        try:
            # 1. Validate uploaded files
            if 'file1' not in request.files or 'file2' not in request.files:
                return jsonify({'error': 'Both documents are required.'}), 400

            file1 = request.files['file1']
            file2 = request.files['file2']

            if not file1.filename or not file2.filename:
                return jsonify({'error': 'Please select both files.'}), 400

            if not allowed_file(file1.filename) or not allowed_file(file2.filename):
                return jsonify({'error': 'Unsupported file type. Use PDF, DOCX, or TXT.'}), 400

            # 2. Save uploads
            fname1, path1 = save_upload(file1)
            fname2, path2 = save_upload(file2)

            try:
                # 3. Extract text
                text1 = extract_text(path1)
                text2 = extract_text(path2)

                if not text1.strip() or not text2.strip():
                    return jsonify({'error': 'Could not extract text from one or both files.'}), 422

                # 4. Run plagiarism engine
                result = analyze_plagiarism(text1, text2)

                pct = result.get('similarity_percent', 0.0)
                status = result.get('status', 'Low')
                matched_sentences = result.get('matched_sentences', [])
                matched_paragraphs = result.get('matched_paragraphs', 0)
                words_compared = result.get('words_compared', 0)
                summary = result.get('summary', '')
                recommendation = result.get('recommendation', '')

                # 5. Generate PDF
                report_filename = f"plagiarism_{uuid.uuid4().hex}.pdf"
                report_path = os.path.join(app.config['REPORTS_FOLDER'], report_filename)

                generate_plagiarism_pdf(
                    output_path=report_path,
                    user_name=session['user_name'],
                    file1_name=file1.filename,
                    file2_name=file2.filename,
                    similarity=pct,
                    status=status,
                    matched=matched_sentences,
                    summary=summary,
                    recommendation=recommendation,
                    

                )

                # 6. Save main report
                report = Report(
                    user_id=user_id,
                    report_type='plagiarism',
                    filename=f"{file1.filename} vs {file2.filename}",
                    pdf_filename=report_filename,
                    score=pct,
                    status_label=status,
                    created_at=datetime.utcnow()
                )
                db.session.add(report)
                db.session.flush()

                # 7. Save plagiarism details
                plag_report = PlagiarismReport(
                    report_id=report.id,
                    user_id=user_id,
                    file1_name=file1.filename,
                    file2_name=file2.filename,
                    similarity_percent=pct,
                    status=status,
                    matched_count=len(matched_sentences),
                    matched_sentences=json.dumps(matched_sentences),
                    summary=summary,
                    recommendation=recommendation,
                    pdf_filename=report_filename,
                    created_at=datetime.utcnow()
                )
                db.session.add(plag_report)
                db.session.commit()

                # 8. Log activity
                try:
                    log_activity(
                        user_id=user_id,
                        action='Plagiarism Report Generated',
                        detail=f"{file1.filename} — {pct:.1f}% similarity",
                        report_type='plagiarism',
                        report_id=report.id
                    )
                except Exception as log_err:
                    print("Activity log failed:", log_err)

                # 9. Return response
                return jsonify({
                    'report_id': report.id,
                    'similarity_percent': round(pct, 2),
                    'status': status,
                    'matched_sentences': matched_sentences,
                    'matched_paragraphs': matched_paragraphs,
                    'words_compared': words_compared,
                    'summary': summary,
                    'recommendation': recommendation,
                })

            finally:
                delete_upload(path1)
                delete_upload(path2)

        except Exception as e:
            print("PLAGIARISM ERROR:", e)
            db.session.rollback()
            return jsonify({'error': f'Plagiarism analysis failed: {str(e)}'}), 500
    # =========================================================================
    # RESUME ANALYZER  +  JOB ROLE RECOMMENDER
    # =========================================================================

    @app.route('/resume')
    @login_required
    def resume():
        return render_template('resume.html',
                               active_page='resume',
                               user_name=session['user_name'])

    @app.route('/api/resume/analyze', methods=['POST'])
    @login_required
    def api_resume_analyze():
        user_id = session['user_id']

        if 'file' not in request.files:
            return jsonify({'error': 'Resume file is required.'}), 400

        file = request.files['file']
        role = request.form.get('role', '').strip()

        if not file.filename:
            return jsonify({'error': 'No file selected.'}), 400
        if not role:
            return jsonify({'error': 'Please select a target role.'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file type. Use PDF or DOCX.'}), 400

        fname, fpath = save_upload(file)
        resume_text  = extract_resume_text(fpath)

        if not resume_text.strip():
            delete_upload(fpath)
            return jsonify({'error': 'Could not extract text from the resume.'}), 422

        # ---- ATS Analysis ----
        ats_result = analyze_resume(resume_text, role)

        ats_report_filename = f"resume_{uuid.uuid4().hex}.pdf"
        ats_report_path     = os.path.join(app.config['REPORTS_FOLDER'], ats_report_filename)
        generate_resume_pdf(
            output_path = ats_report_path,
            user_name   = session['user_name'],
            resume_name = file.filename,
            role        = role,
            result      = ats_result,
        )

        ats_report = Report(
            user_id      = user_id,
            report_type  = 'resume',
            filename     = file.filename,
            pdf_filename = ats_report_filename,
            score        = ats_result['ats_score'],
            status_label = 'Strong' if ats_result['ats_score'] >= 70 else 'Average',
            created_at   = datetime.utcnow()
        )
        db.session.add(ats_report)
        db.session.flush()

        resume_report = ResumeReport(
            report_id        = ats_report.id,
            user_id          = user_id,
            resume_name      = file.filename,
            target_role      = role,
            ats_score        = ats_result['ats_score'],
            role_match_score = ats_result['role_match_score'],
            skills_found     = json.dumps(ats_result['skills_found']),
            missing_skills   = json.dumps(ats_result['missing_skills']),
            strengths        = json.dumps(ats_result['strengths']),
            suggestions      = json.dumps(ats_result['suggestions']),
            section_scores   = json.dumps(ats_result['section_scores']),
            pdf_filename     = ats_report_filename,
            created_at       = datetime.utcnow()
        )
        db.session.add(resume_report)
        db.session.flush()

        log_activity(
            user_id      = user_id,
            action       = 'Resume Analysis Completed',
            detail       = f"{file.filename} — ATS: {ats_result['ats_score']:.0f} | {role}",
            report_type  = 'resume',
            report_id    = ats_report.id

        )
        db.session.commit()
        delete_upload(fpath)

        return jsonify({
            'report_id': ats_report.id,
            'ats_score': round(ats_result['ats_score'], 2),
            'role_match_score': round(ats_result['role_match_score'], 2),
            'skills_found': ats_result['skills_found'],
            'missing_skills': ats_result['missing_skills'],
            'strengths': ats_result['strengths'],
            'suggestions': ats_result['suggestions'],
            'section_scores': ats_result['section_scores'],
            'job_recommendations': {
                'report_id': None,
                'recommended_roles': []
            }
        })
    
        '''# ---- Job Role Recommender (same request, same resume text) ----
        rec_result = recommend_roles(resume_text)

        rec_report_filename = f"jobrec_{uuid.uuid4().hex}.pdf"
        rec_report_path     = os.path.join(app.config['REPORTS_FOLDER'], rec_report_filename)
        generate_recommender_pdf(
            output_path       = rec_report_path,
            user_name         = session['user_name'],
            resume_name       = file.filename,
            recommended_roles = rec_result['recommended_roles'],
        )

        rec_report = Report(
            user_id      = user_id,
            report_type  = 'job_recommendation',
            filename     = file.filename,
            pdf_filename = rec_report_filename,
            score        = rec_result['recommended_roles'][0]['match_percent']
                           if rec_result['recommended_roles'] else 0,
            status_label = rec_result['recommended_roles'][0]['role']
                           if rec_result['recommended_roles'] else '',
            created_at   = datetime.utcnow()
        )
        db.session.add(rec_report)
        db.session.flush()

        job_rec = JobRecommendation(
            report_id         = rec_report.id,
            resume_report_id  = resume_report.id,
            user_id           = user_id,
            resume_name       = file.filename,
            top_role          = rec_result['recommended_roles'][0]['role']
                                if rec_result['recommended_roles'] else '',
            top_match_percent = rec_result['recommended_roles'][0]['match_percent']
                                if rec_result['recommended_roles'] else 0,
            recommended_roles = json.dumps(rec_result['recommended_roles']),
            extracted_skills  = json.dumps(rec_result.get('extracted_skills', [])),
            pdf_filename      = rec_report_filename,
            created_at        = datetime.utcnow()
        )
        db.session.add(job_rec)
        db.session.commit()
    
        log_activity(
            user_id      = user_id,
            action       = 'ATS Score Calculated',
            detail       = f"Top role: {job_rec.top_role} ({job_rec.top_match_percent:.0f}%)",
            report_type  = 'job_recommendation',
            report_id    = rec_report.id,
        )

        delete_upload(fpath)

        return jsonify({
            'report_id':        ats_report.id,
            'ats_score':        round(ats_result['ats_score'], 2),
            'role_match_score': round(ats_result['role_match_score'], 2),
            'skills_found':     ats_result['skills_found'],
            'missing_skills':   ats_result['missing_skills'],
            'strengths':        ats_result['strengths'],
            'suggestions':      ats_result['suggestions'],
            'section_scores':   ats_result['section_scores'],
            'job_recommendations': {
                'report_id':         rec_report.id,
                'recommended_roles': rec_result['recommended_roles'],
            },
        })'''

    # =========================================================================
    # INTERVIEW PREPARATION
    # =========================================================================

    @app.route('/interview')
    @login_required
    def interview():
        return render_template('interview.html',
                               active_page='interview',
                               user_name=session['user_name'])

    @app.route('/api/interview/generate', methods=['POST'])
    @login_required
    def api_interview_generate():
        user_id = session['user_id']

        if 'file' not in request.files:
            return jsonify({'error': 'Resume file is required.'}), 400

        file = request.files['file']

        role = request.form.get('role', 'Software Engineer')
        role = role.strip() if role else 'Software Engineer'

        if not file.filename:
            return jsonify({'error': 'No file selected.'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file type. Use PDF or DOCX.'}), 400

        fname, fpath = save_upload(file)
        resume_text  = extract_resume_text(fpath)

        if not resume_text.strip():
            delete_upload(fpath)
            return jsonify({'error': 'Could not read resume text.'}), 422

        questions = generate_interview_questions(resume_text, role)
        total     = sum(len(v) for v in questions.values())

        report_filename = f"interview_{uuid.uuid4().hex}.pdf"
        report_path     = os.path.join(app.config['REPORTS_FOLDER'], report_filename)
        generate_interview_pdf(
            output_path = report_path,
            user_name   = session['user_name'],
            role        = role,
            questions   = questions,
        )

        report = Report(
            user_id      = user_id,
            report_type  = 'interview',
            filename     = file.filename,
            pdf_filename = report_filename,
            score        = None,
            status_label = role,
            created_at   = datetime.utcnow()
        )
        db.session.add(report)
        db.session.flush()

        print("ROLE =", role)
        print("QUESTIONS =", questions)

        interview_report = InterviewReport(
            report_id=report.id,
            user_id=user_id,
            role_name=role,
            resume_name=file.filename,
            technical_questions=json.dumps(questions.get('technical', [])),
            hr_questions=json.dumps(questions.get('hr', [])),
            project_questions=json.dumps(questions.get('project', [])),
            behavioral_questions=json.dumps(questions.get('behavioral', [])),
            pdf_filename=report_filename,
            created_at=datetime.utcnow()
        )

        log_activity(
            user_id     = user_id,
            action      = 'Interview Questions Generated',
            detail      = f"{role} — {total} questions",
            report_type = 'interview',
            report_id   = report.id,
        )

        delete_upload(fpath)

        return jsonify({
            'report_id':   report.id,
            'role':        role,
            'questions':   questions,
            'total_count': total,
        })

    # =========================================================================
    # REPORT DOWNLOAD
    # =========================================================================

    @app.route('/download/report/<int:report_id>')
    @login_required
    def download_report(report_id):
        report = Report.query.filter_by(
            id      = report_id,
            user_id = session['user_id']
        ).first_or_404()

        if not report.pdf_filename:
            abort(404)

        filepath = os.path.join(app.config['REPORTS_FOLDER'], report.pdf_filename)
        if not os.path.exists(filepath):
            abort(404)

        return send_from_directory(
            app.config['REPORTS_FOLDER'],
            report.pdf_filename,
            as_attachment = True,
            download_name = f"CareerVerse_{report.report_type}_{report.id}.pdf"
        )

    # =========================================================================
    # ERROR HANDLERS
    # =========================================================================

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({'error': 'File too large. Maximum upload size is 10 MB.'}), 413

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'An unexpected server error occurred.'}), 500

    return app


# =============================================================================
# ENTRY POINT
# =============================================================================

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)