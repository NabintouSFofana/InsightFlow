"""
InsightFlow — Flask web app entry point.

Local dev:  python app.py        (debug on, port 5000)
Production: gunicorn app:app     (used by Render — see Procfile)
"""

import os

import pandas as pd
from flask import Flask, render_template, request

from cleaner import clean_data
from insights import generate_insights

app = Flask(__name__)

# 16 MB upload limit. Anything bigger isn't really a "messy CSV", it's a database export.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None

    if request.method == "POST":
        uploaded = request.files.get("csv")
        if not uploaded or not uploaded.filename:
            error = "Please choose a CSV file."
        elif not uploaded.filename.lower().endswith(".csv"):
            error = "That doesn't look like a CSV. Try a file ending in .csv."
        else:
            try:
                df = pd.read_csv(uploaded)
                cleaned, metrics = clean_data(df)
                result = {
                    "metrics": metrics,
                    "insights": generate_insights(cleaned),
                    "table": cleaned.head(10).to_html(classes="table", index=False),
                }
            except Exception as e:
                error = f"Could not read this CSV: {e}"

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    # Local dev only. In production, gunicorn imports `app` directly and ignores this block.
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
