// Setup:
const API_BASE = "http://127.0.0.1:5000/api";
let allGamesData = [];
let favoriteIds = new Set();

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => (
    { "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]
  ));
}

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);
  return body;
}

// Tab Navigation Logic:
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.target).classList.add('active');
    
    if (btn.dataset.target === 'tab-reports') loadReports();
    if (btn.dataset.target === 'tab-bookmarks') renderFavoritesTable();
  };
});

document.querySelectorAll('.sub-tab-btn').forEach(btn => {
  btn.onclick = () => {
    const parent = btn.closest('.tab-content');
    parent.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
    parent.querySelectorAll('.sub-tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.target).classList.add('active');

    if (btn.dataset.target === 'sub-pub') loadPublishers();
    if (btn.dataset.target === 'sub-dev') loadDevelopers();
  };
});

// Game Directory Search:
async function loadAllGames() {
  const container = document.getElementById('games-table-container');
  try {
    allGamesData = await fetchJSON(`${API_BASE}/games/all`);
    renderGamesTable(allGamesData);
  } catch (err) {
    container.innerHTML = `<p class="err">${esc(err.message)}</p>`;
  }
}

function renderGamesTable(games) {
  const container = document.getElementById('games-table-container');
  if (!games.length) {
    container.innerHTML = "<p>No games found.</p>";
    return;
  }

  const rows = games.map(g => {
    const isFav = favoriteIds.has(g.game_id);
    const star = isFav ? "★" : "☆";
    const starClass = isFav ? "star active" : "star";
    
    return `
    <tr onclick="openProfile(${g.game_id})">
      <td>${g.game_id}</td>
      <td><b>${esc(g.title)}</b></td>
      <td>${esc(g.earliest_release || "—")}</td>
      <td>${esc(g.developer_name || "—")}</td>
      <td>${esc(g.publisher_name || "—")}</td>
      <td>${esc(g.platform_name || "—")}</td>
      <td onclick="event.stopPropagation(); toggleFavorite(${g.game_id}, this)">
        <span class="${starClass}">${star}</span>
      </td>
    </tr>
  `}).join('');

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>ID</th><th>Title</th><th>Release</th><th>Developer</th><th>Publisher</th><th>Platform</th><th>Bookmark</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

document.getElementById('main-search').addEventListener('input', (e) => {
  const term = e.target.value.toLowerCase();
  const filtered = allGamesData.filter(g => g.title.toLowerCase().includes(term));
  renderGamesTable(filtered);
});

function toggleFavorite(gameId, tdElement) {
  const starSpan = tdElement.querySelector('.star');
  
  if (favoriteIds.has(gameId)) {
    favoriteIds.delete(gameId);
    starSpan.className = "star";
    starSpan.innerText = "☆";
  } else {
    favoriteIds.add(gameId);
    starSpan.className = "star active";
    starSpan.innerText = "★";
  }
}

function renderFavoritesTable() {
  const container = document.getElementById('bookmarks-table-container');
  
  const favs = allGamesData.filter(g => favoriteIds.has(g.game_id));
  
  if (!favs.length) {
    container.innerHTML = "<p class='hint'>You haven't bookmarked any games yet. Go to the Games Directory to add some!</p>";
    return;
  }

  const rows = favs.map(g => `
    <tr onclick="openProfile(${g.game_id})">
      <td>${g.game_id}</td>
      <td><b>${esc(g.title)}</b></td>
      <td>${esc(g.earliest_release || "—")}</td>
      <td>${esc(g.developer_name || "—")}</td>
      <td>${esc(g.publisher_name || "—")}</td>
    </tr>
  `).join('');

  container.innerHTML = `
    <table>
      <thead>
        <tr><th>ID</th><th>Title</th><th>Release</th><th>Developer</th><th>Publisher</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// Game Profile Details 
async function openProfile(gameId) {
  const modal = document.getElementById('profile-modal');
  const content = document.getElementById('profile-content');
  modal.classList.remove('hidden');
  content.innerHTML = "Loading profile...";

  try {
    const g = await fetchJSON(`${API_BASE}/games/${gameId}`);
    const list = (arr) => arr && arr.length ? arr.map(esc).join(", ") : "—";
    
    content.innerHTML = `
      <h2>${esc(g.title)}</h2>
      <div class="profile-grid">
        <p><b>Released:</b> ${esc(g.earliest_release || "—")}</p>
        <p><b>Publisher:</b> ${esc(g.publisher_name || "—")}</p>
        <p><b>Developers:</b> ${list(g.developers)}</p>
        <p><b>Genres:</b> ${list(g.genres)}</p>
        <p><b>Perspectives:</b> ${list(g.perspectives)}</p>
        <p><b>Social:</b> ${list(g.socials)}</p>
        <p><b>DLCs:</b> ${g.dlc_count}</p>
        <p><b>Copies Sold:</b> ${g.copies_sold || "—"}</p>
      </div>
      <p><b>Platforms:</b> ${
        g.platforms.length ? g.platforms.map(p => `${esc(p.platform_name)} (${esc(p.type || "?")})`).join(", ") : "—"
      }</p>
      <p><b>Prices:</b> ${
        g.prices.length ? g.prices.map(p => `${esc(p.platform_name)}: ${p.regular_price != null ? "$" + p.regular_price : esc(p.price_type)}`).join(", ") : "—"
      }</p>
    `;
  } catch (err) {
    content.innerHTML = `<p class="err">${esc(err.message)}</p>`;
  }
}

document.getElementById('close-modal').onclick = () => {
  document.getElementById('profile-modal').classList.add('hidden');
};

// Modify Data:
document.getElementById('f-add-pub').onsubmit = async (e) => {
  e.preventDefault();
  const name = document.getElementById('pub-name').value.trim();
  const out = document.getElementById('out-pub');
  try {
    const r = await fetchJSON(`${API_BASE}/publishers`, {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ name })
    });
    out.innerHTML = `<p class="ok">Added publisher #${r.publisher_id}: ${esc(r.publisher_name)}</p>`;
    document.getElementById('pub-name').value = '';
    loadPublishers();
  } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
};

document.getElementById('f-add-dev').onsubmit = async (e) => {
  e.preventDefault();
  const name = document.getElementById('dev-name').value.trim();
  const out = document.getElementById('out-dev');
  try {
    const r = await fetchJSON(`${API_BASE}/developers`, {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ name })
    });
    out.innerHTML = `<p class="ok">Added developer #${r.developer_id}: ${esc(r.company_name)}</p>`;
    document.getElementById('dev-name').value = '';
    loadDevelopers();
  } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
};

