# =============================================================================
# modules/auth/auth.py  —  CareerVerse AI
# Password hashing + login_required decorator
#
# Uses werkzeug PBKDF2-SHA256 — no extra dependency beyond Flask itself.
# =============================================================================

from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain_text: str) -> str:
    """
    Return a PBKDF2-SHA256 hash of the plaintext password.
    Store the result in User.password_hash — never store plaintext.
    """
    return generate_password_hash(plain_text, method='pbkdf2:sha256')


def verify_password(plain_text: str, password_hash: str) -> bool:
    """
    Return True if plain_text matches the stored hash.
    Constant-time comparison prevents timing attacks.
    """
    return check_password_hash(password_hash, plain_text)


def login_required(f):
    """
    Flask view decorator — redirects unauthenticated requests to /login.

    Usage:
        @app.route('/dashboard')
        @login_required
        def dashboard():
            ...

    Expects session keys:  user_id  |  user_name  |  user_email
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """Return the logged-in user's PK from session, or None."""
    return session.get('user_id')


def get_current_user_name() -> str:
    """Return the logged-in user's display name, or empty string."""
    return session.get('user_name', '')


def is_logged_in() -> bool:
    """Return True if a valid user session exists."""
    return 'user_id' in session
