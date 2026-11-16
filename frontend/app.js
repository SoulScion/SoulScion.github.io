const API_BASE = "http://127.0.0.1:5000/api";
const panel = document.getElementById("panel");

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);
  return body;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => (
    { "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]
  ));
}

// ─── Operation 1 ────────────────────────────
function opSearch() {
  panel.innerHTML = `
    <h2>Search games</h2>
    <form id="f"><input id="q" placeholder="Title contains..." autofocus>
      <button>Search</button></form>
    <div id="out"></div>`;
  document.getElementById("f").onsubmit = async (e) => {
    e.preventDefault();
    const q = document.getElementById("q").value.trim();
    if (!q) return;
    const out = document.getElementById("out");
    out.innerHTML = "Searching...";
    try {
      const rows = await fetchJSON(`${API_BASE}/games/search?q=${encodeURIComponent(q)}`);
      out.innerHTML = rows.length
        ? `<table><tr><th>ID</th><th>Title</th><th>Released</th><th>Publisher</th></tr>` +
          rows.map(r => `<tr><td>${r.game_id}</td><td>${esc(r.title)}</td>
            <td>${esc(r.earliest_release || "—")}</td>
            <td>${esc(r.publisher_name || "—")}</td></tr>`).join("") + `</table>`
        : "<p>No games found.</p>";
    } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
  };
}

// ─── Operation 2 ────────────────────────────
function opProfile() {
  panel.innerHTML = `
    <h2>Game profile</h2>
    <form id="f"><input id="id" type="number" min="1" placeholder="Game ID" autofocus>
      <button>Load</button></form>
    <div id="out"></div>`;
  document.getElementById("f").onsubmit = async (e) => {
    e.preventDefault();
    const id = document.getElementById("id").value.trim();
    if (!id) return;
    const out = document.getElementById("out");
    out.innerHTML = "Loading...";
    try {
      const g = await fetchJSON(`${API_BASE}/games/${id}`);
      const list = (arr) => arr && arr.length ? arr.map(esc).join(", ") : "—";
      out.innerHTML = `
        <h3>${esc(g.title)}</h3>
        <p><b>Released:</b> ${esc(g.earliest_release || "—")}</p>
        <p><b>Publisher:</b> ${esc(g.publisher_name || "—")}</p>
        <p><b>Developers:</b> ${list(g.developers)}</p>
        <p><b>Genres:</b> ${list(g.genres)}</p>
        <p><b>Platforms:</b> ${
          g.platforms.length
            ? g.platforms.map(p => `${esc(p.platform_name)} (${esc(p.type || "?")})`).join(", ")
            : "—"
        }</p>
        <p><b>Perspectives:</b> ${list(g.perspectives)}</p>
        <p><b>Social:</b> ${list(g.socials)}</p>
        <p><b>Prices:</b> ${
          g.prices.length
            ? g.prices.map(p => `${esc(p.platform_name)}: ${
                p.regular_price != null ? "$" + p.regular_price : esc(p.price_type)
              }`).join(", ")
            : "—"
        }</p>
        <p><b>DLCs:</b> ${g.dlc_count}</p>`;
    } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
  };
}

// ─── Operation 3 ────────────────────────────
function opAddPublisher() {
  panel.innerHTML = `
    <h2>Add publisher</h2>
    <form id="f"><input id="name" placeholder="Publisher name" autofocus>
      <button>Add</button></form>
    <div id="out"></div>`;
  document.getElementById("f").onsubmit = async (e) => {
    e.preventDefault();
    const name = document.getElementById("name").value.trim();
    const out = document.getElementById("out");
    if (!name) { out.innerHTML = `<p class="err">Name required.</p>`; return; }
    try {
      const r = await fetchJSON(`${API_BASE}/publishers`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ name })
      });
      out.innerHTML = `<p class="ok">Added publisher #${r.publisher_id}: ${esc(r.publisher_name)}</p>`;
    } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
  };
}

// ─── Operation 4 ────────────────────────────
function opUpdateCopies() {
  panel.innerHTML = `
    <h2>Update copies sold</h2>
    <form id="f">
      <input id="gid" type="number" min="1" placeholder="Game ID" autofocus>
      <input id="cop" type="number" min="0" placeholder="Copies sold">
      <button>Update</button>
    </form>
    <div id="out"></div>`;
  document.getElementById("f").onsubmit = async (e) => {
    e.preventDefault();
    const gid = document.getElementById("gid").value.trim();
    const cop = document.getElementById("cop").value.trim();
    const out = document.getElementById("out");
    try {
      const r = await fetchJSON(`${API_BASE}/games/${gid}/copies`, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ copies_sold: Number(cop) })
      });
      out.innerHTML = `<p class="ok">Game ${r.game_id} now has ${r.copies_sold} copies sold.</p>`;
    } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
  };
}

// ─── Operation 5 ────────────────────────────
async function opTopGenres() {
  panel.innerHTML = `<h2>Top genres by average price</h2><div id="out">Loading...</div>`;
  const out = document.getElementById("out");
  try {
    const rows = await fetchJSON(`${API_BASE}/reports/top-genres`);
    out.innerHTML = rows.length
      ? `<table><tr><th>Genre</th><th>Games</th><th>Avg price</th></tr>` +
        rows.map(r => `<tr><td>${esc(r.genre_name)}</td>
          <td>${r.game_count}</td><td>$${r.avg_price}</td></tr>`).join("") + `</table>`
      : "<p>No data.</p>";
  } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
}

// ─── Operation 6 ────────────────────────────
async function opNoDlc() {
  panel.innerHTML = `<h2>Games with no DLCs</h2><div id="out">Loading...</div>`;
  const out = document.getElementById("out");
  try {
    const rows = await fetchJSON(`${API_BASE}/reports/no-dlc`);
    out.innerHTML = rows.length
      ? `<table><tr><th>ID</th><th>Title</th><th>Publisher</th></tr>` +
        rows.map(r => `<tr><td>${r.game_id}</td><td>${esc(r.title)}</td>
          <td>${esc(r.publisher_name || "—")}</td></tr>`).join("") + `</table>`
      : "<p>All games have DLCs.</p>";
  } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
}

// ─── Wire up menu ───────────────────────────
document.querySelectorAll("#menu button").forEach(btn => {
  btn.onclick = () => {
    const map = {
      "search": opSearch,
      "profile": opProfile,
      "add-publisher": opAddPublisher,
      "update-copies": opUpdateCopies,
      "top-genres": opTopGenres,
      "no-dlc": opNoDlc,
    };
    map[btn.dataset.op]?.();
  };
});