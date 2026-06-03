"""Writes a one-page PDF summary of the analysis."""

from fpdf import FPDF


def create_report(metrics, insights, output_path):
    """Build a small PDF that lists the metrics and the insights."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=16)
    pdf.cell(0, 10, "InsightFlow Report", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Arial", size=11)
    for key, value in metrics.items():
        pdf.cell(0, 8, f"{key}: {value}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.cell(0, 10, "Insights", new_x="LMARGIN", new_y="NEXT")
    for line in insights:
        pdf.multi_cell(0, 8, f"- {line}")

    pdf.output(output_path)
