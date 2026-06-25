/* ================================================================
   main.js — CareerVerse AI
   Shared utilities loaded on every page (via base.html / base_auth.html):
     - Sidebar collapse/expand + mobile toggle
     - Theme toggle (dark/light)
     - Toast notification system
     - Flash message → toast bridge (reads #flash-data from base.html)
     - File drop zone helpers (used by plagiarism.js, resume.js, interview.js)
     - Accordion toggle (used by interview.html, plagiarism.html compare cards)
     - Particles canvas background (used on login/register hero)
     - Password visibility toggle (used by auth.js)
   ================================================================ */

// ================================================================
// STATE
// ================================================================
let sidebarCollapsed = false;
let isDark = true;

// ================================================================
// SIDEBAR TOGGLE
// ================================================================
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const navbar  = document.getElementById('navbar');
  const main    = document.getElementById('main-content');

  // Pages without the app shell (login/register/404) won't have these
  if (!sidebar || !navbar || !main) return;

  // Mobile: slide sidebar in/out instead of collapsing it
  if (window.innerWidth <= 900) {
    sidebar.classList.toggle('mobile-open');
    return;
  }

  sidebarCollapsed = !sidebarCollapsed;
  sidebar.classList.toggle('collapsed', sidebarCollapsed);
  navbar.classList.toggle('collapsed', sidebarCollapsed);
  main.classList.toggle('collapsed', sidebarCollapsed);
}

// ================================================================
// THEME TOGGLE
// ================================================================
function toggleTheme() {
  isDark = !isDark;
  document.body.classList.toggle('light-mode', !isDark);

  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.innerHTML = isDark
      ? '<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>'
      : '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
  }
}

// ================================================================
// TOAST SYSTEM
// Usage: showToast('success' | 'error' | 'info' | 'warning', title, message)
// ================================================================
function showToast(type, title, msg) {
  const icons = {
    success: '<polyline points="20 6 9 17 4 12"/>',
    error:   '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    info:    '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    warning: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
  };

  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <svg class="toast-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${icons[type] || icons.info}</svg>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${msg ? `<div class="toast-msg">${msg}</div>` : ''}
    </div>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 350);
  }, 3800);
}

// ================================================================
// FLASH MESSAGE → TOAST BRIDGE
// BACKEND NOTE: Flask's flash('message', 'category') populates the
// hidden #flash-data element (see base.html / base_auth.html) with
// a JSON array of [category, message] pairs. This reads that data
// on page load and renders each one as a toast automatically.
// Flask categories map directly to toast types: success, error,
// info, warning. Any unrecognised category falls back to 'info'.
// ================================================================
function renderFlashMessages() {
  const flashEl = document.getElementById('flash-data');
  if (!flashEl) return;

  let flashes = [];
  try {
    flashes = JSON.parse(flashEl.getAttribute('data-flashes')) || [];
  } catch (e) {
    return;
  }

  const validTypes = ['success', 'error', 'info', 'warning'];

  flashes.forEach(([category, message], index) => {
    const type = validTypes.includes(category) ? category : 'info';
    const title = type.charAt(0).toUpperCase() + type.slice(1);
    // Slight stagger so multiple flashes don't all animate at once
    setTimeout(() => showToast(type, title, message), index * 150);
  });
}

// ================================================================
// FILE DROP ZONE HELPERS
// Shared by plagiarism.html, resume.html, interview.html.
// Each page wires its own file <input> + drop-zone <div> IDs to
// these functions via inline onclick/ondrop/ondragover attributes.
// ================================================================
function triggerFileInput(inputId) {
  const input = document.getElementById(inputId);
  if (input) input.click();
}

function dzDragOver(event, dzId) {
  event.preventDefault();
  const dz = document.getElementById(dzId);
  if (dz) dz.classList.add('drag-over');
}

function dzDragLeave(dzId) {
  const dz = document.getElementById(dzId);
  if (dz) dz.classList.remove('drag-over');
}

function dzDrop(event, dzId, cardId) {
  event.preventDefault();
  const dz = document.getElementById(dzId);
  if (dz) dz.classList.remove('drag-over');

  const files = event.dataTransfer.files;
  if (!files.length) return;

  // Find the matching <input type="file"> inside this drop zone
  // and assign the dropped file to it, so the surrounding <form>
  // still submits it correctly via FormData.
  const input = dz ? dz.querySelector('input[type="file"]') : null;
  if (input) {
    input.files = files;
  }

  renderFileCard(files[0], cardId, dzId);
}

function showFileCard(inputId, cardId, dzId) {
  const input = document.getElementById(inputId);
  const file = input && input.files[0];
  if (!file) return;
  renderFileCard(file, cardId, dzId);
}

