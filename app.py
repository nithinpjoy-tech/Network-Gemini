from flask import Flask, jsonify, render_template, request
import os
import requests

app = Flask(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is required."}), 400

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server."}), 500

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are Network Gemini, a helpful network operations assistant."},
            {"role": "user", "content": message},
        ],
        "temperature": 0.4,
    }

    response = requests.post(
        OPENAI_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if response.status_code >= 400:
        return (
            jsonify({"error": "OpenAI request failed", "details": response.text}),
            response.status_code,
        )

    reply = response.json()["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
