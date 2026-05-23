def clean_data(df):

    before = len(df)

    duplicates = df.duplicated().sum()

    df = df.drop_duplicates()

    missing = df.isna().sum().sum()

    df = df.fillna("Unknown")

    metrics = {

        "rows_before": before,

        "rows_after": len(df),

        "duplicates_removed": int(
            duplicates
        ),

        "missing_fixed": int(
            missing
        )

    }

    return df, metrics