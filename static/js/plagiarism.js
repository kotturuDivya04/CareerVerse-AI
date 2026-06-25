/* ================================================================
   plagiarism.js — CareerVerse AI
   Handles plagiarism.html:
     - Submits the two-file upload form via fetch()
     - Shows loading state with animated progress bar
     - Renders results: circular progress arc, status badge,
       stats, and dynamically built matched-passage compare cards
     - Wires the PDF download link once a report_id is returned

   BACKEND NOTE: POST /api/plagiarism/analyze expects multipart
   form-data with fields "file1" and "file2". Expected JSON response:
     {
       "report_id": int,
       "similarity_percent": float,
       "status": "Low" | "Moderate" | "High",
       "matched_sentences": [
         { "doc1_sentence": str, "doc2_sentence": str, "similarity": float },
         ...
       ],
       "matched_paragraphs": int,   (optional, defaults to 0)
       "words_compared": int,       (optional, defaults to 0)
       "summary": str,
       "recommendation": str
     }
   ================================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('plagiarism-form');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    runPlagiarismAnalysis(form);
  });
});

// ================================================================
// MAIN SUBMIT HANDLER
// ================================================================
function runPlagiarismAnalysis(form) {
  const file1 = document.getElementById('plag-file-1');
  const file2 = document.getElementById('plag-file-2');

  if (!file1.files.length || !file2.files.length) {
    showToast('warning', 'Missing Files', 'Please upload both documents before analyzing.');
    return;
  }

  const loading = document.getElementById('plag-loading');
  const results = document.getElementById('plag-results');
  const errorBox = document.getElementById('plag-error');
  const btn = document.getElementById('plag-analyze-btn');

  results.classList.remove('show');
  errorBox.classList.remove('show');
  loading.style.display = 'block';
  btn.disabled = true;

  // ---- Animate the indeterminate progress bar while we wait ----
  let progress = 0;
  const bar = document.getElementById('plag-progress');
  const progressInterval = setInterval(() => {
    progress += Math.random() * 12;
    if (progress >= 92) progress = 92; // hold near-complete until response arrives
    if (bar) bar.style.width = progress + '%';
  }, 200);

  // ---- Build the multipart form-data payload ----
  const formData = new FormData();
  formData.append('file1', file1.files[0]);
  formData.append('file2', file2.files[0]);

  fetch('/api/plagiarism/analyze', {
    method: 'POST',
    body: formData,
  })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
      clearInterval(progressInterval);
      if (bar) bar.style.width = '100%';

      setTimeout(() => {
        loading.style.display = 'none';
        btn.disabled = false;

        if (!ok) {
          showPlagiarismError(data.error || 'Analysis failed. Please try again.');
          return;
        }

        renderPlagiarismResults(data);
        showToast('success', 'Analysis Complete', 'Plagiarism report generated successfully.');
      }, 300);
    })
    .catch((err) => {
      clearInterval(progressInterval);
      loading.style.display = 'none';
      btn.disabled = false;
      showPlagiarismError('Could not reach the server. Please check your connection and try again.');
      console.error('Plagiarism analysis error:', err);
    });
}

// ================================================================
// ERROR STATE
// ================================================================
function showPlagiarismError(message) {
  const errorBox = document.getElementById('plag-error');
  const errorMsg = document.getElementById('plag-error-message');
  if (errorMsg) errorMsg.textContent = message;
  if (errorBox) errorBox.classList.add('show');
  showToast('error', 'Analysis Failed', message);
}

// ================================================================
// RESULTS RENDERING
// ================================================================
function renderPlagiarismResults(data) {
  const pct = Math.round(data.similarity_percent || 0);
  const status = data.status || 'Low';

  // ---- Circular progress arc ----
  // Circle circumference for r=68 is ~427 (2 * π * 68 ≈ 427.26)
  const circumference = 427;
  const offset = circumference - (circumference * pct) / 100;
  const arc = document.getElementById('plag-arc');
  const pctLabel = document.getElementById('plag-pct');

  if (arc) {
    arc.style.stroke = colorForStatus(status);
    // Animate via requestAnimationFrame so the CSS transition catches it
    requestAnimationFrame(() => {
      arc.setAttribute('stroke-dashoffset', offset);
    });
  }
  if (pctLabel) {
    pctLabel.textContent = pct + '%';
    pctLabel.style.color = colorForStatus(status);
  }

  // ---- Status text + badge ----
  const statusText = document.getElementById('plag-status-text');
  const badge = document.getElementById('plag-badge');
  if (statusText) statusText.textContent = `${status} Similarity`;
  if (badge) {
    badge.className = 'badge ' + badgeClassForStatus(status);
    badge.textContent = (status === 'High' ? '⚠ High Risk' : status === 'Moderate' ? '⚠ Moderate Risk' : '✓ Low Risk');
  }

  // ---- Summary text ----
  const summaryText = document.getElementById('plag-summary-text');
  if (summaryText) {
    summaryText.textContent = data.summary ||
      `${pct}% of the content in Document 1 matches text found in Document 2. Review the highlighted sections below for manual inspection.`;
  }

  // ---- Stat numbers ----
  const matchedSentences = data.matched_sentences || [];
  setText('plag-matched-sentences', matchedSentences.length);
  setText('plag-matched-paragraphs', data.matched_paragraphs || 0);
  setText('plag-words-compared', (data.words_compared || 0).toLocaleString());

  // ---- Matched passages list ----
  renderMatchedPassages(matchedSentences);

  // ---- Download button ----
  const downloadBtn = document.getElementById('plag-download-btn');
  if (downloadBtn && data.report_id) {
    downloadBtn.href = `/download/report/${data.report_id}`;
    downloadBtn.style.pointerEvents = 'auto';
    downloadBtn.style.opacity = '1';
  }

  document.getElementById('plag-results').classList.add('show');
}

function renderMatchedPassages(matches) {
  const container = document.getElementById('plag-matched-list');
  if (!container) return;

  if (!matches.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="es-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
        </div>
        <div class="es-title">No significant matches found</div>
        <div class="es-sub">These documents appear to be substantially original.</div>
      </div>`;
    return;
  }

  container.innerHTML = matches.map((match, index) => {
    const matchPct = Math.round(match.similarity || 0);
    const badgeClass = matchPct >= 70 ? 'badge-danger' : matchPct >= 40 ? 'badge-warning' : 'badge-success';
    const isFirst = index === 0 ? 'open' : '';
    const chevronStyle = index === 0 ? 'style="transform:rotate(180deg);"' : '';

    return `
      <div class="compare-card ${isFirst}">
        <div class="compare-header" onclick="toggleCompare(this)">
          <span class="ch-text">Match ${index + 1}</span>
          <div style="display:flex;align-items:center;gap:8px;">
            <span class="badge ${badgeClass}">${matchPct}% match</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="2" class="accordion-chevron" ${chevronStyle}><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>
        <div class="compare-body">
          <div class="para">Doc 1: "${escapeHtml(match.doc1_sentence || '')}"</div>
          <div class="para" style="border-top:1px solid var(--border);padding-top:14px;">Doc 2: "${escapeHtml(match.doc2_sentence || '')}"</div>
        </div>
      </div>`;
  }).join('');
}

// ================================================================
// HELPERS
// ================================================================
function colorForStatus(status) {
  if (status === 'High') return 'var(--danger)';
  if (status === 'Moderate') return 'var(--warning)';
  return 'var(--success)';
}

function badgeClassForStatus(status) {
  if (status === 'High') return 'badge-danger';
  if (status === 'Moderate') return 'badge-warning';
  return 'badge-success';
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}