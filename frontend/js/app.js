// Login, navigation and routing.
const App = {
  user: null,
  nav: [["dashboard", "Dashboard", "home"], ["bookings", "Bookings", "calendar"], ["rooms", "Rooms", "bed"], ["guests", "Guests", "users"],
    ["room-types", "Room types", "tag", "admin"], ["staff", "Staff", "shield", "admin"]],

  async init() {
    $("#mclose").onclick = UI.closeModal;
    $("#modal").onclick = e => { if (e.target.id === "modal") UI.closeModal(); };
    $("#logout").onclick = () => { localStorage.removeItem("token"); location.hash = ""; location.reload(); };
    $("#lf").onsubmit = async e => {
      e.preventDefault();
      $("#lerr").textContent = "";
      try {
        await API.login(e.target.email.value, e.target.password.value);
        App.user = await API.get("/auth/me");
        App.start();
      } catch (err) { $("#lerr").textContent = err.message; }
    };
    if (API.token()) {
      try { App.user = await API.get("/auth/me"); return App.start(); } catch (_) { localStorage.removeItem("token"); }
    }
    $("#login").classList.remove("hidden");
  },

  start() {
    $("#login").classList.add("hidden");
    $("#shell").classList.remove("hidden");
    $("#who").innerHTML = `<b>${UI.esc(App.user.full_name)}</b><br><small>${UI.esc(App.user.role)}</small>`;
    $("#nav").innerHTML = App.nav.filter(n => !n[3] || n[3] === App.user.role).map(([k, l, i]) => `<a href="#/${k}" data-k="${k}">${UI.icon(i)}${l}</a>`).join("");
    window.onhashchange = App.route;
    App.route();
  },

  async route() {
    const key = location.hash.replace("#/", "") || "dashboard";
    const view = Views[key] || Views.dashboard;
    document.querySelectorAll("#nav a").forEach(a => a.classList.toggle("on", a.dataset.k === (Views[key] ? key : "dashboard")));
    $("#title").textContent = view.title;
    $("#sub").textContent = new Date().toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    $("#bar").innerHTML = "";
    $("#view").onclick = null;
    $("#view").innerHTML = `<p class="mut">Loading…</p>`;
    try { await view.render($("#view"), $("#bar")); }
    catch (e) { $("#view").innerHTML = UI.empty("Could not load this page: " + UI.esc(e.message)); }
  },
};

App.init();
