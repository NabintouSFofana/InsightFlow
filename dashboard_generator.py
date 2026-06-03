"""Writes a standalone HTML dashboard summarising metrics + insights."""

from pathlib import Path


def generate_dashboard(metrics, insights, chart_path, output_dir):
    """Write a self-contained dashboard.html into output_dir.

    Returns the path to the file as a string.
    """
    insights_html = "".join(f"<li>{item}</li>" for item in insights)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>InsightFlow Dashboard</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; padding: 40px; color: #111; }}
    h1 {{ font-size: 28px; margin-bottom: 24px; }}
    .card {{ padding: 20px; margin: 10px 0; background: #f4f4f4; border-radius: 10px; }}
    img {{ max-width: 100%; border-radius: 10px; margin-top: 16px; }}
  </style>
</head>
<body>
  <h1>InsightFlow Dashboard</h1>
  <div class="card">Rows before: {metrics['rows_before']}</div>
  <div class="card">Rows after: {metrics['rows_after']}</div>
  <div class="card">Duplicates removed: {metrics['duplicates_removed']}</div>

  <h2>Insights</h2>
  <ul>{insights_html}</ul>

  <img src="{chart_path}" alt="Distribution chart">
</body>
</html>
"""
    path = Path(output_dir) / "dashboard.html"
    path.write_text(html, encoding="utf-8")
    return str(path)
