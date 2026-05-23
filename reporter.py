from fpdf import FPDF


def create_report(
        metrics,
        insights,
        output
):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font(
        "Arial",
        size=16
    )

    pdf.cell(
        0,
        10,
        "Data Analyzer Report",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.set_font(
        "Arial",
        size=11
    )

    for k, v in metrics.items():

        pdf.cell(
            0,
            8,
            f"{k}: {v}",
            new_x="LMARGIN",
            new_y="NEXT"
        )

    pdf.ln(10)

    pdf.cell(
        0,
        10,
        "Insights",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    for i in insights:

        pdf.multi_cell(
            0,
            8,
            f"- {i}"
        )

    pdf.output(output)