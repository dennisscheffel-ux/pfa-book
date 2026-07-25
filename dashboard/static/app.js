// ---- Tabs ----
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });
});

function esc(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

// ---- Review tab ----
const STATUS_LABELS = {
  pending_review: ["Awaiting review", "pending"],
  published: ["Published", "published"],
  declined: ["Declined", "declined"],
  failed: ["Failed", "failed"],
};

async function loadReview() {
  const pendingEl = document.getElementById("pending-container");
  const recentEl = document.getElementById("recent-container");
  try {
    const res = await fetch("/api/state");
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    renderPending(data.pending);
    renderRecent(data.recent);
  } catch (e) {
    pendingEl.innerHTML = `<div class="empty-card"><div class="headline">Couldn't load state</div><p>${esc(e.message)}</p></div>`;
    recentEl.innerHTML = "";
  }
}

function renderPending(pending) {
  const el = document.getElementById("pending-container");
  if (!pending) {
    el.innerHTML = `<div class="empty-card"><div class="headline">All clear</div><p>Nothing is waiting on you right now.</p></div>`;
    return;
  }
  el.innerHTML = `
    <div class="pending-card">
      <div class="pending-image"><img src="${esc(pending.image_url)}" alt="Preview"></div>
      <div class="pending-detail">
        <div class="pending-top">
          <span class="chip chip-pending">Awaiting review</span>
          <a class="btn-ghost" href="${esc(pending.html_url)}" target="_blank" rel="noopener">View issue #${pending.number} →</a>
        </div>
        <div class="caption-panel" id="pending-caption">Loading caption…</div>
        <div class="cta-row">
          <button class="btn-primary" id="approve-btn">Approve &amp; publish</button>
          <button class="btn-primary btn-decline" id="decline-btn">Decline</button>
        </div>
      </div>
    </div>`;

  // Caption is embedded in the issue body markdown; pull it out of the fenced block.
  const match = /```\n([\s\S]*?)\n```/.exec(pending.body || "");
  document.getElementById("pending-caption").textContent = match ? match[1] : "(caption not found)";

  document.getElementById("approve-btn").addEventListener("click", () => resolvePending(pending, "approved"));
  document.getElementById("decline-btn").addEventListener("click", () => resolvePending(pending, "declined"));
}

async function resolvePending(pending, decision) {
  const verb = decision === "approved" ? "publish this live to Instagram" : "decline this post";
  if (!confirm(`Are you sure you want to ${verb}?`)) return;

  const buttons = document.querySelectorAll("#approve-btn, #decline-btn");
  buttons.forEach((b) => (b.disabled = true));

  try {
    const res = await fetch("/api/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ issue_number: pending.number, decision }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    await loadReview();
  } catch (e) {
    alert("Failed: " + e.message);
    buttons.forEach((b) => (b.disabled = false));
  }
}

function renderRecent(recent) {
  const el = document.getElementById("recent-container");
  if (!recent || recent.length === 0) {
    el.innerHTML = `<div class="empty-note">Nothing resolved yet.</div>`;
    return;
  }
  el.innerHTML = recent.map((item) => {
    const [label, cls] = STATUS_LABELS[item.status] || [item.status, "pending"];
    const mediaNote = item.ig_media_id ? ` · media <code>${esc(item.ig_media_id)}</code>` : "";
    return `
      <div class="row">
        <span class="chip chip-${cls}">${esc(label)}</span>
        <div class="row-body">
          <div class="row-title">${esc(capitalize(item.pillar))} · ${esc(item.slug)}</div>
          <div class="row-excerpt">${esc(item.caption_excerpt)}</div>
        </div>
        <div class="row-meta">${esc(item.date)}${mediaNote}</div>
      </div>`;
  }).join("");
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

// ---- Topics tab ----
async function loadTopics() {
  const el = document.getElementById("topics-container");
  try {
    const res = await fetch("/api/topics");
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    renderTopics(data.pending);
  } catch (e) {
    el.innerHTML = `<div class="empty-card"><div class="headline">Couldn't load topics</div><p>${esc(e.message)}</p></div>`;
  }
}

function renderTopics(pending) {
  const el = document.getElementById("topics-container");
  if (!pending || pending.length === 0) {
    el.innerHTML = `<div class="empty-card"><div class="headline">Nothing to review</div><p>New topic ideas show up here weekly.</p></div>`;
    return;
  }
  el.innerHTML = `<div class="topics-grid">${pending.map((t) => `
    <div class="topic-card" data-id="${esc(t.id)}">
      <div class="topic-eyebrow">${esc(t.eyebrow)}</div>
      <div class="topic-headline">${esc(t.headline)}</div>
      <p class="topic-body">${esc(t.body)}</p>
      <div class="topic-actions">
        <button class="btn-primary" data-accept="${esc(t.id)}">Accept</button>
        <button class="btn-primary btn-decline" data-decline="${esc(t.id)}">Decline</button>
      </div>
    </div>`).join("")}</div>`;

  el.querySelectorAll("[data-accept]").forEach((btn) => {
    btn.addEventListener("click", () => resolveTopic(btn.dataset.accept, "accepted"));
  });
  el.querySelectorAll("[data-decline]").forEach((btn) => {
    btn.addEventListener("click", () => resolveTopic(btn.dataset.decline, "declined"));
  });
}

async function resolveTopic(topicId, decision) {
  const card = document.querySelector(`.topic-card[data-id="${CSS.escape(topicId)}"]`);
  const buttons = card.querySelectorAll("button");
  buttons.forEach((b) => (b.disabled = true));
  try {
    const res = await fetch("/api/topics/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic_id: topicId, decision }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    await loadTopics();
  } catch (e) {
    alert("Failed: " + e.message);
    buttons.forEach((b) => (b.disabled = false));
  }
}

// ---- Queue tab ----
const loadQueueBtn = document.getElementById("load-queue-btn");
if (loadQueueBtn) loadQueueBtn.addEventListener("click", loadQueue);

async function loadQueue() {
  const btn = document.getElementById("load-queue-btn");
  const el = document.getElementById("queue-container");
  btn.disabled = true;
  btn.textContent = "Rendering…";
  el.innerHTML = "";
  try {
    const res = await fetch("/api/queue?count=6");
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    el.innerHTML = data.upcoming.map((item) => `
      <div class="queue-card">
        <img src="${esc(item.image_url)}" alt="${esc(item.item_id)}">
        <div class="queue-card-body">
          <div class="queue-card-pillar">${esc(item.pillar)} · ${esc(item.card_type)}</div>
          <div class="queue-card-excerpt">${esc(item.caption.slice(0, 140))}…</div>
        </div>
      </div>`).join("");
  } catch (e) {
    el.innerHTML = `<div class="empty-card"><div class="headline">Couldn't render queue</div><p>${esc(e.message)}</p></div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Render preview →";
  }
}

// ---- Content tab ----
const PILLAR_FIELDS = {
  pain_points: [["eyebrow", "text"], ["headline", "text"], ["body", "textarea"]],
  insights: [["eyebrow", "text"], ["headline", "text"], ["body", "textarea"], ["pull", "textarea"]],
  chapters: [["number", "text"], ["title", "text"], ["body", "textarea"], ["tag", "text"]],
  testimonials: [["quote", "textarea"], ["name", "text"], ["role", "text"], ["result", "text"]],
  offer_items: [["number", "text"], ["title", "text"], ["body", "textarea"]],
};
const PILLAR_LABELS = {
  pain_points: "Pain Points",
  insights: "Key Insights",
  chapters: "Chapters",
  testimonials: "Testimonials",
  offer_items: "What You Get",
};

let contentBank = null;

async function loadContent() {
  const res = await fetch("/api/content");
  contentBank = await res.json();
  renderContent();
}

function renderContent() {
  const el = document.getElementById("content-container");
  let html = "";

  for (const pillar of Object.keys(PILLAR_FIELDS)) {
    const items = contentBank[pillar] || [];
    html += `<div class="pillar-block" data-pillar="${pillar}">
      <div class="pillar-title">${PILLAR_LABELS[pillar]}</div>
      <div class="pillar-items">
        ${items.map((item, i) => itemCardHtml(pillar, item, i)).join("")}
      </div>
      <button class="btn-add" data-add-pillar="${pillar}">+ Add ${PILLAR_LABELS[pillar].slice(0, -1)}</button>
    </div>`;
  }

  html += `<div class="pillar-block" data-pillar="for_who">
    <div class="pillar-title">Is This Your Book?</div>
    ${forWhoHtml("yes", "This is for you if…")}
    ${forWhoHtml("no", "This isn't for you if…")}
  </div>`;

  el.innerHTML = html;
  wireContentEvents();
}

function itemCardHtml(pillar, item, index) {
  const fields = PILLAR_FIELDS[pillar];
  return `<div class="item-card" data-pillar="${pillar}" data-index="${index}">
    <div><label>ID</label><input type="text" data-field="id" value="${esc(item.id || "")}"></div>
    ${fields.map(([field, kind]) => `
      <div><label>${field}</label>
        ${kind === "textarea"
          ? `<textarea data-field="${field}">${esc(item[field] || "")}</textarea>`
          : `<input type="text" data-field="${field}" value="${esc(item[field] || "")}">`}
      </div>`).join("")}
    <div class="item-card-footer"><button class="btn-remove" data-remove>Remove</button></div>
  </div>`;
}

function forWhoHtml(tone, heading) {
  const lines = (contentBank.for_who && contentBank.for_who[tone]) || [];
  return `<div class="for-who-block" data-tone="${tone}">
    <label style="margin-top:1rem;display:block">${esc(heading)}</label>
    ${lines.map((line, i) => `
      <div class="item-row" style="margin-bottom:0.5rem">
        <input type="text" data-forwho="${tone}" data-index="${i}" value="${esc(line)}">
        <button class="btn-remove" data-remove-forwho="${tone}" data-index="${i}">Remove</button>
      </div>`).join("")}
    <button class="btn-add" data-add-forwho="${tone}">+ Add line</button>
  </div>`;
}

function wireContentEvents() {
  document.querySelectorAll("[data-add-pillar]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const pillar = btn.dataset.addPillar;
      contentBank[pillar] = contentBank[pillar] || [];
      const newId = `${pillar}_new_${Date.now().toString(36)}`;
      contentBank[pillar].push({ id: newId });
      renderContent();
    });
  });

  document.querySelectorAll("[data-add-forwho]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tone = btn.dataset.addForwho;
      contentBank.for_who[tone].push("");
      renderContent();
    });
  });

  document.querySelectorAll(".item-card [data-remove]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const card = btn.closest(".item-card");
      const pillar = card.dataset.pillar;
      const index = parseInt(card.dataset.index, 10);
      contentBank[pillar].splice(index, 1);
      renderContent();
    });
  });

  document.querySelectorAll("[data-remove-forwho]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tone = btn.dataset.removeForwho;
      const index = parseInt(btn.dataset.index, 10);
      contentBank.for_who[tone].splice(index, 1);
      renderContent();
    });
  });

  document.querySelectorAll(".item-card input, .item-card textarea").forEach((input) => {
    input.addEventListener("input", () => {
      const card = input.closest(".item-card");
      const pillar = card.dataset.pillar;
      const index = parseInt(card.dataset.index, 10);
      contentBank[pillar][index][input.dataset.field] = input.value;
    });
  });

  document.querySelectorAll("[data-forwho]").forEach((input) => {
    input.addEventListener("input", () => {
      const tone = input.dataset.forwho;
      const index = parseInt(input.dataset.index, 10);
      contentBank.for_who[tone][index] = input.value;
    });
  });
}

document.getElementById("save-content-btn").addEventListener("click", async () => {
  const statusEl = document.getElementById("save-status");
  statusEl.textContent = "Saving…";
  statusEl.className = "";
  try {
    const res = await fetch("/api/content", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(contentBank),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Save failed");
    statusEl.textContent = "Saved to content/copy_bank.json — commit & push when ready.";
    statusEl.className = "ok";
  } catch (e) {
    statusEl.textContent = "Error: " + e.message;
    statusEl.className = "err";
  }
});

// ---- Init ----
loadReview();
loadTopics();
loadContent();
