// --- Menu mobile (drawer) site ---
(function () {
  const openBtn = document.querySelector("[data-site-open]");
  const closeEls = document.querySelectorAll("[data-site-close]");

  function openMenu() {
    document.body.classList.add("site-open");
  }
  function closeMenu() {
    document.body.classList.remove("site-open");
  }

  openBtn?.addEventListener("click", openMenu);
  closeEls.forEach((el) => el.addEventListener("click", closeMenu));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });
})();

// --- Form loading animation (✅ CSRF SAFE) ---
(function () {
  document.addEventListener("submit", (e) => {
    const form = e.target.closest("form[data-loading-form]");
    if (!form) return;

    const btn = form.querySelector("button[type='submit']");
    if (!btn) return;

    // ✅ On n’empêche pas l’envoi du CSRF (on ne désactive pas les inputs)
    btn.classList.add("is-loading");
    btn.disabled = true;

    // Optionnel: empêcher double submit via flag
    form.dataset.submitted = "1";
  });
})();

// --- Reveal animations ---
(function () {
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!prefersReduced) document.documentElement.classList.add("motion");

  if (!document.documentElement.classList.contains("motion")) return;

  const items = document.querySelectorAll(".reveal");
  if (!items.length) return;

  if (!("IntersectionObserver" in window)) {
    items.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const io = new IntersectionObserver(
    (entries) => entries.forEach((e) => e.isIntersecting && e.target.classList.add("is-visible")),
    { threshold: 0.10 }
  );

  items.forEach((el) => io.observe(el));
})();

// --- Tap feedback ---
(function () {
  document.addEventListener("click", (e) => {
    const el = e.target.closest("a.btn, button.btn, .product-card, .list-item, .iconbtn");
    if (!el) return;

    el.animate(
      [{ transform: "scale(1)" }, { transform: "scale(0.985)" }, { transform: "scale(1)" }],
      { duration: 180, easing: "ease-out" }
    );
  });
})();

// ---- Investment timers + "Terminé" + barre progression (si tu as .inv-card sur dashboard)
(function () {
  const cards = document.querySelectorAll(".inv-card");
  if (!cards.length) return;

  const pad2 = (n) => String(n).padStart(2, "0");

  function formatDuration(ms) {
    ms = Math.max(0, ms);
    const totalSec = Math.floor(ms / 1000);
    const days = Math.floor(totalSec / 86400);
    const hours = Math.floor((totalSec % 86400) / 3600);
    const minutes = Math.floor((totalSec % 3600) / 60);
    const seconds = totalSec % 60;

    if (days > 0) return `${days}j ${pad2(hours)}h ${pad2(minutes)}m`;
    return `${pad2(hours)}h ${pad2(minutes)}m ${pad2(seconds)}s`;
  }

  function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
  }

  function update() {
    const now = Date.now();

    cards.forEach((card) => {
      const startStr = card.getAttribute("data-start");
      const endStr = card.getAttribute("data-end");
      if (!startStr || !endStr) return;

      const start = new Date(startStr).getTime();
      const end = new Date(endStr).getTime();
      if (Number.isNaN(start) || Number.isNaN(end) || end <= start) return;

      const total = end - start;
      const elapsed = now - start;
      const remaining = end - now;

      const elapsedEl = card.querySelector(".elapsed");
      const remainingEl = card.querySelector(".remaining");
      const percentEl = card.querySelector(".percent");
      const barEl = card.querySelector(".bar");

      const badgeEl = card.querySelector(".inv-badge");
      const finishLineEl = card.querySelector(".inv-finish-line");

      const isFinished = remaining <= 0;
      const percent = isFinished ? 100 : clamp((elapsed / total) * 100, 0, 100);

      if (elapsedEl) elapsedEl.textContent = formatDuration(elapsed);
      if (remainingEl) remainingEl.textContent = isFinished ? "Terminé" : formatDuration(remaining);
      if (percentEl) percentEl.textContent = String(Math.round(percent));
      if (barEl) barEl.style.width = `${percent}%`;

      if (isFinished) {
        card.classList.add("inv-finished");
        if (badgeEl) {
          badgeEl.textContent = "TERMINÉ";
          badgeEl.classList.add("pill-approved");
        }
        if (finishLineEl) finishLineEl.style.display = "block";
      } else {
        card.classList.remove("inv-finished");
        if (finishLineEl) finishLineEl.style.display = "none";
      }
    });
  }

  update();
  setInterval(update, 1000);
})();