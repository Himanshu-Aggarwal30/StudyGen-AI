/* ============================================================
   planner.js – Study Planner Agent UI
   ============================================================ */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const resultEl  = document.getElementById("plannerResult");
  const contentEl = document.getElementById("plannerContent");
  const emptyEl   = document.getElementById("plannerEmpty");
  const copyBtn   = document.getElementById("copyPlan");

  let lastResult = "";

  // ── Tab switching ───────────────────────────────────────
  document.querySelectorAll("#plannerTabs .nav-link").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll("#plannerTabs .nav-link").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".sg-planner-tab").forEach((p) => p.classList.add("d-none"));
      tab.classList.add("active");
      const target = document.getElementById("tab-" + tab.dataset.tab);
      if (target) target.classList.remove("d-none");
      resultEl.classList.add("d-none");
      emptyEl.classList.remove("d-none");
    });
  });

  // ── Full Study Plan ─────────────────────────────────────
  document.getElementById("generatePlanBtn")?.addEventListener("click", async () => {
    const subject   = document.getElementById("planSubject").value.trim();
    const examDate  = document.getElementById("planExamDate").value;
    const dailyHrs  = document.getElementById("planHours").value;
    const topics    = document.getElementById("planTopics").value.trim();
    const level     = document.getElementById("planLevel").value;

    if (!subject || !examDate) { sgToast("Subject and exam date are required.", "warning"); return; }
    await callPlanner("plan", { subject, exam_date: examDate, daily_hours: parseFloat(dailyHrs), topics, current_level: level }, "planBtnText", "planSpinner");
  });

  // ── Weekly Schedule ─────────────────────────────────────
  document.getElementById("generateWeeklyBtn")?.addEventListener("click", async () => {
    const subjectsRaw = document.getElementById("weeklySubjects").value.trim();
    const subjects    = subjectsRaw ? subjectsRaw.split(",").map((s) => s.trim()) : [];
    const dailyHrs    = document.getElementById("weeklyHours").value;
    const week        = document.getElementById("weeklyWeek").value;

    if (!subjects.length) { sgToast("Enter at least one subject.", "warning"); return; }
    await callPlanner("weekly", { subjects, daily_hours: parseFloat(dailyHrs), week: parseInt(week) }, "weeklyBtnText", "weeklySpinner");
  });

  // ── Exam Tips ───────────────────────────────────────────
  document.getElementById("generateTipsBtn")?.addEventListener("click", async () => {
    const subject  = document.getElementById("tipsSubject").value.trim();
    const examType = document.getElementById("tipsExamType").value;
    if (!subject) { sgToast("Subject is required.", "warning"); return; }
    await callPlanner("tips", { subject, exam_type: examType }, "tipsBtnText", "tipsSpinner");
  });

  // ── Revision Checklist ──────────────────────────────────
  document.getElementById("generateChecklistBtn")?.addEventListener("click", async () => {
    const subject    = document.getElementById("checklistSubject").value.trim();
    const topicsRaw  = document.getElementById("checklistTopics").value.trim();
    const topics     = topicsRaw ? topicsRaw.split(",").map((t) => t.trim()) : [];
    await callPlanner("checklist", { subject, topics }, "checklistBtnText", "checklistSpinner");
  });

  // ── Copy ────────────────────────────────────────────────
  copyBtn.addEventListener("click", () => sgCopyText(lastResult, copyBtn));

  // ── Shared fetch ─────────────────────────────────────────
  async function callPlanner(action, payload, btnTextId, spinnerId) {
    const btnText = document.getElementById(btnTextId);
    const spinner = document.getElementById(spinnerId);
    setLoading(true, btnText, spinner);
    try {
      const res  = await fetch("/api/planner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, ...payload }),
      });
      const data = await res.json();
      if (data.success) {
        lastResult = data.result;
        contentEl.innerHTML = sgFormatText(data.result);
        resultEl.classList.remove("d-none");
        emptyEl.classList.add("d-none");
        resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
      } else {
        sgToast(data.error || "Planning failed.", "danger");
      }
    } catch (err) {
      sgToast("Network error: " + err.message, "danger");
    } finally {
      setLoading(false, btnText, spinner);
    }
  }

  function setLoading(loading, btnText, spinner) {
    if (btnText) btnText.classList.toggle("d-none", loading);
    if (spinner) spinner.classList.toggle("d-none", !loading);
  }
});
