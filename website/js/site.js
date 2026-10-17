const API = "/api/v1/public";
const FALLBACK = [
  "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=900&q=80"];
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = n => "PKR " + Number(n || 0).toLocaleString("en-US", { maximumFractionDigits: 2 });
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const addDays = (s, n) => { const d = new Date(s + "T00:00:00"); d.setDate(d.getDate() + n); return iso(d); };
const nights = (a, b) => Math.round((new Date(b) - new Date(a)) / 864e5);
const today = iso(new Date());
const msg = d => !d ? "Something went wrong" : Array.isArray(d.detail) ? d.detail.map(x => String(x.msg).replace("Value error, ", "")).join(". ") : (d.detail || "Something went wrong");
let rooms = [], dates = null;

// Hide any broken photo so the coloured block behind it shows instead.
document.addEventListener("error", e => { if (e.target.tagName === "IMG") e.target.remove(); }, true);

const show = html => {
  $("#box").innerHTML = `<button class="x" aria-label="Close" data-close>×</button>` + html;
  $("#modal").classList.add("open");
  const f = $("#box input"); if (f) f.focus();
};
const closeM = () => $("#modal").classList.remove("open");
$("#modal").onclick = e => { if (e.target.id === "modal" || e.target.closest("[data-close]")) closeM(); };
addEventListener("keydown", e => e.key === "Escape" && closeM());
addEventListener("scroll", () => $("#nav").classList.toggle("solid", scrollY > 60));

$("#ci").min = today;
$("#ci").onchange = () => { $("#co").min = addDays($("#ci").value, 1); if (!$("#co").value || $("#co").value <= $("#ci").value) $("#co").value = addDays($("#ci").value, 1); };

async function load() {
  const q = dates ? `?check_in=${dates.ci}&check_out=${dates.co}` : "";
  try {
    const r = await fetch(`${API}/room-types${q}`);
    const d = await r.json().catch(() => null);
    if (!r.ok || !Array.isArray(d)) throw new Error(msg(d));
    rooms = d;
  } catch (e) {
    $("#rooms-sub").textContent = "";
    $("#rooms-grid").innerHTML = `<p class="err" role="alert">Rooms could not be loaded: ${esc(e.message)}</p>`;
    return;
  }
  $("#rooms-sub").textContent = dates ? `${nights(dates.ci, dates.co)} night stay · ${dates.ci} to ${dates.co}` : "Choose your dates above to see which rooms are free.";
  draw();
}

function draw() {
  $("#rooms-grid").innerHTML = rooms.map((r, i) => {
    const out = r.available_rooms === 0;
    const tags = (r.amenities || "WiFi,Air conditioning,Smart TV,Daily housekeeping").split(",").map(a => a.trim()).filter(Boolean);
    return `<article class="card"><div class="img"><img loading="lazy" src="${esc(r.image_url || FALLBACK[i % FALLBACK.length])}" alt="${esc(r.name)} room"></div>
      <div class="body"><h3>${esc(r.name)}</h3>
      <p class="muted">Sleeps ${r.capacity}${r.available_rooms != null ? ` · ${r.available_rooms} left for your dates` : ""}</p>
      <p>${esc(r.description)}</p><ul class="tags">${tags.map(a => `<li>${esc(a)}</li>`).join("")}</ul>
      <div class="foot"><div><b>${money(r.base_price)}</b><small> / night</small>${r.total ? `<small class="total">${money(r.total)} for ${r.nights} night(s)</small>` : ""}</div>
      <button class="btn" data-i="${i}" ${out ? "disabled" : ""}>${out ? "Sold out" : "Book this room"}</button></div></div></article>`;
  }).join("") || "<p>No rooms are listed yet.</p>";
}

$("#search").onsubmit = e => {
  e.preventDefault();
  $("#serr").textContent = "";
  if ($("#co").value <= $("#ci").value) return $("#serr").textContent = "Check-out must be after check-in.";
  dates = { ci: $("#ci").value, co: $("#co").value };
  load().then(() => $("#rooms").scrollIntoView({ behavior: "smooth" }));
};
const tok = () => localStorage.getItem("guest_token");
let me = null;

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json" };
  if (tok()) headers.Authorization = "Bearer " + tok();
  const r = await fetch(API + path, { ...opts, headers });
  const d = await r.json().catch(() => null);
  if (!r.ok) {
    if (r.status === 401 && tok()) { localStorage.removeItem("guest_token"); me = null; renderAcct(); throw new Error("Your session expired. Please sign in again."); }
    throw new Error(msg(d));
  }
  return d;
}

function renderAcct() {
  $("#acct").innerHTML = me
    ? `<button class="btn sm light" id="mb">My bookings</button><button class="link" id="so">Sign out (${esc(me.full_name.split(" ")[0])})</button>`
    : `<button class="btn sm light" id="si">Sign in</button>`;
  if (me) {
    $("#mb").onclick = openMine;
    $("#so").onclick = () => { localStorage.removeItem("guest_token"); me = null; renderAcct(); };
  } else $("#si").onclick = () => openAuth();
}

