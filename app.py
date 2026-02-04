import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

# ----------------------------
# Flask App Init
# ----------------------------
app = Flask(__name__)

# ----------------------------
# OpenAI Client Init
# ----------------------------
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# ----------------------------
# In-memory analysis store
# (for uploaded logs / data)
# ----------------------------
ANALYSIS_STORE = {
    "network_log": None,
    "network_data": None,
    "alarm_data": None,
    "summary": None
}

# ----------------------------
# Home Page
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ----------------------------
# Upload & Parse Logs
# ----------------------------
@app.route("/log-analysis", methods=["GET", "POST"])
def log_analysis():
    if request.method == "GET":
        return render_template("log_analysis.html")
    status_message = None

    uploads = {
        "network_log": request.files.get("network_log"),
        "network_data": request.files.get("network_data"),
        "alarm_data": request.files.get("alarm_data")
    }

    if not any(uploads.values()):
        return render_template(
            "log_analysis.html",
            status_message="Please upload at least one file."
        )

    if uploads["network_log"] and uploads["network_log"].filename:
        ANALYSIS_STORE["network_log"] = uploads["network_log"].read().decode(
            "utf-8", errors="ignore"
        )

    if uploads["network_data"] and uploads["network_data"].filename:
        ANALYSIS_STORE["network_data"] = uploads["network_data"].read().decode(
            "utf-8", errors="ignore"
        )

    if uploads["alarm_data"] and uploads["alarm_data"].filename:
        ANALYSIS_STORE["alarm_data"] = uploads["alarm_data"].read().decode(
            "utf-8", errors="ignore"
        )

    ANALYSIS_STORE["summary"] = (
        f"Latest uploads ready: "
        f"Network log insights: {len(ANALYSIS_STORE['network_log'].splitlines()) if ANALYSIS_STORE['network_log'] else 0} lines scanned. | "
        f"Network data insights: {len(ANALYSIS_STORE['network_data'].splitlines()) if ANALYSIS_STORE['network_data'] else 0} lines parsed. | "
        f"Alarm data insights: {len(ANALYSIS_STORE['alarm_data'].splitlines()) if ANALYSIS_STORE['alarm_data'] else 0} lines scanned."
    )

    status_message = "Uploads received. Analysis is ready in the main chat."

    return render_template("log_analysis.html", status_message=status_message)


# ----------------------------
# Chat Endpoint (OPENAI POWERED)
# ----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get("question", "").strip()

    if not user_message:
        return jsonify({"answer": "Please enter a message."})

    try:
        system_prompt = f"""
You are Network Gemini, an expert 5G Network Operations and Analytics Assistant.

You analyze:
- Network logs
- Site & sector metadata
- Alarm data
- KPIs

Provide:
- RCA
- Impact analysis
- Recommendations
- Executive summaries

Context:
Network Logs:
{ANALYSIS_STORE['network_log'][:4000] if ANALYSIS_STORE['network_log'] else "No logs."}

Network Data:
{ANALYSIS_STORE['network_data'][:4000] if ANALYSIS_STORE['network_data'] else "No data."}

Alarm Data:
{ANALYSIS_STORE['alarm_data'][:4000] if ANALYSIS_STORE['alarm_data'] else "No alarms."}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.4
        )

        reply = response.choices[0].message.content
        return jsonify({"answer": reply})

    except Exception as e:
        # SAFE FALLBACK — UI WILL NEVER HANG
        return jsonify({
            "answer": "⚠️ AI temporarily unavailable. Please check API key, quota, or billing."
        })


# ----------------------------
# NO app.run() HERE
# Gunicorn will start the app
# ----------------------------
