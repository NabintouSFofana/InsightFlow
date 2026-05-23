from cleaner import clean_data
from insights import generate_insights
from dashboard_generator import generate_dashboard
from reporter import create_report

df, metrics = clean_data(df)

insights = generate_insights(df)

dashboard = generate_dashboard(
    metrics,
    insights,
    "column_plot.png",
    "output"
)

create_report(
    metrics,
    insights,
    "output/report.pdf"
)

df.to_csv(
    "output/cleaned_data.csv",
    index=False
)