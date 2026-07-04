/* ============================================================
   studygen.js – Global utilities and dark mode toggle
   ============================================================ */

"use strict";

// ── Dark mode ─────────────────────────────────────────────
(function () {
  const THEME_KEY = "sg-theme";
  const html = document.documentElement;
  const saved = localStorage.getItem(THEME_KEY) || "light";
  html.setAttribute("data-bs-theme", saved);

  document.addEventListener("DOMContentLoaded", () => {
    const btn  = document.getElementById("themeToggle");
    const icon = document.getElementById("themeIcon");
    if (!btn) return;

    const apply = (theme) => {
      html.setAttribute("data-bs-theme", theme);
      localStorage.setItem(THEME_KEY, theme);
      icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
    };
    apply(saved);

    btn.addEventListener("click", () => {
      apply(html.getAttribute("data-bs-theme") === "dark" ? "light" : "dark");
    });
  });
})();

// ── Active nav link highlight ─────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const links = document.querySelectorAll(".sg-navbar .nav-link");
  const path  = window.location.pathname.replace(/\/$/, "") || "/";
  links.forEach((a) => {
    const href = a.getAttribute("href")?.replace(/\/$/, "") || "";
    if (href === path || (href !== "/" && path.startsWith(href))) {
      a.classList.add("active");
    }
  });
});

// ── Shared helpers ─────────────────────────────────────────

/**
 * Convert plain text (possibly with markdown-ish formatting) to HTML.
 * Handles **bold**, ## headings, bullet lists, horizontal rules.
 */
function sgFormatText(text) {
  if (!text) return "";
  let html = escHtml(text);
  // Headings  ## / ###
  html = html.replace(/^### (.+)$/gm, "<h6 class='fw-bold mt-3 mb-1'>$1</h6>");
  html = html.replace(/^## (.+)$/gm,  "<h5 class='fw-bold mt-4 mb-2'>$1</h5>");
  html = html.replace(/^# (.+)$/gm,   "<h4 class='fw-bold mt-4 mb-2'>$1</h4>");
  // Bold  **text**
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Italic *text*
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  // Hr ---
  html = html.replace(/^---+$/gm, "<hr class='my-3' />");
  // Bullet lists  - item
  html = html.replace(/^[•\-] (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/gs, (m) => `<ul class='mb-2'>${m}</ul>`);
  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");
  // Line breaks
  html = html.replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br />");
  return `<p>${html}</p>`;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Show a Bootstrap toast (auto-created if not present).
 */
function sgToast(message, type = "info") {
  const colours = { success: "bg-success", danger: "bg-danger", info: "bg-primary", warning: "bg-warning text-dark" };
  let container = document.getElementById("sgToastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "sgToastContainer";
    container.className = "toast-container position-fixed bottom-0 end-0 p-3";
    container.style.zIndex = 9999;
    document.body.appendChild(container);
  }
  const id = "toast-" + Date.now();
  container.insertAdjacentHTML("beforeend", `
    <div id="${id}" class="toast align-items-center text-white ${colours[type] || "bg-secondary"} border-0" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">${escHtml(message)}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`);
  const el = document.getElementById(id);
  new bootstrap.Toast(el, { delay: 3500 }).show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
}

/**
 * Copy text to clipboard and show feedback on a button.
 */
function sgCopyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Copied!';
      setTimeout(() => (btn.innerHTML = orig), 2000);
    }
    sgToast("Copied to clipboard!", "success");
  }).catch(() => sgToast("Failed to copy.", "danger"));
}
