const elements = {
  form: document.querySelector("#shortenForm"),
  input: document.querySelector("#urlInput"),
  message: document.querySelector("#formMessage"),
  resultCard: document.querySelector("#resultCard"),
  resultLink: document.querySelector("#resultLink"),
  copyResult: document.querySelector("#copyResult"),
  apiState: document.querySelector("#apiState"),
  refresh: document.querySelector("#refreshButton"),
  loading: document.querySelector("#loadingState"),
  empty: document.querySelector("#emptyState"),
  table: document.querySelector("#tableWrap"),
  body: document.querySelector("#linksBody"),
  totalLinks: document.querySelector("#totalLinks"),
  totalClicks: document.querySelector("#totalClicks"),
  topLink: document.querySelector("#topLink"),
  toast: document.querySelector("#toast"),
  logout: document.querySelector("#logoutButton"),
};

let toastTimer;
const isOwnerDashboard = window.location.pathname === "/dashboard";

if (isOwnerDashboard) document.body.classList.remove("public-page");

function shortUrl(code) {
  return `${window.location.origin}/${code}`;
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (response.ok) return response.status === 204 ? null : response.json();

  if (response.status === 401 && isOwnerDashboard) {
    window.location.replace("/login");
    throw new Error("Your session expired");
  }

  let payload = {};
  try { payload = await response.json(); } catch (_) { /* non-JSON error */ }
  const validationMessage = payload.details?.[0]?.message;
  throw new Error(validationMessage || payload.message || payload.detail || `Request failed (${response.status})`);
}

function toast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => elements.toast.classList.remove("show"), 2200);
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch (_) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
  toast("Link copied to clipboard");
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function icon(path) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${path}"/></svg>`;
}

function renderLinks(links) {
  elements.loading.hidden = true;
  elements.totalLinks.textContent = links.length;
  elements.totalClicks.textContent = links.reduce((total, link) => total + link.clicks, 0).toLocaleString();
  const top = [...links].sort((a, b) => b.clicks - a.clicks)[0];
  elements.topLink.textContent = top ? `/${top.short_code}` : "—";

  if (!links.length) {
    elements.empty.hidden = false;
    elements.table.hidden = true;
    return;
  }

  elements.empty.hidden = true;
  elements.table.hidden = false;
  elements.body.replaceChildren(...links.map((link) => {
    const row = document.createElement("tr");
    const url = shortUrl(link.short_code);
    row.innerHTML = `
      <td><div class="short-cell"><span class="link-favicon">↗</span><a class="short-url" href="${url}" target="_blank" rel="noopener">/${link.short_code}</a></div></td>
      <td><a class="destination" href="${link.original_url}" target="_blank" rel="noopener" title="${link.original_url}">${link.original_url}</a></td>
      <td>${formatDate(link.created_at)}</td>
      <td><span class="click-count">${link.clicks}</span></td>
      <td><div class="actions">
        <button class="icon-button copy" type="button" title="Copy short link" aria-label="Copy short link">${icon("M8 8h11v11H8z M5 16H4V5h11v1")}</button>
        <button class="icon-button delete" type="button" title="Delete link" aria-label="Delete link">${icon("M4 7h16 M9 7V4h6v3 M7 7l1 13h8l1-13 M10 11v5 M14 11v5")}</button>
      </div></td>`;
    row.querySelector(".copy").addEventListener("click", () => copy(url));
    row.querySelector(".delete").addEventListener("click", () => deleteLink(link.id, row));
    return row;
  }));
}

async function loadLinks({ quiet = false } = {}) {
  if (!quiet) {
    elements.loading.hidden = false;
    elements.empty.hidden = true;
    elements.table.hidden = true;
  }
  try {
    const links = await request("/urls/all?limit=100");
    renderLinks(links);
  } catch (error) {
    elements.loading.hidden = true;
    elements.empty.hidden = false;
    elements.empty.querySelector("h3").textContent = "Couldn’t load your links";
    elements.empty.querySelector("p").textContent = error.message;
  }
}

async function deleteLink(id, row) {
  if (!window.confirm("Delete this short link? This cannot be undone.")) return;
  try {
    await request(`/urls/${id}`, { method: "DELETE" });
    row.remove();
    toast("Short link deleted");
    if (isOwnerDashboard) await loadLinks({ quiet: true });
  } catch (error) {
    toast(error.message);
  }
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.message.textContent = "";
  elements.resultCard.hidden = true;

  let value = elements.input.value.trim();
  if (value && !/^https?:\/\//i.test(value)) value = `https://${value}`;
  try { new URL(value); } catch (_) {
    elements.message.textContent = "Enter a complete, valid URL.";
    elements.input.focus();
    return;
  }

  const button = elements.form.querySelector("button");
  button.disabled = true;
  button.querySelector("span:first-child").textContent = "Shortening...";
  try {
    const link = await request("/urls", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original_url: value }),
    });
    const url = shortUrl(link.short_code);
    elements.resultLink.href = url;
    elements.resultLink.textContent = url;
    elements.resultCard.hidden = false;
    elements.input.value = "";
    if (isOwnerDashboard) await loadLinks({ quiet: true });
  } catch (error) {
    elements.message.textContent = error.message;
  } finally {
    button.disabled = false;
    button.querySelector("span:first-child").textContent = "Shorten link";
  }
});

elements.copyResult.addEventListener("click", () => copy(elements.resultLink.href));
elements.refresh.addEventListener("click", () => loadLinks());
elements.logout.addEventListener("click", async () => {
  await fetch("/admin/logout", { method: "POST" });
  window.location.replace("/login");
});

async function checkHealth() {
  try {
    await request("/health");
    elements.apiState.className = "api-state online";
    elements.apiState.lastElementChild.textContent = "API online";
  } catch (_) {
    elements.apiState.className = "api-state offline";
    elements.apiState.lastElementChild.textContent = "API offline";
  }
}

checkHealth();
if (isOwnerDashboard) loadLinks();
