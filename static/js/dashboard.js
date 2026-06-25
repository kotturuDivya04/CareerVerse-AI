/* ================================================================
   dashboard.js — CareerVerse AI
   Renders the Analysis Trend bar chart from server-provided data
   and adds small entrance animations to the stat cards.

   BACKEND NOTE: dashboard.html embeds a hidden element:
     <div id="chart-data" data-chart='{{ chart_data | safe }}'></div>
   where chart_data is a JSON string built by app.py's
   _get_weekly_chart_data() helper, e.g.:
     [{"day":"Mon","count":3}, {"day":"Tue","count":5}, ...]
   This script reads that JSON and redraws the demo SVG bars with
   real values once the backend is connected. If no data attribute
   is present (or it's an empty array), the static demo bars
   already in the HTML are left untouched.
   ================================================================ */

document.addEventListener('DOMContentLoaded', () => {
  renderTrendChart();
  animateStatValues();
});

// ================================================================
// ANALYSIS TREND BAR CHART
// ================================================================
function renderTrendChart() {
  const dataEl = document.getElementById('chart-data');
  const svg = document.getElementById('trend-bar-chart');
  if (!dataEl || !svg) return;

  let chartData = [];
  try {
    chartData = JSON.parse(dataEl.getAttribute('data-chart') || '[]');
  } catch (e) {
    chartData = [];
  }

  // No real data yet (frontend phase) — keep the existing demo bars.
  if (!Array.isArray(chartData) || chartData.length === 0) return;

  // ---- Layout constants (match the original 400x160 viewBox) ----
  const viewWidth = 400;
  const viewHeight = 160;
  const chartTop = 30;       // topmost y a full-height bar can reach
  const chartBottom = 150;   // baseline y where every bar starts
  const maxBarHeight = chartBottom - chartTop;
  const barWidth = 40;
  const slotWidth = viewWidth / chartData.length;

  const counts = chartData.map(d => d.count || 0);
  const maxCount = Math.max(...counts, 1); // avoid divide-by-zero

  // Clear everything except the <defs> gradient definition
  const defs = svg.querySelector('defs');
  svg.innerHTML = '';
  if (defs) svg.appendChild(defs);

  chartData.forEach((point, index) => {
    const barHeight = Math.max((point.count / maxCount) * maxBarHeight, 4);
    const x = slotWidth * index + (slotWidth - barWidth) / 2;
    const y = chartBottom - barHeight;

    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', x);
    rect.setAttribute('y', y);
    rect.setAttribute('width', barWidth);
    rect.setAttribute('height', barHeight);
    rect.setAttribute('rx', 6);
    rect.setAttribute('fill', 'url(#barGrad)');
    svg.appendChild(rect);

    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', x + barWidth / 2);
    label.setAttribute('y', 158);
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('fill', '#94A3B8');
    label.setAttribute('font-size', '10');
    label.textContent = point.day || '';
    svg.appendChild(label);
  });
}

// ================================================================
// STAT CARD ENTRANCE ANIMATION
// Purely cosmetic — counts up from 0 to the server-rendered value
// on first paint, reading the number already in the DOM (works
// whether it's a real backend value or the demo fallback).
// ================================================================
function animateStatValues() {
  const valueEls = document.querySelectorAll('.stat-card .stat-value');

  valueEls.forEach(el => {
    const raw = el.textContent.trim();
    const target = parseInt(raw.replace(/[^\d]/g, ''), 10);

    // Skip values that aren't plain numbers (e.g. "12/17") to avoid
    // mangling formatted text.
    if (isNaN(target) || String(target) !== raw) return;

    let current = 0;
    const duration = 900; // ms
    const steps = 30;
    const increment = target / steps;
    const stepTime = duration / steps;

    el.textContent = '0';

    const interval = setInterval(() => {
      current += increment;
      if (current >= target) {
        el.textContent = target;
        clearInterval(interval);
      } else {
        el.textContent = Math.floor(current);
      }
    }, stepTime);
  });
}