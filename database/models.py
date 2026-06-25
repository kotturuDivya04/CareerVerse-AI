# =============================================================================
# database/models.py  —  CareerVerse AI
# SQLAlchemy ORM models + SQLite schema
#
# Tables:
#   User               — registered accounts
#   Report             — parent row for every analysis (any type)
#   PlagiarismReport   — plagiarism-specific results
#   ResumeReport       — ATS scoring results
#   JobRecommendation  — job role recommender results
#   ActivityLog        — per-user action feed
# =============================================================================

from datetime import datetime
import json as _json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# =============================================================================
# USER
# =============================================================================

class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer,     primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    institution   = db.Column(db.String(200), nullable=True,  default='')
    bio           = db.Column(db.Text,        nullable=True,  default='')
    target_role   = db.Column(db.String(100), nullable=True,  default='')
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)

    reports        = db.relationship('Report',           backref='owner', lazy=True, cascade='all, delete-orphan')
    activity_logs  = db.relationship('ActivityLog',      backref='user',  lazy=True, cascade='all, delete-orphan')
    plag_reports   = db.relationship('PlagiarismReport', backref='user',  lazy=True, cascade='all, delete-orphan')
    resume_reports = db.relationship('ResumeReport',     backref='user',  lazy=True, cascade='all, delete-orphan')
    job_recs       = db.relationship('JobRecommendation',backref='user',  lazy=True, cascade='all, delete-orphan')
    interview_reports = db.relationship('InterviewReport', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':          self.id,
            'name':        self.name,
            'email':       self.email,
            'institution': self.institution or '',
            'bio':         self.bio or '',
            'target_role': self.target_role or '',
            'created_at':  self.created_at.strftime('%b %d, %Y'),
        }

    def __repr__(self):
        return f'<User {self.email}>'


# =============================================================================
# REPORT  (parent summary row)
# =============================================================================

class Report(db.Model):
    """
    One row per analysis run.
    report_type: 'plagiarism' | 'resume' | 'job_recommendation'
    """
    __tablename__ = 'reports'

    id           = db.Column(db.Integer,      primary_key=True)
    user_id      = db.Column(db.Integer,      db.ForeignKey('users.id'), nullable=False)
    report_type  = db.Column(db.String(30),   nullable=False)
    filename     = db.Column(db.String(255),  nullable=False)
    pdf_filename = db.Column(db.String(255),  nullable=True)
    score        = db.Column(db.Float,        nullable=True)
    status_label = db.Column(db.String(50),   nullable=True)
    created_at   = db.Column(db.DateTime,     default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           self.id,
            'report_type':  self.report_type,
            'filename':     self.filename,
            'pdf_filename': self.pdf_filename,
            'score':        self.score,
            'status_label': self.status_label,
            'created_at':   self.created_at.strftime('%b %d, %Y · %H:%M'),
        }

    def __repr__(self):
        return f'<Report {self.id} {self.report_type}>'


# =============================================================================
# PLAGIARISM REPORT
# =============================================================================

class PlagiarismReport(db.Model):
    """
    Detailed plagiarism results.
    matched_sentences — JSON list of
      {"doc1_sentence": str, "doc2_sentence": str, "similarity": float}
    """
    __tablename__ = 'plagiarism_reports'

    id                 = db.Column(db.Integer,    primary_key=True)
    report_id          = db.Column(db.Integer,    db.ForeignKey('reports.id'), nullable=False)
    user_id            = db.Column(db.Integer,    db.ForeignKey('users.id'),   nullable=False)
    file1_name         = db.Column(db.String(255),nullable=False)
    file2_name         = db.Column(db.String(255),nullable=False)
    similarity_percent = db.Column(db.Float,      nullable=False, default=0.0)
    status             = db.Column(db.String(20), nullable=False, default='Low')
    matched_count      = db.Column(db.Integer,    nullable=False, default=0)
    matched_sentences  = db.Column(db.Text,       nullable=True)   # JSON
    summary            = db.Column(db.Text,       nullable=True)
    recommendation     = db.Column(db.Text,       nullable=True)
    pdf_filename       = db.Column(db.String(255),nullable=True)
    created_at         = db.Column(db.DateTime,   default=datetime.utcnow)

    def matched_list(self):
        return _json.loads(self.matched_sentences) if self.matched_sentences else []

    def to_dict(self):
        return {
            'id':                 self.id,
            'report_id':          self.report_id,
            'file1_name':         self.file1_name,
            'file2_name':         self.file2_name,
            'similarity_percent': self.similarity_percent,
            'status':             self.status,
            'matched_count':      self.matched_count,
            'matched_sentences':  self.matched_list(),
            'summary':            self.summary or '',
            'recommendation':     self.recommendation or '',
            'pdf_filename':       self.pdf_filename,
            'created_at':         self.created_at.strftime('%b %d, %Y · %H:%M'),
        }

    def __repr__(self):
        return f'<PlagiarismReport {self.id} {self.similarity_percent}%>'


