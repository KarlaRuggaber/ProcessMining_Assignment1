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

    return mo, pd, pm4py


@app.cell(hide_code=True)
def _(pm4py):
    event_log_from_disk =  pm4py.read_xes('Road_Traffic_Fine_Management_Process.xes', variant="rustxes")

    print(len(event_log_from_disk), 'events read.')
    event_log_from_disk
    return (event_log_from_disk,)


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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
def _(df, mo):
    # 2.1.1 granularity of the timestamps
    seconds = sorted(df['time:timestamp'].dt.second.unique())
    minutes = sorted(df['time:timestamp'].dt.minute.unique())
    hours   = sorted(df['time:timestamp'].dt.hour.unique())

    mo.md(f"""
    **Timestamp granularity check:**
    - Distinct second values: `{seconds}`
    - Distinct minute values: `{minutes}`
    - Distinct hour values:   `{hours}`

    Every timestamp has seconds = 0 and minutes = 0, and only two distinct hour
    values occur ({hours}). These correspond to midnight (00:00) in the log's
    original Italian local time (CET/CEST), shifted to UTC depending on
    daylight saving time (00:00 CET -> 23:00 UTC, 00:00 CEST -> 22:00 UTC). So
    the timestamps carry **day-level granularity only**: every event is dated
    to a specific calendar day, with no meaningful hour/minute/second
    information recorded.
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, pd):
    # 2.1.2a activity schemas and their missing values
    _mandatory_cols = {'case:concept:name', 'concept:name', 'time:timestamp'}
    _attribute_cols = [c for c in df.columns if c not in _mandatory_cols]

    _schema_rows = []
    for _activity, _sub in df.groupby('concept:name'):
        _n_events = len(_sub)
        for _attr in _attribute_cols:
            _filled = _sub[_attr].notna().sum()
            if _filled > 0:
                _schema_rows.append({
                    'activity': _activity,
                    'attribute': _attr,
                    'events_of_activity': _n_events,
                    'filled': _filled,
                    'missing': _n_events - _filled,
                })

    _schema_df = pd.DataFrame(_schema_rows).sort_values(['activity', 'attribute']).reset_index(drop=True)
    _incomplete_df = _schema_df[_schema_df['missing'] > 0].reset_index(drop=True)

    mo.vstack([
        mo.md("**Activity schemas** (attributes filled for at least one event of that activity, i.e. local attributes):"),
        mo.ui.table(_schema_df),
        mo.md("**Attributes with missing values, per activity schema:**"),
        mo.ui.table(_incomplete_df),
        mo.md(f"""
    Only one activity schema is incomplete: `Insert Fine Notification`'s
    `lastSent` attribute is missing for {int(_incomplete_df['missing'].iloc[0]) if len(_incomplete_df) else 0}
    out of {int(_incomplete_df['events_of_activity'].iloc[0]) if len(_incomplete_df) else 0}
    events. Every other local attribute of every other activity schema is
    complete (filled for 100% of that activity's events).
    """),
    ])
    return


@app.cell(hide_code=True)
def _(df, mo, pd):
    # 2.1.2b attributes shared across activity schemas, classified as cumulative or incremental
    _mandatory_cols = {'case:concept:name', 'concept:name', 'time:timestamp'}
    _attribute_cols = [c for c in df.columns if c not in _mandatory_cols]

    _activities_per_attr = {
        _attr: sorted(df.loc[df[_attr].notna(), 'concept:name'].unique())
        for _attr in _attribute_cols
    }
    _n_activities = df['concept:name'].nunique()

    _global_attrs    = [a for a, acts in _activities_per_attr.items() if len(acts) == _n_activities]
    _shared_attrs    = {a: acts for a, acts in _activities_per_attr.items() if 1 < len(acts) < _n_activities}
    _exclusive_attrs = [a for a, acts in _activities_per_attr.items() if len(acts) == 1]

    _shared_df = pd.DataFrame([
        {
            'attribute': a,
            'numerical': pd.api.types.is_numeric_dtype(df[a]),
            'shared_by_activities': ', '.join(acts),
        }
        for a, acts in _shared_attrs.items()
    ])

    # verify the "amount" attribute: does it grow monotonically per case
    # between Create Fine and Add penalty, and by roughly what factor?
    _cf = df.loc[df['concept:name'] == 'Create Fine', ['case:concept:name', 'amount']].rename(columns={'amount': 'amount_create'})
    _ap = df.loc[df['concept:name'] == 'Add penalty', ['case:concept:name', 'amount']].rename(columns={'amount': 'amount_penalty'})
    _amount_check = _cf.merge(_ap, on='case:concept:name')
    _amount_ratio = (_amount_check['amount_penalty'] / _amount_check['amount_create']).replace([float('inf')], pd.NA).dropna()

    # verify the "totalPaymentAmount" attribute: is it the running sum of
    # paymentAmount across the Payment events of the same case?
    _pay = df.loc[df['concept:name'] == 'Payment', ['case:concept:name', 'time:timestamp', 'paymentAmount', 'totalPaymentAmount']] \
             .sort_values(['case:concept:name', 'time:timestamp']).copy()
    _pay['cumsum_check'] = _pay.groupby('case:concept:name')['paymentAmount'].cumsum()
    _pay_match_rate = (( _pay['cumsum_check'] - _pay['totalPaymentAmount']).abs() < 0.01).mean()

    mo.vstack([
        mo.md(f"""
    Of the {len(_attribute_cols)} non-mandatory attributes:
    - **Global** (filled for all {_n_activities} activities, so not local): `{_global_attrs}`.
    - **Shared** (local to more than one, but not all, activities): {len(_shared_attrs)} attributes.
    - **Exclusive** (local to exactly one activity): {len(_exclusive_attrs)} attributes.
    """),
        mo.ui.table(_shared_df),
        mo.md(f"""
    **Classifying the numerical shared attributes as cumulative or incremental:**

    - `amount` (`Create Fine`, `Add penalty`) is **case-cumulative**. Checked
      across all {len(_amount_check):,} cases that have both events: `amount`
      always increases from `Create Fine` to `Add penalty`, by a ratio of
      {_amount_ratio.mean():.2f} on average (median {_amount_ratio.median():.2f}),
      consistent with the statutory late-payment penalty roughly doubling the
      fine. So it is not a running *sum* of increments, but a recalculated
      running total that only grows within a case — i.e. an aggregated,
      case-cumulative number rather than a standalone one.
    - `totalPaymentAmount` (`Create Fine`, `Payment`) is **case-cumulative**.
      Checked across all {len(_pay):,} `Payment` events: `totalPaymentAmount`
      equals `cumsum(paymentAmount)` within the same case in
      {_pay_match_rate:.1%} of events (small deviations likely stem from
      payments made before the log's observation window). It is a genuine
      running sum of payments made so far for that case.
    - `org:resource` and `dismissal` are shared but not numerical (they are
      categorical/textual), so no cumulative/incremental classification
      applies to them.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(df, mo):
    # 2.1.3 case inspection: select a case with more than three events
    selected_case_id = 'A10000'
    case_events = df[df['case:concept:name'] == selected_case_id].sort_values('time:timestamp')

    display_cols = [
        'time:timestamp', 'concept:name', 'amount', 'totalPaymentAmount',
        'paymentAmount', 'expense', 'notificationType', 'dismissal', 'org:resource',
    ]

    mo.vstack([
        mo.md(f"**Case `{selected_case_id}`** ({len(case_events)} events):"),
        mo.ui.table(case_events[display_cols].reset_index(drop=True)),
        mo.md("""
    **Event-by-event summary:**

    - **2007-03-08 — `Create Fine`**: the fine is created with a base `amount`
      of 36 and `totalPaymentAmount` initialized to 0. No penalty points are
      recorded for this violation.
    - **2007-07-16 — `Send Fine`** (~4 months later): the fine notice is sent
      to the offender; an `expense` of 13 is recorded for the sending cost.
    - **2007-08-01 — `Insert Fine Notification`** (~2 weeks after sending): the
      notification is formally registered, with `notificationType` "P" and
      `lastSent` set to "P" as well.
    - **2007-09-30 — `Add penalty`** (~2 months after notification, i.e. past
      the payment deadline): a penalty is applied, and `amount` increases from
      36 to 74, reflecting the case-cumulative total now owed.
    - **2008-09-08 — `Payment`** (~11 months later): a payment of
      `paymentAmount` 87 is made, and `totalPaymentAmount` is updated to 87 —
      matching the full penalized amount of 74 plus additional accrued costs,
      effectively settling the case.

    Overall the case spans about 1.5 years from fine creation to payment, with
    long gaps between events (payment only happens well after the penalty was
    added), illustrating the typical slow-moving, escalating nature of an
    unpaid traffic fine that is eventually settled after a penalty increase.
    """),
    ])
    return


if __name__ == "__main__":
    app.run()
