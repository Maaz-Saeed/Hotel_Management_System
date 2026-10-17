// One object per page. Each has a title and render(container, headerBar).
const Views = {};

const stat = (t, val, s = "", icon = "home", tone = "ind") =>
  `<div class="stat"><div class="ico t-${tone}">${UI.icon(icon)}</div><div><span>${t}</span><b>${val}</b><small>${s}</small></div></div>`;

function bookingList(items) {
  if (!items.length) return UI.empty("Nobody today");
  return UI.table(["Guest", "Room", "Status"], items.map(b =>
    `<tr><td>${UI.esc(b.guest.full_name)}</td><td>${UI.esc(b.room.room_number)}</td><td>${UI.badge(b.status)}</td></tr>`).join(""));
}

/* ---------------- Dashboard ---------------- */
Views.dashboard = {
  title: "Dashboard",
  async render(el) {
    const [occ, arrivals, departures] = await Promise.all([
      API.get("/reports/occupancy"), API.get("/reports/arrivals"), API.get("/reports/departures"),
    ]);
    let revenue = "";
    if (UI.can("admin", "manager")) {
      const end = UI.today();
      const r = await API.get("/reports/revenue", { start_date: UI.addDays(end, -6), end_date: end });
      revenue = stat("Revenue (7 days)", UI.money(r.total_revenue), `${r.payments_count} payments`, "cash", "amb");
    }
    const hr = new Date().getHours();
    const greet = hr < 12 ? "Good morning" : hr < 18 ? "Good afternoon" : "Good evening";
    el.innerHTML = `
      <div class="banner"><div><h2>${greet}, ${UI.esc(App.user.full_name.split(" ")[0])} 👋</h2>
        <p>${arrivals.length} arrival(s) and ${departures.length} departure(s) today.</p></div>
        <div><a class="btn" href="#/bookings">Bookings</a><a class="btn" href="#/guests">Guests</a></div></div>
      <div class="stats">
        <div class="stat"><div class="ring" style="--p:${Number(occ.occupancy_rate)}"><i>${Number(occ.occupancy_rate)}%</i></div>
          <div><span>Occupancy today</span><b>${occ.occupied_rooms}/${occ.bookable_rooms}</b><small>rooms occupied</small></div></div>
        ${stat("Available rooms", occ.available_rooms, `${occ.maintenance_rooms} in maintenance`, "bed", "grn")}
        ${stat("Arrivals today", arrivals.length, "guests arriving", "door", "ind")}
        ${stat("Departures today", departures.length, "guests leaving", "calendar", "pnk")}
        ${revenue}
      </div>
      <div class="grid2">
        <div class="card"><h3>Arrivals today</h3>${bookingList(arrivals)}</div>
        <div class="card"><h3>Departures today</h3>${bookingList(departures)}</div>
      </div>`;
  },
};

/* ---------------- Rooms ---------------- */
Views.rooms = {
  title: "Rooms",
  async render(el, bar) {
    const types = await API.get("/room-types");
    el.innerHTML = `<div class="card">
      <div class="filters"><select id="fs"><option value="">All statuses</option><option>available</option><option>maintenance</option></select></div>
      <div id="tbl"></div></div>`;

    const load = async () => {
      const rooms = await API.get("/rooms", { status: $("#fs").value, limit: 100 });
      $("#tbl").innerHTML = rooms.length ? UI.table(
        ["Room", "Floor", "Type", "Price / night", "Capacity", "Status", ""],
        rooms.map(r => `<tr><td><b>${UI.esc(r.room_number)}</b></td><td>${r.floor}</td><td>${UI.esc(r.room_type.name)}</td>
          <td>${UI.money(r.room_type.base_price)}</td><td>${r.room_type.capacity}</td><td>${UI.badge(r.status)}</td>
          <td class="acts">${UI.can("admin") ? `<button class="btn ghost sm" data-toggle="${r.id}" data-to="${r.status === "available" ? "maintenance" : "available"}">
            Set ${r.status === "available" ? "maintenance" : "available"}</button>` : ""}</td></tr>`).join("")) : UI.empty("No rooms found");
    };
    $("#fs").onchange = load;
    el.onclick = e => {
      const b = e.target.closest("[data-toggle]");
      if (b) UI.run(async () => { await API.patch("/rooms/" + b.dataset.toggle, { status: b.dataset.to }); UI.toast("Room updated"); load(); });
    };
    if (UI.can("admin")) bar.append(UI.button("+ Add room", () => addRoom(types, load)));
    await load();
  },
};

