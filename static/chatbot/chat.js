document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("chat-toggle");
  const widget = document.getElementById("chat-widget");
  const closeBtn = document.getElementById("chat-close");
  const body = document.getElementById("chat-body");
  const input = document.getElementById("chat-input");
  const send = document.getElementById("chat-send");

  let conversationId = null;

  //  Get CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie("csrftoken");

  //  Append a chat message
  function appendMessage(role, text) {
    const wrapper = document.createElement("div");
    wrapper.className = "flex " + (role === "user" ? "justify-end" : "justify-start");

    const el = document.createElement("div");
    el.className =
      role === "bot"
        ? "bg-indigo-50 text-gray-800 p-2 rounded-md max-w-[75%]"
        : "bg-gray-100 text-gray-900 p-2 rounded-md max-w-[75%]";
    el.innerText = text;

    wrapper.appendChild(el);
    body.appendChild(wrapper);
    body.scrollTop = body.scrollHeight;
  }

  //  Show widget & hide bubble
  toggle?.addEventListener("click", () => {
    widget.classList.remove("hidden");
    toggle.classList.add("hidden");

    if (!conversationId) {
      fetch("/api/chatbot/start/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({}),
      })
        .then((r) => r.json())
        .then((data) => {
          conversationId = data.conversation_id;
        })
        .catch(() => {
          conversationId = null;
        });
    }
  });

  //  Close widget & show bubble again
  closeBtn?.addEventListener("click", () => {
    widget.classList.add("hidden");
    toggle.classList.remove("hidden");
  });

  //  Send message to backend
  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    appendMessage("user", text);
    input.value = "";

    // typing indicator
    const typingWrapper = document.createElement("div");
    typingWrapper.className = "flex justify-start";
    const typingEl = document.createElement("div");
    typingEl.className =
      "bg-indigo-50 text-gray-400 p-2 rounded-md max-w-[75%] italic";
    typingEl.innerText = "…";
    typingWrapper.appendChild(typingEl);
    body.appendChild(typingWrapper);
    body.scrollTop = body.scrollHeight;

    try {
      const res = await fetch("/api/chatbot/message/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ conversation_id: conversationId, text }),
      });

      const data = await res.json();
      typingWrapper.remove();
      appendMessage("bot", data.reply || "I didn’t get that.");
    } catch (err) {
      typingWrapper.remove();
      appendMessage("bot", "⚠️ Sorry — network error.");
    }
  }

  // Events
  send?.addEventListener("click", sendMessage);
  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });
});
