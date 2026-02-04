from flask import Flask, jsonify, render_template, request
import os
import requests

app = Flask(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
ANALYSIS_STORE = {
    "network_log": None,
    "network_data": None,
    "alarm_data": None,
    "summary": None,
}


def _build_analysis_summary():
    sections = []
    if ANALYSIS_STORE["network_log"]:
        sections.append(f"Network log insights: {ANALYSIS_STORE['network_log']}")
    if ANALYSIS_STORE["network_data"]:
        sections.append(f"Network data insights: {ANALYSIS_STORE['network_data']}")
    if ANALYSIS_STORE["alarm_data"]:
        sections.append(f"Alarm data insights: {ANALYSIS_STORE['alarm_data']}")
    return " | ".join(sections) if sections else None


def _analyze_network_log(content):
    lines = [line for line in content.splitlines() if line.strip()]
    error_lines = [line for line in lines if "error" in line.lower() or "fail" in line.lower()]
    return (
        f"{len(lines)} lines scanned, {len(error_lines)} potential error lines detected."
        if lines
        else "No log entries detected."
    )


def _analyze_network_data(content):
    lines = [line for line in content.splitlines() if line.strip()]
    key_values = [line for line in lines if ":" in line]
    return (
        f"{len(lines)} lines parsed with {len(key_values)} site parameter entries."
        if lines
        else "No network data entries detected."
    )


def _analyze_alarm_data(content):
    lines = [line for line in content.splitlines() if line.strip()]
    alarm_lines = [line for line in lines if "alarm" in line.lower()]
    return (
        f"{len(lines)} lines scanned with {len(alarm_lines)} alarm indicators."
        if lines
        else "No alarm entries detected."
    )


@app.route("/")
def index():
        return render_template("index.html", analysis_summary=ANALYSIS_STORE["summary"])


@app.route("/log-analysis", methods=["GET", "POST"])
def log_analysis():
    status_message = None
    if request.method == "POST":
        uploads = {
            "network_log": request.files.get("network_log"),
            "network_data": request.files.get("network_data"),
            "alarm_data": request.files.get("alarm_data"),
        }
        if not any(uploads.values()):
            status_message = "Please select at least one file to upload."
        else:
            if uploads["network_log"] and uploads["network_log"].filename:
                content = uploads["network_log"].read().decode("utf-8", errors="ignore")
                ANALYSIS_STORE["network_log"] = _analyze_network_log(content)
            if uploads["network_data"] and uploads["network_data"].filename:
                content = uploads["network_data"].read().decode("utf-8", errors="ignore")
                ANALYSIS_STORE["network_data"] = _analyze_network_data(content)
            if uploads["alarm_data"] and uploads["alarm_data"].filename:
                content = uploads["alarm_data"].read().decode("utf-8", errors="ignore")
                ANALYSIS_STORE["alarm_data"] = _analyze_alarm_data(content)

            ANALYSIS_STORE["summary"] = _build_analysis_summary()
            status_message = "Uploads received. Analysis is ready in the main chat."

    return render_template("log_analysis.html", status_message=status_message)
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
           {
                "role": "system",
                "content": "You are Network Gemini, a helpful network operations assistant.",
            },
            {"role": "user", "content": message},
        ],
        "temperature": 0.4,
    }
 if ANALYSIS_STORE["summary"]:
        payload["messages"].insert(
            1,
            {
                "role": "system",
                "content": f"Latest uploaded analysis summary: {ANALYSIS_STORE['summary']}",
            },
        )

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