function addRoom(types, done) {
  if (!types.length) return UI.toast("Create a room type first (run the seed script)", "bad");
  UI.modal("Add room", `<form id="f">
    <div class="row"><div><label>Room number</label><input name="room_number" required></div>
    <div><label>Floor</label><input name="floor" type="number" min="0" value="1" required></div></div>
    <label>Room type</label><select name="room_type_id">${types.map(t => `<option value="${t.id}">${UI.esc(t.name)} (${UI.money(t.base_price)})</option>`).join("")}</select>
    <button class="btn full">Save room</button></form>`, m => {
    m.querySelector("#f").onsubmit = e => {
      e.preventDefault();
      const d = UI.data(e.target);
      UI.run(async () => {
        await API.post("/rooms", { room_number: d.room_number, floor: +d.floor, room_type_id: +d.room_type_id });
        UI.closeModal(); UI.toast("Room added"); done();
      });
    };
  });
}

/* ---------------- Guests ---------------- */
Views.guests = {
  title: "Guests",
  async render(el, bar) {
    el.innerHTML = `<div class="card"><div class="filters"><input id="q" placeholder="Search name, phone, ID number or email"></div><div id="tbl"></div></div>`;
    const load = async () => {
      const guests = await API.get("/guests", { q: $("#q").value, limit: 100 });
      $("#tbl").innerHTML = guests.length ? UI.table(["Name", "Phone", "ID", "Email"], guests.map(g =>
        `<tr><td><b>${UI.esc(g.full_name)}</b></td><td>${UI.esc(g.phone)}</td>
         <td>${UI.esc(g.id_type)}: ${UI.esc(g.id_number)}</td><td>${UI.esc(g.email || "-")}</td></tr>`).join("")) : UI.empty("No guests found");
    };
    let timer;
    $("#q").oninput = () => { clearTimeout(timer); timer = setTimeout(() => UI.run(load), 300); };
    if (UI.can("admin", "receptionist")) bar.append(UI.button("+ Add guest", () => addGuest(load)));
    await load();
  },
};

function addGuest(done) {
  UI.modal("Add guest", `<form id="f">
    <label>Full name</label><input name="full_name" required minlength="2">
    <div class="row"><div><label>Phone</label><input name="phone" placeholder="0300-1234567" required></div>
    <div><label>Email (optional)</label><input name="email" type="email"></div></div>
    <div class="row"><div><label>ID type</label><select name="id_type"><option>CNIC</option><option>Passport</option><option>Other</option></select></div>
    <div><label>ID number</label><input name="id_number" required minlength="3"></div></div>
    <label>Address (optional)</label><input name="address">
    <button class="btn full">Save guest</button></form>`, m => {
    m.querySelector("#f").onsubmit = e => {
      e.preventDefault();
      UI.run(async () => { await API.post("/guests", UI.data(e.target)); UI.closeModal(); UI.toast("Guest added"); done(); });
    };
  });
}

/* ---------------- Bookings ---------------- */
Views.bookings = {
  title: "Bookings",
  async render(el, bar) {
    el.innerHTML = `<div class="card"><div class="filters"><select id="fs"><option value="">All statuses</option>
      <option>reserved</option><option>checked_in</option><option>checked_out</option><option>cancelled</option></select></div><div id="tbl"></div></div>`;
    const staff = UI.can("admin", "receptionist");

    const load = async () => {
      const list = await API.get("/bookings", { status: $("#fs").value, limit: 100 });
      $("#tbl").innerHTML = list.length ? UI.table(["#", "Guest", "Room", "Dates", "Total", "Status", ""], list.map(b => {
        const acts = !staff ? "" : [
          b.status === "reserved" ? `<button class="btn ok sm" data-act="check-in" data-id="${b.id}">Check-in</button>` : "",
          b.status === "checked_in" ? `<button class="btn ok sm" data-act="check-out" data-id="${b.id}">Check-out</button>` : "",
          b.status === "reserved" ? `<button class="btn bad sm" data-act="cancel" data-id="${b.id}">Cancel</button>` : "",
        ].join("");
        return `<tr><td>${b.id}</td><td>${UI.esc(b.guest.full_name)}</td><td>${UI.esc(b.room.room_number)}</td>
          <td>${b.check_in} → ${b.check_out}</td><td>${UI.money(b.total_amount)}</td><td>${UI.badge(b.status)}</td>
          <td class="acts">${acts}<button class="btn ghost sm" data-pay="${b.id}">Payments</button></td></tr>`;
      }).join("")) : UI.empty("No bookings yet");
    };

    $("#fs").onchange = load;
    el.onclick = e => {
      const a = e.target.closest("[data-act]"), p = e.target.closest("[data-pay]");
      if (a) UI.run(async () => { await API.request(`/bookings/${a.dataset.id}/${a.dataset.act}`, { method: "POST" }); UI.toast("Booking updated"); load(); });
      if (p) UI.run(() => paymentsModal(p.dataset.pay, staff, load));
    };
    if (staff) bar.append(UI.button("+ New booking", () => UI.run(() => newBooking(load))));
    await load();
  },
};

