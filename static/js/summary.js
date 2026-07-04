/* ============================================================
   summary.js – Summarization Agent UI
   ============================================================ */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const modeSelect = document.getElementById("summaryMode");
  const topicInput = document.getElementById("summaryTopic");
  const generateBtn= document.getElementById("generateSummaryBtn");
  const btnText    = document.getElementById("summaryBtnText");
  const spinner    = document.getElementById("summarySpinner");
  const resultEl   = document.getElementById("summaryResult");
  const resultTitle= document.getElementById("summaryResultTitle");
  const contentEl  = document.getElementById("summaryContent");
  const emptyEl    = document.getElementById("summaryEmpty");
  const copyBtn    = document.getElementById("copyResult");

  const TITLES = {
    summary:    "Full Summary",
    key_points: "Key Points",
    revision:   "Revision Notes",
    topics:     "Important Topics",
  };
  const ICONS = {
    summary:    "bi-journal-check",
    key_points: "bi-key",
    revision:   "bi-pencil-square",
    topics:     "bi-bullseye",
  };

  let lastResult = "";

  generateBtn.addEventListener("click", async () => {
    const mode  = modeSelect.value;
    const topic = topicInput.value.trim();

    setLoading(true);
    try {
      const res  = await fetch("/api/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, topic }),
      });
      const data = await res.json();
      if (data.success) {
        lastResult = data.result;
        showResult(mode, data.result);
      } else {
        sgToast(data.error || "Generation failed.", "danger");
      }
    } catch (err) {
      sgToast("Network error: " + err.message, "danger");
    } finally {
      setLoading(false);
    }
  });

  copyBtn.addEventListener("click", () => sgCopyText(lastResult, copyBtn));

  function showResult(mode, text) {
    const icon = ICONS[mode] || "bi-journal-check";
    resultTitle.innerHTML = `<i class="bi ${icon} text-success me-2"></i>${TITLES[mode] || "Result"}`;
    contentEl.innerHTML   = sgFormatText(text);
    resultEl.classList.remove("d-none");
    emptyEl.classList.add("d-none");
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function setLoading(loading) {
    btnText.classList.toggle("d-none", loading);
    spinner.classList.toggle("d-none", !loading);
    generateBtn.disabled = loading;
  }
});
