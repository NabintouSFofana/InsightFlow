from flask import Flask
from flask import render_template
from flask import request

import pandas as pd

from cleaner import clean_data
from insights import generate_insights

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():

    result = None

    if request.method == "POST":

        file = request.files["csv"]

        df = pd.read_csv(file)

        clean_df, metrics = clean_data(df)

        insights = generate_insights(
            clean_df
        )

        table = clean_df.head(
            10
        ).to_html(
            classes="table"
        )

        result = {

            "metrics": metrics,

            "insights": insights,

            "table": table

        }

    return render_template(
        "index.html",
        result=result
    )


if __name__ == "__main__":

    app.run(
        debug=True
    )