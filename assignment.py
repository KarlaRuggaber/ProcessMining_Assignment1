import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Assignment 1: Road Traffic Fine Management Process
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import pm4py
    import plotly.express as px

    return mo, pd, pm4py, px


@app.cell(hide_code=True)
def _(pm4py):
    event_log_from_disk =  pm4py.read_xes('data/Road_Traffic_Fine_Management_Process.xes', variant="rustxes")
    # the log is stored in UTC, but the events happened at midnight Italian time
    # (see Task 2.1.1), so we convert to local time to get the right dates
    event_log_from_disk['time:timestamp'] = event_log_from_disk['time:timestamp'].dt.tz_convert('Europe/Rome')

    print(len(event_log_from_disk), 'events read.')
    event_log_from_disk
    return (event_log_from_disk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 1

    ## Task 1.1

    **Our hypotheses before running the code:**

    a) We think the log covers a few years, maybe 3 to 5, since it comes
       from one local police department.

    b) We expect only a few vehicle classes (e.g. car, motorbike, truck),
       so around 3 to 6 different values.

    c) We guess that most fines are for small offences and cost a few
       tens of euros, so we expect the median to be around 40. For the
       minimum we guess something between 20 and 40, and for the maximum
       a few hundred euros for more serious offences.

    d) Points are only taken away for more serious offences, so we think
       only a small part of the cases has points. Since the points depend
       on the offence, they should be recorded once at `Create Fine`.
    """)
    return


@app.cell(hide_code=True)
def _(event_log_from_disk, mo, pm4py):
    # 1.1a time interval the log covers
    df = pm4py.convert_to_dataframe(event_log_from_disk)

    start = df['time:timestamp'].min()
    end   = df['time:timestamp'].max()
    # count calendar days, otherwise daylight saving time gives "... days 23:00:00"
    _duration_days = (end.tz_localize(None) - start.tz_localize(None)).days

    mo.md(f"""
    **Time interval:**
    - Start: `{start:%Y-%m-%d}`
    - End:   `{end:%Y-%m-%d}`
    - Duration: `{_duration_days:,} days`
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
def _(df, mo):
    # Task 1.1 answers: every number below is computed here from the event log
    _ts = df['time:timestamp']
    _years = (_ts.max() - _ts.min()).days / 365.25

    _vc_values = sorted(df['vehicleClass'].dropna().unique())
    _vc_missing = int(df['vehicleClass'].isna().sum())
    _vc_activities = sorted(df.loc[df['vehicleClass'].notna(), 'concept:name'].unique())

    _initial = df[df['concept:name'] == 'Create Fine'].groupby('case:concept:name')['amount'].first()
    _n_zero_fines = int((_initial == 0).sum())

    _points = df[df['points'] > 0]
    _points_activities = sorted(_points['concept:name'].unique())
    _n_points_cases = _points['case:concept:name'].nunique()
    _n_cases = df['case:concept:name'].nunique()

    mo.md(f"""
    **Task 1.1, answers:**

    a) The log goes from {_ts.min():%Y-%m-%d} to {_ts.max():%Y-%m-%d}
    (Italian local time, see Task 2.1.1), so about {_years:.1f} years. This is a lot longer
    than the 3 to 5 years we expected. Over such a long time the process
    and the tariffs could have changed, which we should keep in mind.

    b) vehicleClass has {len(_vc_values)} different values
    ({', '.join(_vc_values)}), which is in the range we expected.
    {_vc_missing:,} events have no value, because the attribute is only
    recorded at {', '.join(f'`{a}`' for a in _vc_activities)}. The codes are
    not documented, so we don't know which letter stands for which type of
    vehicle.

    c) For the initial `amount` of each case (at Create Fine) we get
    min {_initial.min():g}, median {_initial.median():g} and max {_initial.max():g}.
    The median is about what we expected, but the minimum and the maximum
    surprised us.

    The distribution is very right-skewed, the max is
    {_initial.max() / _initial.median():.0f} times the median. We would
    investigate further which cases have such high fines (maybe certain
    vehicle classes, violation types or time periods) and whether the
    {_n_zero_fines} fines with amount 0 are a data quality problem or a
    special type of case.

    d) {len(_points):,} events have a points value greater than 0, and all
    of them belong to {', '.join(f'`{a}`' for a in _points_activities)}.
    The number of affected cases is also {_n_points_cases:,}, so every case
    with points gets them exactly once, when the fine is created. This is
    only {_n_points_cases / _n_cases:.1%} of the {_n_cases:,} cases, so our
    hypothesis that points are rare was correct.
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
    ### Task 2.1.1: Timestamp granularity
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, pd):
    # 2.1.1 granularity of the timestamps
    # df is already in Italian local time (first cell), so convert back to
    # UTC to see the timestamps as they are stored in the XES file
    _utc = df['time:timestamp'].dt.tz_convert('UTC')
    _local = df['time:timestamp']
    seconds = sorted(int(v) for v in _utc.dt.second.unique())
    minutes = sorted(int(v) for v in _utc.dt.minute.unique())
    hours   = sorted(int(v) for v in _utc.dt.hour.unique())
    _local_hours = sorted(int(v) for v in _local.dt.hour.unique())
    _example_utc = _utc.iloc[0]

    def calendar_days(start, end):
        # days between two dates, counted on the calendar. We remove the
        # timezone first, otherwise a daylight saving change in between
        # gives e.g. 59 days 23 hours instead of 60 days
        if isinstance(start, pd.Series):
            return (end.dt.tz_localize(None) - start.dt.tz_localize(None)).dt.days
        return (end.tz_localize(None) - start.tz_localize(None)).days

    # how often does the plain difference give a different number of days?
    _sorted = df.sort_values(['case:concept:name', 'time:timestamp'], kind='stable')
    _prev = _sorted.groupby('case:concept:name')['time:timestamp'].shift(1)
    _plain_days = (_sorted['time:timestamp'] - _prev).dt.days
    _calendar = calendar_days(_prev, _sorted['time:timestamp'])
    _n_gaps = int(_prev.notna().sum())
    _n_off = int(((_plain_days != _calendar) & _prev.notna()).sum())

    mo.md(f"""
    **Checking the timestamp granularity:**
    - Distinct second values (UTC, as stored in the log): `{seconds}`
    - Distinct minute values (UTC): `{minutes}`
    - Distinct hour values (UTC):   `{hours}`
    - Distinct hour values in Italian local time: `{_local_hours}`

    Seconds and minutes are always 0 and there are only two different
    hours ({hours}). When we convert the timestamps to Italian local time,
    all of them are at hour {', '.join(str(h) for h in _local_hours)}, so
    at midnight. This means the log was recorded in local time and then
    converted to UTC, and the hour depends on daylight saving time
    (00:00 CET = 23:00 UTC, 00:00 CEST = 22:00 UTC). So the timestamps
    only have **day-level granularity**, we only know the day of an event.

    In UTC, all dates would be one day *earlier* than the real Italian
    date. For example, the first row of the log is stored as
    `{_example_utc}`, but the event actually happened on
    {_local.iloc[0]:%Y-%m-%d}. That's why we convert all timestamps to
    Italian local time right after loading the log (first cell), so the
    dates in this notebook are the real ones.

    When we count the days between two events, we use calendar days
    (`calendar_days()` above). We noticed that if there is a daylight
    saving change in between, the difference of the two timestamps is one
    hour short (e.g. 59 days and 23 hours instead of 60 days), and
    `.dt.days` then gives one day too few. Without our function this
    would happen for {_n_off:,} of the {_n_gaps:,} gaps between two
    events of the same case.

    Also, events of the same case on the same day can't be ordered
    reliably, which causes problems later (see Task 2.2.4b). For the data
    collection, we would suggest recording full timestamps in local time.
    """)
    return (calendar_days,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.1.2: Activity schemas

    #### Task 2.1.2a: Attributes with missing values
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
        mo.md("**Activity schemas** (attributes that are filled for at least one event of that activity, i.e. local attributes):"),
        mo.ui.table(_schema_df),
        mo.md("**Attributes with missing values, per activity schema:**"),
        mo.ui.table(_incomplete_df),
        mo.md(f"""
    Only {len(_incomplete_df)} activity schema has missing values:
    {', '.join(f"for `{r.activity}`, the attribute `{r.attribute}` is missing in {r.missing:,} of {r.events_of_activity:,} events" for r in _incomplete_df.itertuples())}.
    All other local attributes are filled for 100% of the events of their
    activity (see the full schema table above). In addition, `lastSent`
    is not documented at all (the description only says "N/A"), so it
    should either be documented or removed from the log.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 2.1.2b: Shared attributes, cumulative or incremental
    """)
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
    _n_up = int((_amount_check['amount_penalty'] > _amount_check['amount_create']).sum())
    _n_same = int((_amount_check['amount_penalty'] == _amount_check['amount_create']).sum())
    _n_down = int((_amount_check['amount_penalty'] < _amount_check['amount_create']).sum())

    # verify the "totalPaymentAmount" attribute: is it the running sum of
    # paymentAmount across the Payment events of the same case?
    _pay = df.loc[df['concept:name'] == 'Payment', ['case:concept:name', 'time:timestamp', 'paymentAmount', 'totalPaymentAmount']] \
             .sort_values(['case:concept:name', 'time:timestamp'], kind='stable').copy()
    _pay['cumsum_check'] = _pay.groupby('case:concept:name')['paymentAmount'].cumsum()
    _pay_match_rate = (( _pay['cumsum_check'] - _pay['totalPaymentAmount']).abs() < 0.01).mean()

    mo.vstack([
        mo.md(f"""
    Of the {len(_attribute_cols)} non-mandatory attributes:
    - **Global** (filled for all {_n_activities} activities, so not really local): `{_global_attrs}`
    - **Shared** (local to more than one activity, but not to all): {len(_shared_attrs)} attributes
    - **Exclusive** (local to exactly one activity): {len(_exclusive_attrs)} attributes
    """),
        mo.ui.table(_shared_df),
        mo.md(f"""
    **Cumulative or incremental?**

    - `amount` (at `Create Fine` and `Add penalty`) is **case-cumulative**.
      We checked all {len(_amount_check):,} cases that have both events.
      From `Create Fine` to `Add penalty`, `amount` goes up in {_n_up:,}
      cases, stays the same in {_n_same} and goes down in {_n_down}. On
      average it grows by a factor of {_amount_ratio.mean():.2f} (median
      {_amount_ratio.median():.2f}), which fits the late-payment penalty
      that roughly doubles the fine. So `amount` is not a sum of
      increments, but the new total amount, which never goes down within a
      case. That is why we classify it as case-cumulative.
    - `totalPaymentAmount` (at `Create Fine` and `Payment`) is also
      **case-cumulative**. We compared it with `cumsum(paymentAmount)`
      per case: for {_pay_match_rate:.1%} of the {len(_pay):,} `Payment`
      events the two values are the same. The few differences come from
      payments on the same day and from cases where `totalPaymentAmount`
      is higher than the logged payments (see Task 2.2.4b). Apart from that, it is the running
      sum of all payments so far.
    - `org:resource` and `dismissal` are also shared, but they are
      categorical and not numerical, so the question doesn't apply to them.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.1.3: Case inspection
    """)
    return


@app.cell(hide_code=True)
def _(calendar_days, df, mo):
    # 2.1.3 case inspection: select a case with more than three events
    selected_case_id = 'A10000'
    case_events = df[df['case:concept:name'] == selected_case_id].sort_values('time:timestamp').copy()
    case_events['days_since_previous_event'] = calendar_days(case_events['time:timestamp'].shift(1), case_events['time:timestamp'])

    display_cols = [
        'time:timestamp', 'days_since_previous_event', 'concept:name', 'amount', 'totalPaymentAmount',
        'paymentAmount', 'expense', 'article', 'vehicleClass', 'points',
        'notificationType', 'lastSent', 'dismissal', 'org:resource', 'matricola', 'lifecycle:transition',
    ]
    _matricola_activities = sorted(df.loc[df['matricola'].notna(), 'concept:name'].unique())
    _lifecycle_values = sorted(case_events['lifecycle:transition'].dropna().unique())

    _gap = dict(zip(case_events['concept:name'], case_events['days_since_previous_event']))
    _date = dict(zip(case_events['concept:name'], case_events['time:timestamp'].dt.strftime('%Y-%m-%d')))
    _total_days = calendar_days(case_events['time:timestamp'].min(), case_events['time:timestamp'].max())

    mo.vstack([
        mo.md(f"**Case `{selected_case_id}`** ({len(case_events)} events):"),
        mo.ui.table(case_events[display_cols].reset_index(drop=True)),
        mo.md(f"""
    **Summary of each event** (dates in Italian local time, see Task
    2.1.1; the values are from the table above):

    - **{_date['Create Fine']}, `Create Fine`**: The fine is created with an `amount`
      of 36 and `totalPaymentAmount` is 0. The violated `article` is 157,
      the `vehicleClass` is A and there are 0 `points`, so we think it is
      a minor offence. The fine was created by employee
      561 (`org:resource`), and `dismissal` is "NIL", so the fine is not
      dismissed.
    - **{_date['Send Fine']}, `Send Fine`** ({_gap['Send Fine']:.0f} days later): The
      fine is sent to the offender, with an `expense` of 13 for sending it.
    - **{_date['Insert Fine Notification']}, `Insert Fine Notification`** ({_gap['Insert Fine Notification']:.0f}
      days later): The offender receives the notification.
      `notificationType` is "P", so the fine refers to the car owner.
      `lastSent` is also "P", but we don't know what it means because it
      isn't documented.
    - **{_date['Add penalty']}, `Add penalty`** ({_gap['Add penalty']:.0f} days after the
      notification): A penalty is added and `amount` goes up from 36 to
      74. This is the new total amount of the fine. In Task 3.1c we found
      that the penalty always comes exactly 60 days after the
      notification, so this seems to be the payment deadline.
    - **{_date['Payment']}, `Payment`** ({_gap['Payment']:.0f} days later): The
      offender pays 87, and `totalPaymentAmount` is also 87. This is
      exactly the penalized amount plus the expense (74 + 13), so the fine
      is fully paid.

    In this case only `Create Fine` has a resource, for the other events we
    don't know which employee handled them. `matricola` is empty for all
    events of this case, because in the whole log it is only filled at
    {', '.join(f'`{a}`' for a in _matricola_activities)}, and
    `lifecycle:transition` is always "{', '.join(_lifecycle_values)}", so it
    doesn't tell us anything here.

    In total the case takes {_total_days} days from the creation to the
    payment, and there are long gaps between the events. The offender
    only pays long after the penalty was added.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.2
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.2.4: Cumulative sum of payment amounts
    """)
    return


@app.cell(hide_code=True)
def _(df, mo):
    # Task 2.2.4: event enrichment: cumulative sum of payment amounts per case
    # stable sort, so events on the same day (day-level timestamps, Task 2.1.1)
    # keep the order they have in the log
    df_task4 = df.sort_values(['case:concept:name', 'time:timestamp'], kind='stable').copy()

    # both cumsum() and ffill() need their own groupby, otherwise ffill() would
    # copy the payment total of one case into the next case
    df_task4['payment_cumsum'] = df_task4.groupby('case:concept:name')['paymentAmount'].cumsum()
    df_task4['payment_cumsum'] = df_task4.groupby('case:concept:name')['payment_cumsum'].ffill()
    df_task4['payment_cumsum'] = df_task4['payment_cumsum'].fillna(0)

    mo.md("""
    **Enrichment `payment_cumsum`:** For every event, this is the sum of
    `paymentAmount` of all events of the case up to (and including) this
    event. `cumsum()` calculates the running total at each `Payment` event,
    `ffill()` copies it to the following events that are not payments, and
    `fillna(0)` sets it to 0 for the events before the first payment. This
    is the `col::sum` sequential aggregation from the lecture.
    """)
    return (df_task4,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 2.2.4a: Checking the enrichment on one case
    """)
    return


