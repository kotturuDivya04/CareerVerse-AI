/* ================================================================
   interview.js — CareerVerse AI
   Handles interview.html:
     - Submits resume + role via fetch()
     - Renders generated questions into the 4 accordion categories
       (technical, hr, project, behavioral)
     - Wires the PDF export link once a report_id is returned

   BACKEND NOTE: POST /api/interview/generate expects multipart
   form-data with fields "file" and "role". Expected JSON response:
     {
       "report_id": int,
       "role": str,
       "questions": {
         "technical":  [str, ...],
         "hr":         [str, ...],
         "project":    [str, ...],
         "behavioral": [str, ...]
       },
       "total_count": int
     }
   ================================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('interview-form');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    runInterviewGeneration(form);
  });
});

// ================================================================
// MAIN SUBMIT HANDLER
// ================================================================
function runInterviewGeneration(form) {
  const fileInput = document.getElementById('interview-file');
  const roleSelect = document.getElementById('interview-role-select');

  if (!fileInput.files.length) {
    showToast('warning', 'Resume Required', 'Please upload your resume before generating questions.');
    return;
  }

  if (!roleSelect.value) {
    showToast('warning', 'Select a Role', 'Please select a target role before generating questions.');
    return;
  }

  const loading = document.getElementById('interview-loading');
  const results = document.getElementById('interview-results');
  const errorBox = document.getElementById('interview-error');
  const btn = document.getElementById('interview-generate-btn');

  results.classList.remove('show');
  errorBox.classList.remove('show');
  loading.style.display = 'block';
  btn.disabled = true;

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('role', roleSelect.value);

  fetch('/api/interview/generate', {
    method: 'POST',
    body: formData,
  })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
      loading.style.display = 'none';
      btn.disabled = false;

      if (!ok) {
        showInterviewError(data.error || 'Question generation failed. Please try again.');
        return;
      }

      renderInterviewResults(data);
      showToast('success', 'Questions Ready', `${data.total_count || 0} interview questions generated!`);
    })
    .catch((err) => {
      loading.style.display = 'none';
      btn.disabled = false;
      showInterviewError('Could not reach the server. Please check your connection and try again.');
      console.error('Interview generation error:', err);
    });
}

// ================================================================
// ERROR STATE
// ================================================================
function showInterviewError(message) {
  const errorBox = document.getElementById('interview-error');
  const errorMsg = document.getElementById('interview-error-message');
  if (errorMsg) errorMsg.textContent = message;
  if (errorBox) errorBox.classList.add('show');
  showToast('error', 'Generation Failed', message);
}

// ================================================================
// RESULTS RENDERING
// ================================================================
function renderInterviewResults(data) {
  const questions = data.questions || {};
  const categories = ['technical', 'hr', 'project', 'behavioral'];

  // ---- Header text ----
  setText('interview-count-text', `${data.total_count || 0} Questions Generated`);
  setText('interview-role-text', `Based on your resume — ${data.role || 'Selected role'}`);

  // ---- Fill each accordion category ----
  categories.forEach(category => {
    const list = questions[category] || [];
    renderQuestionCategory(category, list);
  });

  // ---- Download button ----
  const downloadBtn = document.getElementById('interview-download-btn');
  if (downloadBtn && data.report_id) {
    downloadBtn.href = `/download/report/${data.report_id}`;
    downloadBtn.style.pointerEvents = 'auto';
    downloadBtn.style.opacity = '1';
  }

  document.getElementById('interview-results').classList.add('show');
}

function renderQuestionCategory(category, questionList) {
  const countBadge = document.getElementById(`interview-${category}-count`);
  const listContainer = document.getElementById(`interview-${category}-list`);

  if (countBadge) countBadge.textContent = `${questionList.length} Qs`;
  if (!listContainer) return;

  if (!questionList.length) {
    listContainer.innerHTML = `
      <div class="empty-state" style="padding:30px 16px;">
        <div class="es-sub">No ${category} questions were generated for this resume.</div>
      </div>`;
    return;
  }

  listContainer.innerHTML = questionList.map((question, index) => `
    <div class="q-card">
      <div class="q-text"><span class="q-num">${index + 1}</span>${escapeHtml(question)}</div>
      <span class="q-copy" onclick="copyToClipboard(this)" title="Copy question">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      </span>
    </div>`).join('');
}

// ================================================================
// HELPERS
// ================================================================
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}