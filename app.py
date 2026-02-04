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
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    if not client.api_key:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server."}), 500

    try:
        system_prompt = f"""
You are Network Gemini, an expert 5G Network Operations and Analytics Assistant.

You can analyze:
- 5G network logs
- Site and sector metadata
- Alarm and fault data
- Network KPIs and performance indicators

Your responsibilities:
- Root cause analysis (RCA)
- Network health assessment
- Alarm correlation
- Impact analysis (site, sector, service)
- Actionable recommendations
- Executive-level summaries when requested

Context available:
Network Logs:
{ANALYSIS_STORE['network_log'][:8000] if ANALYSIS_STORE['network_log'] else "No network logs uploaded."}

Network Data:
{ANALYSIS_STORE['network_data'][:8000] if ANALYSIS_STORE['network_data'] else "No network data uploaded."}

Alarm Data:
{ANALYSIS_STORE['alarm_data'][:8000] if ANALYSIS_STORE['alarm_data'] else "No alarm data uploaded."}
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
        return jsonify({"error": str(e)}), 500


# ----------------------------
# NO app.run() HERE
# Gunicorn will start the app
# ----------------------------
