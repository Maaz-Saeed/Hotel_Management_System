// Admin-only pages: room types and staff users.
Views["room-types"] = {
  title: "Room types",
  async render(el, bar) {
    let types = [];
    const load = async () => {
      types = await API.get("/room-types");
      el.innerHTML = `<div class="card">${types.length ? UI.table(["Name", "Price / night", "Capacity", "Description", ""], types.map(t =>
        `<tr><td><b>${UI.esc(t.name)}</b></td><td>${UI.money(t.base_price)}</td><td>${t.capacity} guest(s)</td><td>${UI.esc(t.description || "-")}</td>
         <td class="acts"><button class="btn ghost sm" data-edit="${t.id}">Edit</button><button class="btn bad sm" data-del="${t.id}">Delete</button></td></tr>`).join("")) : UI.empty("No room types yet")}</div>`;
    };
    el.onclick = e => {
      const ed = e.target.closest("[data-edit]"), del = e.target.closest("[data-del]");
      if (ed) typeForm(types.find(t => t.id == ed.dataset.edit), load);
      if (del && confirm("Delete this room type?"))
        UI.run(async () => { await API.request("/room-types/" + del.dataset.del, { method: "DELETE" }); UI.toast("Room type deleted"); load(); });
    };
    bar.append(UI.button("+ Add room type", () => typeForm(null, load)));
    await load();
  },
};

function typeForm(t, done) {
  const v = t || { name: "", base_price: "", capacity: 1, description: "" };
  UI.modal(t ? "Edit room type" : "Add room type", `<form id="f">
    <label>Name</label><input name="name" value="${UI.esc(v.name)}" required minlength="2">
    <div class="row"><div><label>Price per night (Rs)</label><input name="base_price" type="number" step="0.01" min="1" value="${UI.esc(v.base_price)}" required></div>
    <div><label>Capacity</label><input name="capacity" type="number" min="1" max="10" value="${v.capacity}" required></div></div>
    <label>Description (optional)</label><input name="description" value="${UI.esc(v.description || "")}">
    <button class="btn full">Save</button></form>`, m => {
    m.querySelector("#f").onsubmit = e => {
      e.preventDefault();
      const f = e.target;
      const body = { name: f.name.value, base_price: f.base_price.value, capacity: +f.capacity.value, description: f.description.value || null };
      UI.run(async () => {
        await (t ? API.patch("/room-types/" + t.id, body) : API.post("/room-types", body));
        UI.closeModal(); UI.toast("Room type saved"); done();
      });
    };
  });
}

Views.staff = {
  title: "Staff",
  async render(el, bar) {
    let users = [];
    const load = async () => {
      users = await API.get("/users", { limit: 100 });
      el.innerHTML = `<div class="card">${UI.table(["Name", "Email", "Role", "Status", ""], users.map(u =>
        `<tr><td><b>${UI.esc(u.full_name)}</b></td><td>${UI.esc(u.email)}</td><td style="text-transform:capitalize">${UI.esc(u.role)}</td>
         <td><span class="badge ${u.is_active ? "paid" : "cancelled"}">${u.is_active ? "active" : "inactive"}</span></td>
         <td class="acts"><button class="btn ghost sm" data-edit="${u.id}">Edit</button></td></tr>`).join(""))}</div>`;
    };
    el.onclick = e => { const b = e.target.closest("[data-edit]"); if (b) staffForm(users.find(u => u.id == b.dataset.edit), load); };
    bar.append(UI.button("+ Add staff", () => staffForm(null, load)));
    await load();
  },
};

function staffForm(u, done) {
  const roles = ["receptionist", "manager", "admin"];
  const opts = r => roles.map(x => `<option ${x === r ? "selected" : ""}>${x}</option>`).join("");
  UI.modal(u ? "Edit staff member" : "Add staff member", `<form id="f">
    ${u ? `<p class="mut">${UI.esc(u.full_name)} · ${UI.esc(u.email)}</p>` : `
    <label>Full name</label><input name="full_name" required minlength="2">
    <label>Email</label><input name="email" type="email" required>`}
    <label>${u ? "New password (leave empty to keep)" : "Password (min 8 characters)"}</label><input name="password" type="password" minlength="8" ${u ? "" : "required"}>
    <div class="row"><div><label>Role</label><select name="role">${opts(u ? u.role : "receptionist")}</select></div>
    ${u ? `<div><label>Status</label><select name="active"><option value="1" ${u.is_active ? "selected" : ""}>Active</option><option value="0" ${u.is_active ? "" : "selected"}>Inactive</option></select></div>` : ""}</div>
    <button class="btn full">Save</button></form>`, m => {
    m.querySelector("#f").onsubmit = e => {
      e.preventDefault();
      const f = e.target;
      UI.run(async () => {
        if (u) {
          const body = { role: f.role.value, is_active: f.active.value === "1" };
          if (f.password.value) body.password = f.password.value;
          await API.patch("/users/" + u.id, body);
        } else {
          await API.post("/users", { full_name: f.full_name.value, email: f.email.value, password: f.password.value, role: f.role.value });
        }
        UI.closeModal(); UI.toast("Staff member saved"); done();
      });
    };
  });
}
