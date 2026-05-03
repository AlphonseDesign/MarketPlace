(function () {
  const input = document.getElementById("productSearch");
  const grid = document.getElementById("productsGrid");
  const countEl = document.getElementById("productsCount");
  const noResults = document.getElementById("noResults");

  if (!input || !grid || !countEl) return;

  const items = Array.from(grid.querySelectorAll(".product-item"));

  function update() {
    const q = (input.value || "").trim().toLowerCase();
    let visible = 0;

    items.forEach((it) => {
      const text = (it.getAttribute("data-filter") || "");
      const show = text.includes(q);
      it.style.display = show ? "" : "none";
      if (show) visible += 1;
    });

    countEl.textContent = visible;
    if (noResults) noResults.style.display = visible === 0 ? "" : "none";
  }

  input.addEventListener("input", update);
  update();
})();