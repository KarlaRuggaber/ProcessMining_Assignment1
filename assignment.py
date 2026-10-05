import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


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

    print(len(event_log_from_disk), 'events read.')
    event_log_from_disk
    return (event_log_from_disk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 1

    ## Task 1.1

    **Hypotheses, before running any code:**

    a) A single police department's log probably covers a few years,
       we'd guess 3 to 5.

    b) Only a handful of vehicle classes, e.g. car, motorbike, truck,
       so around 3 to 6 distinct values.

    c) A typical Italian parking fine costs around 40 euros, so we expect
       a median in that range, a minimum of maybe 20 to 40, and a maximum
       of a few hundred euros for serious offences.

    d) Points are only deducted for more serious offences, so we expect a
       small minority of cases. Since the points depend on the offence
       itself, they should be recorded once, at `Create Fine`.
    """)
    return


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
def _(df, mo):
    # Task 1.1 answers: every number below is computed here from the event log
    _ts = df['time:timestamp']
    _ts_local = _ts.dt.tz_convert('Europe/Rome')
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

    a) The log covers the period from {_ts.min()} to {_ts.max()} (UTC),
    i.e. from {_ts_local.min():%Y-%m-%d} to {_ts_local.max():%Y-%m-%d} in
    Italian local time (cf. Task 2.1.1), roughly {_years:.1f} years. That's
    much longer than the 3 to 5 years we expected, so the process (and the
    tariffs) may well have changed over the observed period.

    b) vehicleClass has {len(_vc_values)} distinct values:
    {', '.join(_vc_values)}, within our expected range. {_vc_missing:,}
    events don't have a value for this attribute, because it is only
    recorded at {', '.join(f'`{a}`' for a in _vc_activities)}. The meaning
    of the codes isn't documented, though, so we can only guess which
    letter stands for which kind of vehicle.

    c) For the initial `amount` of each case (at its Create Fine event):
    min {_initial.min():g}, median {_initial.median():g}, max {_initial.max():g}.
    The median is about what we expected, but both the minimum and the
    maximum surprised us.

    The distribution is heavily right-skewed: the max is
    {_initial.max() / _initial.median():.0f} times the median, so there are
    clearly some extreme outliers in there. It would be worth digging into
    which cases end up with such high fines, maybe certain vehicle classes,
    violation types, or time periods stand out, and checking whether the
    {_n_zero_fines} zero-amount fines are a data quality issue or an actual
    case type of their own.

    d) There are {len(_points):,} events with a points value greater than
    0, and all of them are tied to
    {', '.join(f'`{a}`' for a in _points_activities)}. That number matches
    the number of affected cases ({_n_points_cases:,}) exactly, so each case
    that gets points, gets them exactly once, right when the fine is
    created. With only {_n_points_cases / _n_cases:.1%} of the
    {_n_cases:,} cases, this confirms our hypothesis that points are rare.
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
    seconds = sorted(int(v) for v in df['time:timestamp'].dt.second.unique())
    minutes = sorted(int(v) for v in df['time:timestamp'].dt.minute.unique())
    hours   = sorted(int(v) for v in df['time:timestamp'].dt.hour.unique())
    # converted to Italian local time (CET/CEST), what hours remain?
    _local = df['time:timestamp'].dt.tz_convert('Europe/Rome')
    _local_hours = sorted(int(v) for v in _local.dt.hour.unique())
    _example_utc = df['time:timestamp'].iloc[0]

    mo.md(f"""
    **Checking the timestamp granularity:**
    - Distinct second values: `{seconds}`
    - Distinct minute values: `{minutes}`
    - Distinct hour values:   `{hours}`
    - Distinct hour values after converting to Italian local time: `{_local_hours}`

    Seconds and minutes are always 0, and only two hour values ever show up
    ({hours}). Converted to Italian local time, every single timestamp is
    at hour {', '.join(str(h) for h in _local_hours)}, i.e. midnight: the log was recorded in local
    time and shifted to UTC depending on whether daylight saving was
    active (00:00 CET becomes 23:00 UTC, 00:00 CEST becomes 22:00 UTC). So in
    practice the timestamps only carry **day-level granularity**: every event
    is dated to a specific calendar day, nothing more precise than that.
    One side effect: since the log stores UTC, every date shown in this
    notebook is one day *earlier* than the actual Italian date (e.g. the
    first event of the log is stored as `{_example_utc}`, but really
    happened on {_local.iloc[0]:%Y-%m-%d}).
    Another one: events of the same case on the same day can't be ordered
    reliably, which causes problems later on (cf. Task 2.2.4b). For the
    data collection, we'd suggest recording full timestamps in local time.
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
    Only {len(_incomplete_df)} activity schema turns out to be incomplete:
    {', '.join(f"`{r.activity}`'s `{r.attribute}` attribute is missing for {r.missing:,} out of {r.events_of_activity:,} events" for r in _incomplete_df.itertuples())}.
    Every other local attribute, for every other activity, is complete,
    filled for 100% of that activity's events (cf. the full schema table
    above). On top of that, the meaning of `lastSent` isn't documented at
    all (the attribute description just says "N/A"), so it should be
    documented or dropped.
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
    Out of {len(_attribute_cols)} non-mandatory attributes:
    - **Global**, filled for all {_n_activities} activities and therefore not really local: `{_global_attrs}`.
    - **Shared**, local to more than one activity but not all of them: {len(_shared_attrs)} attributes.
    - **Exclusive**, local to exactly one activity: {len(_exclusive_attrs)} attributes.
    """),
        mo.ui.table(_shared_df),
        mo.md(f"""
    **Are the numerical shared attributes cumulative or incremental?**

    - `amount` (shows up at `Create Fine` and `Add penalty`) turns out to be
      **case-cumulative**. We checked all {len(_amount_check):,} cases that
      have both events: `amount` goes up from `Create Fine` to `Add penalty`
      in {_n_up:,} of them, stays the same in {_n_same}, and goes down in
      exactly {_n_down}. On average it grows by a factor of
      {_amount_ratio.mean():.2f}
      (median {_amount_ratio.median():.2f}). That lines up with the statutory
      late-payment penalty roughly doubling the fine. So it's not really a
      running sum of increments, it's a recalculated total that never goes
      down within a case, which is exactly what makes it case-cumulative
      rather than a standalone value.
    - `totalPaymentAmount` (shows up at `Create Fine` and `Payment`) is also
      **case-cumulative**, and here the check is even more direct: across
      all {len(_pay):,} `Payment` events, `totalPaymentAmount` matches
      `cumsum(paymentAmount)` within the same case for {_pay_match_rate:.1%}
      of them. The few deviations come from same-day payments and from
      payments that were apparently counted twice, see Task 2.2.4b. So
      apart from those, this one really is a running sum of payments made
      so far.
    - `org:resource` and `dismissal` are shared too, but they're categorical,
      not numerical, so the cumulative/incremental question doesn't apply to
      them.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(df, mo):
    # 2.1.3 case inspection: select a case with more than three events
    selected_case_id = 'A10000'
    case_events = df[df['case:concept:name'] == selected_case_id].sort_values('time:timestamp').copy()
    case_events['days_since_previous_event'] = case_events['time:timestamp'].diff().dt.days

    display_cols = [
        'time:timestamp', 'days_since_previous_event', 'concept:name', 'amount', 'totalPaymentAmount',
        'paymentAmount', 'expense', 'article', 'vehicleClass', 'points',
        'notificationType', 'lastSent', 'dismissal', 'org:resource',
    ]

    _gap = dict(zip(case_events['concept:name'], case_events['days_since_previous_event']))
    _total_days = (case_events['time:timestamp'].max() - case_events['time:timestamp'].min()).days

    mo.vstack([
        mo.md(f"**Case `{selected_case_id}`** ({len(case_events)} events):"),
        mo.ui.table(case_events[display_cols].reset_index(drop=True)),
        mo.md(f"""
    **Going through the case event by event** (dates as stored in the log,
    i.e. UTC, cf. Task 2.1.1; the values are the ones in the table above):

    - **2007-03-08, `Create Fine`**: the fine gets created with a base
      `amount` of 36, and `totalPaymentAmount` starts at 0. The violation
      is `article` 157 (stopping and parking), committed with a vehicle of
      `vehicleClass` A, and it costs 0 `points`, so it's a minor offence.
      Employee `org:resource` 561 created the fine, and `dismissal` is
      initialized to "NIL", meaning the fine hasn't been dismissed.
    - **2007-07-16, `Send Fine`** ({_gap['Send Fine']:.0f} days later): the
      fine notice goes out to the offender, with an `expense` of 13
      recorded for sending it.
    - **2007-08-01, `Insert Fine Notification`** ({_gap['Insert Fine Notification']:.0f}
      days after sending): the offender receives the notification.
      `notificationType` is "P", so the fine refers to the car owner, and
      `lastSent` is "P" too (its meaning isn't documented).
    - **2007-09-30, `Add penalty`** ({_gap['Add penalty']:.0f} days after the
      notification, which is the payment deadline under Italian law): a
      penalty kicks in and `amount` jumps from 36 to 74, the new
      case-cumulative total owed.
    - **2008-09-08, `Payment`** ({_gap['Payment']:.0f} days later): a
      payment of 87 comes in, `totalPaymentAmount` updates to 87 too.
      That's exactly the penalized amount plus the sending expense
      (74 + 13), so the case is settled.

    Only `Create Fine` carries a resource here; none of the later events
    record which employee handled them.

    All in all the case stretches over {_total_days} days from creation to
    payment, with long gaps between events. The payment only shows up
    well after the penalty was added: a fine that drags on, escalates
    once, and eventually gets paid off.
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
def _(df, mo):
    # Task 2.2.4: event enrichment: cumulative sum of payment amounts per case
    # Use a stable sort so that events tied on the same calendar day (the log
    # only has day-level granularity, cf. Task 2.1.1) keep their original,
    # correct relative order instead of being reshuffled by an unstable sort.
    df_task4 = df.sort_values(['case:concept:name', 'time:timestamp'], kind='stable').copy()

    # cumsum() and ffill() must each be grouped by case individually: chaining
    # them in one groupby call would let ffill() leak values across case
    # boundaries and carry the last payment total of one case into the next.
    df_task4['payment_cumsum'] = df_task4.groupby('case:concept:name')['paymentAmount'].cumsum()
    df_task4['payment_cumsum'] = df_task4.groupby('case:concept:name')['payment_cumsum'].ffill()
    df_task4['payment_cumsum'] = df_task4['payment_cumsum'].fillna(0)

    mo.md("""
    **Enrichment `payment_cumsum`:** for every event, this is the running
    total of `paymentAmount` across all earlier (and the current) events of
    that case. `cumsum()` builds the running total at each `Payment` event,
    `ffill()` carries it forward to the events that aren't payments
    themselves, and `fillna(0)` sets it to 0 before any payment has happened
    yet. Basically the `col::sum` sequential-aggregation pattern from the
    lecture.
    """)
    return (df_task4,)


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
    This case has two `Payment` events, {_payments[0]:.0f} and {_payments[1]:.0f}.
    Before either payment happens, `payment_cumsum` sits at 0. After the
    first one it's {_payments[0]:.0f}, and after the second it's
    {sum(_payments):.0f}, matching `totalPaymentAmount` at every step. So the
    enrichment does what it's supposed to.
    """),
    ])
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

    mo.vstack([
        mo.md(f"""
    We compared `payment_cumsum` to `totalPaymentAmount` at the
    {len(_comparable):,} events where `totalPaymentAmount` is actually
    defined (`Create Fine` and `Payment`). They agree in
    {(1 - len(_mismatch) / len(_comparable)):.3%} of these events, leaving
    {len(_mismatch)} deviating events ({len(_mismatch) / len(_comparable):.3%}).
    {'All' if _all_at_payment else 'Not all'} of these happen at a `Payment` event,
    and {'in every single one' if _all_smaller else 'not in every one'},
    `payment_cumsum` is *smaller* than `totalPaymentAmount`, by
    {_mismatch['deviation'].abs().mean():.1f} on average and up to
    {_mismatch['deviation'].abs().max():.1f}.

    The deviating events belong to {len(_dev_cases)} cases, which fall into
    two groups.
    """),
        mo.md(f"""
    **1. Two payments on the same day ({len(_same_day_dev)} cases),** e.g.
    case `{_same_day_dev[0]}`:
    """),
        mo.ui.table(_ex_same_day),
        mo.md("""
    The two `Payment` events share a calendar day, so at day-level
    granularity the log can't say which came first. `totalPaymentAmount`
    already shows the total after *both* payments on the first of the two
    rows, while `payment_cumsum` only adds up the payments up to that row.
    """),
        mo.md(f"""
    **2. A payment counted twice in `totalPaymentAmount` ({len(_other_dev)} cases),** e.g.
    case `{_other_dev[0]}`:
    """),
        mo.ui.table(_ex_other),
        mo.md(f"""
    Here `totalPaymentAmount` goes up by *more* than the `paymentAmount` of
    the event itself. At first sight this could mean that some payments
    were never logged as `Payment` events. But in this case the first
    payment is {_ex_first_payment['paymentAmount']:g}, while
    `totalPaymentAmount` already jumps to
    {_ex_first_payment['totalPaymentAmount']:g}
    ({_ex_first_payment['totalPaymentAmount'] / _ex_first_payment['paymentAmount']:g} times
    the payment). And the logged payments add up to
    {_ex_other['paymentAmount'].sum():g}, the same as the full amount owed
    ({_ex_owed:g}, penalized fine plus expense), so no payment is missing
    here. Across the group, the surplus
    in `totalPaymentAmount` equals one of the logged payments of the same
    case in {_n_double_counted} of {len(_other_dev)} cases. So the system
    most likely **counted a logged payment twice** when computing
    `totalPaymentAmount`, rather than missing payments.

    Either way, `totalPaymentAmount` isn't fully reliable as a running sum
    of the logged payments. That's a good reminder of why the lecture says
    to verify a pre-existing attribute instead of just trusting it. For
    the data collection, we'd suggest deriving `totalPaymentAmount` from
    the `Payment` events instead of storing it separately.
    """),
    ])
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

    # round to cents: amounts like 33.6 or 31.3 leave float residues such as
    # 1e-14 that would otherwise be counted as > 0 or < 0 (cf. lecture slide
    # on floating point imprecision for money)
    _unrounded = df_task5['amount_due_so_far'] + df_task5['expense_so_far'] - df_task5['payment_cumsum']
    df_task5['outstanding_amount'] = _unrounded.round(2)
    # how many events would be misclassified as owing/overpaid without rounding?
    _residues = _unrounded[(_unrounded != 0) & (df_task5['outstanding_amount'] == 0)]
    _n_float_residues = len(_residues)

    mo.md(f"""
    **Enrichment `outstanding_amount`:** for every event, how much the
    offender still has to pay at that point, built up from three
    preliminary event enrichments:
    - `amount_due_so_far`, the latest known `amount` in the case
      (`ffill()` of `amount`, which already holds the base fine or, once a
      penalty gets added, the higher penalized amount).
    - `expense_so_far`, the running total of `expense` in the case so far
      (same `cumsum()` + `ffill()` + `fillna(0)` pattern as `payment_cumsum`).
    - `payment_cumsum`, the running total of payments so far, already built
      in Task 2.2.4.

    Put together: `outstanding_amount = amount_due_so_far + expense_so_far - payment_cumsum`,
    rounded to 2 decimals. Without the rounding, floating point leftovers
    (tiny values instead of exactly 0) would wrongly count as "still owed"
    or "overpaid" (the lecture's warning about floats and money). That's
    not just theoretical: {_n_float_residues:,} events in this log have
    such a leftover (the largest one is `{_residues.abs().max():.0e}`), and
    the rounding sets them back to exactly 0.
    """)
    return (df_task5,)


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
    `outstanding_amount` starts out at the base fine amount, climbs once the
    sending `expense` and then the penalty are added, drops with the first
    partial payment, and lands exactly on 0 once the second payment fully
    covers the penalized amount plus expenses. Exactly what we'd expect.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(df_task5, mo):
    # Task 2.2.5b: number of events with outstanding_amount > 0
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

    mo.md(f"""
    **Events with `outstanding_amount` > 0:** {_n_positive:,} out of
    {_n_total:,} ({_n_positive / _n_total:.1%}).

    The remaining {_n_total - _n_positive:,} events aren't just "everything
    else", they split into two different groups:
    - **Exactly 0:** {_n_zero:,} events ({_n_zero / _n_total:.1%}). Mostly
      ({_n_zero_payment:,}) `Payment` events where that payment fully settles
      the case, plus {_n_zero_create_fine:,} `Create Fine` events where the
      fine itself is 0 (the zero-amount fines from Task 1.1c), plus
      {_n_zero - _n_zero_payment - _n_zero_create_fine} other events in
      cases that are already settled at that point.
    - **Negative:** {_n_negative:,} events ({_n_negative / _n_total:.1%}),
      meaning the case looks overpaid at that point. They belong to
      {len(_neg_cases):,} cases, and {len(_final_neg):,} of these are still
      negative at their last event, so this isn't a temporary effect of
      how same-day events are ordered. According to the logged payments,
      these offenders paid more than the fine plus expenses, mostly by a
      small amount (median overpayment {-_final_neg.median():g}). Either
      they really overpaid, or some amount owed (e.g. an extra expense)
      isn't recorded in the log. Another question for the data providers.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 2.3
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
    Here's the **case log**, built by aggregating the event log per case
    ({len(case_log):,} cases in total). On top of `start_time`, `end_time`
    and `no_of_events`, it includes every **case attribute**, meaning an
    attribute with at most one distinct non-null value per case. We found
    these by checking
    `event_log.groupby(case_id)[attr].nunique().max() <= 1` for each
    non-mandatory attribute, which gives: `{_case_attr_cols}`.

    New enrichment: **`initial_fine_amount`**, the first non-null value of
    `amount` per case. This is the same as the `amount` at the case's
    `Create Fine` event, because {'every' if _all_start_with_create_fine else 'NOT every'}
    case starts with `Create Fine` (we checked the first event of all
    {len(case_log):,} cases). While we're at it, we also
    add `final_fine_amount` (last non-null value of `amount`) the same way,
    since it's needed again in Task 2.3.6 below.
    """),
        mo.ui.table(case_log.reset_index().head(20)),
    ])
    return (case_log,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Task 2.3.5a, hypothesis about the distribution of `initial_fine_amount`:**

    Italian traffic fines follow a statutory tariff schedule tied to the
    specific violation (the `article` of the traffic code that was broken),
    they're not set freely case by case. Our hypothesis is that
    `initial_fine_amount` won't look like a smooth, continuous distribution
    at all, but a **discrete, multimodal** one: a handful of standard tariff
    amounts should show up over and over, sharp spikes at those exact
    values, on top of a right-skewed shape with a long tail of rarer,
    bigger fines for more serious violations. That would also fit the
    min/median/max we already saw in Task 1.1c (0 / 35 / 4,351).
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
    # (article 157) at different points in time? Most frequent amount per year,
    # with the year taken in Italian local time (the log stores UTC, cf. Task 2.1.1)
    _art157 = case_log[case_log['article'] == 157]
    _art157_year = _art157['start_time'].dt.tz_convert('Europe/Rome').dt.year
    _tariff_by_year = _art157.groupby(_art157_year)['initial_fine_amount'] \
                             .agg(most_frequent_amount=lambda s: s.mode().iloc[0], no_of_cases='count') \
                             .rename_axis('year').reset_index()
    _top_cases = case_log[case_log['initial_fine_amount'].isin(_top_values.index)]
    _top_art157_share = (_top_cases['article'] == 157).mean()

    mo.vstack([
        mo.ui.plotly(_fig),
        mo.ui.plotly(_fig_zoom),
        mo.md(f"""
    The first chart shows the full range, but there the individual amounts
    can't be told apart: {_share_20_to_40:.1%} of all cases have an amount
    between 20 and 40, so they're squeezed into the leftmost bars. The
    second chart zooms in on the amounts up to {_zoom_max}
    ({_zoom_share:.1%} of all cases) and shows every exact amount as its
    own bar.

    **Two things stand out here**, and both confirm the hypothesis above:
    1. The distribution really is **discrete and spiky**, not continuous
       (see the zoomed chart). The 5 most common exact amounts
       ({', '.join(f'{a:g} ({n:,} cases)' for a, n in _top_values.items())})
       alone cover {_top_share:.1%} of all {len(case_log):,} cases.
       Surprisingly, these five amounts are mostly not different
       violations, but the same violation at different points in time:
       {_top_art157_share:.1%} of the cases behind them are `article` 157
       (stopping and parking), whose tariff gets raised every year or two
       (table below), from {_tariff_by_year['most_frequent_amount'].iloc[0]:g}
       in {_tariff_by_year['year'].iloc[0]} up to
       {_tariff_by_year['most_frequent_amount'].iloc[-1]:g} in {_tariff_by_year['year'].iloc[-1]}.
       For the data collection, we'd suggest recording which tariff
       version applied to a fine, since the same violation otherwise looks
       like different amounts.
    2. It's also **strongly right-skewed**, with a long tail. The mean
       ({case_log['initial_fine_amount'].mean():.1f}) sits well above the
       median ({case_log['initial_fine_amount'].median():.1f}), because of a
       thin trail of large fines reaching all the way up to
       {case_log['initial_fine_amount'].max():,.0f}. You can see that in the
       first histogram as a sparse scatter of bars far to the right of the
       main mass.
    """),
        mo.md("**Most frequent initial fine amount for `article` 157, per year:**"),
        mo.ui.table(_tariff_by_year),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Task 2.3.6, hypothesis:** since `amount` never goes down within a case
    (Task 2.1.2b), we expect `final_fine_amount` to be either equal to
    `initial_fine_amount` (no penalty was added) or about twice as high
    (late-payment penalty), and never lower.
    """)
    return


@app.cell(hide_code=True)
def _(case_log, mo, px):
    # Task 2.3.6: relate initial_fine_amount and final_fine_amount per case
    _fig = px.scatter(
        case_log, x='initial_fine_amount', y='final_fine_amount',
        opacity=0.15, title='Final vs. initial fine amount per case',
    )
    # diagonal reference line must span the actual data range (final_fine_amount
    # goes well beyond initial_fine_amount's max) or it would visibly stop
    # short of the top of the chart
    _axis_max = max(case_log['initial_fine_amount'].max(), case_log['final_fine_amount'].max())
    _fig.add_shape(type='line', x0=0, y0=0, x1=_axis_max, y1=_axis_max, line=dict(color='gray', dash='dot'))

    _no_penalty_share = (case_log['final_fine_amount'] == case_log['initial_fine_amount']).mean()
    _penalty_share = (case_log['final_fine_amount'] > case_log['initial_fine_amount']).mean()
    _below_share = (case_log['final_fine_amount'] < case_log['initial_fine_amount']).mean()

    # cases clearly above the doubling line (zero-amount fines have no defined ratio)
    _ratio = (case_log['final_fine_amount'] / case_log['initial_fine_amount']) \
                 .replace([float('inf')], float('nan'))
    _n_high_ratio = int((_ratio > 2.5).sum())

    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(f"""
    The scatter shows two clearly separated clusters, both on or above the
    dotted diagonal where `final = initial`:
    - **{_no_penalty_share:.1%} of cases** land exactly **on the diagonal**,
      meaning `final_fine_amount` equals `initial_fine_amount`. No penalty
      was ever added.
    - **{_penalty_share:.1%} of cases** sit on a second line clearly
      **above** the diagonal, at roughly double the initial amount. That
      matches the statutory late-payment penalty we found in Task 2.1.2b.
    - **No case falls below the diagonal** ({_below_share:.1%}). The fine
      amount never goes down within a case, which fits with `amount` being
      case-cumulative (Task 2.1.2b).

    So the hypothesis holds. Only {_n_high_ratio} cases sit even further
    above the doubling line (final amount more than 2.5 times the initial
    one, up to {_ratio.max():.1f} times), i.e. cases with an apparently
    higher penalty multiplier. Might be worth a closer look if you want to
    chase outliers further.
    """),
    ])
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
        mo.md("**Distribution of `article` (the traffic-code article that was violated), top 3:**"),
        mo.ui.table(_top3.reset_index().rename(columns={'count': 'no_of_cases'})),
        mo.ui.plotly(_fig),
        mo.md(f"""
    **Noteworthy fact:** just **3 article codes, {', '.join(f'{a:g}' for a in _top3.index)}, account
    for {_top3_share:.1%}** of all {case_log['article'].notna().sum():,} cases
    that have a recorded article, out of {case_log['article'].nunique()}
    distinct codes that occur at all. So almost all fines in this log come
    from a very small set of standard violations, while the rest of the
    articles are each individually rare. That's a pretty concentrated,
    long-tailed categorical distribution, and it echoes the same
    tariff-based concentration we already saw for `initial_fine_amount`
    above. The bar chart makes it easy to see too: a steep drop right after
    the 3 dominant codes, then a long thin tail of rare ones.
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
    **Task 3.1, defining three business-level process outcomes:**

    Looking at the activities in the log, there are three natural, business-relevant
    ways a traffic fine case can resolve, and they aren't mutually exclusive, so
    this is a good candidate for outcome overlap analysis:

    1. **Paid**: the offender settled the debt, meaning the running
       `outstanding_amount` (built in Task 2.2.5) reaches 0 or less at some
       point in the case.
    2. **Sent to credit collection**: the case was escalated to debt
       collection enforcement, i.e. the case contains a
       `Send for Credit Collection` event.
    3. **Appealed**: the offender formally contested the fine, i.e. the case
       contains at least one of the appeal-related activities
       (`Insert Date Appeal to Prefecture`, `Send Appeal to Prefecture`,
       `Receive Result Appeal from Prefecture`,
       `Notify Result Appeal to Offender`, `Appeal to Judge`).

    By common sense, these can co-occur (e.g. a case can be appealed and
    still be paid, or appealed and still sent to collection), and some cases
    might end without reaching any of them, so it's worth checking the
    overlaps and the "no outcome" bucket (Task 3.1a below) rather than
    assuming the three partition the cases cleanly.
    """)
    return


@app.cell(hide_code=True)
def _(case_log, df_task5, mo, pd):
    # Task 3.1a: enrich the case log with the three outcome indicators and
    # count cases per outcome, per pairwise combination, and with no outcome
    _appeal_activities = {
        'Insert Date Appeal to Prefecture', 'Send Appeal to Prefecture',
        'Receive Result Appeal from Prefecture', 'Notify Result Appeal to Offender',
        'Appeal to Judge',
    }

    case_log_outcomes = case_log.copy()
    case_log_outcomes['outcome_paid'] = df_task5.groupby('case:concept:name')['outstanding_amount'].apply(lambda s: (s <= 0).any())
    case_log_outcomes['outcome_credit_collection'] = df_task5.groupby('case:concept:name')['concept:name'].apply(lambda s: 'Send for Credit Collection' in set(s))
    case_log_outcomes['outcome_appealed'] = df_task5.groupby('case:concept:name')['concept:name'].apply(lambda s: len(set(s) & _appeal_activities) > 0)

    _outcomes = ['outcome_paid', 'outcome_credit_collection', 'outcome_appealed']
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

    _is_none = ~case_log_outcomes[_outcomes[0]] & ~case_log_outcomes[_outcomes[1]] & ~case_log_outcomes[_outcomes[2]]
    _n_none = int(_is_none.sum())

    # do the no-outcome cases just stop because the log ends?
    _log_end = df_task5['time:timestamp'].max()
    _n_none_ended_early = int((case_log_outcomes.loc[_is_none, 'end_time'] < _log_end - pd.Timedelta(days=365)).sum())

    # edge cases of the definitions: zero-amount fines count as "paid" without any
    # payment, and dismissed fines (dismissal other than NIL) have no outcome of their own
    _has_payment = df_task5.groupby('case:concept:name')['concept:name'].apply(lambda s: 'Payment' in set(s))
    _paid_without_payment = case_log_outcomes['outcome_paid'] & ~_has_payment
    _n_paid_without_payment = int(_paid_without_payment.sum())
    _all_zero_fines = bool((case_log_outcomes.loc[_paid_without_payment, 'initial_fine_amount'] == 0).all())
    _is_dismissed = df_task5.groupby('case:concept:name')['dismissal'].apply(lambda s: s.dropna().ne('NIL').any())
    _n_dismissed = int(_is_dismissed.sum())
    _n_none_dismissed = int((_is_none & _is_dismissed).sum())

    # at which activities do the non-NIL dismissal codes get recorded?
    _dismissal_events = df_task5[df_task5['dismissal'].notna() & (df_task5['dismissal'] != 'NIL')]
    _codes_per_activity = _dismissal_events.groupby('concept:name')['dismissal'].apply(
        lambda s: ', '.join(f'{code} ({n:,})' for code, n in s.value_counts().items())
    ).reset_index().rename(columns={'concept:name': 'activity', 'dismissal': 'dismissal codes (no. of events)'})
    _undocumented = _dismissal_events[~_dismissal_events['dismissal'].isin(['#', 'G'])]
    _n_undocumented = len(_undocumented)
    _n_codes_at_create = int((_undocumented['concept:name'] == 'Create Fine').sum())

    mo.vstack([
        mo.md("**Cases per outcome:**"),
        mo.ui.table(_single_counts),
        mo.md("**Cases per pairwise outcome combination:**"),
        mo.ui.table(_pair_counts),
        mo.md(f"""
    **Cases with none of the three outcomes:** {_n_none:,} out of {_n_total:,}
    ({_n_none / _n_total:.1%}). In these cases the fine was created and
    maybe sent, but the log never records a full payment, an escalation to
    collection or an appeal. {_n_none_ended_early:,} of them
    ({_n_none_ended_early / _n_none:.1%}) have their last event more than
    a year before the log ends ({_log_end:%Y-%m-%d}), so it's not just that
    the recording period ran out. {_n_none_dismissed:,} of them have a
    non-NIL `dismissal` code (see below). Other possible explanations are a
    payment that was never logged, or an offender who couldn't be reached
    (see Task 3.1d).

    **Two edge cases of our definitions:**
    - {_n_paid_without_payment} cases count as paid without a single
      `Payment` event. {'All of these are' if _all_zero_fines else 'Not all of these are'}
      zero-amount fines (`initial_fine_amount` = 0, cf. Task 1.1c):
      nothing is owed, so `outstanding_amount` is 0 right away. That's
      technically correct, but worth knowing.
    - {_n_dismissed:,} cases have a `dismissal` value other than "NIL" at
      some point. Where the code is documented, the fine was dismissed:
      "#" (by the prefecture) only ever shows up at
      `Send Appeal to Prefecture`, and "G" (by the judge) only at
      `Appeal to Judge` (table below). None of our three outcomes covers a
      dismissal on its own, so "dismissed" would be a natural fourth
      outcome. The undocumented codes are a different story:
      {_n_codes_at_create:,} of their {_n_undocumented:,} events are already set at
      `Create Fine`, i.e. when the fine is created, before anything could
      have been dismissed. So we can't assume they mean "dismissed" at all;
      they might as well mark a special type of fine. These codes should
      be documented.
    """),
        mo.md("**Non-NIL `dismissal` codes, per activity:**"),
        mo.ui.table(_codes_per_activity),
    ])
    return (case_log_outcomes,)


@app.cell(hide_code=True)
def _(case_log_outcomes, df_task5, mo):
    # Task 3.1b: inspect and interpret a case for each of the three outcomes
    _outcome_cols = ['outcome_paid', 'outcome_credit_collection', 'outcome_appealed']
    _cols = ['time:timestamp', 'concept:name', 'amount_due_so_far', 'expense_so_far', 'payment_cumsum', 'outstanding_amount', 'dismissal']

    def _case_table(case_id):
        _table = df_task5.loc[df_task5['case:concept:name'] == case_id, _cols].reset_index(drop=True)
        # the outcome indicators are case-level (one value per case), repeated
        # on every row here so they're visible right next to the events
        for _col in _outcome_cols:
            _table[_col] = case_log_outcomes.loc[case_id, _col]
        return _table

    _a100 = _case_table('A100').set_index('concept:name')['time:timestamp']
    _a100_days_to_collection = (_a100['Send for Credit Collection'] - _a100['Add penalty']).days

    mo.vstack([
        mo.md("**Paid: case `A10000`**"),
        mo.ui.table(_case_table('A10000')),
        mo.md("""
    This is the same case walked through in Task 2.1.3: a penalty gets
    added (36 to 74), and the single payment of 87 then covers it in full,
    `outstanding_amount` lands exactly on 0. A clean, single-payment
    resolution, which is what `outcome_paid` is meant to capture.
    """),
        mo.md("**Sent to credit collection: case `A100`**"),
        mo.ui.table(_case_table('A100')),
        mo.md(f"""
    Here the fine is created, sent, and a penalty gets added once the
    notification deadline passes, but no payment ever comes in.
    {_a100_days_to_collection} days after the penalty
    ({_a100['Send for Credit Collection']:%Y-%m-%d}), the case gets escalated to
    `Send for Credit Collection`. `outstanding_amount` just keeps climbing
    and never gets paid down, the offender simply never settled the debt.
    """),
        mo.md("**Appealed: case `A10001`**"),
        mo.ui.table(_case_table('A10001')),
        mo.md("""
    This offender contests the fine: right after the notification arrives,
    `Insert Date Appeal to Prefecture` happens, then `Send Appeal to
    Prefecture` follows a bit later (the penalty still gets added in
    between, since the appeal doesn't automatically freeze the fine
    amount). `outcome_appealed` picks this up through the appeal-related
    activities. In this case the appeal actually succeeded: the
    `Send Appeal to Prefecture` event carries `dismissal` "#", which means
    the prefecture dismissed the fine. That explains why no payment and no
    credit collection ever follow, even though `outstanding_amount` stays
    positive (the enrichment doesn't know about dismissals). One oddity:
    the "#" is recorded at the moment the appeal is *sent* to the
    prefecture, and there is no `Receive Result Appeal from Prefecture`
    event at all. So the log has the result before the appeal could have
    been decided. The `dismissal` value was probably filled in afterwards
    on the latest available event, which would be worth clarifying with
    the data providers.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(case_log_outcomes, df_task5, mo):
    # Task 3.1c: inspect and interpret a case with more than one outcome
    _multi_cases = case_log_outcomes[
        case_log_outcomes[['outcome_paid', 'outcome_credit_collection', 'outcome_appealed']].sum(axis=1) > 1
    ]
    _n_multi = len(_multi_cases)

    _outcome_cols = ['outcome_paid', 'outcome_credit_collection', 'outcome_appealed']
    _cols = ['time:timestamp', 'concept:name', 'amount_due_so_far', 'expense_so_far', 'payment_cumsum', 'outstanding_amount', 'dismissal']
    _case_id = 'A10125'
    _case_table = df_task5.loc[df_task5['case:concept:name'] == _case_id, _cols].reset_index(drop=True)
    for _col in _outcome_cols:
        _case_table[_col] = case_log_outcomes.loc[_case_id, _col]

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
    _days_to_penalty = (_first_ts['Add penalty'] - _first_ts['Insert Fine Notification']).dt.days.dropna()

    # how many "paid" cases end up owing money again by their last event?
    _last_outstanding = df_task5.groupby('case:concept:name')['outstanding_amount'].last()
    _n_paid_but_owing = int((case_log_outcomes['outcome_paid'] & (_last_outstanding > 0)).sum())

    mo.vstack([
        mo.md(f"""
    {_n_multi:,} cases have more than one outcome at once. Here's one of
    them, case `{_case_id}` (paid *and* appealed):
    """),
        mo.ui.table(_case_table),
        mo.md(f"""
    Going through it step by step:
    - The fine (36) is sent with an expense of 13 and the offender is
      notified on {_notified:%Y-%m-%d}. A few days later, they appeal to the
      prefecture (`Insert Date Appeal to Prefecture`).
    - On {_paid_on:%Y-%m-%d}, {(_paid_on - _notified).days} days after the
      notification and so **within the 60-day payment deadline**, the
      offender pays {_payment:g}. That's exactly what was owed at that
      point (36 + 13 expense), so `outstanding_amount` drops to 0.
    - Even so, on {_penalized:%Y-%m-%d}, exactly
      {(_penalized - _notified).days} days after the notification,
      `Add penalty` raises the fine to 74. Since the offender had already
      paid on time, this penalty shouldn't have been applied at all. It
      pushes `outstanding_amount` back up to {_final_outstanding:g}.
    - On the very same day, the appeal is sent to the prefecture, with
      `dismissal` "NIL". After that the case simply ends: the
      {_final_outstanding:g} are never paid, and the case is never sent
      for credit collection.

    **Why does a fine that was paid on time get penalized?** It's not just
    this case. In the whole log, of the {_n_notified:,} cases with an
    `Insert Fine Notification`, {_n_notified_and_penalized:,}
    ({_n_notified_and_penalized / _n_notified:.0%}) also have an
    `Add penalty`, always
    {_days_to_penalty.min():.0f} to {_days_to_penalty.max():.0f} days
    after the notification. So `Add penalty` seems to be recorded
    **automatically when the 60-day deadline passes, without checking
    whether the fine was already paid**. That the remaining
    {_final_outstanding:g} are never collected in this case suggests the
    authority itself didn't treat this penalty as owed. For the process,
    the penalty should only be applied if the fine is still unpaid at the
    deadline. For the data, a penalty that doesn't apply shouldn't be
    logged (or should at least be marked as cancelled), because right now
    `amount` overstates what the offender actually owes.

    So the case counts as both paid (`outstanding_amount` reached 0) and
    appealed, even though our enrichment says {_final_outstanding:g} are
    still owed at the end. It isn't alone either: {_n_paid_but_owing:,} cases flagged as
    paid end with `outstanding_amount` > 0. A good reminder that "paid"
    here means "settled at some point", not necessarily "the final state of
    the case".
    """),
    ])
    return


@app.cell(hide_code=True)
def _(case_log_outcomes, df_task5, mo):
    # Task 3.1d: inspect and interpret a case with none of the three outcomes
    _none_cases = case_log_outcomes[
        ~case_log_outcomes['outcome_paid'] & ~case_log_outcomes['outcome_credit_collection'] & ~case_log_outcomes['outcome_appealed']
    ]
    _n_none = len(_none_cases)

    _outcome_cols = ['outcome_paid', 'outcome_credit_collection', 'outcome_appealed']
    _cols = ['time:timestamp', 'concept:name', 'amount_due_so_far', 'expense_so_far', 'payment_cumsum', 'outstanding_amount', 'dismissal']
    _case_id = 'A1'
    _case_table = df_task5.loc[df_task5['case:concept:name'] == _case_id, _cols].reset_index(drop=True)
    for _col in _outcome_cols:
        _case_table[_col] = case_log_outcomes.loc[_case_id, _col]

    _log_end = df_task5['time:timestamp'].max()
    _years_before_end = (_log_end - _case_table['time:timestamp'].iloc[-1]).days / 365.25

    # how many cases have exactly this sequence of activities?
    _sequences = df_task5.groupby('case:concept:name')['concept:name'].apply(tuple)
    _case_sequence = _sequences[_case_id]
    _n_same_sequence = int((_sequences == _case_sequence).sum())

    mo.vstack([
        mo.md(f"""
    {_n_none:,} cases have none of the three outcomes. Here's one of them,
    case `{_case_id}`:
    """),
        mo.ui.table(_case_table),
        mo.md(f"""
    This case only has {len(_case_table)} events: the fine gets created,
    then it gets sent to the offender on
    {_case_table['time:timestamp'].iloc[-1]:%Y-%m-%d}, and that's it. No
    payment, no penalty, no escalation to collection, no appeal, and
    `dismissal` stays "NIL". The log runs until {_log_end:%Y-%m-%d}, so the
    case wasn't simply cut off by the end of the recording period; it just
    stops {_years_before_end:.1f} years earlier. Notably, `Insert Fine Notification` never happens, so the
    offender apparently never received the fine. That would explain why
    no penalty follows, since the payment deadline only starts with the
    notification. Possible reasons are an offender who couldn't be reached
    (e.g. a wrong address), or a payment that happened outside the system
    and was never logged. Either way, the log leaves this case unresolved.

    Case `A1` isn't an exception: {_n_same_sequence:,} cases follow exactly
    this `{' -> '.join(_case_sequence)}` pattern (variant 3 in Task 4.1.1b). An open
    question for us is whether these fines were never delivered, paid
    outside the system, or simply dropped.
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
    A **sequential variant** is the equivalence class of all cases that
    share the exact same sequence of activities. Across all {_n_cases:,}
    cases, there are **{_n_variants} distinct variants**. Here are the 10
    most frequent ones:
    """),
        mo.ui.table(_top_df),
    ])
    return (variant_counts,)


@app.cell(hide_code=True)
def _(mo, variant_counts):
    # Task 4.1.1a: minimum number of variants needed to cover 80% of the cases
    _n_cases = int(variant_counts.sum())
    _cum_share = variant_counts.cumsum() / _n_cases
    _n_needed = int((_cum_share < 0.8).sum()) + 1
    _actual_share = _cum_share.iloc[_n_needed - 1]

    mo.md(f"""
    Just **{_n_needed} variants** are needed to cover 80% of the cases: the
    top {_n_needed} variants together already account for
    {_actual_share:.1%} of all {_n_cases:,} cases. That's a steep head,
    consistent with the heavily skewed, tariff-driven nature of this
    process that we've already seen for other attributes (Task 2.3.5b,
    2.3.7): most cases funnel through just a handful of standard paths.
    This surprised us a bit, since the {len(variant_counts)} distinct
    variants suggest a much messier process than it actually is.
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, variant_counts):
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
    _v2_median_days = (_v2['last'] - _v2['first']).dt.days.median()
    _v3_end_years = _cases_of(_top4.index[2])['last'].dt.tz_convert('Europe/Rome').dt.year
    _v3_years_covered = sorted(_v3_end_years.unique())

    mo.md(f"""
    **The top 4 variants:**

    {chr(10).join(_rows)}

    In one sentence each:
    1. `{' -> '.join(_top4.index[0])}`: the fine is created, sent, formally
       notified, hit with a late-payment penalty, and finally escalated to
       credit collection without ever being paid.
    2. `{' -> '.join(_top4.index[1])}`: the fine is created and paid
       quickly (a median of {_v2_median_days:.0f} days later), without any
       of the sending or notification steps ever happening.
    3. `{' -> '.join(_top4.index[2])}`: the fine is created and sent, but
       no notification is ever recorded as received and nothing else
       happens (these cases end in {len(_v3_years_covered)} different
       years, from {_v3_years_covered[0]} to {_v3_years_covered[-1]}, so
       it's not just the end of the log, cf. Task 3.1d).
    4. `{' -> '.join(_top4.index[3])}`: the fine goes through the full
       notify-and-penalize cycle, but this time it does get paid off
       afterward, so no escalation is needed.
    """)
    return


@app.cell(hide_code=True)
def _(mo, variant_counts):
    mo.md(f"""
    **Task 4.1.1c, hypothesis:** the 5 appeal-related activities only occur in
    a small share of cases, but they can show up at many different points of
    a case, so each of them creates new variants. Without them, we expect
    the number of variants to drop sharply, to well under half of the {len(variant_counts)}.
    """)
    return


@app.cell(hide_code=True)
def _(case_log_outcomes, df, mo):
    # Task 4.1.1c: filter to the fine object sub-log, compare variant counts
    fine_activities = [
        'Create Fine', 'Send Fine', 'Insert Fine Notification', 'Add penalty',
        'Send for Credit Collection', 'Payment',
    ]
    _df_sorted = df.sort_values(['case:concept:name', 'time:timestamp'], kind='stable')
    df_fine = _df_sorted[_df_sorted['concept:name'].isin(fine_activities)].copy()

    _full_variants = _df_sorted.groupby('case:concept:name')['concept:name'].apply(tuple)
    _fine_variants = df_fine.groupby('case:concept:name')['concept:name'].apply(tuple)

    mo.md(f"""
    Filtering the event log down to just the fine object's 6 activities
    (`{fine_activities}`) keeps all {len(_fine_variants):,} cases (every
    case starts with `Create Fine`, cf. Task 2.3.5), but the number of
    distinct sequential variants drops from **{_full_variants.nunique()} to
    {_fine_variants.nunique()}**, which confirms our hypothesis. Removing the 5 appeal-related activities
    collapses a lot of near-duplicate variants into the same shorter
    sequence: those extra activities were responsible for most of the
    variant diversity in the full log, even though they only occur in a
    small minority of cases (`outcome_appealed` is true for
    {case_log_outcomes['outcome_appealed'].mean():.1%} of cases, cf. Task 3.1a).
    """)
    return (df_fine,)


@app.cell(hide_code=True)
def _(mo):
    # Task 4.1.2: process map (absolute frequency) for the fine object sub-log, inspected in Disco
    mo.vstack([
        mo.md("**Process map (absolute frequency) for the fine object sub-log, from Disco:**"),
        mo.image(src="screenshots/task_4.1.2_process_map.png"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Task 4.1.2a, three observations that are unexpected and worth investigating further:**

    1. **`Payment` is directly followed by `Add penalty` 3,902 times.** A
       penalty for not paying gets applied even though a payment was
       already recorded right before it. That's backwards from what you'd
       expect, a payment should prevent or cancel a pending penalty, not
       be followed by one. Worth checking whether the penalty logic simply
       doesn't check for existing payments before firing, or whether the
       payment just didn't cover the full amount and a partial payment
       still triggers the penalty.
    2. **`Payment` is directly followed by another `Payment` 4,310 times**
       (the self-loop on `Payment`). The same case gets multiple separate
       payment postings one after another. Worth investigating whether
       this reflects a genuine installment arrangement, or duplicate or
       erroneous payment entries, since a single fine normally shouldn't
       need more than one payment record if it's paid in full the first
       time.
    3. **`Add penalty` is directly followed by the end of the case 3,252
       times** (the dashed edge straight from `Add penalty` to the end
       marker). These cases get penalized and then just stop: no `Payment`
       and no `Send for Credit Collection` ever follows within this
       sub-log. That's neither a resolution nor an escalation, so it's
       worth checking whether these cases are genuinely still open at the
       end of the log's observation window, or whether they continue
       through an appeal-related activity that this filtered sub-log hides.
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

    mo.md(f"""
    **Checking observation 1 in Python.** Of the {_n:,} `Payment -> Add penalty`
    transitions, {_n_after_notification:,} come from payments made between
    `Insert Fine Notification` and `Add penalty`, i.e. within the payment
    deadline. In only
    {_n_fully_paid} of them had the offender already paid everything owed
    at that point (`outstanding_amount` <= 0, cf. case `A10125` in
    Task 3.1c). In the other {len(_remaining):,} the payment fell short,
    though mostly only by a little (median {_remaining.median():g} still
    owed when the penalty came). So mostly, a payment that doesn't cover
    the full amount doesn't prevent the penalty, which is plausible. But
    why would so many offenders pay just a few euros too little? That
    shortfall is about the same size as the typical overpayment in
    Task 2.2.5b, so maybe the `expense` in the log doesn't always match
    what the offender was actually asked to pay. That's an open question
    for us. There's also a bigger pattern behind it: there are exactly
    as many `Add penalty` events ({_n_penalized:,}) as
    `Insert Fine Notification` events ({_n_notified:,}), and every notified
    case gets a penalty (Task 3.1c). Fines that are paid without a penalty
    never have a notification recorded at all; they're paid right after
    `Create Fine` or `Send Fine` (the `Create Fine -> Payment` and
    `Send Fine -> Payment` edges in the process map).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.vstack([
        mo.md(r"""
    **Task 4.1.2b, a sequential variant exhibiting unexpected behavior:**

    Using Disco's Follower filter (`Payment` directly followed by `Payment`)
    on the fine object sub-log isolates the 4,018 cases behind the
    `Payment -> Payment` self-loop from the process map. Within that filtered
    set, the dominant variant (3,793 of those cases, 94.4%) is:

    ```
    Create Fine -> Send Fine -> Insert Fine Notification -> Add penalty -> Payment -> Payment
    ```

    i.e. the fine goes through the full notify-and-penalize path, and only
    once the penalty has been applied do two separate `Payment` events
    follow one right after another. Case `A10009`, below, is an example of
    this variant:
    """),
        mo.image(src="screenshots/task_4.1.2b_case_A10009_part1.png"),
        mo.image(src="screenshots/task_4.1.2b_case_A10009_part2.png"),
    ])
    return


@app.cell(hide_code=True)
def _(df, df_fine, mo):
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
    _days_to_penalty = (_penalty_date - _value('Insert Fine Notification', 'time:timestamp')).days

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
    _median_days = (_per_case('Add penalty', 'time:timestamp') - _per_case('Insert Fine Notification', 'time:timestamp')).dt.days.median()

    mo.vstack([
        mo.md("**Case `A10009`:**"),
        mo.ui.table(_case),
        mo.md(f"""
    **Explanation for the `Payment -> Payment` behavior:**

    The numbers line up too precisely to be a coincidence:
    - `{_base_amount:.0f}` (base fine) `+ {_expense:.0f}` (sending `expense`)
      `= {_base_amount + _expense:.0f}`, exactly the first `paymentAmount`
      ({_payment_1:.0f}).
    - `{_penalized_amount:.0f}` (penalized `amount`) `- {_base_amount:.0f}`
      (base fine) `= {_penalized_amount - _base_amount:.0f}`, exactly the
      second `paymentAmount` ({_payment_2:.0f}).

    So the first payment covers exactly what the offender was originally
    told they owed (the base fine plus the sending expense), from before
    any penalty existed. `Add penalty` happens on {_penalty_date:%Y-%m-%d},
    exactly {_days_to_penalty} days after the notification (the payment
    deadline), but the first payment only arrives on
    {_payment_dates[0]:%Y-%m-%d}, after the penalty was already applied.
    So the offender paid an amount that was already outdated, just
    {(_payment_dates[0] - _penalty_date).days} days too late. The second payment on {_payment_dates[1]:%Y-%m-%d}
    covers exactly the extra amount added by the penalty.

    This looks less like a data quality issue (e.g. a duplicate or
    erroneous payment posting, which is what we first suspected in
    Task 4.1.2a) and more like the offender paying what the
    original notice said, then having to make a second, separate payment
    once they were informed of the late-payment surcharge.

    **Is A10009 typical?** Looking at all {_sub['case:concept:name'].nunique():,}
    cases of this variant in the fine object sub-log, the first payment
    equals base fine + expense in {_share_first:.0%} of them, and the
    second payment equals exactly the penalty increment in
    {_share_second:.0%}. The penalty also comes a median of
    {_median_days:.0f} days after the notification. So the explanation
    holds for most of the variant, not just this one case. A process
    improvement would be to tell offenders the updated amount as soon as
    the penalty is added, so they don't pay a stale amount.
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
    The model was built in bpmn.io on top of the Canvas template
    (`bpmn/Fine-Object-Template.bpmn`), so the 6 fine object activities keep the
    template's names and IDs. It shows our current understanding of how a
    fine *should* move through the process. Each of the 6 activities
    appears exactly once as a task in the model:

    - Every case starts with `Create Fine`. If the offender pays right away
      (on the spot), the fine goes straight to `Payment`, which matches
      variant 2 from Task 4.1.1b (`Create Fine -> Payment`).
    - Otherwise the fine is mailed (`Send Fine`) and the offender is
      formally notified (`Insert Fine Notification`). If they pay within
      the deadline, the fine goes to `Payment` without any penalty. This
      is how we think the process *should* work, but the log never shows
      it: every notified case gets `Add penalty`, even when it was already
      paid on time (Tasks 3.1c and 4.1.2a). We kept the branch anyway,
      because penalizing on-time payments looks like a flaw of the
      process (or of the logging), not intended behavior.
    - If they don't, `Add penalty` raises the amount (the late-payment
      surcharge from Task 2.1.2b). The offender then either pays the
      penalized amount or the fine is escalated via `Send for Credit
      Collection`, which ends the fine object's lifecycle without a payment
      (variant 1 from Task 4.1.1b).
    - `Payment` can repeat as long as the fine isn't fully paid yet, since
      we'd expect paying in installments to be allowed, as long as the full
      amount is paid in the end (case `A10009` from Task 4.1.2c is an
      example of this). The three "paid"
      branches are first merged by one XOR join, and the installment loop
      has its own XOR join right before `Payment`, so the loop stays a
      clean, structured block.
    - The only way out of that loop is "Fully paid? yes". So we assume that
      once an offender starts paying, they eventually pay the full amount.

    The model is meant to be a proper workflow graph: one start event, one
    end event, only XOR gateways (each one either a split or a join), every
    task with exactly one incoming and one outgoing flow, and every node on
    a path from start to end. The cell below checks each of these
    properties on the BPMN file. Because it uses only XOR gateways, there's
    never more than one token in the net, so a lack of synchronization
    can't happen. And since there's no AND-join, it can't deadlock either,
    so the model should be **sound**. The cell below also verifies this by
    converting the BPMN file into a Petri net with pm4py and running its
    Woflan soundness check.
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