async function newBooking(done) {
  const guests = await API.get("/guests", { limit: 100 });
  if (!guests.length) return UI.toast("Add a guest first", "bad");
  const t = UI.today();
  let rooms = [];
  UI.modal("New booking", `<form id="f">
    <div class="row"><div><label>Check-in</label><input type="date" name="check_in" min="${t}" value="${t}" required></div>
    <div><label>Check-out</label><input type="date" name="check_out" min="${UI.addDays(t, 1)}" value="${UI.addDays(t, 1)}" required></div></div>
    <button type="button" class="btn ghost full" id="find">Find available rooms</button>
    <label>Room</label><select name="room_id" required disabled><option value="">Find rooms first</option></select>
    <label>Guest</label><select name="guest_id">${guests.map(g => `<option value="${g.id}">${UI.esc(g.full_name)} (${UI.esc(g.phone)})</option>`).join("")}</select>
    <div id="est" class="hint"></div>
    <button class="btn full">Create booking</button></form>`, m => {
    const f = m.querySelector("#f"), sel = f.room_id, est = m.querySelector("#est");
    const estimate = () => {
      const r = rooms.find(x => x.id == sel.value);
      const n = UI.nights(f.check_in.value, f.check_out.value);
      est.textContent = r ? `${n} night(s) x ${UI.money(r.room_type.base_price)} = ${UI.money(n * r.room_type.base_price)}` : "";
    };
    m.querySelector("#find").onclick = () => UI.run(async () => {
      rooms = await API.get("/rooms/available", { check_in: f.check_in.value, check_out: f.check_out.value });
      sel.disabled = !rooms.length;
      sel.innerHTML = rooms.length ? rooms.map(r => `<option value="${r.id}">${UI.esc(r.room_number)} · ${UI.esc(r.room_type.name)} · ${UI.money(r.room_type.base_price)}/night</option>`).join("")
        : `<option value="">No rooms free for these dates</option>`;
      estimate();
    });
    sel.onchange = estimate;
    f.onsubmit = e => {
      e.preventDefault();
      UI.run(async () => {
        await API.post("/bookings", { guest_id: +f.guest_id.value, room_id: +sel.value, check_in: f.check_in.value, check_out: f.check_out.value });
        UI.closeModal(); UI.toast("Booking created"); done();
      });
    };
  });
}

async function paymentsModal(id, staff, done) {
  const render = async () => {
    const [bal, pays] = await Promise.all([API.get(`/bookings/${id}/balance`), API.get("/payments", { booking_id: id })]);
    const due = Number(bal.balance_due);
    const rows = pays.length ? UI.table(["Date", "Method", "Amount"], pays.map(p =>
      `<tr><td>${new Date(p.paid_at).toLocaleString()}</td><td>${UI.esc(p.method)}</td><td>${UI.money(p.amount)}</td></tr>`).join("")) : `<p class="hint">No payments yet</p>`;
    const form = staff && due > 0 ? `<form id="pf"><div class="row"><div><label>Amount</label><input name="amount" type="number" step="0.01" min="0.01" max="${due}" value="${due}" required></div>
      <div><label>Method</label><select name="method"><option>cash</option><option>card</option><option>online</option></select></div></div>
      <button class="btn full">Take payment</button></form>` : "";
    UI.modal(`Booking #${id} payments`, `
      <div class="sum"><span>Total</span><b>${UI.money(bal.total_amount)}</b></div>
      <div class="sum"><span>Paid</span><b>${UI.money(bal.total_paid)}</b></div>
      <div class="sum"><span>Balance due</span><b>${UI.money(bal.balance_due)}</b> ${UI.badge(bal.payment_status)}</div>
      ${rows}${form}`, m => {
      const pf = m.querySelector("#pf");
      if (pf) pf.onsubmit = e => {
        e.preventDefault();
        const d = UI.data(pf);
        UI.run(async () => {
          await API.post("/payments", { booking_id: +id, amount: d.amount, method: d.method });
          UI.toast("Payment saved"); await render(); done();
        });
      };
    });
  };
  await render();
}
