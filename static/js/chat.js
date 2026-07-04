/* ============================================================
   chat.js – Doubt Solving Agent chat interface
   ============================================================ */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const messages  = document.getElementById("chatMessages");
  const input     = document.getElementById("chatInput");
  const sendBtn   = document.getElementById("sendBtn");
  const sendIcon  = document.getElementById("sendIcon");
  const sendSpin  = document.getElementById("sendSpinner");
  const clearBtn  = document.getElementById("clearChat");
  const suggestions = document.querySelectorAll(".sg-chip");

  let history = [];
  let sending  = false;

  // ── Auto-resize textarea ────────────────────────────────
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 180) + "px";
  });

  // ── Send on Enter (Shift+Enter = new line) ──────────────
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
  sendBtn.addEventListener("click", send);

  // ── Suggestion chips ────────────────────────────────────
  suggestions.forEach((chip) => {
    chip.addEventListener("click", () => {
      input.value = chip.dataset.msg;
      input.dispatchEvent(new Event("input"));
      send();
    });
  });

  // ── Clear chat ──────────────────────────────────────────
  clearBtn.addEventListener("click", () => {
    history = [];
    // Remove all messages except welcome
    const allMsgs = messages.querySelectorAll(".sg-msg");
    allMsgs.forEach((m, i) => { if (i > 0) m.remove(); });
    const sugg = document.getElementById("suggestions");
    if (sugg) sugg.classList.remove("d-none");
  });

  // ── Send message ────────────────────────────────────────
  async function send() {
    const msg = input.value.trim();
    if (!msg || sending) return;

    sending = true;
    setSending(true);
    input.value = "";
    input.style.height = "auto";

    // Hide suggestions after first message
    const sugg = document.getElementById("suggestions");
    if (sugg) sugg.classList.add("d-none");

    appendMsg("user", msg);
    const typingEl = appendTyping();

    try {
      const res  = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history }),
      });
      const data = await res.json();
      typingEl.remove();

      const answer = data.success ? data.answer : "Sorry, I couldn't generate a response. " + (data.error || "");
      appendMsg("ai", answer);
      history.push(["user", msg], ["ai", answer]);
      // Keep history to last 12 turns
      if (history.length > 24) history = history.slice(-24);
    } catch (err) {
      typingEl.remove();
      appendMsg("ai", "Network error: " + err.message);
    } finally {
      sending = false;
      setSending(false);
      input.focus();
    }
  }

  // ── DOM helpers ──────────────────────────────────────────
  function appendMsg(role, text) {
    const isUser = role === "user";
    const div = document.createElement("div");
    div.className = `sg-msg d-flex gap-3 mb-3 ${isUser ? "sg-msg-user" : "sg-msg-ai"}`;

    const avatarHtml = isUser
      ? `<div class="sg-avatar bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width:36px;height:36px;min-width:36px;"><i class="bi bi-person-fill"></i></div>`
      : `<div class="sg-avatar bg-primary text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width:36px;height:36px;min-width:36px;"><i class="bi bi-robot"></i></div>`;

    const bubbleClass = isUser ? "sg-bubble-user" : "sg-bubble-ai";
    div.innerHTML = `
      ${isUser ? "" : avatarHtml}
      <div class="sg-bubble ${bubbleClass} p-3 rounded-4">${isUser ? escHtml(text) : sgFormatText(text)}</div>
      ${isUser ? avatarHtml : ""}`;

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function appendTyping() {
    const div = document.createElement("div");
    div.className = "sg-msg sg-msg-ai d-flex gap-3 mb-3";
    div.innerHTML = `
      <div class="sg-avatar bg-primary text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" style="width:36px;height:36px;min-width:36px;"><i class="bi bi-robot"></i></div>
      <div class="sg-bubble sg-bubble-ai p-3 rounded-4 sg-typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function setSending(s) {
    sendIcon.classList.toggle("d-none", s);
    sendSpin.classList.toggle("d-none", !s);
    sendBtn.disabled = s;
  }
});
