/* ============================================================
   flashcards.js – Flashcard Generator UI
   ============================================================ */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const topicInput  = document.getElementById("flashTopic");
  const countSelect = document.getElementById("flashCount");
  const generateBtn = document.getElementById("generateFlashBtn");
  const btnText     = document.getElementById("flashBtnText");
  const spinner     = document.getElementById("flashSpinner");
  const section     = document.getElementById("flashcardsSection");
  const emptyEl     = document.getElementById("flashEmpty");
  const flipper     = document.getElementById("cardFlipper");
  const cardFront   = document.getElementById("cardFront");
  const cardBack    = document.getElementById("cardBack");
  const prevBtn     = document.getElementById("prevCard");
  const nextBtn     = document.getElementById("nextCard");
  const progress    = document.getElementById("flashProgress");
  const rawContent  = document.getElementById("flashRawContent");
  const flashTitle  = document.getElementById("flashCardTitle");

  let cards = [];
  let current = 0;

  generateBtn.addEventListener("click", async () => {
    const topic = topicInput.value.trim();
    const count = parseInt(countSelect.value, 10);

    setLoading(true);
    try {
      const res  = await fetch("/api/flashcards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, count }),
      });
      const data = await res.json();
      if (data.success) {
        cards = parseCards(data.result, count);
        rawContent.innerHTML = sgFormatText(data.result);
        flashTitle.textContent = `Flashcards (${cards.length} cards)`;
        section.classList.remove("d-none");
        emptyEl.classList.add("d-none");
        current = 0;
        showCard(0);
      } else {
        sgToast(data.error || "Flashcard generation failed.", "danger");
      }
    } catch (err) {
      sgToast("Network error: " + err.message, "danger");
    } finally {
      setLoading(false);
    }
  });

  // ── Flipper click ────────────────────────────────────────
  document.querySelector(".sg-card-scene")?.addEventListener("click", () => {
    flipper.classList.toggle("flipped");
  });

  // ── Navigation ──────────────────────────────────────────
  prevBtn.addEventListener("click", () => {
    if (current > 0) { current--; showCard(current); }
  });
  nextBtn.addEventListener("click", () => {
    if (current < cards.length - 1) { current++; showCard(current); }
  });

  function showCard(idx) {
    const c = cards[idx];
    if (!c) return;
    flipper.classList.remove("flipped");
    setTimeout(() => {
      cardFront.textContent = c.front;
      cardBack.innerHTML    = sgFormatText(c.back);
    }, 150);
    progress.textContent  = `${idx + 1} / ${cards.length}`;
    prevBtn.disabled = idx === 0;
    nextBtn.disabled = idx === cards.length - 1;
  }

  /**
   * Parse the AI-generated flashcard text into [{front, back}] objects.
   * Handles the format: FRONT: ...\nBACK: ...
   */
  function parseCards(text, expectedCount) {
    const cardBlocks = text.split(/\*\*Card \d+\*\*|\n---\n/).filter((b) => b.trim());
    const parsed = [];
    for (const block of cardBlocks) {
      const frontMatch = block.match(/FRONT:\s*(.+?)(?:\n|$)/i);
      const backMatch  = block.match(/BACK:\s*([\s\S]+?)(?=FRONT:|$)/i);
      if (frontMatch) {
        parsed.push({
          front: frontMatch[1].trim(),
          back:  backMatch ? backMatch[1].trim() : "See notes",
        });
      }
    }
    // Fallback: split by numbered pattern if parsing failed
    if (parsed.length === 0) {
      const lines = text.split("\n").filter((l) => l.trim());
      for (let i = 0; i < lines.length; i += 2) {
        parsed.push({ front: lines[i] || "?", back: lines[i + 1] || "See notes" });
      }
    }
    return parsed.slice(0, expectedCount);
  }

  function setLoading(loading) {
    btnText.classList.toggle("d-none", loading);
    spinner.classList.toggle("d-none", !loading);
    generateBtn.disabled = loading;
  }
});
