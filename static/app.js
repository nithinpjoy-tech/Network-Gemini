const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatMessage = document.getElementById("chat-message");

function appendMessage(role, text) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  message.appendChild(bubble);
  chatWindow.appendChild(message);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(message) {
  appendMessage("user", message);
  chatMessage.value = "";
  appendMessage("assistant", "Thinking...");

  const placeholder = chatWindow.lastElementChild;
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    if (!response.ok) {
      placeholder.querySelector(".bubble").textContent =
        data.error || "Something went wrong.";
      return;
    }

    placeholder.querySelector(".bubble").textContent = data.reply;
  } catch (error) {
    placeholder.querySelector(".bubble").textContent =
      "Unable to reach the server.";
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = chatMessage.value.trim();
  if (!message) {
    return;
  }
  sendMessage(message);
});

const menuButtons = document.querySelectorAll(".menu-button");
menuButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const targetId = button.getAttribute("data-target");
    const submenu = document.getElementById(targetId);
    if (submenu) {
      submenu.classList.toggle("open");
    }
  });
});

// Open the first section by default
const firstSubmenu = document.getElementById("copilot");
if (firstSubmenu) {
  firstSubmenu.classList.add("open");
}