# =============================================================================
# RESUME REPORT
# =============================================================================

class ResumeReport(db.Model):
    """
    ATS scoring results.
    ATS weights: projects 30% | skills 25% | experience 20% |
                 role_match 15% | achievements 5% | certifications 5%
    """
    __tablename__ = 'resume_reports'

    id               = db.Column(db.Integer,    primary_key=True)
    report_id        = db.Column(db.Integer,    db.ForeignKey('reports.id'), nullable=False)
    user_id          = db.Column(db.Integer,    db.ForeignKey('users.id'),   nullable=False)
    resume_name      = db.Column(db.String(255),nullable=False)
    target_role      = db.Column(db.String(100),nullable=False)
    ats_score        = db.Column(db.Float,      nullable=False, default=0.0)
    role_match_score = db.Column(db.Float,      nullable=False, default=0.0)
    skills_found     = db.Column(db.Text,       nullable=True)   # JSON list
    missing_skills   = db.Column(db.Text,       nullable=True)   # JSON list
    strengths        = db.Column(db.Text,       nullable=True)   # JSON list
    suggestions      = db.Column(db.Text,       nullable=True)   # JSON list
    section_scores   = db.Column(db.Text,       nullable=True)   # JSON dict
    pdf_filename     = db.Column(db.String(255),nullable=True)
    created_at       = db.Column(db.DateTime,   default=datetime.utcnow)

    job_recommendation = db.relationship(
        'JobRecommendation', backref='resume_report',
        uselist=False, cascade='all, delete-orphan'
    )

    def skills_found_list(self):    return _json.loads(self.skills_found)    if self.skills_found    else []
    def missing_skills_list(self):  return _json.loads(self.missing_skills)  if self.missing_skills  else []
    def strengths_list(self):       return _json.loads(self.strengths)       if self.strengths       else []
    def suggestions_list(self):     return _json.loads(self.suggestions)     if self.suggestions     else []
    def section_scores_dict(self):  return _json.loads(self.section_scores)  if self.section_scores  else {}

    def to_dict(self):
        return {
            'id':               self.id,
            'report_id':        self.report_id,
            'resume_name':      self.resume_name,
            'target_role':      self.target_role,
            'ats_score':        self.ats_score,
            'role_match_score': self.role_match_score,
            'skills_found':     self.skills_found_list(),
            'missing_skills':   self.missing_skills_list(),
            'strengths':        self.strengths_list(),
            'suggestions':      self.suggestions_list(),
            'section_scores':   self.section_scores_dict(),
            'pdf_filename':     self.pdf_filename,
            'created_at':       self.created_at.strftime('%b %d, %Y · %H:%M'),
        }

    def __repr__(self):
        return f'<ResumeReport {self.id} ATS={self.ats_score}>'


# =============================================================================
# JOB RECOMMENDATION
# =============================================================================

class JobRecommendation(db.Model):
    """
    Job role recommender results.

    recommended_roles — JSON list of dicts, sorted by match_percent desc:
    [
      {
        "role":            "Data Scientist",
        "match_percent":   87.5,
        "matched_skills":  ["Python", "ML", "SQL"],
        "missing_skills":  ["PyTorch", "Spark"],
        "strengths":       ["Strong Python background"],
        "suggestions":     ["Learn PyTorch", "Add cloud certs"]
      },
      ...
    ]

    extracted_skills — JSON list of skills found in the resume.
    """
    __tablename__ = 'job_recommendations'

    id                = db.Column(db.Integer,    primary_key=True)
    report_id         = db.Column(db.Integer,    db.ForeignKey('reports.id'),        nullable=False)
    resume_report_id  = db.Column(db.Integer,    db.ForeignKey('resume_reports.id'), nullable=True)
    user_id           = db.Column(db.Integer,    db.ForeignKey('users.id'),          nullable=False)
    resume_name       = db.Column(db.String(255),nullable=False)
    top_role          = db.Column(db.String(100),nullable=True)
    top_match_percent = db.Column(db.Float,      nullable=True)
    recommended_roles = db.Column(db.Text,       nullable=True)   # JSON
    extracted_skills  = db.Column(db.Text,       nullable=True)   # JSON
    pdf_filename      = db.Column(db.String(255),nullable=True)
    created_at        = db.Column(db.DateTime,   default=datetime.utcnow)

    def recommended_roles_list(self):
        return _json.loads(self.recommended_roles) if self.recommended_roles else []

    def extracted_skills_list(self):
        return _json.loads(self.extracted_skills) if self.extracted_skills else []

    def to_dict(self):
        return {
            'id':                self.id,
            'report_id':         self.report_id,
            'resume_name':       self.resume_name,
            'top_role':          self.top_role or '',
            'top_match_percent': self.top_match_percent or 0,
            'recommended_roles': self.recommended_roles_list(),
            'extracted_skills':  self.extracted_skills_list(),
            'pdf_filename':      self.pdf_filename,
            'created_at':        self.created_at.strftime('%b %d, %Y · %H:%M'),
        }

    def __repr__(self):
        return f'<JobRecommendation {self.id} top={self.top_role}>'