function openAuth(after, mode = "in") {
  const up = mode === "up";
  show(`<h3>${up ? "Create your account" : "Sign in to book"}</h3>
    <p class="muted">${up ? "Already registered?" : "New here?"} <a href="#" id="sw">${up ? "Sign in" : "Create an account"}</a></p>
    <form id="af">${up ? `<label>Full name<input name="full_name" required minlength="2" autocomplete="name"></label>
    <label>Phone<input name="phone" required pattern="\\+?[0-9\\- ]{7,20}" title="Digits, spaces and dashes only" autocomplete="tel" placeholder="0300-1234567"></label>` : ""}
    <label>Email<input type="email" name="email" required autocomplete="email"></label>
    <label>Password<input type="password" name="password" required ${up ? 'minlength="8" maxlength="72"' : ""} autocomplete="${up ? "new-password" : "current-password"}"></label>
    <p class="err" id="aerr" role="alert"></p><button class="btn full">${up ? "Create account" : "Sign in"}</button></form>`);
  $("#sw").onclick = e => { e.preventDefault(); openAuth(after, up ? "in" : "up"); };
  $("#af").onsubmit = async e => {
    e.preventDefault();
    try {
      const d = await api(up ? "/auth/register" : "/auth/login", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(e.target))) });
      localStorage.setItem("guest_token", d.access_token); me = d.customer; renderAcct(); closeM();
      if (after) after();
    } catch (err) { $("#aerr").textContent = err.message; }
  };
}

$("#rooms-grid").onclick = e => {
  const b = e.target.closest("button[data-i]");
  if (!b) return;
  const rt = rooms[b.dataset.i];
  if (me) openBook(rt); else openAuth(() => openBook(rt));
};

function openBook(rt) {
  const ci = dates ? dates.ci : today, co = dates ? dates.co : addDays(today, 1);
  show(`<h3>Book ${esc(rt.name)}</h3><p class="muted">Booking as ${esc(me.full_name)} (${esc(me.email)})</p><form id="bf">
    <div class="two"><label>Check-in<input type="date" name="check_in" required min="${today}" value="${ci}"></label>
    <label>Check-out<input type="date" name="check_out" required value="${co}"></label></div>
    <p class="sum" id="sum"></p><p class="err" id="err" role="alert"></p>
    <button class="btn full">Confirm booking</button></form>`);
  const f = $("#bf");
  const upd = () => { const n = nights(f.check_in.value, f.check_out.value); $("#sum").textContent = n > 0 ? `${n} night(s) × ${money(rt.base_price)} = ${money(n * rt.base_price)}. Pay at the hotel.` : ""; };
  f.oninput = upd; upd();
  f.onsubmit = async e => {
    e.preventDefault(); $("#err").textContent = "";
    try {
      const d = await api("/bookings", { method: "POST", body: JSON.stringify({ room_type_id: rt.id, check_in: f.check_in.value, check_out: f.check_out.value }) });
      show(`<h3>Booking confirmed</h3><p>Your booking code is</p><div class="ref">${esc(d.reference)}</div>
        <p>${esc(d.room_type)} · ${esc(d.check_in)} to ${esc(d.check_out)}<br>Total ${money(d.total_amount)}, payable at the hotel.</p>
        <p class="muted">You can see or cancel it any time under My bookings.</p><button class="btn full" data-close>Done</button>`);
      load();
    } catch (err) { $("#err").textContent = err.message; }
  };
}

async function openMine() {
  try {
    const list = await api("/my-bookings");
    show(`<h3>My bookings</h3>` + (list.length ? list.map(b => `<div class="found"><b>${esc(b.reference)}</b> <span class="badge ${esc(b.status)}">${esc(b.status)}</span><br>${esc(b.room_type)}, room ${esc(b.room_number)}<br>${esc(b.check_in)} to ${esc(b.check_out)} · ${money(b.total_amount)}${b.status === "reserved" ? `<br><button class="btn sm" data-cx="${esc(b.reference)}" style="margin-top:8px">Cancel booking</button>` : ""}</div>`).join("") : `<p class="muted">You have no bookings yet.</p>`));
    $("#box").onclick = async e => {
      const c = e.target.closest("[data-cx]");
      if (!c || !confirm("Cancel this booking?")) return;
      try { await api(`/my-bookings/${encodeURIComponent(c.dataset.cx)}/cancel`, { method: "POST" }); openMine(); load(); }
      catch (err) { alert(err.message); }
    };
  } catch (err) { show(`<p class="err" role="alert">${esc(err.message)}</p>`); }
}

const card = d => `<div class="found"><h3>${esc(d.reference)} <span class="badge ${esc(d.status)}">${esc(d.status)}</span></h3>
  <p>${esc(d.room_type)}, room ${esc(d.room_number)}<br>${esc(d.check_in)} to ${esc(d.check_out)}<br>Total ${money(d.total_amount)}</p>
  ${d.status === "reserved" ? `<button class="btn" id="cx" style="margin-top:12px">Cancel booking</button>` : ""}</div>`;

$("#mf").onsubmit = async e => {
  e.preventDefault();
  const ref = e.target.ref.value.trim(), q = `?email=${encodeURIComponent(e.target.email.value.trim())}`;
  const r = await fetch(`${API}/bookings/${encodeURIComponent(ref)}${q}`), d = await r.json().catch(() => null);
  if (!r.ok) return $("#found").innerHTML = `<p class="err" role="alert">${esc(msg(d))}</p>`;
  $("#found").innerHTML = card(d);
  const cx = $("#cx");
  if (cx) cx.onclick = async () => {
    if (!confirm("Cancel this booking?")) return;
    const r2 = await fetch(`${API}/bookings/${encodeURIComponent(ref)}/cancel${q}`, { method: "POST" }), d2 = await r2.json().catch(() => null);
    $("#found").innerHTML = r2.ok ? card(d2) : `<p class="err" role="alert">${esc(msg(d2))}</p>`;
    load();
  };
};
(async () => { if (tok()) { try { me = await api("/auth/me"); } catch (_) {} } renderAcct(); })();
load();
