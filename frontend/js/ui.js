// Small reusable helpers: escaping, formatting, toasts, modal, buttons.
const $ = sel => document.querySelector(sel);

const ICONS = {
  home: '<path d="M3 11l9-8 9 8v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  bed: '<path d="M3 18v-7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v7M3 18h18M3 21v-3m18 3v-3M7 9V6a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v3"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M17 4.5a3.5 3.5 0 0 1 0 7M21.5 20a6.5 6.5 0 0 0-4-6"/>',
  tag: '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="8" cy="8" r="1.5"/>',
  shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
  cash: '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>',
  door: '<path d="M14 3h5v18h-5M3 21h18M14 3L5 5v14l9 2"/>',
};

const UI = {
  icon: n => `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[n] || ""}</svg>`,
  esc: s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])),
  money: v => "PKR " + Number(v || 0).toLocaleString("en-US", { maximumFractionDigits: 2 }),
  fmtDate(d) {
    const p = n => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  },
  today: () => UI.fmtDate(new Date()),
  addDays(date, n) { const d = new Date(date + "T00:00:00"); d.setDate(d.getDate() + n); return UI.fmtDate(d); },
  nights: (a, b) => Math.round((new Date(b) - new Date(a)) / 864e5),
  badge: s => `<span class="badge ${UI.esc(s)}">${UI.esc(String(s).replace("_", " "))}</span>`,
  can: (...roles) => roles.includes(App.user && App.user.role),
  empty: msg => `<div class="empty">${msg}</div>`,
  table: (heads, rows) => `<table><thead><tr>${heads.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table>`,

  button(label, onclick, cls = "btn") {
    const b = document.createElement("button");
    b.className = cls; b.textContent = label; b.onclick = onclick;
    return b;
  },

  toast(msg, type = "ok") {
    const t = document.createElement("div");
    t.className = "toast " + type; t.textContent = msg;
    $("#toasts").append(t);
    setTimeout(() => t.remove(), 3800);
  },

  async run(fn) {
    try { return await fn(); } catch (e) { UI.toast(e.message, "bad"); }
  },

  modal(title, bodyHtml, mount) {
    $("#mtitle").textContent = title;
    $("#mbody").innerHTML = bodyHtml;
    $("#modal").classList.remove("hidden");
    if (mount) mount($("#mbody"));
  },
  closeModal: () => $("#modal").classList.add("hidden"),

  // Turn a <form> into a plain object, dropping empty fields.
  data(form) {
    const out = {};
    new FormData(form).forEach((v, k) => { if (v !== "") out[k] = v; });
    return out;
  },
};