# =============================================================================
# ACTIVITY LOG
# =============================================================================

class ActivityLog(db.Model):
    """
    One row per user action — powers the dashboard activity feed
    and the notifications page.
    report_type: 'plagiarism' | 'resume' | 'job_recommendation' | None
    """
    __tablename__ = 'activity_log'

    id          = db.Column(db.Integer,    primary_key=True)
    user_id     = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False)
    action      = db.Column(db.String(200),nullable=False)
    detail      = db.Column(db.String(500),nullable=True)
    report_type = db.Column(db.String(30), nullable=True)
    report_id   = db.Column(db.Integer,    nullable=True)
    created_at  = db.Column(db.DateTime,   default=datetime.utcnow)

    def time_ago(self):
        delta = datetime.utcnow() - self.created_at
        secs  = int(delta.total_seconds())
        if secs < 60:       return 'Just now'
        if secs < 3600:     return f'{secs // 60} min ago'
        if secs < 86400:    return f'{secs // 3600} hr{"s" if secs//3600 > 1 else ""} ago'
        d = secs // 86400
        if d == 1:          return 'Yesterday'
        if d < 7:           return f'{d} days ago'
        return self.created_at.strftime('%b %d, %Y')

    def to_dict(self):
        return {
            'id':          self.id,
            'action':      self.action,
            'detail':      self.detail or '',
            'report_type': self.report_type or '',
            'report_id':   self.report_id,
            'time_ago':    self.time_ago(),
            'created_at':  self.created_at.strftime('%b %d, %Y · %H:%M'),
        }

    def __repr__(self):
        return f'<ActivityLog {self.id} {self.action[:30]}>'
# =============================================================================
# INTERVIEW REPORT
# =============================================================================

class InterviewReport(db.Model):
    """
    Interview Preparation results.

    technical_questions,
    hr_questions,
    project_questions,
    behavioral_questions

    are stored as JSON arrays.
    """

    __tablename__ = 'interview_reports'

    id                    = db.Column(db.Integer, primary_key=True)

    report_id             = db.Column(
        db.Integer,
        db.ForeignKey('reports.id'),
        nullable=False
    )

    user_id               = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    role_name             = db.Column(
        db.String(100),
        nullable=False
    )

    resume_name           = db.Column(
        db.String(255),
        nullable=True
    )

    technical_questions   = db.Column(
        db.Text,
        nullable=True
    )

    hr_questions          = db.Column(
        db.Text,
        nullable=True
    )

    project_questions     = db.Column(
        db.Text,
        nullable=True
    )

    behavioral_questions  = db.Column(
        db.Text,
        nullable=True
    )

    pdf_filename          = db.Column(
        db.String(255),
        nullable=True
    )

    created_at            = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def technical_questions_list(self):
        return _json.loads(
            self.technical_questions
        ) if self.technical_questions else []

    def hr_questions_list(self):
        return _json.loads(
            self.hr_questions
        ) if self.hr_questions else []

    def project_questions_list(self):
        return _json.loads(
            self.project_questions
        ) if self.project_questions else []

    def behavioral_questions_list(self):
        return _json.loads(
            self.behavioral_questions
        ) if self.behavioral_questions else []

    def to_dict(self):
        return {
            'id':
                self.id,

            'report_id':
                self.report_id,

            'role_name':
                self.role_name,

            'resume_name':
                self.resume_name or '',

            'technical_questions':
                self.technical_questions_list(),

            'hr_questions':
                self.hr_questions_list(),

            'project_questions':
                self.project_questions_list(),

            'behavioral_questions':
                self.behavioral_questions_list(),

            'pdf_filename':
                self.pdf_filename,

            'created_at':
                self.created_at.strftime(
                    '%b %d, %Y · %H:%M'
                )
        }

    def __repr__(self):
        return (
            f'<InterviewReport '
            f'{self.id} '
            f'{self.role_name}>'
        )