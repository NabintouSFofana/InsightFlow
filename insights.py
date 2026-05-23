import pandas as pd


def generate_insights(df):

    insights = []

    rows = len(df)

    insights.append(
        f"Analyzed {rows} rows"
    )

    missing = (
        df.isna()
        .sum()
        .sum()
    )

    if missing:

        insights.append(
            f"⚠ {missing} missing values detected"
        )

    duplicates = (
        df.duplicated()
        .sum()
    )

    if duplicates:

        insights.append(
            f"⚠ {duplicates} duplicates detected"
        )

    numeric = df.select_dtypes(
        include="number"
    )

    for col in numeric.columns:

        s = numeric[col]

        if len(s):

            if (
                    s.min()
                    < 0
            ):

                insights.append(
                    f"⚠ {col} contains negative values"
                )

            q1 = s.quantile(.25)

            q3 = s.quantile(.75)

            iqr = q3 - q1

            high = q3 + 1.5 * iqr

            low = q1 - 1.5 * iqr

            count = (
                    (
                            s < low
                    )
                    |
                    (
                            s > high
                    )
            ).sum()

            if count:

                insights.append(
                    f"⚠ {count} outliers detected in {col}"
                )

            insights.append(
                f"✓ Average {col}: {round(s.mean(),1)}"
            )

    if "Department" in df.columns:

        top = (
            df["Department"]
            .value_counts()
            .idxmax()
        )

        insights.append(
            f"🏆 Largest group: {top}"
        )

    insights.append(
        "✓ Data quality analysis completed"
    )

    return insights