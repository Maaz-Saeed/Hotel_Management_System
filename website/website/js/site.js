const API = "/api/v1/public", CUR = "$";   // change CUR to your currency, e.g. "PKR "
const FALLBACK = [   // used when a room type has no image_url yet
  "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=900&q=80"];
const $ = s => document.querySelector(s);
const money = n => CUR + Number(n).toLocaleString(undefined, {maximumFractionDigits: 2});
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const nights = (a, b) => Math.round((new Date(b) - new Date(a)) / 864e5);
const today = new Date().toISOString().slice(0, 10);
let rooms = [], dates = null;

const msg = d => Array.isArray(d.detail) ? d.detail.map(x => x.msg.replace("Value error, ", "")).join(". ") : (d.detail || "Something went wrong");
const show = html => { $("#box").innerHTML = `<button class="x" aria-label="Close" onclick="closeM()">×</button>` + html; $("#modal").classList.add("open"); };
const closeM = () => $("#modal").classList.remove("open");
$("#modal").onclick = e => { if (e.target.id === "modal") closeM(); };
addEventListener("keydown", e => e.key === "Escape" && closeM());
addEventListener("scroll", () => $("#nav").classList.toggle("solid", scrollY > 60));

$("#ci").min = today;
$("#ci").onchange = () => { const d = new Date($("#ci").value); d.setDate(d.getDate() + 1); $("#co").min = d.toISOString().slice(0, 10); };

async function load() {
  const q = dates ? `?check_in=${dates.ci}&check_out=${dates.co}` : "";
  const r = await fetch(`${API}/room-types${q}`);
  rooms = await r.json();
  $("#rooms-sub").textContent = dates ? `${nights(dates.ci, dates.co)} night stay · ${dates.ci} to ${dates.co}` : "Choose dates above to see which rooms are free.";
  draw();
}

function draw() {
  $("#rooms-grid").innerHTML = rooms.map((r, i) => {
    const out = r.available_rooms === 0;
    const am = (r.amenities || "WiFi,Air conditioning,Smart TV,Daily housekeeping").split(",");
    return `<article class="card"><div class="img"><img loading="lazy" src="${esc(r.image_url || FALLBACK[i % FALLBACK.length])}" alt="${esc(r.name)} room" onerror="this.remove()"></div>
    <div class="body"><h3>${esc(r.name)}</h3>
    <p class="muted">Sleeps ${r.capacity}${r.available_rooms != null ? `, ${r.available_rooms} left for your dates` : ""}</p>
    <p>${esc(r.description)}</p><ul class="tags">${am.map(a => `<li>${esc(a.trim())}</li>`).join("")}</ul>
    <div class="foot"><div><b>${money(r.base_price)}</b><small> / night</small>${r.total ? `<small class="total">${money(r.total)} for ${r.nights} nights</small>` : ""}</div>
    <button class="btn" data-i="${i}" ${out ? "disabled" : ""}>${out ? "Sold out" : "Book this room"}</button></div></div></article>`;
  }).join("") || "<p>No rooms are listed yet.</p>";
}

$("#search").onsubmit = e => { e.preventDefault(); dates = {ci: $("#ci").value, co: $("#co").value}; load().then(() => $("#rooms").scrollIntoView({behavior: "smooth"})); };
$("#rooms-grid").onclick = e => { const b = e.target.closest("button[data-i]"); if (b) openBook(rooms[b.dataset.i]); };

function openBook(rt) {
  show(`<h3>Book ${esc(rt.name)}</h3><form id="bf">
  <div class="two"><label>Check-in<input type="date" name="check_in" required min="${today}" value="${dates?.ci || ""}"></label>
  <label>Check-out<input type="date" name="check_out" required value="${dates?.co || ""}"></label></div>
  <label>Full name<input name="full_name" required minlength="2"></label>
  <label>Email<input type="email" name="email" required></label>
  <label>Phone<input name="phone" required minlength="6"></label>
  <p class="sum" id="sum"></p><p class="err" id="err" role="alert"></p>
  <button class="btn full">Confirm booking</button></form>`);
  const f = $("#bf"), upd = () => { const n = nights(f.check_in.value, f.check_out.value); $("#sum").textContent = n > 0 ? `${n} night${n > 1 ? "s" : ""} × ${money(rt.base_price)} = ${money(n * rt.base_price)}. Pay at the hotel.` : ""; };
  f.oninput = upd; upd();
  f.onsubmit = async e => {
    e.preventDefault(); $("#err").textContent = "";
    const r = await fetch(`${API}/bookings`, {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({room_type_id: rt.id, ...Object.fromEntries(new FormData(f))})});
    const d = await r.json();
    if (!r.ok) return $("#err").textContent = msg(d);
    show(`<h3>Booking confirmed</h3><p>Your booking code is</p><div class="ref">${esc(d.reference)}</div>
    <p>${esc(d.room_type)} · ${d.check_in} to ${d.check_out}<br>Total ${money(d.total_amount)}, payable at the hotel.</p>
    <p class="muted">Keep this code. You will need it with your email to view or cancel the booking.</p>
    <button class="btn full" onclick="closeM()">Done</button>`);
    load();
  };
}

function card(d) {
  return `<div class="found"><h3>${esc(d.reference)} <span class="badge ${esc(d.status)}">${esc(d.status)}</span></h3>
  <p>${esc(d.room_type)}, room ${esc(d.room_number)}<br>${d.check_in} to ${d.check_out}<br>Total ${money(d.total_amount)}</p>
  ${d.status === "reserved" ? `<button class="btn" id="cx">Cancel booking</button>` : ""}</div>`;
}

$("#mf").onsubmit = async e => {
  e.preventDefault();
  const ref = e.target.ref.value.trim(), email = e.target.email.value.trim(), q = `?email=${encodeURIComponent(email)}`;
  const r = await fetch(`${API}/bookings/${encodeURIComponent(ref)}${q}`), d = await r.json();
  if (!r.ok) return $("#found").innerHTML = `<p class="err" role="alert">${esc(msg(d))}</p>`;
  $("#found").innerHTML = card(d);
  const cx = $("#cx");
  if (cx) cx.onclick = async () => {
    if (!confirm("Cancel this booking?")) return;
    const r2 = await fetch(`${API}/bookings/${encodeURIComponent(ref)}/cancel${q}`, {method: "POST"}), d2 = await r2.json();
    $("#found").innerHTML = r2.ok ? card(d2) : `<p class="err" role="alert">${esc(msg(d2))}</p>`;
    load();
  };
};
load();
