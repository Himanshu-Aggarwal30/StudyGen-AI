/* ============================================================
   quiz.js – Quiz Generation Agent UI
   ============================================================ */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const typeSelect = document.getElementById("quizType");
  const countSelect= document.getElementById("quizCount");
  const topicInput = document.getElementById("quizTopic");
  const generateBtn= document.getElementById("generateQuizBtn");
  const btnText    = document.getElementById("quizBtnText");
  const spinner    = document.getElementById("quizSpinner");
  const resultEl   = document.getElementById("quizResult");
  const resultTitle= document.getElementById("quizResultTitle");
  const contentEl  = document.getElementById("quizContent");
  const emptyEl    = document.getElementById("quizEmpty");
  const copyBtn    = document.getElementById("copyQuiz");

  let lastResult = "";

  generateBtn.addEventListener("click", async () => {
    const type  = typeSelect.value;
    const count = parseInt(countSelect.value, 10);
    const topic = topicInput.value.trim();

    setLoading(true);
    try {
      const res  = await fetch("/api/quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, count, topic }),
      });
      const data = await res.json();
      if (data.success) {
        if (type === "mixed" && typeof data.result === "object") {
          lastResult = [data.result.mcq, data.result.short_answer, data.result.long_answer].join("\n\n---\n\n");
          showMixed(data.result);
        } else {
          lastResult = data.result;
          showResult(type, data.result);
        }
      } else {
        sgToast(data.error || "Quiz generation failed.", "danger");
      }
    } catch (err) {
      sgToast("Network error: " + err.message, "danger");
    } finally {
      setLoading(false);
    }
  });

  copyBtn.addEventListener("click", () => sgCopyText(lastResult, copyBtn));

  function showResult(type, text) {
    const labels = { mcq: "MCQ Questions", short: "Short-Answer Questions", long: "Long-Answer Questions" };
    resultTitle.innerHTML = `<i class="bi bi-patch-check text-warning me-2"></i>${labels[type] || "Quiz"}`;
    contentEl.innerHTML   = sgFormatText(text);
    resultEl.classList.remove("d-none");
    emptyEl.classList.add("d-none");
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showMixed(result) {
    resultTitle.innerHTML = '<i class="bi bi-patch-check text-warning me-2"></i>Mixed Quiz';
    contentEl.innerHTML = `
      <h5 class="fw-bold text-primary mb-3">Multiple Choice Questions</h5>
      ${sgFormatText(result.mcq)}
      <hr class="my-4"/>
      <h5 class="fw-bold text-success mb-3">Short-Answer Questions</h5>
      ${sgFormatText(result.short_answer)}
      <hr class="my-4"/>
      <h5 class="fw-bold text-danger mb-3">Long-Answer Questions</h5>
      ${sgFormatText(result.long_answer)}`;
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
