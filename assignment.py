import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Assigment 1 Template
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd 
    import pm4py

    return mo, pm4py


@app.cell
def _(pm4py):
    event_log_from_disk =  pm4py.read_xes('Road_Traffic_Fine_Management_Process.xes', variant="rustxes")

    print(len(event_log_from_disk), 'events read.')
    event_log_from_disk
    return (event_log_from_disk,)


@app.cell
def _(event_log_from_disk, mo, pm4py):
    # 1.1a time interval the log covers
    df = pm4py.convert_to_dataframe(event_log_from_disk)

    start = df['time:timestamp'].min()
    end   = df['time:timestamp'].max()

    mo.md(f"""
    **Time interval:**
    - Start: `{start}`
    - End:   `{end}`
    - Duration: `{end - start}`
    """)
    return (df,)


@app.cell
def _(df, mo):
    # 1.1b distinct values for vehicleClass
    distinct_vehicle_classes = df['vehicleClass'].dropna().unique()
    null_count = df['vehicleClass'].isna().sum()

    mo.md(f"""
    **Distinct vehicleClass values:** {df['vehicleClass'].nunique()}

    {', '.join(str(v) for v in sorted(distinct_vehicle_classes))}

    *(+ {null_count:,} events with no vehicleClass recorded)*
    """)
    return


@app.cell
def _(df, mo):
    # 1.1c min, median, max of amount
    create_fine_df = df[df['concept:name'] == 'Create Fine']

    # Keep only the first occurrence per case (initial value)
    initial_amounts = create_fine_df.sort_values('time:timestamp') \
                                    .groupby('case:concept:name')['amount'] \
                                    .first()

    stats = initial_amounts.describe()

    mo.md(f"""
    **Amount stats for initial 'Create Fine' event per case:**
    - Min:    `{initial_amounts.min()}`
    - Median: `{initial_amounts.median()}`
    - Max:    `{initial_amounts.max()}`
    """)
    return


@app.cell
def _(df, mo):
    # 1.1d events with points > 0
    points_df = df[df['points'] > 0]

    activities = points_df['concept:name'].value_counts()
    n_cases    = points_df['case:concept:name'].nunique()

    mo.vstack([
        mo.md(f"""
    **Events with points > 0:** {len(points_df):,}  
    **Cases affected:** {n_cases:,}
    """),
        mo.md("**Activities associated with points > 0:**"),
        mo.ui.table(activities.reset_index().rename(columns={'concept:name': 'activity', 'count': 'event_count'}))
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 1

    ## Task 1.1

    a) The log covers the time interval from 1999-12-31 23:00:00 UTC to 2013-06-17 22:00:00 UTC.

    b) The attribute vehicleClass has 4 distinct values: A, C, M, and R. Note that some
       events have no value recorded for this attribute.

    c) For Create Fine events, the amount attribute has the following statistics:
      - Min: 0.0
      - Median: 35.0
      - Max: 4351.0

      The distribution is heavily right-skewed, with the maximum value (4351) being more
      than 100 times the median (35). This suggests the presence of extreme outliers. It
      would be worth investigating which cases incur unusually high fines — for example,
      whether specific vehicle classes, violation types, or time periods are associated
      with these high amounts, and whether the zero-amount fines are data quality issues
      or represent a specific case type.

    d) There are 3,548 events with a points value greater than 0. All of them are
      associated with the activity "Create Fine". The number of affected cases is 3,548,
      meaning each affected case has exactly one such event — every case with points > 0
      received them at the moment the fine was created.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 2

    ## Task 2.1
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.2
    """)
    return


if __name__ == "__main__":
    app.run()
