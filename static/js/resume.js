/* ================================================================
   resume.js — CareerVerse AI
   Handles resume.html:
     - Submits resume + target role via fetch()
     - Renders ATS analysis results (score, role match, skills,
       strengths, suggestions)
     - Renders Job Role Recommender results on the SAME page,
       directly below the ATS results, from the same upload
     - Wires the PDF download link(s) once report_id(s) are returned

   ASSUMPTION / VERIFY AGAINST YOUR resume.html:
   This script expects the following element IDs to exist. If your
   resume.html (generated separately) uses different IDs, update
   either the HTML or the constants below so they match:

     Form:               #resume-form
     File input:          #resume-file
     Drop zone:            #dz-resume
     File card container:  #resume-file-card
     Role select:          #role-select
     Submit button:        #resume-analyze-btn

     Loading state:        #resume-loading
     Error state:          #resume-error
     Error message text:   #resume-error-message

     ATS results section:  #resume-ats-results
     ATS score value:      #resume-ats-score
     Role match value:     #resume-role-match-score
     Skills matched value: #resume-skills-matched-count
     Skills found list:    #resume-skills-found-list
     Missing skills list:  #resume-missing-skills-list
     Strengths list:       #resume-strengths-list
     Suggestions list:     #resume-suggestions-list
     ATS download button:  #resume-download-btn

     Job Recommender section: #resume-job-recommender-results
     Job role cards container: #resume-role-cards-list
     Job recommender download: #resume-job-download-btn

   BACKEND NOTE: POST /api/resume/analyze expects multipart
   form-data with fields "file" and "role". Expected JSON response:
     {
       "report_id": int,
       "ats_score": float,
       "role_match_score": float,
       "skills_found": [str, ...],
       "missing_skills": [str, ...],
       "strengths": [str, ...],
       "suggestions": [str, ...],
       "section_scores": { "projects": float, "skills": float,
                            "experience": float, "role_match": float,
                            "achievements": float, "certifications": float },
       "job_recommendations": {
         "report_id": int,
         "recommended_roles": [
           {
             "role": str,
             "match_percent": float,
             "matched_skills": [str, ...],
             "missing_skills": [str, ...],
             "strengths": [str, ...],
             "suggestions": [str, ...]
           },
           ...
         ]
       }
     }

   The Job Role Recommender is NOT a separate upload — it runs as
   part of the same /api/resume/analyze call and its results are
   nested under "job_recommendations" in the same JSON response.
   ================================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('resume-form');
  if (!form) return;

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    runResumeAnalysis(form);
  });
});

// ================================================================
// MAIN SUBMIT HANDLER
// ================================================================
function runResumeAnalysis(form) {
  const fileInput = document.getElementById('resume-file');
  const roleSelect = document.getElementById('role-select');

  if (!fileInput || !fileInput.files.length) {
    showToast('warning', 'Resume Required', 'Please upload your resume before analyzing.');
    return;
  }

  if (!roleSelect || !roleSelect.value) {
    showToast('warning', 'Select a Role', 'Please select a target role before analyzing.');
    return;
  }

  const loading = document.getElementById('resume-loading');
  const atsResults = document.getElementById('resume-ats-results');
  const jobResults = document.getElementById('resume-job-recommender-results');
  const errorBox = document.getElementById('resume-error');
  const btn = document.getElementById('resume-analyze-btn');

  if (atsResults) atsResults.classList.remove('show');
  if (jobResults) jobResults.classList.remove('show');
  if (errorBox) errorBox.classList.remove('show');
  if (loading) loading.style.display = 'block';
  if (btn) btn.disabled = true;

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('role', roleSelect.value);

  fetch('/api/resume/analyze', {
    method: 'POST',
    body: formData,
  })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
      if (loading) loading.style.display = 'none';
      if (btn) btn.disabled = false;

      if (!ok) {
        showResumeError(data.error || 'Resume analysis failed. Please try again.');
        return;
      }

      renderAtsResults(data);

      // Job recommendations arrive nested in the same response —
      // render them immediately below the ATS results, no second upload.
      if (data.job_recommendations) {
        renderJobRecommendations(data.job_recommendations);
      }

      showToast('success', 'Resume Analyzed', `ATS report generated. Score: ${Math.round(data.ats_score || 0)}/100.`);
    })
    .catch((err) => {
      if (loading) loading.style.display = 'none';
      if (btn) btn.disabled = false;
      showResumeError('Could not reach the server. Please check your connection and try again.');
      console.error('Resume analysis error:', err);
    });
}

// ================================================================
// ERROR STATE
// ================================================================
function showResumeError(message) {
  const errorBox = document.getElementById('resume-error');
  const errorMsg = document.getElementById('resume-error-message');
  if (errorMsg) errorMsg.textContent = message;
  if (errorBox) errorBox.classList.add('show');
  showToast('error', 'Analysis Failed', message);
}

// ================================================================
// ATS RESULTS RENDERING
// ================================================================
function renderAtsResults(data) {
  const atsScore = Math.round(data.ats_score || 0);
  const roleMatch = Math.round(data.role_match_score || 0);
  const skillsFound = data.skills_found || [];
  const missingSkills = data.missing_skills || [];

  setText('resume-ats-score', atsScore);
  setText('resume-role-match-score', roleMatch + '%');
  setText('resume-skills-matched-count', `${skillsFound.length}/${skillsFound.length + missingSkills.length}`);

  setProgressWidth('resume-ats-score-bar', atsScore);
  setProgressWidth('resume-role-match-bar', roleMatch);
  setProgressWidth('resume-skills-matched-bar',
    skillsFound.length + missingSkills.length > 0
      ? (skillsFound.length / (skillsFound.length + missingSkills.length)) * 100
      : 0
  );

  renderChipList('resume-skills-found-list', skillsFound, 'chip chip-success');
  renderChipList('resume-missing-skills-list', missingSkills, 'chip chip-missing');

  renderRecCardList('resume-strengths-list', data.strengths || [], 'success', okIcon());
  renderRecCardList('resume-suggestions-list', data.suggestions || [], 'warning', warnIcon());

  const downloadBtn = document.getElementById('resume-download-btn');
  if (downloadBtn && data.report_id) {
    downloadBtn.href = `/download/report/${data.report_id}`;
    downloadBtn.style.pointerEvents = 'auto';
    downloadBtn.style.opacity = '1';
  }

  const atsResults = document.getElementById('resume-ats-results');
  if (atsResults) atsResults.classList.add('show');
}

// ================================================================
// JOB ROLE RECOMMENDER RENDERING
// Renders directly underneath the ATS results on the same page —
// this is intentionally NOT a separate page/route.
// ================================================================
function renderJobRecommendations(jobData) {
  const container = document.getElementById('resume-role-cards-list');
  const section = document.getElementById('resume-job-recommender-results');
  if (!container || !section) return;

  const roles = jobData.recommended_roles || [];

  if (!roles.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="es-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </div>
        <div class="es-title">No strong role matches found</div>
        <div class="es-sub">Try uploading a more detailed resume or selecting a different target role.</div>
      </div>`;
    section.classList.add('show');
    return;
  }

  // Sort by match_percent descending so the top role is always first
  const sorted = [...roles].sort((a, b) => (b.match_percent || 0) - (a.match_percent || 0));

  container.innerHTML = sorted.map((role, index) => {
    const matchPct = Math.round(role.match_percent || 0);
    const isTop = index === 0;
    const matchedSkills = role.matched_skills || [];
    const missingSkills = role.missing_skills || [];

    return `
      <div class="role-card ${isTop ? 'top-match' : ''}">
        <div class="role-card-header">
          <div style="display:flex;align-items:center;gap:10px;">
            <span class="role-card-title">${escapeHtml(role.role || '')}</span>
            ${isTop ? '<span class="badge badge-primary">Top Match</span>' : ''}
          </div>
          <span class="role-card-match">${matchPct}%</span>
        </div>

        <div class="progress-wrap" style="margin-bottom:16px;">
          <div class="progress-bar" style="width:${matchPct}%;"></div>
        </div>

        <div style="display:flex;flex-direction:column;gap:10px;">
          ${matchedSkills.length ? `
          <div>
            <div class="text-xs text-muted" style="margin-bottom:6px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Matched Skills</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
              ${matchedSkills.map(s => `<span class="chip chip-success">${escapeHtml(s)}</span>`).join('')}
            </div>
          </div>` : ''}

          ${missingSkills.length ? `
          <div>
            <div class="text-xs text-muted" style="margin-bottom:6px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Missing Skills</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
              ${missingSkills.map(s => `<span class="chip chip-missing">${escapeHtml(s)}</span>`).join('')}
            </div>
          </div>` : ''}
        </div>
      </div>`;
  }).join('');

  section.classList.add('show');
}

// ================================================================
// HELPERS
// ================================================================
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setProgressWidth(id, percent) {
  const el = document.getElementById(id);
  if (el) el.style.width = Math.max(0, Math.min(100, percent)) + '%';
}

function renderChipList(containerId, items, chipClass) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!items.length) {
    container.innerHTML = `<span class="text-muted text-sm">None found.</span>`;
    return;
  }
  container.innerHTML = items.map(item => `<span class="${chipClass}">${escapeHtml(item)}</span>`).join('');
}

function renderRecCardList(containerId, items, type, iconSvg) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!items.length) {
    container.innerHTML = `<span class="text-muted text-sm">Nothing to show.</span>`;
    return;
  }

  const bgVar = type === 'success' ? 'var(--success-bg)' : 'var(--warning-bg)';
  const colorVar = type === 'success' ? 'var(--success)' : 'var(--warning)';

  container.innerHTML = items.map(text => `
    <div class="rec-card" style="border:none;padding:0;">
      <div class="rec-icon" style="background:${bgVar};color:${colorVar};">
        ${iconSvg}
      </div>
      <div class="rec-body">
        <div class="rec-text">${escapeHtml(text)}</div>
      </div>
    </div>`).join('');
}

function okIcon() {
  return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/></svg>';
}

function warnIcon() {
  return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}