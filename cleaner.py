"""Cleans incoming CSV data: drops duplicates, fills missing values."""


def clean_data(df):
    """Remove duplicates and fill missing values.

    Returns the cleaned DataFrame and a small metrics dict
    describing what changed.
    """
    rows_before = len(df)
    duplicates = int(df.duplicated().sum())
    df = df.drop_duplicates()

    missing = int(df.isna().sum().sum())
    df = df.fillna("Unknown")

    metrics = {
        "rows_before": rows_before,
        "rows_after": len(df),
        "duplicates_removed": duplicates,
        "missing_fixed": missing,
    }
    return df, metrics
