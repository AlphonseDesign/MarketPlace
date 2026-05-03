(function () {
  const body = document.body;

  const openBtn = document.querySelector("[data-bo-open]");
  const closeTargets = document.querySelectorAll("[data-bo-close]");

  function openMenu() {
    body.classList.add("bo-open");
  }
  function closeMenu() {
    body.classList.remove("bo-open");
  }

  if (openBtn) openBtn.addEventListener("click", openMenu);
  closeTargets.forEach((el) => el.addEventListener("click", closeMenu));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeMenu();
  });

  // Marquer le lien actif (selon l'URL)
  const path = window.location.pathname;
  const links = document.querySelectorAll(".bo-nav a[href]");

  let best = null;
  let bestLen = -1;

  links.forEach((a) => {
    const href = a.getAttribute("href");
    if (!href) return;

    // On choisit le lien dont le href est le préfixe le plus long du path
    if (path.startsWith(href) && href.length > bestLen) {
      best = a;
      bestLen = href.length;
    }
  });

  if (best) best.classList.add("is-active");
})();