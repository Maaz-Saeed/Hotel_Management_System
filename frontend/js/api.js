// All communication with the FastAPI backend lives here.
function parseError(data) {
  if (!data) return "";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail))
    return data.detail.map(e => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ");
  return "";
}

const API = {
  base: "/api/v1",
  token: () => localStorage.getItem("token"),

  async request(path, { method = "GET", body, form, params } = {}) {
    const url = new URL(API.base + path, location.origin);
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== "" && v != null) url.searchParams.set(k, v);
    });
    const headers = {};
    if (API.token()) headers.Authorization = "Bearer " + API.token();
    let payload;
    if (form) payload = new URLSearchParams(form);
    else if (body) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }

    const res = await fetch(url, { method, headers, body: payload });
    if (res.status === 401 && path !== "/auth/login") {
      localStorage.removeItem("token");
      location.reload();
    }
    if (res.status === 204) return null;
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new Error(parseError(data) || res.statusText);
    return data;
  },

  get: (path, params) => API.request(path, { params }),
  post: (path, body) => API.request(path, { method: "POST", body }),
  patch: (path, body) => API.request(path, { method: "PATCH", body }),

  async login(email, password) {
    const data = await API.request("/auth/login", { method: "POST", form: { username: email, password } });
    localStorage.setItem("token", data.access_token);
  },
};