@app.cell(hide_code=True)
def _(df_task4, mo):
    # Task 2.2.4a: verify the enrichment on a selected case (two payments)
    _case_id = 'A10009'
    _cols = ['time:timestamp', 'concept:name', 'paymentAmount', 'payment_cumsum', 'totalPaymentAmount']
    _case_events = df_task4.loc[df_task4['case:concept:name'] == _case_id, _cols].reset_index(drop=True)
    _payments = _case_events.loc[_case_events['concept:name'] == 'Payment', 'paymentAmount'].tolist()

    mo.vstack([
        mo.md(f"**Case `{_case_id}`**, checking `payment_cumsum`:"),
        mo.ui.table(_case_events),
        mo.md(f"""
    This case has two `Payment` events ({_payments[0]:.0f} and {_payments[1]:.0f}).
    Before the first payment `payment_cumsum` is 0, after the first payment
    it is {_payments[0]:.0f} and after the second one it is {sum(_payments):.0f}.
    At every event where `totalPaymentAmount` has a value, the two are the
    same, so the enrichment is computed correctly.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 2.2.4b: Comparison with `totalPaymentAmount`
    """)
    return


@app.cell(hide_code=True)
def _(df_task4, mo):
    # Task 2.2.4b: compare payment_cumsum against the pre-existing totalPaymentAmount
    _comparable = df_task4[df_task4['totalPaymentAmount'].notna()].copy()
    _comparable['deviation'] = _comparable['payment_cumsum'] - _comparable['totalPaymentAmount']
    _mismatch = _comparable[_comparable['deviation'].abs() > 0.01]

    # split the deviating cases: those with two Payment events on the same day vs. the rest
    _payments = df_task4[df_task4['concept:name'] == 'Payment']
    _payments_per_day = _payments.groupby(['case:concept:name', 'time:timestamp']).size()
    _same_day_cases = set(_payments_per_day[_payments_per_day > 1].index.get_level_values(0))
    _dev_cases = list(_mismatch['case:concept:name'].unique())
    _same_day_dev = [c for c in _dev_cases if c in _same_day_cases]
    _other_dev = [c for c in _dev_cases if c not in _same_day_cases]

    _all_at_payment = bool((_mismatch['concept:name'] == 'Payment').all())
    _all_smaller = bool((_mismatch['deviation'] < 0).all())

    _dev_cols = ['time:timestamp', 'concept:name', 'amount', 'expense', 'paymentAmount', 'payment_cumsum', 'totalPaymentAmount']
    _ex_same_day = df_task4.loc[df_task4['case:concept:name'] == _same_day_dev[0], _dev_cols].reset_index(drop=True)
    _ex_other = df_task4.loc[df_task4['case:concept:name'] == _other_dev[0], _dev_cols].reset_index(drop=True)
    # total owed in the example case: last (penalized) amount plus all expenses
    _ex_owed = _ex_other['amount'].dropna().iloc[-1] + _ex_other['expense'].sum()

    # for the second group: is the surplus in totalPaymentAmount exactly one of
    # the payments that IS logged in the same case (i.e. a payment counted twice)?
    def _surplus_is_logged_payment(case_id):
        _first_dev = _mismatch[_mismatch['case:concept:name'] == case_id].iloc[0]
        _surplus = _first_dev['totalPaymentAmount'] - _first_dev['payment_cumsum']
        _case_payments = _payments.loc[_payments['case:concept:name'] == case_id, 'paymentAmount']
        return bool(((_case_payments - _surplus).abs() < 0.01).any())

    _n_double_counted = sum(_surplus_is_logged_payment(c) for c in _other_dev)
    _ex_first_payment = _ex_other.loc[_ex_other['concept:name'] == 'Payment'].iloc[0]

    # is the deviation still there at the last Payment event of the case?
    _last_payment_dev = _comparable[_comparable['concept:name'] == 'Payment'].groupby('case:concept:name')['deviation'].last()
    _n_same_day_resolved = int((_last_payment_dev[_same_day_dev].abs() <= 0.01).sum())

    # second group: which of the two totals actually settles the fine?
    # owed = last (penalized) amount + all expenses of the case
    _g2 = df_task4[df_task4['case:concept:name'].isin(_other_dev)].groupby('case:concept:name')
    _owed = _g2['amount'].apply(lambda s: s.dropna().iloc[-1]) + _g2['expense'].sum()
    _logged_total = _g2['paymentAmount'].sum()
    _reported_total = _g2['totalPaymentAmount'].last()
    _n_logged_settles = int(((_logged_total - _owed).abs() < 0.01).sum())
    _n_reported_settles = int(((_reported_total - _owed).abs() < 0.01).sum())
    _n_reported_too_low = int((_reported_total < _owed - 0.01).sum())

    mo.vstack([
        mo.md(f"""
    We compared `payment_cumsum` with `totalPaymentAmount` for the
    {len(_comparable):,} events where `totalPaymentAmount` has a value
    (`Create Fine` and `Payment`). The two are the same for
    {(1 - len(_mismatch) / len(_comparable)):.3%} of these events, so
    there are {len(_mismatch)} events with a deviation
    ({len(_mismatch) / len(_comparable):.3%}). {'All' if _all_at_payment else 'Not all'}
    of them are `Payment` events, and {'in all of them' if _all_smaller else 'not in all of them'}
    `payment_cumsum` is *smaller* than `totalPaymentAmount`, on average by
    {_mismatch['deviation'].abs().mean():.1f} and at most by
    {_mismatch['deviation'].abs().max():.1f}.

    These events belong to {len(_dev_cases)} cases, which we split into two
    groups.
    """),
        mo.md(f"""
    **1. Two payments on the same day ({len(_same_day_dev)} cases),** for example
    case `{_same_day_dev[0]}`:
    """),
        mo.ui.table(_ex_same_day),
        mo.md(f"""
    Both `Payment` events have the same date, so with day-level timestamps
    we can't know which one came first. On the first of the two rows,
    `totalPaymentAmount` already contains *both* payments, while
    `payment_cumsum` only adds up the payments up to this row. In
    {_n_same_day_resolved} of these {len(_same_day_dev)} cases the
    difference is gone at the last `Payment` event, so it is only a
    temporary effect of the order of the events.
    """),
        mo.md(f"""
    **2. `totalPaymentAmount` higher than the logged payments ({len(_other_dev)} cases),** for example
    case `{_other_dev[0]}`:
    """),
        mo.ui.table(_ex_other),
        mo.md(f"""
    Here `totalPaymentAmount` increases by *more* than the `paymentAmount`
    of the event. In this case the first payment is
    {_ex_first_payment['paymentAmount']:g} and `totalPaymentAmount` is
    already {_ex_first_payment['totalPaymentAmount']:g}
    ({_ex_first_payment['totalPaymentAmount'] / _ex_first_payment['paymentAmount']:g} times
    the payment). The logged payments add up to
    {_ex_other['paymentAmount'].sum():g}, which is the same as the total
    amount owed ({_ex_owed:g}, penalized fine plus expense). So for this
    case it looks like the system **counted a payment twice** when
    calculating `totalPaymentAmount`.

    For the whole group, the difference in `totalPaymentAmount` is equal
    to one of the logged payments of the case in {_n_double_counted} of
    {len(_other_dev)} cases. But this fits two explanations: a payment
    that was counted twice, or a second payment with the same amount on
    the same day that is missing as an event (with day-level timestamps,
    two such payments look exactly the same). So we checked which of the
    two totals actually pays off the fine (penalized amount plus
    expenses) at the end of the case:
    - the logged payments pay it off exactly in {_n_logged_settles} of
      {len(_other_dev)} cases (fits "counted twice"),
    - `totalPaymentAmount` pays it off exactly in {_n_reported_settles}
      cases (fits "payment event missing"),
    - in {_n_reported_too_low} cases even `totalPaymentAmount` is lower
      than the amount owed, so neither total settles the fine.

    So the evidence is mixed, and from the log alone we can't decide
    which explanation is right. We would ask the data providers about it.

    In both groups, `totalPaymentAmount` is not a fully reliable running
    sum of the logged payments. This shows why we should check existing
    attributes instead of just trusting them (as mentioned in the lecture).
    For the data collection, we would suggest giving every payment a
    unique ID and calculating `totalPaymentAmount` from the `Payment`
    events instead of storing it as a separate attribute.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.2.5: Outstanding amount
    """)
    return


@app.cell(hide_code=True)
def _(df_task4, mo):
    # Task 2.2.5: event enrichment: outstanding_amount = amount owed so far - amount paid so far
    df_task5 = df_task4.copy()

    # amount owed = current fine amount (base amount, replaced by the higher
    # penalized amount once "Add penalty" occurs) plus any expenses recorded
    df_task5['amount_due_so_far'] = df_task5.groupby('case:concept:name')['amount'].ffill()

    df_task5['expense_so_far'] = df_task5.groupby('case:concept:name')['expense'].cumsum()
    df_task5['expense_so_far'] = df_task5.groupby('case:concept:name')['expense_so_far'].ffill()
    df_task5['expense_so_far'] = df_task5['expense_so_far'].fillna(0)

    # round to cents, otherwise floating point errors (tiny values like 1e-14)
    # would count as > 0 or < 0 (see lecture on floats and money)
    _unrounded = df_task5['amount_due_so_far'] + df_task5['expense_so_far'] - df_task5['payment_cumsum']
    df_task5['outstanding_amount'] = _unrounded.round(2)
    # how many events would be wrong without rounding?
    _residues = _unrounded[(_unrounded != 0) & (df_task5['outstanding_amount'] == 0)]
    _n_float_residues = len(_residues)

    mo.md(f"""
    **Enrichment `outstanding_amount`:** For every event, this is the
    amount the offender still has to pay at that point. We built it from
    three preliminary event enrichments:
    - `amount_due_so_far`: the last known `amount` of the case (`ffill()`
      of `amount`). This is the base fine, or the penalized amount once a
      penalty was added.
    - `expense_so_far`: the running total of `expense` in the case (same
      `cumsum()` + `ffill()` + `fillna(0)` as for `payment_cumsum`).
    - `payment_cumsum`: the running total of payments from Task 2.2.4.

    So `outstanding_amount = amount_due_so_far + expense_so_far - payment_cumsum`,
    rounded to 2 decimals. We round because of floating point errors: without
    rounding, some values would be tiny numbers instead of exactly 0 and
    would count as "still owed" or "overpaid" (see the lecture about floats
    and money). In this log this happens for {_n_float_residues:,} events
    (the largest error is `{_residues.abs().max():.0e}`), and the rounding
    sets them to exactly 0.
    """)
    return (df_task5,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 2.2.5a: Checking the enrichment on one case
    """)
    return


@app.cell(hide_code=True)
def _(df_task5, mo):
    # Task 2.2.5a: verify the enrichment on a selected case
    _case_id = 'A10009'
    _cols = ['time:timestamp', 'concept:name', 'amount_due_so_far', 'expense_so_far', 'payment_cumsum', 'outstanding_amount']
    _case_events = df_task5.loc[df_task5['case:concept:name'] == _case_id, _cols].reset_index(drop=True)

    mo.vstack([
        mo.md(f"**Case `{_case_id}`**, checking `outstanding_amount`:"),
        mo.ui.table(_case_events),
        mo.md("""
    `outstanding_amount` starts with the base fine and goes up when the
    `expense` and later the penalty are added. It goes down with the first
    (partial) payment and is exactly 0 after the second payment, which
    covers the rest of the penalized amount plus expenses. This is what we
    expected, so the enrichment works.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 2.2.5b: Events with an outstanding amount > 0
    """)
    return


@app.cell(hide_code=True)
def _(df_task5, mo):
    # Task 2.2.5b: number of events with outstanding_amount > 0
    # (hypothesis in the text below, written before running this cell)
    _n_positive = int((df_task5['outstanding_amount'] > 0).sum())
    _n_negative = int((df_task5['outstanding_amount'] < 0).sum())
    _n_zero = int((df_task5['outstanding_amount'] == 0).sum())
    _n_total = len(df_task5)

    _zero_df = df_task5[df_task5['outstanding_amount'] == 0]
    _n_zero_payment = int((_zero_df['concept:name'] == 'Payment').sum())
    _n_zero_create_fine = int((_zero_df['concept:name'] == 'Create Fine').sum())

    # are the negative values temporary (e.g. ordering of same-day events) or
    # do these cases stay overpaid until their last event?
    _neg_cases = df_task5.loc[df_task5['outstanding_amount'] < 0, 'case:concept:name'].unique()
    _last_outstanding = df_task5.groupby('case:concept:name')['outstanding_amount'].last()
    _final_neg = _last_outstanding[_last_outstanding.index.isin(_neg_cases) & (_last_outstanding < 0)]

    # are the overpayments random, or do some exact amounts occur very often?
    _overpaid_by = (-_final_neg).round(2)
    _top_overpayments = _overpaid_by.value_counts().head(5)
    _top_overpayments_df = _top_overpayments.rename_axis('overpaid_by').reset_index(name='no_of_cases')
    _n_about_5 = int(_overpaid_by.between(5.16, 5.17).sum())
    _n_below_1 = int((_overpaid_by < 1).sum())

    _text = mo.md(f"""
    **Hypothesis:** Every case starts with an unpaid fine, and the amount
    only goes down to 0 with a payment. Many cases are never paid (e.g.
    the ones sent to credit collection), so we expect that most events,
    maybe around 80 to 90%, have an outstanding amount > 0.

    **Events with `outstanding_amount` > 0:** {_n_positive:,} out of
    {_n_total:,} ({_n_positive / _n_total:.1%}), {'which fits our hypothesis' if 0.8 <= _n_positive / _n_total <= 0.9 else 'which is different from our hypothesis'}.

    The other {_n_total - _n_positive:,} events can be split into two
    groups:
    - **Exactly 0:** {_n_zero:,} events ({_n_zero / _n_total:.1%}). Most of
      them ({_n_zero_payment:,}) are `Payment` events where the payment
      pays off the fine completely. There are also {_n_zero_create_fine:,}
      `Create Fine` events where the fine is 0 (the zero-amount fines from
      Task 1.1c) and {_n_zero - _n_zero_payment - _n_zero_create_fine}
      other events in cases that were already paid at that point.
    - **Negative:** {_n_negative:,} events ({_n_negative / _n_total:.1%}).
      Here the case looks overpaid. These events belong to
      {len(_neg_cases):,} cases, and {len(_final_neg):,} of them are still
      negative at the last event. So it is not just a temporary effect of
      the order of events on the same day. Based on the logged payments,
      these offenders paid more than the fine plus expenses, but mostly
      only a little more (median overpayment {-_final_neg.median():g}).

    We then looked at how much these cases are overpaid (see the table
    below), and the amounts are not random. {_n_about_5:,} of the
    {len(_final_neg):,} cases are overpaid by exactly 5.16 or 5.17, and
    {_n_below_1:,} by less than 1 (e.g. 0.01, which looks like a rounding
    difference). Since so many offenders pay the same extra 5.16, we think
    there is some fixed fee that the offenders have to pay, but that is
    not logged as `expense`. We would ask the data providers about this.
    """)
    mo.vstack([
        _text,
        mo.md("**Most frequent final overpayments:**"),
        mo.ui.table(_top_overpayments_df),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.3
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.3.5: Case log and initial fine amount
    """)
    return


@app.cell(hide_code=True)
def _(df, mo):
    # Task 2.3.5: build the initial case log with all case attributes, plus initial_fine_amount
    _df_sorted = df.sort_values(['case:concept:name', 'time:timestamp'], kind='stable')
    _cases = _df_sorted.groupby('case:concept:name')

    # case attributes = attributes with at most one distinct non-null value per case
    _mandatory_cols = {'case:concept:name', 'concept:name', 'time:timestamp'}
    _attribute_cols = [c for c in df.columns if c not in _mandatory_cols]
    _n_unique_per_case = _df_sorted.groupby('case:concept:name')[_attribute_cols].nunique()
    _case_attr_cols = [c for c in _attribute_cols if _n_unique_per_case[c].max() <= 1]

    case_log = _cases.agg(
        start_time=('time:timestamp', 'first'),
        end_time=('time:timestamp', 'last'),
        no_of_events=('concept:name', 'count'),
    )
    case_log = case_log.join(_cases[_case_attr_cols].first())

    # amount only ever increases within a case (cf. Task 2.1.2b), so the
    # first non-null value is the initial fine amount and the last non-null
    # value is the final fine amount
    case_log['initial_fine_amount'] = _cases['amount'].apply(lambda s: s.dropna().iloc[0] if s.notna().any() else None)
    case_log['final_fine_amount'] = _cases['amount'].apply(lambda s: s.dropna().iloc[-1] if s.notna().any() else None)

    _all_start_with_create_fine = bool((_cases['concept:name'].first() == 'Create Fine').all())

    mo.vstack([
        mo.md(f"""
    We built the **case log** by aggregating the event log per case
    ({len(case_log):,} cases). Besides `start_time`, `end_time` and
    `no_of_events`, it contains all **case attributes**. We define a case
    attribute as an attribute with at most one distinct (non-null) value
    per case, and we found them by checking
    `event_log.groupby(case_id)[attr].nunique().max() <= 1` for every
    non-mandatory attribute. This gives: `{_case_attr_cols}`.

    The new attribute **`initial_fine_amount`** is the first non-null value
    of `amount` per case. This is the same as the `amount` of the
    `Create Fine` event, because {'every' if _all_start_with_create_fine else 'NOT every'}
    case starts with `Create Fine` (we checked the first event of all
    {len(case_log):,} cases). We also added `final_fine_amount` (the last
    non-null value of `amount`) in the same way, because we need it for
    Task 2.3.6.
    """),
        mo.ui.table(case_log.reset_index().head(20)),
    ])
    return (case_log,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 2.3.5a: Hypothesis about the distribution
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Hypothesis:**

    We think that the amount of a fine mainly depends on the violation
    (the `article`), and that the police can't choose the amount freely
    for every single fine. So we expect that `initial_fine_amount` is not a
    smooth, continuous distribution, but a **discrete and multimodal** one:
    a few standard amounts should appear very often (spikes at these
    values). We also expect it to be right-skewed, with a long tail of
    rare but high fines for more serious violations. This would also fit
    the min/median/max from Task 1.1c (0 / 35 / 4,351).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 2.3.5b: Distribution of the initial fine amount
    """)
    return


@app.cell(hide_code=True)
def _(case_log, mo, px):
    # Task 2.3.5b: visualize the distribution of initial_fine_amount
    _fig = px.histogram(case_log, x='initial_fine_amount', nbins=200, log_y=True)
    _fig.update_layout(bargap=0.1, title='Distribution of initial_fine_amount (log-scaled y-axis)')

    _top_values = case_log['initial_fine_amount'].value_counts().head(5)
    _top_share = _top_values.sum() / len(case_log)

    # in the full-range histogram the frequent amounts close to each other all
    # merge into the same bars; zoom in on amounts <= 100 and plot every exact
    # amount as its own bar to make the individual spikes visible
    _share_20_to_40 = case_log['initial_fine_amount'].between(20, 40, inclusive='left').mean()
    _zoom_max = 100
    _zoom_counts = case_log.loc[case_log['initial_fine_amount'] <= _zoom_max, 'initial_fine_amount'] \
                           .value_counts().sort_index().reset_index()
    _zoom_counts.columns = ['initial_fine_amount', 'no_of_cases']
    _zoom_share = (case_log['initial_fine_amount'] <= _zoom_max).mean()
    _fig_zoom = px.bar(
        _zoom_counts, x='initial_fine_amount', y='no_of_cases', log_y=True,
        title=f'Zoomed in: exact initial_fine_amount values up to {_zoom_max} (log-scaled y-axis)',
    )
    _fig_zoom.update_traces(width=0.4)

    # the top amounts are close to each other: are they the same violation
    # (article 157) at different points in time? Most frequent amount per year
    _art157 = case_log[case_log['article'] == 157]
    _art157_year = _art157['start_time'].dt.year
    _tariff_by_year = _art157.groupby(_art157_year)['initial_fine_amount'] \
                             .agg(most_frequent_amount=lambda s: s.mode().iloc[0], no_of_cases='count') \
                             .rename_axis('year').reset_index()
    _top_cases = case_log[case_log['initial_fine_amount'].isin(_top_values.index)]
    _top_art157_share = (_top_cases['article'] == 157).mean()
    # are the top 5 amounts all yearly tariffs of article 157?
    _n_top_are_tariffs = int(_top_values.index.isin(_tariff_by_year['most_frequent_amount']).sum())
    # how often does the most frequent amount go up or down from one year to the next?
    _change = _tariff_by_year['most_frequent_amount'].diff()
    _n_up_years = int((_change > 0).sum())
    _prev_year = _tariff_by_year.shift(1)
    _down = _change < 0
    _down_text = ', '.join(
        f"from {int(py)} to {int(y)}: {pa:g} to {a:g}"
        for py, y, pa, a in zip(_prev_year.loc[_down, 'year'], _tariff_by_year.loc[_down, 'year'],
                                _prev_year.loc[_down, 'most_frequent_amount'], _tariff_by_year.loc[_down, 'most_frequent_amount'])
    )
    _n_down_years = int(_down.sum())

    mo.vstack([
        mo.ui.plotly(_fig),
        mo.ui.plotly(_fig_zoom),
        mo.md(f"""
    The first chart shows the whole range. In this chart we can't see the
    single amounts, because {_share_20_to_40:.1%} of all cases have an
    amount between 20 and 40 and end up in the bars on the far left.
    That's why we added a second chart, which only shows amounts up to
    {_zoom_max} ({_zoom_share:.1%} of all cases), with one bar for every
    exact amount.

    **Two observations** (both confirm our hypothesis):
    1. The distribution is **discrete with clear spikes** (see the second
       chart). The 5 most common amounts
       ({', '.join(f'{a:g} ({n:,} cases)' for a, n in _top_values.items())})
       already cover {_top_share:.1%} of all {len(case_log):,} cases.
       What surprised us is that these five amounts are mostly not
       different violations, but the same violation in different years.
       {_top_art157_share:.1%} of these cases are `article` 157, and
       {'all 5' if _n_top_are_tariffs == 5 else f'{_n_top_are_tariffs} of the 5'} amounts
       are the most frequent amount for this article in one of the years. The fine for this
       article went up over time (see the table below), from
       {_tariff_by_year['most_frequent_amount'].iloc[0]:g} in
       {_tariff_by_year['year'].iloc[0]} to
       {_tariff_by_year['most_frequent_amount'].iloc[-1]:g} in {_tariff_by_year['year'].iloc[-1]}.
       It goes up {_n_up_years} times and only goes down
       {'once' if _n_down_years == 1 else f'{_n_down_years} times'} ({_down_text}).
       For the data collection, we would suggest recording which tariff
       version was used for a fine, because otherwise the same violation
       shows up with different amounts.
    2. The distribution is **strongly right-skewed** with a long tail.
       The mean ({case_log['initial_fine_amount'].mean():.1f}) is clearly
       higher than the median ({case_log['initial_fine_amount'].median():.1f}),
       because of a small number of very high fines (up to
       {case_log['initial_fine_amount'].max():,.0f}). In the first
       histogram these are the few small bars far on the right.
    """),
        mo.md("**Most frequent initial fine amount for `article` 157, per year:**"),
        mo.ui.table(_tariff_by_year),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.3.6: Initial vs. final fine amount
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Hypothesis:** Since `amount` never goes down within a
    case (Task 2.1.2b), we expect `final_fine_amount` to be either the
    same as `initial_fine_amount` (no penalty) or about twice as high
    (with penalty), but never lower.
    """)
    return


@app.cell(hide_code=True)
def _(case_log, df, mo, pd, px):
    # Task 2.3.6: relate initial_fine_amount and final_fine_amount per case
    # colour the cases by final / initial, so cases with an unusual
    # penalty factor are easy to see
    _ratio = (case_log['final_fine_amount'] / case_log['initial_fine_amount']) \
                 .replace([float('inf')], float('nan'))
    _band_labels = ['x1 (no penalty)', 'x1 to x1.9', 'x1.9 to x2.1 (about double)', 'x2.1 to x3', 'more than x3']
    _plot_df = case_log.assign(
        ratio=_ratio,
        ratio_band=pd.cut(_ratio, [0, 1, 1.9, 2.1, 3, float('inf')], labels=_band_labels)
                     .cat.add_categories(['initial amount 0']).fillna('initial amount 0'),
    )
    _fig = px.scatter(
        _plot_df, x='initial_fine_amount', y='final_fine_amount', color='ratio_band',
        category_orders={'ratio_band': _band_labels + ['initial amount 0']},
        hover_data=['article', 'ratio'], opacity=0.3,
        title='Final vs. initial fine amount per case, coloured by final / initial',
    )
    # the diagonal goes up to the max of both axes, otherwise it stops too early
    _axis_max = max(case_log['initial_fine_amount'].max(), case_log['final_fine_amount'].max())
    _fig.add_shape(type='line', x0=0, y0=0, x1=_axis_max, y1=_axis_max, line=dict(color='gray', dash='dot'))

    _no_penalty_share = (case_log['final_fine_amount'] == case_log['initial_fine_amount']).mean()
    _penalty_share = (case_log['final_fine_amount'] > case_log['initial_fine_amount']).mean()
    _below_share = (case_log['final_fine_amount'] < case_log['initial_fine_amount']).mean()

    # how close to "double" are the penalized cases, and which articles are in the unusual bands?
    _penalized_ratio = _ratio[_ratio > 1]
    _share_double = _penalized_ratio.between(1.9, 2.1, inclusive='right').mean()
    _band_table = _plot_df.groupby('ratio_band', observed=True).agg(
        no_of_cases=('ratio', 'size'),
        articles=('article', lambda s: ', '.join(f'{a:g} ({n})' for a, n in s.value_counts().head(5).items())),
    ).reset_index()
    _band_table.loc[_band_table['no_of_cases'] > 1000, 'articles'] = '(many)'

    def _articles_in(band):
        return ', '.join(f'{a:g}' for a in sorted(_plot_df.loc[_plot_df['ratio_band'] == band, 'article'].unique()))

    _low = _plot_df[_plot_df['ratio_band'] == 'x1 to x1.9']
    _max_initial_case = case_log['initial_fine_amount'].idxmax()

    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(f"""
    In the scatter plot we can see two separate groups, both on or above
    the dotted diagonal (`final = initial`):
    - **{_no_penalty_share:.1%} of the cases** are exactly **on the
      diagonal**, so `final_fine_amount` is the same as
      `initial_fine_amount` and no penalty was added.
    - **{_penalty_share:.1%} of the cases** are on a second line
      **above** the diagonal, at about double the initial amount. This
      fits the late-payment penalty from Task 2.1.2b.
    - **No case is below the diagonal** ({_below_share:.1%}). The amount
      never goes down within a case, which fits `amount` being
      case-cumulative (Task 2.1.2b).

    So our hypothesis is correct for almost all cases. The penalty really
    doubles the fine: {_share_double:.2%} of the penalized cases have a
    factor between 1.9 and 2.1 (median {_penalized_ratio.median():.2f}).
    But with the colours (and the table below) we found a few small groups
    with a different factor, which we didn't see in the plot before:
    - **x2.1 to x3:** {int((_plot_df['ratio_band'] == 'x2.1 to x3').sum())} cases,
      all with `article` {_articles_in('x2.1 to x3')}.
    - **more than x3:** {int((_plot_df['ratio_band'] == 'more than x3').sum())} cases
      (up to {_ratio.max():.1f} times), with `article` {_articles_in('more than x3')}.
    - **x1 to x1.9:** {len(_low)} cases. One of them is the largest fine
      in the log (case `{_max_initial_case}`, {case_log.loc[_max_initial_case, 'initial_fine_amount']:,.0f}
      to {case_log.loc[_max_initial_case, 'final_fine_amount']:,.0f}). This
      final amount is also the largest `amount` in the whole log
      ({df['amount'].max():,.0f}), so it might be a maximum that the
      penalty can't go above.

    So it looks like the penalty factor depends on the article. For almost
    all articles the fine is doubled, but for a few it is more. We would
    check these exceptions (and the possible maximum) with the domain
    experts.
    """),
        mo.md("**Cases per ratio band (final / initial), with the most frequent articles:**"),
        mo.ui.table(_band_table),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 2.3.7: Noteworthy fact about `article`
    """)
    return


@app.cell(hide_code=True)
def _(case_log, mo, pd, px):
    # Task 2.3.7: noteworthy fact about the distribution of `article`
    _counts = case_log['article'].value_counts()
    _top3 = _counts.head(3)
    _top3_share = _top3.sum() / case_log['article'].notna().sum()

    # top 15 codes individually, the rest bucketed into "Other" so the long
    # tail of rare articles is still visible in a single chart
    _top15 = _counts.head(15)
    _other_count = _counts.iloc[15:].sum()
    _bar_data = pd.concat([_top15, pd.Series({'Other': _other_count})]).reset_index()
    _bar_data.columns = ['article', 'no_of_cases']

    _fig = px.bar(
        _bar_data, x='article', y='no_of_cases', log_y=True,
        title='Distribution of article (top 15 codes + Other, log-scaled y-axis)',
    )
    _fig.update_xaxes(type='category')

    mo.vstack([
        mo.md("**Distribution of `article` (the article that was violated), top 3:**"),
        mo.ui.table(_top3.reset_index().rename(columns={'count': 'no_of_cases'})),
        mo.ui.plotly(_fig),
        mo.md(f"""
    **Noteworthy fact:** Only **3 articles ({', '.join(f'{a:g}' for a in _top3.index)})
    account for {_top3_share:.1%}** of the {case_log['article'].notna().sum():,}
    cases with an article, even though {case_log['article'].nunique()}
    different articles occur in the log. So almost all fines are for a
    few standard violations, and all other articles are rare. This is
    similar to what we saw for `initial_fine_amount` above. In the bar
    chart this is easy to see: after the 3 most common articles the number
    of cases drops a lot, followed by a long tail of rare articles.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 3

    ## Task 3.1
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Our three business-level process outcomes:**

    For us, an outcome should say how a fine *ends*, not which steps it
    went through. Based on the activities and attributes in the log, we
    chose these three outcomes:

    1. **Paid**: The offender paid the fine, i.e. the case has at least
       one `Payment` event and `outstanding_amount` (from Task 2.2.5) is
       0 or less at the last event of the case.
    2. **Sent to credit collection**: The case contains a
       `Send for Credit Collection` event, so the fine was handed over to
       a collection agency.
    3. **Dismissed**: The fine was cancelled after an appeal, i.e.
       `dismissal` is "#" (dismissed by the prefecture) or "G" (dismissed
       by the judge) at some event of the case. We only use these two
       documented codes, because the meaning of the other codes is
       unknown (see Task 3.1a).

    First we also thought about "appealed" as an outcome. But an appeal
    is more a step in the process than an end. An appealed fine can still
    be dismissed, paid or sent to credit collection (see Task 3.1a), so we
    use "dismissed" instead.

    **Hypothesis:** Each outcome is a different way how the fine can end,
    so we expect that the three outcomes (almost) never overlap. Paid and
    credit collection should cover most cases, and dismissed should be
    rare, because only few offenders appeal. Some
    cases might not have any of the outcomes, so we also look at the
    combinations and at the cases without an outcome in Task 3.1a.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 3.1a: Outcome indicators and number of cases
    """)
    return


@app.cell(hide_code=True)
def _(case_log, df_task5, mo, pd):
    # Task 3.1a: enrich the case log with the three outcome indicators and
    # count cases per outcome, per pairwise combination, and with no outcome
    _by_case = df_task5.groupby('case:concept:name')
    _has_payment = _by_case['concept:name'].apply(lambda s: 'Payment' in set(s))
    _final_outstanding = _by_case['outstanding_amount'].last()

    case_log_outcomes = case_log.copy()
    case_log_outcomes['outcome_paid'] = _has_payment & (_final_outstanding <= 0)
    case_log_outcomes['outcome_credit_collection'] = _by_case['concept:name'].apply(lambda s: 'Send for Credit Collection' in set(s))
    case_log_outcomes['outcome_dismissed'] = _by_case['dismissal'].apply(lambda s: s.isin(['#', 'G']).any())

    _outcomes = ['outcome_paid', 'outcome_credit_collection', 'outcome_dismissed']
    _n_total = len(case_log_outcomes)

    _single_counts = pd.DataFrame([
        {'outcome': o, 'no_of_cases': int(case_log_outcomes[o].sum()), 'share': f'{case_log_outcomes[o].mean():.1%}'}
        for o in _outcomes
    ])

    _pair_counts = pd.DataFrame([
        {
            'outcome_pair': f'{a} & {b}',
            'no_of_cases': int((case_log_outcomes[a] & case_log_outcomes[b]).sum()),
        }
        for i, a in enumerate(_outcomes) for b in _outcomes[i + 1:]
    ])

    _n_multi = int((case_log_outcomes[_outcomes].sum(axis=1) > 1).sum())
    _paid_or_cc_share = (case_log_outcomes['outcome_paid'] | case_log_outcomes['outcome_credit_collection']).mean()
    _is_none = ~case_log_outcomes[_outcomes].any(axis=1)
    _n_none = int(_is_none.sum())

    # do the no-outcome cases just stop because the log ends?
    _log_end = df_task5['time:timestamp'].max()
    _n_none_ended_early = int((case_log_outcomes.loc[_is_none, 'end_time'] < _log_end - pd.Timedelta(days=365)).sum())

    # why "appealed" is not an outcome: how do the appealed cases end?
    _appeal_activities = {
        'Insert Date Appeal to Prefecture', 'Send Appeal to Prefecture',
        'Receive Result Appeal from Prefecture', 'Notify Result Appeal to Offender',
        'Appeal to Judge',
    }
    _is_appealed = _by_case['concept:name'].apply(lambda s: len(set(s) & _appeal_activities) > 0)
    _appealed = case_log_outcomes[_is_appealed]
    _appealed_end = pd.DataFrame([
        {'appealed cases that end ...': 'dismissed', 'no_of_cases': int(_appealed['outcome_dismissed'].sum())},
        {'appealed cases that end ...': 'paid', 'no_of_cases': int(_appealed['outcome_paid'].sum())},
        {'appealed cases that end ...': 'sent to credit collection', 'no_of_cases': int(_appealed['outcome_credit_collection'].sum())},
        {'appealed cases that end ...': 'with none of these', 'no_of_cases': int((~_appealed[_outcomes].any(axis=1)).sum())},
    ])

    # edge cases of the definitions: zero-amount fines without a payment, and
    # cases that were paid off at some point but owe money again at the end
    _zero_without_payment = (case_log_outcomes['initial_fine_amount'] == 0) & ~_has_payment
    _n_zero_without_payment = int(_zero_without_payment.sum())
    _n_zero_without_payment_none = int((_zero_without_payment & _is_none).sum())
    _paid_at_some_point = _has_payment & _by_case['outstanding_amount'].apply(lambda s: (s <= 0).any())
    _n_paid_then_owing = int((_paid_at_some_point & ~case_log_outcomes['outcome_paid']).sum())

    # at which activities do the non-NIL dismissal codes get recorded?
    _dismissal_events = df_task5[df_task5['dismissal'].notna() & (df_task5['dismissal'] != 'NIL')]
    _codes_per_activity = _dismissal_events.groupby('concept:name')['dismissal'].apply(
        lambda s: ', '.join(f'{code} ({n:,})' for code, n in s.value_counts().items())
    ).reset_index().rename(columns={'concept:name': 'activity', 'dismissal': 'dismissal codes (no. of events)'})
    _undocumented = _dismissal_events[~_dismissal_events['dismissal'].isin(['#', 'G'])]
    _n_undocumented = len(_undocumented)
    _n_codes_at_create = int((_undocumented['concept:name'] == 'Create Fine').sum())
    _n_none_undocumented = int((_is_none & case_log_outcomes.index.isin(_undocumented['case:concept:name'])).sum())

    mo.vstack([
        mo.md("**Cases per outcome:**"),
        mo.ui.table(_single_counts),
        mo.md("**Cases per pairwise outcome combination:**"),
        mo.ui.table(_pair_counts),
        mo.md(f"""
    As we expected, the outcomes almost never overlap. Only {_n_multi}
    cases have more than one outcome (see Task 3.1c). Paid and credit
    collection together cover {_paid_or_cc_share:.1%} of the cases, and
    only {case_log_outcomes['outcome_dismissed'].mean():.1%} are dismissed,
    so the rest of our hypothesis is also right.

    **Cases with none of the three outcomes:** {_n_none:,} of {_n_total:,}
    ({_n_none / _n_total:.1%}). This surprised us, because almost every
    fifth fine ends without a full payment, credit collection or
    dismissal. For {_n_none_ended_early:,} of them ({_n_none_ended_early / _n_none:.1%})
    the last event is more than one year before the end of the log
    ({_log_end:%Y-%m-%d}), so they are not just cases that were still
    running when the log ended. In Task 3.1d we look at which variants
    these cases follow.

    **Why we don't use "appealed" as an outcome:** the
    {len(_appealed):,} cases with at least one appeal activity end in
    very different ways (one case can be in more than one row):
    """),
        mo.ui.table(_appealed_end),
        mo.md(f"""
    **Special cases of our definitions:**
    - {_n_zero_without_payment} fines with amount 0
      (`initial_fine_amount` = 0, see Task 1.1c) have no `Payment` event.
      Nothing was paid, so they don't count as paid, and
      {_n_zero_without_payment_none} of them have no outcome at all.
    - {_n_paid_then_owing:,} cases were paid off at some point
      (`outstanding_amount` <= 0 after a payment), but owe money again at
      the end, so they don't count as paid. Case `A10125` in Task 3.1c
      shows how this happens.
    - Only the documented `dismissal` codes count as dismissed: "#"
      (prefecture) only appears at `Send Appeal to Prefecture` and "G"
      (judge) only at `Appeal to Judge` (see the table below). The
      undocumented codes are different: {_n_codes_at_create:,} of their
      {_n_undocumented:,} events are already at `Create Fine`, so they are
      set when the fine is created, before it could be dismissed. That's
      why we don't think they mean "dismissed". Maybe they mark a special
      type of fine. {_n_none_undocumented:,} of the cases without
      an outcome have such a code. These codes should be documented.
    """),
        mo.md("**Non-NIL `dismissal` codes, per activity:**"),
        mo.ui.table(_codes_per_activity),
    ])
    return (case_log_outcomes,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 3.1b: One case per outcome
    """)
    return


@app.cell(hide_code=True)
def _(calendar_days, case_log_outcomes, df_task5, mo):
    # Task 3.1b: inspect and interpret a case for each of the three outcomes
    _outcome_cols = ['outcome_paid', 'outcome_credit_collection', 'outcome_dismissed']
    _cols = ['time:timestamp', 'concept:name', 'amount_due_so_far', 'expense_so_far', 'payment_cumsum', 'outstanding_amount', 'dismissal']

    def outcome_case_table(case_id):
        _table = df_task5.loc[df_task5['case:concept:name'] == case_id, _cols].reset_index(drop=True)
        # the outcome indicators are case-level (one value per case), repeated
        # on every row here so they're visible right next to the events
        for _col in _outcome_cols:
            _table[_col] = case_log_outcomes.loc[case_id, _col]
        return _table

    _a100 = outcome_case_table('A100').set_index('concept:name')['time:timestamp']
    _a100_days_to_collection = calendar_days(_a100['Add penalty'], _a100['Send for Credit Collection'])

    mo.vstack([
        mo.md("**Paid: case `A10000`**"),
        mo.ui.table(outcome_case_table('A10000')),
        mo.md("""
    This is the same case as in Task 2.1.3. A penalty is added (36 to 74),
    and then the offender pays 87 in one payment, which covers everything,
    so `outstanding_amount` is exactly 0 at the end. This is a clear
    example of what we mean with `outcome_paid`.
    """),
        mo.md("**Sent to credit collection: case `A100`**"),
        mo.ui.table(outcome_case_table('A100')),
        mo.md(f"""
    The fine is created and sent, and after the deadline a penalty is
    added. The offender never pays anything. On
    {_a100['Send for Credit Collection']:%Y-%m-%d} ({_a100_days_to_collection}
    days after the penalty) the case is sent for credit collection.
    `outstanding_amount` only goes up and never down, because the
    offender didn't pay at all.
    """),
        mo.md("**Dismissed: case `A10001`**"),
        mo.ui.table(outcome_case_table('A10001')),
        mo.md("""
    Shortly after the notification, the offender appeals to the
    prefecture (`Insert Date Appeal to Prefecture`), and a bit later the
    appeal is sent to the prefecture (`Send Appeal to Prefecture`). In
    between, the penalty is still added, so the appeal doesn't stop the
    penalty. The appeal was successful: the `Send Appeal to Prefecture`
    event has `dismissal` "#", which means the prefecture dismissed the
    fine, so `outcome_dismissed` is true. This explains why there is no
    payment and no credit collection, even though `outstanding_amount`
    stays positive (our enrichment doesn't consider dismissals).

    One thing is strange though: the "#" is recorded when the appeal is
    *sent* to the prefecture, and there is no
    `Receive Result Appeal from Prefecture` event. So the result is in the
    log before the prefecture could have decided anything. We guess that
    the `dismissal` value was added later to the last available event,
    but we would have to ask the data providers about this.
    """),
    ])
    return (outcome_case_table,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 3.1c: Cases with more than one outcome
    """)
    return


@app.cell(hide_code=True)
def _(calendar_days, case_log_outcomes, df_task5, mo, outcome_case_table):
    # Task 3.1c: inspect and interpret the cases with more than one outcome
    _outcome_cols = ['outcome_paid', 'outcome_credit_collection', 'outcome_dismissed']
    _multi = case_log_outcomes[case_log_outcomes[_outcome_cols].sum(axis=1) > 1]

    _items = []
    for _cid in _multi.index:
        _flags = [c.replace('outcome_', '') for c in _outcome_cols if _multi.loc[_cid, c]]
        _items += [mo.md(f"**Case `{_cid}`** ({' & '.join(_flags)}):"), mo.ui.table(outcome_case_table(_cid))]

    # paid and sent to credit collection: was the fine already paid off when it was handed over?
    _lines = []
    for _cid in _multi.index[_multi['outcome_paid'] & _multi['outcome_credit_collection']]:
        _t = outcome_case_table(_cid)
        _cc = _t[_t['concept:name'] == 'Send for Credit Collection'].iloc[0]
        _before = _t[(_t['concept:name'] == 'Payment') & (_t['time:timestamp'] <= _cc['time:timestamp'])]
        if len(_before) and _before['outstanding_amount'].iloc[-1] <= 0:
            _lines.append(
                f"- `{_cid}`: the fine is paid off on {_before['time:timestamp'].iloc[-1]:%Y-%m-%d} "
                f"(`outstanding_amount` {_before['outstanding_amount'].iloc[-1]:g}), but "
                f"{calendar_days(_before['time:timestamp'].iloc[-1], _cc['time:timestamp']):,} days later "
                f"it is still sent for credit collection."
            )
        else:
            _lines.append(f"- `{_cid}`: the fine is sent for credit collection on {_cc['time:timestamp']:%Y-%m-%d} "
                          f"and only paid off afterwards.")

    # paid and dismissed: did the offender pay before or after the dismissal?
    for _cid in _multi.index[_multi['outcome_paid'] & _multi['outcome_dismissed']]:
        _t = outcome_case_table(_cid)
        _dis = _t[_t['dismissal'].isin(['#', 'G'])].iloc[0]
        _pays = _t[_t['concept:name'] == 'Payment']
        _lines.append(
            f"- `{_cid}`: the fine is dismissed (`dismissal` \"{_dis['dismissal']}\" at `{_dis['concept:name']}` "
            f"on {_dis['time:timestamp']:%Y-%m-%d}), but the offender still pays {_pays['payment_cumsum'].iloc[-1]:g} "
            f"in total (last payment on {_pays['time:timestamp'].iloc[-1]:%Y-%m-%d})."
        )

    _lines_md = '\n    '.join(_lines)

    # A limit of our "paid" definition: case A10125
    _case_id = 'A10125'
    _case_table = outcome_case_table(_case_id)

    def _date(activity):
        return _case_table.loc[_case_table['concept:name'] == activity, 'time:timestamp'].iloc[0]

    _notified = _date('Insert Fine Notification')
    _paid_on = _date('Payment')
    _penalized = _date('Add penalty')
    _payment = _case_table.loc[_case_table['concept:name'] == 'Payment', 'payment_cumsum'].iloc[0]
    _final_outstanding = _case_table['outstanding_amount'].iloc[-1]

    # is the penalty in this case an exception? Check how Add penalty relates
    # to Insert Fine Notification across the whole log
    _first_ts = df_task5.groupby(['case:concept:name', 'concept:name'])['time:timestamp'].first().unstack()
    _notified_cases = _first_ts['Insert Fine Notification'].notna()
    _penalized_cases = _first_ts['Add penalty'].notna()
    _n_notified = int(_notified_cases.sum())
    _n_notified_and_penalized = int((_notified_cases & _penalized_cases).sum())
    _days_to_penalty = calendar_days(_first_ts['Insert Fine Notification'], _first_ts['Add penalty']).dropna()
    if _days_to_penalty.min() == _days_to_penalty.max():
        _days_text = f'always exactly {_days_to_penalty.min():.0f} days'
    else:
        _days_text = f'always {_days_to_penalty.min():.0f} to {_days_to_penalty.max():.0f} days'

    mo.vstack([
        mo.md(f"""
    Only {len(_multi)} cases have more than one outcome:
    """),
        *_items,
        mo.md(f"""
    {_lines_md}

    Sending a fine to credit collection when it is already paid is a
    process error. We think nobody checks if the fine was paid in the
    meantime before it is sent. The paid and dismissed case is also
    strange. Either the dismissal was taken back later, or the offender
    paid a fine that was cancelled and should get the money back. These
    are only {len(_multi)} cases, so they don't really matter for the
    overall picture, but we would still ask the data providers about
    them.
    """),
        mo.md(f"""
    **A limit of our "paid" definition: case `{_case_id}`**

    This case was paid on time, but it doesn't count as paid with our
    definition:
    """),
        mo.ui.table(_case_table),
        mo.md(f"""
    What happens in this case:
    - The fine (36) is sent with an expense of 13, and the offender is
      notified on {_notified:%Y-%m-%d}. A few days later they appeal to the
      prefecture (`Insert Date Appeal to Prefecture`).
    - On {_paid_on:%Y-%m-%d}, {calendar_days(_notified, _paid_on)} days after the
      notification, the offender pays {_payment:g}. This is **within the
      60-day deadline** and exactly the amount owed at that time
      (36 + 13 expense), so `outstanding_amount` goes down to 0.
    - Still, on {_penalized:%Y-%m-%d} ({calendar_days(_notified, _penalized)} days
      after the notification), `Add penalty` increases the fine to 74.
      Because the offender already paid on time, the penalty should not
      have been added. `outstanding_amount` goes up again to
      {_final_outstanding:g}.
    - On the same day, the appeal is sent to the prefecture with
      `dismissal` "NIL". After that the case ends. The
      {_final_outstanding:g} are never paid, and the case is also not sent
      for credit collection.

    **Why is a fine that was paid on time penalized?** We checked if this
    happens in other cases too. Of the {_n_notified:,} cases with an
    `Insert Fine Notification`, {_n_notified_and_penalized:,}
    ({_n_notified_and_penalized / _n_notified:.0%}) also have an
    `Add penalty`, {_days_text} after the notification. So we think
    `Add penalty` is recorded **automatically when the 60-day deadline is
    over, without checking if the fine was already paid**. In this case
    the remaining {_final_outstanding:g} are never collected, so it seems
    like the police didn't really expect the penalty to be paid. For the
    process, we would suggest adding the penalty only if the fine is still
    unpaid at the deadline. For the data, a penalty that doesn't apply
    should not be logged (or at least be marked as cancelled), because
    otherwise `amount` is higher than what the offender actually owes.

    Because of this penalty, our enrichment says that
    {_final_outstanding:g} are still owed at the end, so the case is not
    `outcome_paid` (and it has no other outcome either). So our definition
    doesn't work well for cases like this, because it just uses the
    `amount` from the log, even if the penalty shouldn't have been there.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 3.1d: Cases without an outcome
    """)
    return


@app.cell(hide_code=True)
def _(case_log_outcomes, df_task5, mo, outcome_case_table, pd):
    # Task 3.1d: inspect and interpret the cases with none of the three outcomes
    _outcome_cols = ['outcome_paid', 'outcome_credit_collection', 'outcome_dismissed']
    _is_none = ~case_log_outcomes[_outcome_cols].any(axis=1)
    _none_ids = case_log_outcomes.index[_is_none]
    _n_none = len(_none_ids)

    # which sequences of activities do the cases without an outcome follow?
    _sequences = df_task5.groupby('case:concept:name')['concept:name'].apply(tuple)
    _none_variants = _sequences[_none_ids].value_counts()
    _none_variants_df = pd.DataFrame([
        {'variant': ' -> '.join(v), 'no_of_cases': int(c), 'share_of_no_outcome_cases': f'{c / _n_none:.1%}'}
        for v, c in _none_variants.head(5).items()
    ])

    # group 1: the fine is only created and sent
    _case_id = 'A1'
    _case_table = outcome_case_table(_case_id)
    _log_end = df_task5['time:timestamp'].max()
    _years_before_end = (_log_end - _case_table['time:timestamp'].iloc[-1]).days / 365.25
    _case_sequence = _sequences[_case_id]
    _n_same_sequence = int((_sequences == _case_sequence).sum())

    # group 2: the offender paid something, but not everything
    _final_outstanding = df_task5.groupby('case:concept:name')['outstanding_amount'].last()
    _has_payment = _sequences[_none_ids].apply(lambda s: 'Payment' in s)
    _partial_ids = _has_payment[_has_payment].index
    _partial_rest = _final_outstanding[_partial_ids]
    _partial_variant = _sequences[_partial_ids].value_counts().index[0]
    _partial_example = _sequences[_partial_ids][_sequences[_partial_ids] == _partial_variant].index[0]
    _partial_table = outcome_case_table(_partial_example)
    _partial_payments = _partial_table.loc[_partial_table['concept:name'] == 'Payment', 'payment_cumsum'].diff() \
                                      .fillna(_partial_table.loc[_partial_table['concept:name'] == 'Payment', 'payment_cumsum'])

    mo.vstack([
        mo.md(f"""
    {_n_none:,} cases have none of the three outcomes. These are the most
    frequent variants among them:
    """),
        mo.ui.table(_none_variants_df),
        mo.md(f"""
    Most of these cases are in two groups. Either the fine is only
    created and sent, or the offender paid something, but not everything.
    We looked at one case of each group.

    **1. Only created and sent: case `{_case_id}`**
    """),
        mo.ui.table(_case_table),
        mo.md(f"""
    This case only has {len(_case_table)} events. The fine is created and
    then sent to the offender on
    {_case_table['time:timestamp'].iloc[-1]:%Y-%m-%d}, and after that
    nothing happens: no payment, no penalty, no credit collection, no
    appeal, and `dismissal` stays "NIL". The log goes until
    {_log_end:%Y-%m-%d}, so the case didn't stop because the log ended,
    it stops {_years_before_end:.1f} years earlier. There is also no
    `Insert Fine Notification`, so it looks like the offender never
    received the fine. This would explain why there is no penalty, since
    the payment deadline only starts with the notification. Possible
    reasons could be that the offender couldn't be reached (e.g. wrong
    address) or that the fine was paid outside of the system and the
    payment was never logged. From the log alone, we can't tell how this
    case ended.

    `A1` is not a special case: {_n_same_sequence:,} cases have exactly
    the sequence `{' -> '.join(_case_sequence)}` (variant 3 in Task 4.1.1b).
    An open question for us is whether these fines were never delivered,
    paid outside the system, or just dropped.

    **2. Paid, but not everything: case `{_partial_example}`**
    """),
        mo.ui.table(_partial_table),
        mo.md(f"""
    {len(_partial_ids):,} of the cases without an outcome
    ({len(_partial_ids) / _n_none:.1%}) have at least one `Payment`, but
    still owe money at the end (median {_partial_rest.median():g}). In
    case `{_partial_example}` (the most frequent variant of this group),
    the offender pays {' and '.join(f'{p:g}' for p in _partial_payments)}, but
    after the penalty {_partial_rest[_partial_example]:g} are still
    owed when the case ends. The rest is never paid and the case is also
    not sent for credit collection. We look at this variant in more
    detail in Task 4.1.2a. An open question for us is why these remaining
    amounts are never sent for credit collection, like in the cases of
    variant 1 in Task 4.1.1b.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 4

    ## Task 4.1
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 4.1.1: Sequential variants
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, pd):
    # Task 4.1.1: distribution of sequential variants
    _variant_series = df.sort_values(['case:concept:name', 'time:timestamp'], kind='stable') \
                         .groupby('case:concept:name')['concept:name'].apply(tuple)
    variant_counts = _variant_series.value_counts()

    _n_cases = len(_variant_series)
    _n_variants = len(variant_counts)

    _top_df = pd.DataFrame([
        {'variant': ' -> '.join(v), 'no_of_cases': int(c), 'share': f'{c / _n_cases:.1%}'}
        for v, c in variant_counts.head(10).items()
    ])

    mo.vstack([
        mo.md(f"""
    A **sequential variant** is the group (equivalence class) of all cases
    with exactly the same sequence of activities. The {_n_cases:,} cases
    have **{_n_variants} different variants**. These are the 10 most
    frequent ones:
    """),
        mo.ui.table(_top_df),
    ])
    return (variant_counts,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 4.1.1a: Variants needed to cover 80% of the cases
    """)
    return


@app.cell(hide_code=True)
def _(mo, variant_counts):
    # Task 4.1.1a: minimum number of variants needed to cover 80% of the cases
    _n_cases = int(variant_counts.sum())
    _cum_share = variant_counts.cumsum() / _n_cases
    _n_needed = int((_cum_share < 0.8).sum()) + 1
    _actual_share = _cum_share.iloc[_n_needed - 1]

    mo.md(f"""
    We only need **{_n_needed} variants** to cover 80% of the cases. The
    top {_n_needed} variants together already cover {_actual_share:.1%} of
    all {_n_cases:,} cases. So most cases follow a few standard paths,
    similar to the skewed distributions we saw before (Task 2.3.5b and
    2.3.7). This surprised us a bit, because with {len(variant_counts)}
    variants we expected the process to be much messier.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 4.1.1b: The top 4 variants
    """)
    return


@app.cell(hide_code=True)
def _(calendar_days, df, mo, variant_counts):
    # Task 4.1.1b: summarize each of the top 4 sequential variants in one sentence
    _n_cases = int(variant_counts.sum())
    _top4 = variant_counts.head(4)
    _rows = [f"- `{' -> '.join(v)}` ({c:,} cases, {c / _n_cases:.1%})" for v, c in _top4.items()]

    # facts used in the sentences below, per variant: duration and end year of its cases
    _df_sorted = df.sort_values(['case:concept:name', 'time:timestamp'], kind='stable')
    _sequences = _df_sorted.groupby('case:concept:name')['concept:name'].apply(tuple)
    _bounds = _df_sorted.groupby('case:concept:name')['time:timestamp'].agg(['first', 'last'])

    def _cases_of(variant):
        return _bounds[_sequences == variant]

    _v2 = _cases_of(_top4.index[1])
    _v2_median_days = calendar_days(_v2['first'], _v2['last']).median()
    _v3_end_years = _cases_of(_top4.index[2])['last'].dt.year
    _v3_years_covered = sorted(_v3_end_years.unique())

    mo.md(f"""
    **The top 4 variants:**

    {chr(10).join(_rows)}

    Summary in one sentence each:
    1. `{' -> '.join(_top4.index[0])}`: The fine is created, sent and
       notified, then a penalty is added because it wasn't paid, and in the
       end it is sent for credit collection without any payment.
    2. `{' -> '.join(_top4.index[1])}`: The fine is created and paid
       quickly (median {_v2_median_days:.0f} days later), so it never has to
       be sent or notified.
    3. `{' -> '.join(_top4.index[2])}`: The fine is created and sent, but
       there is no notification and nothing else happens afterwards (these
       cases end in {len(_v3_years_covered)} different years, from
       {_v3_years_covered[0]} to {_v3_years_covered[-1]}, so not only at the
       end of the log, see Task 3.1d).
    4. `{' -> '.join(_top4.index[3])}`: The fine is sent, notified and
       penalized like in variant 1, but this time the offender pays in the
       end, so it is not sent for credit collection.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 4.1.1c: Fine object sub-log
    """)
    return


@app.cell(hide_code=True)
def _(mo, variant_counts):
    mo.md(f"""
    **Hypothesis:** The 5 appeal activities only occur in a
    small part of the cases, but they can appear at different points in a
    case, which creates many new variants. So we expect that without them
    the number of variants drops a lot, to clearly less than half of the {len(variant_counts)}.
    """)
    return


@app.cell(hide_code=True)
def _(df, mo):
    # Task 4.1.1c: filter to the fine object sub-log, compare variant counts
    fine_activities = [
        'Create Fine', 'Send Fine', 'Insert Fine Notification', 'Add penalty',
        'Send for Credit Collection', 'Payment',
    ]
    _df_sorted = df.sort_values(['case:concept:name', 'time:timestamp'], kind='stable')
    df_fine = _df_sorted[_df_sorted['concept:name'].isin(fine_activities)].copy()

    _full_variants = _df_sorted.groupby('case:concept:name')['concept:name'].apply(tuple)
    _fine_variants = df_fine.groupby('case:concept:name')['concept:name'].apply(tuple)
    # share of cases with at least one of the 5 appeal activities (= the activities that were filtered out)
    _appealed_share = _df_sorted.loc[~_df_sorted['concept:name'].isin(fine_activities), 'case:concept:name'].nunique() \
                      / _df_sorted['case:concept:name'].nunique()

    mo.md(f"""
    After filtering the log to the 6 activities of the fine object
    (`{fine_activities}`), we still have all {len(_fine_variants):,} cases
    (every case starts with `Create Fine`, see Task 2.3.5). But the number
    of sequential variants goes down from **{_full_variants.nunique()} to
    {_fine_variants.nunique()}**, which confirms our hypothesis. Without the
    5 appeal activities, many variants that were only slightly different
    become the same shorter sequence. So most of the variants in the full
    log come from the appeal activities, even though only
    {_appealed_share:.1%} of the cases contain at least one appeal
    activity.
    """)
    return (df_fine,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task 4.1.2: Process map of the fine object
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # Task 4.1.2: process map (absolute frequency) for the fine object sub-log, inspected in Disco
    mo.vstack([
        mo.md("**Process map (absolute frequency) for the fine object sub-log, from Disco:**"),
        mo.image(src="screenshots/task_4.1.2_process_map.png"),
    ])
    return


@app.cell(hide_code=True)
def _(df_fine, mo):
    # Task 4.1.2: directly-follows relations of the fine object sub-log in Python,
    # to back the numbers we read off the Disco process map
    _f = df_fine[['case:concept:name', 'concept:name']].copy()
    _f['next_activity'] = _f.groupby('case:concept:name')['concept:name'].shift(-1).fillna('[end]')
    dfg_fine = _f.groupby(['concept:name', 'next_activity']).size().sort_values(ascending=False)
    _dfg_table = dfg_fine.rename('frequency').reset_index().rename(columns={'concept:name': 'activity'})

    mo.vstack([
        mo.md("""
    **Directly-follows relations of the fine object sub-log, computed in
    Python** (`[end]` means that the activity is the last event of the
    case). The frequencies are the same as on the Disco process map above:
    """),
        mo.ui.table(_dfg_table),
    ])
    return (dfg_fine,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 4.1.2a: Unexpected observations
    """)
    return


@app.cell(hide_code=True)
def _(dfg_fine, mo):
    mo.md(f"""
    Three observations that were unexpected for us and that we would investigate further:

    1. **`Payment` is directly followed by `Add penalty` {dfg_fine[('Payment', 'Add penalty')]:,} times.** A
       penalty for not paying is added even though there was a payment
       right before. We would expect the opposite: a payment should
       prevent the penalty. We would check if the system adds the penalty
       without looking at payments, or if these payments didn't cover the
       full amount, so that the penalty is still added.
    2. **`Payment` is directly followed by another `Payment` {dfg_fine[('Payment', 'Payment')]:,} times**
       (the self-loop on `Payment`). So some cases have several payments
       in a row. We would check if these are installments or duplicate /
       wrong payment entries, because normally one payment should be
       enough if the fine is paid in full.
    3. **`Add penalty` is directly followed by the end of the case {dfg_fine[('Add penalty', '[end]')]:,}
       times** (the dashed arrow from `Add penalty` to the end). These
       cases get a penalty and then stop, without `Payment` or
       `Send for Credit Collection` in this sub-log. So the fine is neither
       paid nor sent to collection. We would check if these cases were
       still open when the log ended, or if they continue with an appeal
       activity that we filtered out in this sub-log.
    """)
    return


@app.cell(hide_code=True)
def _(df_fine, df_task5, mo):
    # Task 4.1.2a: check observation 1 (Payment directly followed by Add penalty) in Python
    _f = df_fine.copy()
    # df_fine keeps the event index of the full log, so the outstanding amount
    # from Task 2.2.5 can be looked up per event
    _f['outstanding_amount'] = df_task5.loc[_f.index, 'outstanding_amount']
    _f['prev_activity'] = _f.groupby('case:concept:name')['concept:name'].shift(1)
    _f['prev_outstanding'] = _f.groupby('case:concept:name')['outstanding_amount'].shift(1)
    _f['prev_timestamp'] = _f.groupby('case:concept:name')['time:timestamp'].shift(1)

    _penalty_after_payment = _f[(_f['concept:name'] == 'Add penalty') & (_f['prev_activity'] == 'Payment')]
    _n = len(_penalty_after_payment)

    # were these payments made after the notification, i.e. within the deadline?
    _notification_ts = _f[_f['concept:name'] == 'Insert Fine Notification'].groupby('case:concept:name')['time:timestamp'].first()
    _n_after_notification = int(
        (_penalty_after_payment['prev_timestamp'].values
         >= _notification_ts.reindex(_penalty_after_payment['case:concept:name']).values).sum()
    )
    _n_fully_paid = int((_penalty_after_payment['prev_outstanding'] <= 0).sum())
    _remaining = _penalty_after_payment.loc[_penalty_after_payment['prev_outstanding'] > 0, 'prev_outstanding']

    _n_notified = int((_f['concept:name'] == 'Insert Fine Notification').sum())
    _n_penalized = int((_f['concept:name'] == 'Add penalty').sum())

    # observation 3: the cases that end with Add penalty in the sub-log, do they
    # continue with one of the appeal activities that we filtered out?
    _last_in_sub = _f.groupby('case:concept:name').tail(1)
    _end_penalty = _last_in_sub.loc[_last_in_sub['concept:name'] == 'Add penalty', 'case:concept:name']
    _full = df_task5[df_task5['case:concept:name'].isin(_end_penalty)]
    _appeal_rows = ~_full['concept:name'].isin(df_fine['concept:name'].unique())
    _n_with_appeal = _full.loc[_appeal_rows, 'case:concept:name'].nunique()
    _n_end_dismissed = _full.loc[_full['dismissal'].isin(['#', 'G']), 'case:concept:name'].nunique()
    _last_full = _full.groupby('case:concept:name')['concept:name'].last().value_counts()

    mo.md(f"""
    **Checking observation 1 in Python:** Of the {_n:,}
    `Payment -> Add penalty` transitions, {_n_after_notification:,} come
    from payments between `Insert Fine Notification` and `Add penalty`, so
    the payment was made within the deadline. But only in
    {_n_fully_paid} of them the offender had already paid the full amount
    (`outstanding_amount` <= 0, like case `A10125` in Task 3.1c). In the
    other {len(_remaining):,} cases the payment was too low, but mostly
    only by a small amount (median {_remaining.median():g} still owed when
    the penalty was added). So in most cases the penalty is added because
    the payment didn't cover everything, which makes sense.

    What we don't understand is why so many offenders pay just a few euros
    too little. The median is almost the same as the 5.16 / 5.17 that many
    cases are overpaid by in Task 2.2.5b. So maybe the `expense` in the log
    is not always the amount the offender was asked to pay. This is an
    open question for us.

    We also noticed that there are exactly as many `Add penalty` events
    ({_n_penalized:,}) as `Insert Fine Notification` events
    ({_n_notified:,}), and every notified case gets a penalty (Task 3.1c).
    Fines that are paid without a penalty never have a notification, they
    are paid directly after `Create Fine` or `Send Fine` (the
    `Create Fine -> Payment` and `Send Fine -> Payment` arrows in the
    process map).

    **Checking observation 3 in Python:** {_n_with_appeal:,} of the
    {len(_end_penalty):,} cases that end with `Add penalty` in the sub-log
    contain at least one appeal activity in the full log. In the full log
    their last activity is mostly
    {', '.join(f'`{a}` ({n:,})' for a, n in _last_full.head(2).items())}.
    {_n_end_dismissed:,} of them ({_n_end_dismissed / len(_end_penalty):.0%})
    were dismissed (`dismissal` "#" or "G"). So these fines were not just
    forgotten. The offender appealed, and in most cases the fine was
    dismissed, so there is no payment and no credit collection.
    For the other {len(_end_penalty) - _n_end_dismissed:,} cases the log
    doesn't show a result of the appeal.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 4.1.2b: A variant with unexpected behavior
    """)
    return


@app.cell(hide_code=True)
def _(df_fine, mo):
    # Task 4.1.2b: the same follower filter as in Disco, recomputed in Python
    _seqs = df_fine.groupby('case:concept:name')['concept:name'].apply(tuple)
    _has_loop = _seqs.apply(lambda s: any(a == b == 'Payment' for a, b in zip(s, s[1:])))
    _loop_variants = _seqs[_has_loop].value_counts()
    _top_variant, _top_count = _loop_variants.index[0], int(_loop_variants.iloc[0])

    mo.vstack([
        mo.md(f"""
    We used the Follower filter in Disco (`Payment` directly followed by
    `Payment`) on the fine object sub-log. This gives the {int(_has_loop.sum()):,} cases with
    the `Payment -> Payment` self-loop from the process map. Most of them
    ({_top_count:,} cases, {_top_count / _has_loop.sum():.1%}) follow this variant
    (we checked both numbers in Python):

    ```
    {' -> '.join(_top_variant)}
    ```

    So the fine is sent, notified and penalized, and only after the
    penalty there are two separate payments in a row. Case `A10009` (see
    the screenshots below) is an example of this variant:
    """),
        mo.image(src="screenshots/task_4.1.2b_case_A10009_part1.png"),
        mo.image(src="screenshots/task_4.1.2b_case_A10009_part2.png"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Task 4.1.2c: Explanation for the unexpected behavior
    """)
    return


@app.cell(hide_code=True)
def _(calendar_days, df, df_fine, mo):
    # Task 4.1.2c: inspect case A10009 (the example of the variant from 4.1.2b) and explain the unexpected behavior
    _cols = ['time:timestamp', 'concept:name', 'amount', 'expense', 'paymentAmount', 'totalPaymentAmount']
    _case = df.loc[df['case:concept:name'] == 'A10009', _cols].sort_values('time:timestamp', kind='stable').reset_index(drop=True)

    def _value(activity, col):
        return _case.loc[_case['concept:name'] == activity, col].iloc[0]

    _base_amount = _value('Create Fine', 'amount')
    _penalized_amount = _value('Add penalty', 'amount')
    _expense = _case['expense'].sum()
    _payment_1, _payment_2 = _case.loc[_case['concept:name'] == 'Payment', 'paymentAmount'].tolist()
    _payment_dates = _case.loc[_case['concept:name'] == 'Payment', 'time:timestamp'].tolist()
    _penalty_date = _value('Add penalty', 'time:timestamp')
    _days_to_penalty = calendar_days(_value('Insert Fine Notification', 'time:timestamp'), _penalty_date)

    # does the same pattern hold for the other cases of this variant (fine object sub-log)?
    _variant = ('Create Fine', 'Send Fine', 'Insert Fine Notification', 'Add penalty', 'Payment', 'Payment')
    _seqs = df_fine.groupby('case:concept:name')['concept:name'].apply(tuple)
    _sub = df_fine[df_fine['case:concept:name'].isin(_seqs[_seqs == _variant].index)]

    def _per_case(activity, col):
        return _sub[_sub['concept:name'] == activity].groupby('case:concept:name')[col].first()

    _init = _per_case('Create Fine', 'amount')
    _pen = _per_case('Add penalty', 'amount')
    _exp = _sub.groupby('case:concept:name')['expense'].sum()
    _pays = _sub[_sub['concept:name'] == 'Payment'].groupby('case:concept:name')['paymentAmount']
    _share_first = ((_pays.first() - (_init + _exp)).abs() < 0.01).mean()
    _share_second = ((_pays.last() - (_pen - _init)).abs() < 0.01).mean()
    _median_days = calendar_days(_per_case('Insert Fine Notification', 'time:timestamp'), _per_case('Add penalty', 'time:timestamp')).median()

    mo.vstack([
        mo.md("**Case `A10009`:**"),
        mo.ui.table(_case),
        mo.md(f"""
    **Our explanation for the two payments:**

    When we looked at the amounts, we noticed that they fit exactly:
    - `{_base_amount:.0f}` (base fine) `+ {_expense:.0f}` (`expense`)
      `= {_base_amount + _expense:.0f}`, which is the first `paymentAmount`
      ({_payment_1:.0f}).
    - `{_penalized_amount:.0f}` (penalized `amount`) `- {_base_amount:.0f}`
      (base fine) `= {_penalized_amount - _base_amount:.0f}`, which is the
      second `paymentAmount` ({_payment_2:.0f}).

    So with the first payment, the offender paid the amount from the
    original fine notice (base fine plus expense), before the penalty.
    `Add penalty` happens on {_penalty_date:%Y-%m-%d}, {_days_to_penalty}
    days after the notification (the payment deadline), but the first
    payment only comes on {_payment_dates[0]:%Y-%m-%d}, when the penalty
    was already added. So the offender paid
    {calendar_days(_penalty_date, _payment_dates[0])} days too late and the amount
    was not correct anymore. The second payment on
    {_payment_dates[1]:%Y-%m-%d} is exactly the extra amount from the
    penalty.

    In Task 4.1.2a we thought the double payments could be duplicate or
    wrong entries. But now we think it is not a data quality problem. It
    looks like the offender first paid the amount from the original
    notice and then paid the rest after finding out about the penalty.

    **Is A10009 a typical case?** We checked all
    {_sub['case:concept:name'].nunique():,} cases of this variant in the
    fine object sub-log. In {_share_first:.0%} of them the first payment
    is base fine + expense, and in {_share_second:.0%} the second payment
    is exactly the penalty amount. The median time between notification
    and penalty is {_median_days:.0f} days. So our explanation works for
    most cases of this variant and not just for A10009. To improve the
    process, offenders could be informed about the new amount as soon as
    the penalty is added, so they don't pay an old amount.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 4.2
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # Task 4.2.3: BPMN workflow graph of how the fine object *should* behave (bpmn/fine_object.bpmn, made with bpmn.io)
    mo.vstack([
        mo.md("**Task 4.2.3, BPMN workflow graph for the fine object (`bpmn/fine_object.bpmn`):**"),
        mo.image(src="bpmn/fine_object.svg"),
        mo.md(r"""
    We built the model in bpmn.io, starting from the Canvas template
    (`bpmn/Fine-Object-Template.bpmn`), so the 6 activities have the same
    names and IDs as in the template. The model shows how we currently
    think the fine *should* go through the process. Each of the 6
    activities appears exactly once as a task:

    - Every case starts with `Create Fine`. If the offender pays directly
      (on the spot), the fine goes to `Payment`. This is variant 2 from
      Task 4.1.1b (`Create Fine -> Payment`).
    - Otherwise the fine is sent (`Send Fine`) and the offender is
      notified (`Insert Fine Notification`). If they pay within the
      deadline, the fine goes to `Payment` without a penalty. This is how
      we think the process *should* work, but it never happens in the log:
      every notified case gets `Add penalty`, even if it was already paid
      on time (Tasks 3.1c and 4.1.2a). We still kept this branch, because
      we think penalizing on-time payments is a problem of the process (or
      of the logging) and not how it is supposed to work.
    - If they don't pay in time, `Add penalty` increases the amount (the
      late-payment penalty from Task 2.1.2b). Then the offender either
      pays the penalized amount, or the fine is sent to
      `Send for Credit Collection`. In that case the fine object ends
      without a payment (variant 1 from Task 4.1.1b).
    - `Payment` can be repeated as long as the fine is not fully paid,
      because we think paying in installments should be allowed as long as
      the full amount is paid in the end (like in case `A10009` from Task
      4.1.2c). The three "paid" branches are merged with one XOR join, and
      the installment loop has its own XOR join before `Payment`, so the
      loop is a clean block.
    - The only way out of the loop is "Fully paid? yes". So we assume that
      once an offender starts paying, they pay the full amount in the end.

    The model should be a workflow graph: one start event, one end event,
    only XOR gateways (each one either a split or a join), every task with
    exactly one incoming and one outgoing flow, and every node on a path
    from start to end. We check these properties in the cell below. Since
    we only use XOR gateways, there is never more than one token, so there
    can't be a lack of synchronization. And because there is no AND join,
    there also can't be a deadlock, so the model should be **sound**. To be
    sure, the cell below also converts the BPMN file into a Petri net with
    pm4py and runs the Woflan soundness check.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo, pd, pm4py):
    # Task 4.2.3: check the structure of the BPMN model, then verify soundness
    # (BPMN -> Petri net -> Woflan)
    from pm4py.objects.bpmn.obj import BPMN as _BPMN

    _bpmn = pm4py.read_bpmn('bpmn/fine_object.bpmn')
    _template = pm4py.read_bpmn('bpmn/Fine-Object-Template.bpmn')
    _nodes = list(_bpmn.get_nodes())

    # 1. same tasks (IDs and names) as the Canvas template, each exactly once
    _tasks = {n.get_id(): n.get_name() for n in _nodes if isinstance(n, _BPMN.Task)}
    _template_tasks = {n.get_id(): n.get_name() for n in _template.get_nodes() if isinstance(n, _BPMN.Task)}
    _task_names = [n.get_name() for n in _nodes if isinstance(n, _BPMN.Task)]

    # 2. workflow graph properties
    _starts = [n for n in _nodes if isinstance(n, _BPMN.StartEvent)]
    _ends = [n for n in _nodes if isinstance(n, _BPMN.EndEvent)]
    _gateways = [n for n in _nodes if isinstance(n, _BPMN.Gateway)]
    _only_xor = all(isinstance(g, _BPMN.ExclusiveGateway) for g in _gateways)
    _split_or_join = all(
        (len(g.get_in_arcs()) == 1) != (len(g.get_out_arcs()) == 1) for g in _gateways
    )
    _tasks_one_in_one_out = all(
        len(n.get_in_arcs()) == 1 and len(n.get_out_arcs()) == 1 for n in _nodes if isinstance(n, _BPMN.Task)
    )

    # 3. every node lies on a path from start to end (reachable from start, can reach end)
    _succ = {n: [] for n in _nodes}
    _pred = {n: [] for n in _nodes}
    for _flow in _bpmn.get_flows():
        _succ[_flow.get_source()].append(_flow.get_target())
        _pred[_flow.get_target()].append(_flow.get_source())

    def _reachable(start, neighbours):
        _seen, _stack = {start}, [start]
        while _stack:
            for _next in neighbours[_stack.pop()]:
                if _next not in _seen:
                    _seen.add(_next)
                    _stack.append(_next)
        return _seen

    _on_path = (len(_starts) == 1 and len(_ends) == 1
                and _reachable(_starts[0], _succ) == set(_nodes)
                and _reachable(_ends[0], _pred) == set(_nodes))

    _checks = pd.DataFrame([
        {'check': 'tasks have the same IDs and names as in the template', 'result': _tasks == _template_tasks},
        {'check': 'each task occurs exactly once', 'result': len(_task_names) == len(set(_task_names))},
        {'check': 'exactly one start event and one end event', 'result': len(_starts) == 1 and len(_ends) == 1},
        {'check': 'only XOR gateways', 'result': _only_xor},
        {'check': 'every gateway is either a split or a join', 'result': _split_or_join},
        {'check': 'every task has exactly one incoming and one outgoing flow', 'result': _tasks_one_in_one_out},
        {'check': 'every node lies on a path from start to end', 'result': _on_path},
    ])

    _net, _im, _fm = pm4py.convert_to_petri_net(_bpmn)
    _is_sound = pm4py.check_soundness(_net, _im, _fm)[0]

    mo.vstack([
        mo.md(f"""
    **Structure checks on `bpmn/fine_object.bpmn`** ({len(_tasks)} tasks,
    {len(_gateways)} gateways):
    """),
        mo.ui.table(_checks),
        mo.md(f"""
    **Soundness check (pm4py, Woflan):** the converted Petri net has
    {len(_net.places)} places and {len(_net.transitions)} transitions, and
    the model is **{'sound' if _is_sound else 'NOT sound'}**.
    """),
    ])
    return


if __name__ == "__main__":
    app.run()
