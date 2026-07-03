const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const webSearchInput = document.querySelector("#web-search-input");

function addMessage(role, content, sources = []) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${role === "assistant" ? "assistant-avatar" : ""}`;
  avatar.textContent = role === "assistant" ? "C" : "T";

  const contentWrapper = document.createElement("div");
  contentWrapper.className = "message-content";

  const paragraph = document.createElement("p");
  paragraph.textContent = content;

  contentWrapper.appendChild(paragraph);
  if (sources.length > 0) {
    const list = document.createElement("ol");
    list.className = "sources";
    sources.forEach((source) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = source.title || source.domain || source.url;
      item.appendChild(link);
      list.appendChild(item);
    });
    contentWrapper.appendChild(list);
  }
  article.appendChild(avatar);
  article.appendChild(contentWrapper);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function setLoading(isLoading) {
  const button = form.querySelector("button");
  button.disabled = isLoading;
  input.disabled = isLoading;
  webSearchInput.disabled = isLoading;
  button.textContent = isLoading ? "..." : "↑";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = input.value.trim();
  if (!message) return;

  addMessage("user", message);
  input.value = "";
  setLoading(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, web_search: webSearchInput.checked }),
    });

    const data = await response.json();
    addMessage("assistant", data.answer, data.sources || []);
  } catch (error) {
    addMessage("assistant", "There was an error connecting to the app.");
  } finally {
    setLoading(false);
    input.focus();
  }
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
