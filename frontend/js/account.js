// Staff: forgot password, reset link and change password.
const Account = {
  notice(text) {
    UI.modal("Password", `<p>${UI.esc(text)}</p><button class="btn full" id="ok">OK</button>`, m => { m.querySelector("#ok").onclick = UI.closeModal; });
  },
  forgot() {
    UI.modal("Reset your password", `<p class="mut">Enter your staff email. If it is registered, we send a reset link.</p>
      <form id="f"><label>Email</label><input name="email" type="email" required><button class="btn full">Send reset link</button></form>`, m => {
      m.querySelector("#f").onsubmit = e => {
        e.preventDefault();
        UI.run(async () => Account.notice((await API.post("/auth/forgot", { email: e.target.email.value })).message));
      };
    });
  },
  reset(token) {
    UI.modal("Set a new password", `<form id="f"><label>New password (min 8 characters)</label><input name="p1" type="password" minlength="8" maxlength="72" required>
      <label>Repeat new password</label><input name="p2" type="password" required><button class="btn full">Save password</button></form>`, m => {
      m.querySelector("#f").onsubmit = e => {
        e.preventDefault();
        const f = e.target;
        if (f.p1.value !== f.p2.value) return UI.toast("Passwords do not match", "bad");
        UI.run(async () => Account.notice((await API.post("/auth/reset", { token, new_password: f.p1.value })).message));
      };
    });
  },
  change() {
    UI.modal("Change my password", `<form id="f"><label>Current password</label><input name="cur" type="password" required>
      <label>New password (min 8 characters)</label><input name="p1" type="password" minlength="8" maxlength="72" required>
      <label>Repeat new password</label><input name="p2" type="password" required><button class="btn full">Change password</button></form>`, m => {
      m.querySelector("#f").onsubmit = e => {
        e.preventDefault();
        const f = e.target;
        if (f.p1.value !== f.p2.value) return UI.toast("Passwords do not match", "bad");
        UI.run(async () => {
          await API.post("/auth/change-password", { current_password: f.cur.value, new_password: f.p1.value });
          UI.closeModal(); UI.toast("Password changed");
        });
      };
    });
  },
};

$("#fgt").onclick = e => { e.preventDefault(); Account.forgot(); };
$("#cpw").onclick = Account.change;
const resetToken = new URLSearchParams(location.search).get("reset");
if (resetToken) { history.replaceState(null, "", location.pathname); Account.reset(resetToken); }
