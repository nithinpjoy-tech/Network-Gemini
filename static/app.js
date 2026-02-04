const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatMessage = document.getElementById("chat-message");

// -----------------------------
// UI helper
// -----------------------------
function appendMessage(role, text) {
  const msg = document.createElement("div");
  msg.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  msg.appendChild(bubble);
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// -----------------------------
// Upload handling
// -----------------------------
function triggerUpload() {
  document.getElementById("network-log").click();

  document.getElementById("network-log").onchange = uploadFiles;
}

async function uploadFiles() {
  const formData = new FormData();

  const networkLog = document.getElementById("network-log").files[0];
  const alarmLog = document.getElementById("alarm-log").files[0];
  const networkData = document.getElementById("network-data").files[0];

  if (networkLog) formData.append("network_log", networkLog);
  if (alarmLog) formData.append("alarm_log", alarmLog);
  if (networkData) formData.append("network_data", networkData);

  const res = await fetch("/upload", {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  appendMessage(
    "system",
    "📂 Files uploaded. Network Gemini is ready for analysis."
  );
}

// -----------------------------
// Chat
// -----------------------------
async function sendMessage(message) {
  appendMessage("user", message);
  appendMessage("assistant", "Analyzing…");

  const placeholder = chatWindow.lastElementChild;

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    const data = await res.json();
    placeholder.querySelector(".bubble").textContent =
      data.answer || "No response";

  } catch {
    placeholder.querySelector(".bubble").textContent =
      "⚠️ Server not reachable";
  }
}

// -----------------------------
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const msg = chatMessage.value.trim();
  if (!msg) return;
  chatMessage.value = "";
  sendMessage(msg);
});

// -----------------------------
// Sidebar toggle
// -----------------------------
document.querySelectorAll(".menu-button").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = document.getElementById(
      btn.getAttribute("data-target")
    );
    if (target) target.classList.toggle("open");
  });
});
