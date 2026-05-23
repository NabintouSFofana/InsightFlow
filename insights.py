import pandas as pd


def generate_insights(df):

    insights = []

    insights.append(f"Rows: {len(df)}")

    if "Salary" in df.columns:
        salary = pd.to_numeric(
            df["Salary"],
            errors="coerce"
        )

        insights.append(
            f"Average salary: ${salary.mean():,.0f}"
        )

        insights.append(
            f"Highest salary: ${salary.max():,.0f}"
        )

    if "Department" in df.columns:

        dep = df["Department"].mode()

        if not dep.empty:
            insights.append(
                f"Top department: {dep.iloc[0]}"
            )

    return insights