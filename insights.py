"""Generates plain-English insights from a cleaned DataFrame."""


def generate_insights(df):
    """Return a list of short human-readable observations about df."""
    insights = [f"Analyzed {len(df)} rows"]

    missing = int(df.isna().sum().sum())
    if missing:
        insights.append(f"⚠ {missing} missing values detected")

    duplicates = int(df.duplicated().sum())
    if duplicates:
        insights.append(f"⚠ {duplicates} duplicates detected")

    # Numeric columns: check for negatives and outliers (Tukey's IQR rule)
    numeric = df.select_dtypes(include="number")
    for col in numeric.columns:
        series = numeric[col]
        if series.empty:
            continue

        if series.min() < 0:
            insights.append(f"⚠ {col} contains negative values")

        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = int(((series < low) | (series > high)).sum())
        if outliers:
            insights.append(f"⚠ {outliers} outliers detected in {col}")

        insights.append(f"✓ Average {col}: {round(series.mean(), 1)}")

    # If the data has a Department column, name the biggest group
    if "Department" in df.columns:
        top = df["Department"].value_counts().idxmax()
        insights.append(f"🏆 Largest group: {top}")

    insights.append("✓ Data quality analysis completed")
    return insights
