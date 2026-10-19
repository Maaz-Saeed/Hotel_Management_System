// Admin-only pages: room types and staff users.
Views["room-types"] = {
  title: "Room types",
  async render(el, bar) {
    let types = [];
    const load = async () => {
      types = await API.get("/room-types");
      el.innerHTML = `<div class="card">${types.length ? UI.table(["Name", "Price / night", "Capacity", "Description", ""], types.map(t =>
        `<tr><td>${t.image_url ? `<img src="${UI.esc(t.image_url)}" alt="" width="48" height="36" style="object-fit:cover;border-radius:6px;vertical-align:middle;margin-right:10px" onerror="this.remove()">` : ""}<b>${UI.esc(t.name)}</b></td><td>${UI.money(t.base_price)}</td><td>${t.capacity} guest(s)</td><td>${UI.esc(t.description || "-")}</td>
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
  const v = t || { name: "", base_price: "", capacity: 1, description: "", image_url: "", amenities: "" };
  UI.modal(t ? "Edit room type" : "Add room type", `<form id="f">
    <label>Name</label><input name="name" value="${UI.esc(v.name)}" required minlength="2">
    <div class="row"><div><label>Price per night (PKR)</label><input name="base_price" type="number" step="0.01" min="1" value="${UI.esc(v.base_price)}" required></div>
    <div><label>Capacity</label><input name="capacity" type="number" min="1" max="10" value="${v.capacity}" required></div></div>
    <label>Description (optional)</label><input name="description" value="${UI.esc(v.description || "")}">
    <label>Room photo (JPG, PNG or WebP, up to 3 MB)</label>
    ${v.image_url ? `<img src="${UI.esc(v.image_url)}" alt="" style="width:100%;max-height:150px;object-fit:cover;border-radius:10px;margin-bottom:8px" onerror="this.remove()">` : ""}
    <input name="file" type="file" accept="image/png,image/jpeg,image/webp">
    <label>Or paste a photo link (optional)</label><input name="image_url" value="${UI.esc(v.image_url || "")}" placeholder="https://...">
    <label>Amenities, separated by commas (optional)</label><input name="amenities" value="${UI.esc(v.amenities || "")}" placeholder="WiFi, Air conditioning, Smart TV">
    <button class="btn full">Save</button></form>`, m => {
    m.querySelector("#f").onsubmit = e => {
      e.preventDefault();
      const f = e.target, file = f.file.files[0];
      if (file && file.size > 3 * 1024 * 1024) return UI.toast("Image must be 3 MB or smaller", "bad");
      const body = { name: f.name.value, base_price: f.base_price.value, capacity: +f.capacity.value,
        description: f.description.value || null, image_url: f.image_url.value || null, amenities: f.amenities.value || null };
      UI.run(async () => {
        const saved = await (t ? API.patch("/room-types/" + t.id, body) : API.post("/room-types", body));
        if (file) { const fd = new FormData(); fd.append("file", file); await API.upload(`/room-types/${saved.id}/image`, fd); }
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
  const v = u || { full_name: "", email: "", role: "receptionist", is_active: true };
  UI.modal(u ? "Edit staff member" : "Add staff member", `<form id="f">
    <label>Full name</label><input name="full_name" value="${UI.esc(v.full_name)}" required minlength="2" maxlength="100">
    <label>Email</label><input name="email" type="email" value="${UI.esc(v.email)}" required>
    <label>${u ? "New password (leave empty to keep the current one)" : "Password (min 8 characters)"}</label>
    <input name="password" type="password" minlength="8" maxlength="72" autocomplete="new-password" ${u ? "" : "required"}>
    <div class="row"><div><label>Role</label><select name="role">${opts(v.role)}</select></div>
    ${u ? `<div><label>Status</label><select name="active"><option value="1" ${v.is_active ? "selected" : ""}>Active</option><option value="0" ${v.is_active ? "" : "selected"}>Inactive</option></select></div>` : ""}</div>
    <button class="btn full">Save</button></form>`, m => {
    m.querySelector("#f").onsubmit = e => {
      e.preventDefault();
      const f = e.target;
      const body = { full_name: f.full_name.value, email: f.email.value, role: f.role.value };
      if (f.password.value) body.password = f.password.value;
      UI.run(async () => {
        if (u) { body.is_active = f.active.value === "1"; await API.patch("/users/" + u.id, body); }
        else await API.post("/users", body);
        UI.closeModal(); UI.toast("Staff member saved"); done();
      });
    };
  });
}
