from pathlib import Path


def generate_dashboard(
        metrics,
        insights,
        chart_path,
        output_dir
):

    html = f"""
<html>

<head>

<title>Data Analyzer Dashboard</title>

<style>

body {{
font-family:Arial;
padding:40px;
}}

.card {{
padding:20px;
margin:10px;
background:#f4f4f4;
border-radius:10px;
}}

</style>

</head>

<body>

<h1>Smart CSV Analyzer</h1>

<div class='card'>
Rows Before:
{metrics['rows_before']}
</div>

<div class='card'>
Rows After:
{metrics['rows_after']}
</div>

<div class='card'>
Duplicates Removed:
{metrics['duplicates_removed']}
</div>

<h2>Insights</h2>

<ul>

{''.join(f'<li>{i}</li>' for i in insights)}

</ul>

<img width=800 src="{chart_path}">

</body>

</html>
"""

    p = Path(output_dir) / "dashboard.html"

    p.write_text(
        html,
        encoding="utf-8"
    )

    return str(p)