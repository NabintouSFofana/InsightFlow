"""
InsightFlow — the CLI version.

A small tool that takes a messy CSV and writes a clean PDF report
with stats, a chart, and plain-English observations.

Usage:
    python csv_data_analyzer.py --file data.csv --column SomeColumn
    python csv_data_analyzer.py --file data.csv     # auto-pick first numeric column
    python csv_data_analyzer.py --file data.csv --no-pdf  # skip the PDF
    python csv_data_analyzer.py --file data.csv --no-plot # skip the chart

Outputs (in output/):
    cleaned_data.csv      de-duplicated input
    column_plot.png       histogram or bar chart of the analyzed column
    analysis_report.pdf   one-page summary with stats + plot

Author: Nabintou S. Fofana
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF

# ─── Rich is optional — fall back to plain print if not installed ──────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


# ╔══════════════════════════════════════════════════════════════════╗
# ║  PRETTY PRINTING                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝
def say(message: str, style: str = "") -> None:
    """Print with optional Rich styling. Falls back to plain text."""
    if HAS_RICH:
        console.print(message, style=style)
    else:
        # strip simple [tag]...[/tag] markup if present
        import re
        plain = re.sub(r"\[/?[a-z #]+\]", "", message)
        print(plain)


def header(title: str) -> None:
    if HAS_RICH:
        console.rule(f"[bold #B6411C]{title}")
    else:
        print(f"\n=== {title} ===")


def stats_table(stats: dict) -> None:
    """Render a stats dict as a Rich table, or plain key:value if Rich missing."""
    if not stats:
        say("[dim]No numeric stats — column appears to be non-numeric.[/dim]")
        return

    if HAS_RICH:
        t = Table(show_header=False, show_edge=False, padding=(0, 2))
        t.add_column(style="bold #5C5247", justify="right")
        t.add_column(style="#14110D")
        for k, v in stats.items():
            t.add_row(k.capitalize(), f"{v:,.2f}")
        console.print(t)
    else:
        for k, v in stats.items():
            print(f"  {k.capitalize():<10} {v:,.2f}")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  REPORT TYPE                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝
@dataclass
class AnalysisReport:
    """A small structured summary of what the analyzer found."""
    file_path: str
    column: str
    rows_initial: int
    rows_after_clean: int
    duplicates_removed: int
    missing_values: int
    missing_pct: float
    constant_columns: list = field(default_factory=list)
    quality_score: float = 0.0
    stats: dict = field(default_factory=dict)
    plot_file: Optional[str] = None


# ╔══════════════════════════════════════════════════════════════════╗
# ║  LOAD                                                             ║
# ╚══════════════════════════════════════════════════════════════════╝
def load_csv(file_path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(file_path):
        say(f"[bold red]✗[/bold red] File not found: {file_path}")
        return None
    try:
        df = pd.read_csv(file_path)
        say(f"[bold #2A6F4E]✓[/bold #2A6F4E] Loaded [bold]{len(df):,}[/bold] rows × [bold]{len(df.columns)}[/bold] columns")
        return df
    except pd.errors.EmptyDataError:
        say("[bold red]✗[/bold red] CSV is empty.")
    except pd.errors.ParserError as e:
        say(f"[bold red]✗[/bold red] Couldn't parse CSV: {e}")
    except Exception as e:
        say(f"[bold red]✗[/bold red] Unexpected error: {e}")
    return None


# ╔══════════════════════════════════════════════════════════════════╗
# ║  CLEAN                                                            ║
# ╚══════════════════════════════════════════════════════════════════╝
def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = before - len(df)
    if removed:
        say(f"[bold #2A6F4E]✓[/bold #2A6F4E] Removed [bold]{removed:,}[/bold] duplicate row{'s' if removed != 1 else ''}")
    else:
        say(f"[dim]No duplicates found.[/dim]")
    return df, removed


# ╔══════════════════════════════════════════════════════════════════╗
# ║  QUALITY SCORE                                                    ║
# ╚══════════════════════════════════════════════════════════════════╝
def compute_quality(df: pd.DataFrame) -> tuple[float, dict]:
    """
    A composite 0-100 score derived from:
      - missing-value percentage
      - residual duplicate percentage (should be 0 if clean_data ran)
      - count of single-value (constant) columns × 5 penalty
    """
    total_cells = df.size or 1
    missing = int(df.isnull().sum().sum())
    missing_pct = (missing / total_cells) * 100

    dup = int(df.duplicated().sum())
    dup_pct = (dup / (len(df) or 1)) * 100

    constant_cols = [col for col in df.columns if df[col].nunique(dropna=False) == 1]

    score = 100 - missing_pct - dup_pct - len(constant_cols) * 5
    score = round(max(0.0, min(100.0, score)), 2)

    details = {
        "missing":         missing,
        "missing_pct":     round(missing_pct, 2),
        "duplicates":      dup,
        "constant_cols":   constant_cols,
        "score":           score,
    }
    return score, details


# ╔══════════════════════════════════════════════════════════════════╗
# ║  COLUMN STATS                                                     ║
# ╚══════════════════════════════════════════════════════════════════╝
def analyze_column(
        df,
        column
):

    if column not in df.columns:

        return {}

    series = pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()

    if len(series) == 0:

        return {}

    return {

        "count":
            len(series),

        "mean":
            series.mean(),

        "median":
            series.median(),

        "std":
            series.std(),

        "min":
            series.min(),

        "max":
            series.max(),

    }

def detect_anomalies(
        df,
        column
):

    s = pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()

    if len(s) < 3:

        return []

    q1 = s.quantile(.25)

    q3 = s.quantile(.75)

    iqr = q3 - q1

    low = q1 - 1.5 * iqr

    high = q3 + 1.5 * iqr

    outliers = s[
        (s < low)
        |
        (s > high)
        ]

    return list(
        outliers
    )

def auto_pick_column(df):

    numeric = []

    for col in df.columns:

        converted = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        if converted.notna().sum() >= 3:

            numeric.append(col)

    if numeric:

        return numeric[0]

    if "Department" in df.columns:
        return "Department"

    return df.columns[0]
# ╔══════════════════════════════════════════════════════════════════╗
# ║  PLOT                                                             ║
# ╚══════════════════════════════════════════════════════════════════╝
def plot_column(df: pd.DataFrame, column: str, out_file: str) -> bool:
    """Return True if a plot was actually saved."""
    series = df[column].dropna()
    if series.empty:
        say(f"[yellow]⚠[/yellow]  Column [bold]{column}[/bold] has no data — skipping plot.")
        return False

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5.5))

    accent = "#B6411C"
    edge = "#14110D"

    if pd.api.types.is_numeric_dtype(series) and series.nunique() > 20:
        ax.hist(series, bins=24, color=accent, edgecolor=edge, alpha=0.85, linewidth=0.7)
        ax.set_ylabel("Frequency")
    else:
        counts = series.value_counts().head(20)  # cap to top 20 categories
        ax.bar(counts.index.astype(str), counts.values,
               color=accent, edgecolor=edge, alpha=0.85, linewidth=0.7)
        ax.set_ylabel("Count")
        plt.xticks(rotation=35, ha="right")

    ax.set_title(f"Distribution of {column}", fontsize=14, fontweight="bold", color=edge)
    ax.set_xlabel(column)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_file, dpi=160, facecolor="#FAF6EE")
    plt.close()
    say(f"[bold #2A6F4E]✓[/bold #2A6F4E] Plot saved → [dim]{out_file}[/dim]")
    return True


# ╔══════════════════════════════════════════════════════════════════╗
# ║  PDF                                                              ║
# ╚══════════════════════════════════════════════════════════════════╝
def generate_pdf(report, out_file="analysis_report.pdf"):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_auto_page_break(
        auto=True,
        margin=18
    )

    pdf.set_margins(
        20,
        18,
        20
    )

    pdf.set_font(
        "Helvetica",
        "B",
        22
    )

    pdf.cell(
        0,
        12,
        "InsightFlow Report",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.set_font(
        "Helvetica",
        size=10
    )

    pdf.cell(
        0,
        6,
        f"File: {os.path.basename(report.file_path)} | Column: {report.column}",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.ln(6)

    pdf.set_font(
        "Helvetica",
        "B",
        12
    )

    pdf.cell(
        0,
        8,
        "Data Quality",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.set_font(
        "Helvetica",
        size=11
    )

    rows = [

        (
            "Rows",
            report.rows_after_clean
        ),

        (
            "Duplicates removed",
            report.duplicates_removed
        ),

        (
            "Missing values",
            report.missing_values
        ),

        (
            "Quality score",
            report.quality_score
        ),

    ]

    for label, value in rows:

        pdf.cell(
            60,
            8,
            str(label)
        )

        pdf.cell(
            0,
            8,
            str(value),
            new_x="LMARGIN",
            new_y="NEXT"
        )

    pdf.ln(4)

    pdf.set_font(
        "Helvetica",
        "B",
        12
    )

    pdf.cell(
        0,
        8,
        f"Stats for {report.column}",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.set_font(
        "Helvetica",
        size=11
    )

    if report.stats:

        for k, v in report.stats.items():

            pdf.cell(
                60,
                8,
                str(k)
            )

            pdf.cell(
                0,
                8,
                f"{v:,.2f}",
                new_x="LMARGIN",
                new_y="NEXT"
            )

    else:

        pdf.cell(
            0,
            8,
            "Non-numeric column - see plot for distribution.",
            new_x="LMARGIN",
            new_y="NEXT"
        )

    pdf.ln(6)

    if (
            report.plot_file
            and
            os.path.exists(
                report.plot_file
            )
    ):

        pdf.set_font(
            "Helvetica",
            "B",
            12
        )

        pdf.cell(
            0,
            8,
            "Visualization",
            new_x="LMARGIN",
            new_y="NEXT"
        )

        pdf.image(
            report.plot_file,
            x=20,
            w=170
        )

    pdf.output(
        out_file
    )

    say(
        f"[green]✓ PDF saved → {out_file}[/green]"
    )


# ╔══════════════════════════════════════════════════════════════════╗
# ║  CLI                                                              ║
# ╚══════════════════════════════════════════════════════════════════╝
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a CSV — clean it, score its quality, plot a column, and write a PDF report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python csv_data_analyzer.py --file sales.csv --column revenue
  python csv_data_analyzer.py --file data.csv             # auto-pick column
  python csv_data_analyzer.py --file data.csv --no-pdf    # skip PDF generation
"""
    )
    parser.add_argument("--file",   required=True, help="Path to the input CSV.")
    parser.add_argument("--column", help="Column to analyze. If omitted, the first numeric column is used.")
    parser.add_argument("--out-dir", default=".",  help="Directory for outputs (default: current dir).")
    parser.add_argument("--no-pdf",  action="store_true", help="Skip PDF generation.")
    parser.add_argument("--no-plot", action="store_true", help="Skip plot generation.")
    args = parser.parse_args()

    header("InsightFlow · CLI")
    say(f"[dim]File:[/dim] {args.file}")

    df = load_csv(args.file)
    if df is None:
        return 1

    df, removed = clean_data(df)
    rows_after = len(df)
    score, details = compute_quality(df)

    # Pick column
    column = args.column or auto_pick_column(df)
    if not column:
        say("[bold red]✗[/bold red] No columns to analyze.")
        return 1
    if not args.column:
        say(f"[dim]No --column specified, auto-picked:[/dim] [bold]{column}[/bold]")

    header("Data quality")
    say(f"  Missing values:   [bold]{details['missing']:,}[/bold] ({details['missing_pct']}%)")
    say(f"  Duplicates:       [bold]{details['duplicates']:,}[/bold]")
    say(f"  Constant columns: [bold]{len(details['constant_cols'])}[/bold]")
    say(f"  [bold #B6411C]Quality score:    {details['score']} / 100[/bold #B6411C]")

    stats = analyze_column(df, column)

    header(f"Stats for '{column}'")
    stats_table(stats)

    anomalies = detect_anomalies(
        df,
        column
    )

    if anomalies:

       header(
        "Anomalies"
       )

       for a in anomalies:

        say(
            f"[yellow]⚠ Suspicious value:[/yellow] {a}"
        )

    # Outputs
    os.makedirs(args.out_dir, exist_ok=True)
    output_dir = os.path.join(
        args.out_dir,
        "output"
    )

    os.makedirs(
      output_dir,
    exist_ok=True
    )

    cleaned_path = os.path.join(
       output_dir,
    "cleaned_data.csv"
     )

    plot_path = os.path.join(
      output_dir,
    "column_plot.png"
    )

    pdf_path = os.path.join(
       output_dir,
     "analysis_report.pdf"
    )
    df.to_csv(cleaned_path, index=False)
    say(f"\n[bold #2A6F4E]✓[/bold #2A6F4E] Cleaned CSV saved → [dim]{cleaned_path}[/dim]")

    plot_ok = False
    if not args.no_plot:
        plot_ok = plot_column(df, column, plot_path)

    if not args.no_pdf:
        report = AnalysisReport(
            file_path=args.file,
            column=column,
            rows_initial=rows_after + removed,
            rows_after_clean=rows_after,
            duplicates_removed=removed,
            missing_values=details["missing"],
            missing_pct=details["missing_pct"],
            constant_columns=details["constant_cols"],
            quality_score=details["score"],
            stats=stats,
            plot_file=plot_path if plot_ok else None,
        )
        generate_pdf(report, pdf_path)

    say("\n[bold]Done.[/bold]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
