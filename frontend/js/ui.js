// Small reusable helpers: escaping, formatting, toasts, modal, buttons.
const $ = sel => document.querySelector(sel);

const UI = {
  esc: s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])),
  money: v => "Rs " + Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 }),
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
