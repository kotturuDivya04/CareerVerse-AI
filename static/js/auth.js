/* ================================================================
   auth.js — CareerVerse AI
   Handles login.html and register.html form interactions:
     - Client-side validation before submit
     - Loading state on the submit button
     - Both forms perform a REAL POST to Flask (not fetch/AJAX),
       since auth typically relies on server-rendered redirects
       and flash() messages rather than JSON responses.
   ================================================================ */

document.addEventListener('DOMContentLoaded', () => {
  initLoginForm();
  initRegisterForm();
});

// ================================================================
// LOGIN FORM
// BACKEND NOTE: Submits a standard POST to /login (see action=
// attribute on the <form> in login.html). Flask validates the
// credentials, creates a session, and redirects to /dashboard.
// On failure, Flask calls flash('message', 'error') and re-renders
// login.html — main.js's renderFlashMessages() then shows the toast.
// ================================================================
function initLoginForm() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    const email = document.getElementById('login-email');
    const password = document.getElementById('login-password');

    // Basic client-side validation — Flask still validates again,
    // this just avoids an unnecessary round-trip for empty fields.
    if (!email.value.trim() || !password.value.trim()) {
      event.preventDefault();
      showToast('error', 'Missing Fields', 'Please enter your email and password.');
      return;
    }

    // Show a loading state on the button while the browser
    // navigates to handle the real form POST.
    const btn = document.getElementById('login-submit-btn');
    if (btn) {
      btn.innerHTML = `
        <div class="spinner-sm" style="border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;width:18px;height:18px;animation:spin 0.8s linear infinite;"></div>
        Signing in…`;
      btn.disabled = true;
    }
    // Form submits normally from here — no preventDefault() on success path.
  });
}

// ================================================================
// REGISTER FORM
// BACKEND NOTE: Submits a standard POST to /register. Flask
// validates name/email/password/confirm_password, checks for an
// existing account with that email, hashes the password, inserts
// the new user row, creates a session, and redirects to /dashboard.
// Validation failures use flash('message', 'error').
// ================================================================
function initRegisterForm() {
  const form = document.getElementById('register-form');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    const name = document.getElementById('register-name');
    const email = document.getElementById('register-email');
    const password = document.getElementById('register-password');
    const confirmPassword = document.getElementById('register-confirm-password');
    const agreeTerms = document.getElementById('agree-terms');

    if (!name.value.trim() || !email.value.trim() || !password.value || !confirmPassword.value) {
      event.preventDefault();
      showToast('error', 'Missing Fields', 'Please fill in all fields to continue.');
      return;
    }

    if (password.value.length < 8) {
      event.preventDefault();
      showToast('error', 'Weak Password', 'Password must be at least 8 characters.');
      return;
    }

    if (password.value !== confirmPassword.value) {
      event.preventDefault();
      showToast('error', 'Password Mismatch', 'Your passwords do not match.');
      return;
    }

    if (!agreeTerms.checked) {
      event.preventDefault();
      showToast('warning', 'Terms Required', 'Please agree to the Terms & Privacy Policy.');
      return;
    }

    // All good — show loading state and let the form submit normally.
    const btn = document.getElementById('register-submit-btn');
    if (btn) {
      btn.innerHTML = `
        <div class="spinner-sm" style="border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;width:18px;height:18px;animation:spin 0.8s linear infinite;"></div>
        Creating account…`;
      btn.disabled = true;
    }
  });
}