document.getElementById('f-up-cop').onsubmit = async (e) => {
  e.preventDefault();
  const gid = document.getElementById('gid').value;
  const cop = document.getElementById('cop').value;
  const out = document.getElementById('out-cop');
  try {
    const r = await fetchJSON(`${API_BASE}/games/${gid}/copies`, {
      method: "PATCH", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ copies_sold: Number(cop) })
    });
    out.innerHTML = `<p class="ok">Game ${r.game_id} now has ${r.copies_sold} copies sold.</p>`;
  } catch (err) { out.innerHTML = `<p class="err">${esc(err.message)}</p>`; }
};

// Two Basic Reports:
async function loadReports() {
  try {
    const genres = await fetchJSON(`${API_BASE}/reports/top-genres`);
    document.getElementById('out-genres').innerHTML = genres.length
      ? `<table><tr><th>Genre</th><th>Games</th><th>Average Price</th></tr>` +
        genres.map(r => `<tr><td>${esc(r.genre_name)}</td><td>${r.game_count}</td><td>$${r.avg_price}</td></tr>`).join("") + `</table>`
      : "<p>No data.</p>";
  } catch (err) { document.getElementById('out-genres').innerHTML = `<p class="err">${esc(err.message)}</p>`; }

  try {
    const dlc = await fetchJSON(`${API_BASE}/reports/no-dlc`);
    document.getElementById('out-dlc').innerHTML = dlc.length
      ? `<table><tr><th>ID</th><th>Title</th><th>Developer</th><th>Publisher</th></tr>` +
        dlc.map(r => `<tr><td>${r.game_id}</td><td>${esc(r.title)}</td><td>${esc(r.developer_name || "—")}</td><td>${esc(r.publisher_name || "—")}</td></tr>`).join("") + `</table>`
      : "<p>All games have DLCs.</p>";
  } catch (err) { document.getElementById('out-dlc').innerHTML = `<p class="err">${esc(err.message)}</p>`; }
}


// Adding the Publisher Table:
async function loadPublishers() {
  const container = document.getElementById('pub-table-container');
  container.innerHTML = "<p class='hint'>Loading publishers...</p>";
  try {
    const pubs = await fetchJSON(`${API_BASE}/publishers`);
    if (!pubs.length) {
      container.innerHTML = "<p class='hint'>No publishers found.</p>";
      return;
    }

    const rows = pubs.map(p => `
      <tr>
        <td>${p.publisher_id}</td>
        <td>${esc(p.publisher_name)}</td>
        <td style="text-align: right;">
          <button class="undo-btn" onclick="deletePublisher(${p.publisher_id})">Undo</button>
        </td>
      </tr>
    `).join('');

    container.innerHTML = `
      <table>
        <thead>
          <tr><th>ID</th><th>Publisher Name</th><th style="text-align: right;">Action</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<p class="err">${esc(err.message)}</p>`;
  }
}

async function deletePublisher(id) {
  if (!confirm("Are you sure you want to undo this addition?")) return;
  try {
    await fetchJSON(`${API_BASE}/publishers/${id}`, { method: 'DELETE' });
    loadPublishers();
  } catch (err) {
    alert(err.message);
  }
}

// Adding the Developers Table:
async function loadDevelopers() {
  const container = document.getElementById('dev-table-container');
  container.innerHTML = "<p class='hint'>Loading developers...</p>";
  try {
    const devs = await fetchJSON(`${API_BASE}/developers`);
    if (!devs.length) {
      container.innerHTML = "<p class='hint'>No developers found.</p>";
      return;
    }

    const rows = devs.map(d => `
      <tr>
        <td>${d.developer_id}</td>
        <td>${esc(d.company_name)}</td>
        <td style="text-align: right;">
          <button class="undo-btn" onclick="deleteDeveloper(${d.developer_id})">Undo</button>
        </td>
      </tr>
    `).join('');

    container.innerHTML = `
      <table>
        <thead>
          <tr><th>ID</th><th>Developer Name</th><th style="text-align: right;">Action</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = `<p class="err">${esc(err.message)}</p>`;
  }
}

async function deleteDeveloper(id) {
  if (!confirm("Are you sure you want to undo this addition?")) return;
  try {
    await fetchJSON(`${API_BASE}/developers/${id}`, { method: 'DELETE' });
    loadDevelopers();
  } catch (err) {
    alert(err.message);
  }
}

// Loading on inital page load:
loadPublishers();
loadDevelopers();

// Initialize Page:
loadAllGames();