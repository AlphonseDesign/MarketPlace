(function () {
  const root = document.querySelector("[data-chat]");
  if (!root) return;

  const convId = root.dataset.convId;
  const pollUrl = root.dataset.pollUrl;
  const sendUrl = root.dataset.sendUrl;

  const bodyEl = document.getElementById("chatBody");
  const formEl = document.getElementById("chatForm");
  const inputEl = document.getElementById("chatText");

  let afterId = 0;

  // init afterId depuis les bulles existantes (si on veut)
  // sinon on va juste poll après 0 (ça renverra les derniers > 0)
  // pour éviter doublons : on met afterId au dernier id reçu via polling.
  function scrollBottom() {
    if (!bodyEl) return;
    bodyEl.scrollTop = bodyEl.scrollHeight;
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[m]));
  }

  function renderBubble(msg) {
    const div = document.createElement("div");
    div.className = "bubble " + (msg.sender === "me" ? "bubble-me" : "bubble-admin");
    div.innerHTML = `
      <div class="bubble-text">${escapeHtml(msg.body)}</div>
      <div class="bubble-time">${new Date(msg.created_at).toLocaleString()}</div>
    `;
    bodyEl.appendChild(div);
  }

  async function poll() {
    try {
      const url = `${pollUrl}?after_id=${afterId}`;
      const res = await fetch(url, { credentials: "same-origin" });
      const data = await res.json();
      if (!data.ok) return;

      if (data.messages && data.messages.length) {
        data.messages.forEach((m) => {
          renderBubble(m);
          afterId = Math.max(afterId, m.id);
        });
        scrollBottom();
      }
    } catch (e) {
      // silence (évite spam console)
    }
  }

  async function send(body) {
    const csrf = getCookie("csrftoken");
    const fd = new FormData();
    fd.append("body", body);

    const res = await fetch(sendUrl, {
      method: "POST",
      body: fd,
      headers: { "X-CSRFToken": csrf },
      credentials: "same-origin",
    });

    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "Erreur");

    renderBubble({ ...data.message, created_at: data.message.created_at });
    afterId = Math.max(afterId, data.message.id);
    scrollBottom();
  }

  formEl.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = (inputEl.value || "").trim();
    if (!text) return;

    inputEl.value = "";
    inputEl.focus();

    try {
      await send(text);
    } catch (err) {
      // si erreur, on peut afficher un message
      alert("Échec envoi: " + err.message);
    }
  });

  scrollBottom();
  poll();
  setInterval(poll, 2000);
})();