function renderFileCard(file, cardId, dzId) {
  const ext = file.name.split('.').pop().toUpperCase();
  const size = (file.size / 1024).toFixed(0) + ' KB';
  const wrap = document.getElementById(cardId);
  if (!wrap) return;

  wrap.innerHTML = `
    <div class="file-card">
      <div class="fc-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      </div>
      <div class="fc-info">
        <div class="fc-name">${file.name}</div>
        <div class="fc-meta">${ext} · ${size}</div>
      </div>
      <div class="progress-wrap" style="width:80px;">
        <div class="progress-bar" id="${cardId}-prog" style="width:0%"></div>
      </div>
      <div class="fc-remove" onclick="removeFile('${cardId}','${dzId}')" title="Remove file">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
        </svg>
      </div>
    </div>`;

  wrap.style.display = 'block';
  const dz = document.getElementById(dzId);
  if (dz) dz.style.display = 'none';

  // Animate the little progress bar to 100% to indicate "ready"
  setTimeout(() => {
    const pb = document.getElementById(cardId + '-prog');
    if (pb) pb.style.width = '100%';
  }, 100);
}

function removeFile(cardId, dzId) {
  const wrap = document.getElementById(cardId);
  const dz = document.getElementById(dzId);

  if (wrap) {
    wrap.style.display = 'none';
    wrap.innerHTML = '';
  }
  if (dz) {
    dz.style.display = 'block';
    // Clear the underlying file input so a fresh selection is required
    const input = dz.querySelector('input[type="file"]');
    if (input) input.value = '';
  }
}

// ================================================================
// ACCORDION TOGGLE
// Used by interview.html (question categories) and plagiarism.html
// (matched passage compare cards use a near-identical pattern,
// see toggleCompare below).
// ================================================================
function toggleAccordion(headerEl) {
  const item = headerEl.closest('.accordion-item');
  if (item) item.classList.toggle('open');
}

function toggleCompare(headerEl) {
  const card = headerEl.closest('.compare-card');
  if (!card) return;
  card.classList.toggle('open');

  const chevron = headerEl.querySelector('.accordion-chevron');
  if (chevron) {
    chevron.style.transform = card.classList.contains('open') ? 'rotate(180deg)' : '';
  }
}

// ================================================================
// COPY TO CLIPBOARD
// Used by the q-copy buttons inside interview.html question cards.
// ================================================================
function copyToClipboard(el) {
  const card = el.closest('.q-card');
  if (!card) return;

  const qText = card.querySelector('.q-text').textContent.trim();
  navigator.clipboard.writeText(qText).then(() => {
    showToast('success', 'Copied!', 'Question copied to clipboard.');
    el.style.color = 'var(--success)';
    setTimeout(() => { el.style.color = ''; }, 1500);
  }).catch(() => {
    showToast('error', 'Copy Failed', 'Could not access clipboard.');
  });
}

// ================================================================
// PASSWORD VISIBILITY TOGGLE
// Generic version: works for both login (single field) and
// register (two independent fields) by taking explicit IDs.
// Used by login.html and register.html, called from auth.js context
// but defined here since it is a shared DOM utility.
// ================================================================
function togglePassword(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(iconId);
  if (!input || !icon) return;

  if (input.type === 'password') {
    input.type = 'text';
    icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
  } else {
    input.type = 'password';
    icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
  }
}

// ================================================================
// PARTICLES CANVAS (Login / Register hero background)
// Guarded so it silently does nothing on pages without the canvas
// (i.e. dashboard, plagiarism, resume, interview, 404).
// ================================================================
function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;

  const particles = Array.from({ length: 55 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 2.5 + 0.5,
    dx: (Math.random() - 0.5) * 0.5,
    dy: (Math.random() - 0.5) * 0.5,
    opacity: Math.random() * 0.5 + 0.1,
  }));

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(99,102,241,${p.opacity})`;
      ctx.fill();
      p.x += p.dx;
      p.y += p.dy;
      if (p.x < 0 || p.x > canvas.width)  p.dx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.dy *= -1;
    });

    // Connecting lines between nearby particles
    particles.forEach((a, i) => {
      particles.slice(i + 1).forEach(b => {
        const dist = Math.hypot(a.x - b.x, a.y - b.y);
        if (dist < 100) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(99,102,241,${0.08 * (1 - dist / 100)})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      });
    });

    requestAnimationFrame(draw);
  }
  draw();

  window.addEventListener('resize', () => {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  });
}

// ================================================================
// INIT
// ================================================================
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  renderFlashMessages();
});