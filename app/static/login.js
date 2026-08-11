const form = document.querySelector("#loginForm");
const password = document.querySelector("#password");
const message = document.querySelector("#loginMessage");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  message.textContent = "";
  button.disabled = true;
  button.firstElementChild.textContent = "Checking...";
  try {
    const response = await fetch("/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: password.value }),
    });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.message || "Unable to log in");
    }
    window.location.replace("/dashboard");
  } catch (error) {
    message.textContent = error.message;
    password.select();
  } finally {
    button.disabled = false;
    button.firstElementChild.textContent = "Open dashboard";
  }
});
