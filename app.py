import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from openai import OpenAI

# ----------------------------
# App Init
# ----------------------------
app = Flask(__name__)

# ----------------------------
# OpenAI Client (safe)
# ----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ----------------------------
# GLOBAL IN-MEMORY STORAGE
# (Overwritten on every upload)
# ----------------------------
MEMORY_STORE = {
    "network_log": "",
    "alarm_log": "",
    "network_data": ""
}

# ----------------------------
# HOME
# ----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/home")
def home_redirect():
    return redirect(url_for("home"))

# ----------------------------
# FILE UPLOAD API
# ----------------------------
@app.route("/upload", methods=["POST"])
def upload():
    for key in ["network_log", "alarm_log", "network_data"]:
        file = request.files.get(key)
        if file and file.filename:
            MEMORY_STORE[key] = file.read().decode("utf-8", errors="ignore")

    return jsonify({
        "status": "success",
        "message": "Files stored in memory (old data overwritten)",
        "stats": {
            "network_log_lines": len(MEMORY_STORE["network_log"].splitlines()),
            "alarm_log_lines": len(MEMORY_STORE["alarm_log"].splitlines()),
            "network_data_lines": len(MEMORY_STORE["network_data"].splitlines())
        }
    })

# ----------------------------
# CHAT API
# ----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (
        data.get("message")
        or data.get("question")
        or ""
    ).strip()

    if not user_message:
        return jsonify({"answer": "Please enter a question."})

    # Fallback if AI disabled
    if not client:
        return jsonify({
            "answer": (
                "⚠️ AI not enabled.\n\n"
                f"Loaded data:\n"
                f"- Network logs: {len(MEMORY_STORE['network_log'].splitlines())} lines\n"
                f"- Alarm logs: {len(MEMORY_STORE['alarm_log'].splitlines())} lines\n"
                f"- Network data: {len(MEMORY_STORE['network_data'].splitlines())} lines"
            )
        })

    system_prompt = f"""
You are Network Gemini, a 5G Network Operations Copilot.

Answer questions ONLY using the uploaded data.
Do RCA, impact analysis, and recommendations.

Network Logs:
{MEMORY_STORE['network_log'][:4000] or "No network logs uploaded."}

Alarm Logs:
{MEMORY_STORE['alarm_log'][:4000] or "No alarm logs uploaded."}

Network Data:
{MEMORY_STORE['network_data'][:4000] or "No network data uploaded."}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3
        )

        return jsonify({"answer": response.choices[0].message.content})

    except Exception:
        return jsonify({
            "answer": "⚠️ AI service unavailable (quota / key issue)."
        })

# ----------------------------
# LOCAL RUN
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
