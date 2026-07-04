/* ============================================================
   upload.js – Document Processing Agent UI
   ============================================================ */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const dropZone   = document.getElementById("dropZone");
  const fileInput  = document.getElementById("fileInput");
  const filePreview = document.getElementById("filePreview");
  const fileName   = document.getElementById("fileName");
  const fileSize   = document.getElementById("fileSize");
  const removeFile = document.getElementById("removeFile");
  const uploadBtn  = document.getElementById("uploadBtn");
  const uploadBtnText = document.getElementById("uploadBtnText");
  const uploadSpinner = document.getElementById("uploadSpinner");
  const progressSection = document.getElementById("progressSection");
  const uploadResult = document.getElementById("uploadResult");
  const uploadProgress = document.getElementById("uploadProgress");
  const procSteps  = document.querySelectorAll(".sg-proc-step");

  let selectedFile = null;

  // ── File selection ──────────────────────────────────────
  fileInput.addEventListener("change", () => handleFile(fileInput.files[0]));

  dropZone.addEventListener("click", (e) => {
    if (e.target === dropZone || e.target.tagName !== "LABEL") fileInput.click();
  });
  dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  removeFile.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    filePreview.classList.add("d-none");
    uploadBtn.classList.add("d-none");
    uploadResult.classList.add("d-none");
    uploadResult.innerHTML = "";
  });

  function handleFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      sgToast("Only PDF files are supported.", "danger");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      sgToast("File exceeds 50 MB limit.", "danger");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    filePreview.classList.remove("d-none");
    uploadBtn.classList.remove("d-none");
    uploadBtn.disabled = false;
    uploadResult.classList.add("d-none");
  }

  // ── Upload ───────────────────────────────────────────────
  uploadBtn.addEventListener("click", async () => {
    if (!selectedFile) return;
    setUploading(true);
    progressSection.classList.remove("d-none");
    animateSteps();

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res  = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      showResult(data);
    } catch (err) {
      showResult({ success: false, error: "Network error: " + err.message });
    } finally {
      setUploading(false);
    }
  });

  // ── UI helpers ───────────────────────────────────────────
  function setUploading(uploading) {
    uploadBtnText.classList.toggle("d-none", uploading);
    uploadSpinner.classList.toggle("d-none", !uploading);
    uploadBtn.disabled = uploading;
  }

  function animateSteps() {
    uploadProgress.style.width = "0%";
    procSteps.forEach((s) => { s.classList.remove("done"); s.style.opacity = "0.3"; });
    let i = 0;
    const interval = setInterval(() => {
      if (i < procSteps.length) {
        procSteps[i].style.opacity = "1";
        procSteps[i].classList.add("done");
        procSteps[i].querySelector(".sg-proc-icon i").className = "bi bi-check-circle-fill text-success";
        uploadProgress.style.width = ((i + 1) / procSteps.length * 100) + "%";
        i++;
      } else {
        clearInterval(interval);
      }
    }, 600);
  }

  function showResult(data) {
    uploadResult.classList.remove("d-none");
    if (data.success) {
      uploadResult.innerHTML = `
        <div class="alert alert-success d-flex gap-3 align-items-start">
          <i class="bi bi-check-circle-fill fs-4 flex-shrink-0 mt-1"></i>
          <div>
            <div class="fw-bold mb-1">Document processed successfully!</div>
            <div class="small">
              📄 <strong>${escHtml(data.filename)}</strong><br>
              📦 ${data.total_chunks} chunks indexed &nbsp;·&nbsp;
              📝 ${data.word_count?.toLocaleString() || "–"} words<br>
              <span class="text-success fw-semibold">✅ Knowledge base ready – All 6 AI agents are active!</span>
            </div>
            <div class="mt-3 d-flex flex-wrap gap-2">
              <a href="/chat"      class="btn btn-sm btn-success rounded-pill">Ask AI Tutor</a>
              <a href="/summary"   class="btn btn-sm btn-outline-success rounded-pill">Summarize</a>
              <a href="/quiz"      class="btn btn-sm btn-outline-success rounded-pill">Generate Quiz</a>
              <a href="/planner"   class="btn btn-sm btn-outline-success rounded-pill">Study Planner</a>
            </div>
          </div>
        </div>`;
    } else {
      uploadResult.innerHTML = `
        <div class="alert alert-danger">
          <i class="bi bi-exclamation-circle me-2"></i>
          <strong>Error:</strong> ${escHtml(data.error || "Upload failed.")}
        </div>`;
    }
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }
});
