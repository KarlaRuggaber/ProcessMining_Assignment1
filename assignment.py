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
def _(mo):
    mo.md(r"""
    **Task 1.1, answers:**

    a) The log covers the period from 1999-12-31 23:00:00 UTC to 2013-06-17 22:00:00 UTC,
    i.e. from 2000-01-01 to 2013-06-18 in Italian local time (cf. Task 2.1.1), roughly
    13.5 years.

    b) vehicleClass has 4 distinct values: A, C, M, and R. 411,100 events don't have a
    value for this attribute, because it is only recorded at `Create Fine`.

    c) For the initial `amount` of each case (at its Create Fine event):
    min 0.0, median 35.0, max 4351.0.

    The distribution is heavily right-skewed: the max (4351) is more than 100 times
    the median (35), so there are clearly some extreme outliers in there. It would be
    worth digging into which cases end up with such high fines, maybe certain vehicle
    classes, violation types, or time periods stand out, and checking whether the
    zero-amount fines are a data quality issue or an actual case type of their own.

    d) There are 3,548 events with a points value greater than 0, and all of them are
    tied to the "Create Fine" activity. That number matches the number of affected
    cases exactly, so each case that gets points, gets them exactly once, right when
    the fine is created.
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

    mo.md(f"""
    **Checking the timestamp granularity:**
    - Distinct second values: `{seconds}`
    - Distinct minute values: `{minutes}`
    - Distinct hour values:   `{hours}`

    Seconds and minutes are always 0, and only two hour values ever show up
    ({hours}). Those are just midnight (00:00) in the log's original Italian
    local time, shifted to UTC depending on whether daylight saving was
    active (00:00 CET becomes 23:00 UTC, 00:00 CEST becomes 22:00 UTC). So in
    practice the timestamps only carry **day-level granularity**: every event
    is dated to a specific calendar day, nothing more precise than that.
    One side effect: since the log stores UTC, every date shown in this
    notebook is one day *earlier* than the actual Italian date (e.g. an
    event shown as `2007-03-08 23:00 UTC` really happened on 2007-03-09).
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
    Only one activity schema turns out to be incomplete: `Insert Fine Notification`'s
    `lastSent` attribute is missing for {int(_incomplete_df['missing'].iloc[0]) if len(_incomplete_df) else 0:,}
    out of {int(_incomplete_df['events_of_activity'].iloc[0]) if len(_incomplete_df) else 0:,}
    events. Every other local attribute, for every other activity, is
    complete, filled for 100% of that activity's events. On top of that,
    the meaning of `lastSent` isn't documented at all (the attribute
    description just says "N/A"), so it should be documented or dropped.
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
      payments that never show up as `Payment` events, see Task 2.2.4b. So
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
    case_events = df[df['case:concept:name'] == selected_case_id].sort_values('time:timestamp')

    display_cols = [
        'time:timestamp', 'concept:name', 'amount', 'totalPaymentAmount',
        'paymentAmount', 'expense', 'article', 'vehicleClass', 'points',
        'notificationType', 'lastSent', 'dismissal', 'org:resource',
    ]

    mo.vstack([
        mo.md(f"**Case `{selected_case_id}`** ({len(case_events)} events):"),
        mo.ui.table(case_events[display_cols].reset_index(drop=True)),
        mo.md("""
    **Going through the case event by event** (dates as stored in the log,
    i.e. UTC, cf. Task 2.1.1):

    - **2007-03-08, `Create Fine`**: the fine gets created with a base
      `amount` of 36, and `totalPaymentAmount` starts at 0. The violation
      is `article` 157 (stopping and parking), committed with a vehicle of
      `vehicleClass` A, and it costs 0 `points`, so it's a minor offence.
      Employee `org:resource` 561 created the fine, and `dismissal` is
      initialized to "NIL", meaning the fine hasn't been dismissed.
    - **2007-07-16, `Send Fine`** (about 4 months later): the fine notice
      goes out to the offender, with an `expense` of 13 recorded for
      sending it.
    - **2007-08-01, `Insert Fine Notification`** (roughly 2 weeks after
      sending): the offender receives the notification. `notificationType`
      is "P", so the fine refers to the car owner, and `lastSent` is "P" too
      (its meaning isn't documented).
    - **2007-09-30, `Add penalty`** (exactly 60 days after the
      notification, which is the payment deadline): a penalty kicks in and
      `amount` jumps from 36 to 74, the new case-cumulative total owed.
    - **2008-09-08, `Payment`** (almost a year later): a payment of 87 comes
      in, `totalPaymentAmount` updates to 87 too. That's exactly the
      penalized amount plus the sending expense (74 + 13), so the case is
      settled.

    Only `Create Fine` carries a resource here; none of the later events
    record which employee handled them.

    All in all the case stretches over about 1.5 years from creation to
    payment, with pretty long gaps between events. The payment only shows up
    well after the penalty was added, which fits the typical pattern here: a
    fine that drags on, escalates once, and eventually gets paid off.
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

    _dev_cols = ['time:timestamp', 'concept:name', 'paymentAmount', 'payment_cumsum', 'totalPaymentAmount']
    _ex_same_day = df_task4.loc[df_task4['case:concept:name'] == _same_day_dev[0], _dev_cols].reset_index(drop=True)
    _ex_other = df_task4.loc[df_task4['case:concept:name'] == _other_dev[0], _dev_cols].reset_index(drop=True)

    mo.vstack([
        mo.md(f"""
    We compared `payment_cumsum` to `totalPaymentAmount` at the
    {len(_comparable):,} events where `totalPaymentAmount` is actually
    defined (`Create Fine` and `Payment`). They agree in
    {(1 - len(_mismatch) / len(_comparable)):.3%} of these events, leaving
    {len(_mismatch)} deviating events ({len(_mismatch) / len(_comparable):.3%}).
    All of these happen at a `Payment` event, and in every single one,
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
    **2. Payments missing from the log ({len(_other_dev)} cases),** e.g.
    case `{_other_dev[0]}`:
    """),
        mo.ui.table(_ex_other),
        mo.md("""
    Here `totalPaymentAmount` goes up by *more* than the `paymentAmount` of
    the event itself, so it counts money that never shows up as a `Payment`
    event. Either some payments were never logged as events, or the system
    counted a payment twice. We can't tell which from the log alone.

    Either way, `totalPaymentAmount` isn't fully reliable as a running sum
    of the logged payments. That's a good reminder of why the lecture says
    to verify a pre-existing attribute instead of just trusting it. For
    the data collection, we'd suggest logging every payment as its own
    `Payment` event and deriving `totalPaymentAmount` from those events
    instead of storing it separately.
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
    df_task5['outstanding_amount'] = (
        df_task5['amount_due_so_far'] + df_task5['expense_so_far'] - df_task5['payment_cumsum']
    ).round(2)

    mo.md("""
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
    like `0.00000000000001` would wrongly count as "still owed" or
    "overpaid" (the lecture's warning about floats and money).
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

    mo.md(f"""
    **Events with `outstanding_amount` > 0:** {_n_positive:,} out of
    {_n_total:,} ({_n_positive / _n_total:.1%}).

    The remaining {_n_total - _n_positive:,} events aren't just "everything
    else", they split into two different groups:
    - **Exactly 0:** {_n_zero:,} events ({_n_zero / _n_total:.1%}). Mostly
      ({_n_zero_payment:,}) `Payment` events where that payment fully settles
      the case, plus {_n_zero_create_fine:,} `Create Fine` events where the
      fine itself is 0 (the zero-amount fines from Task 1.1c), plus a
      handful of later events in cases that are already settled.
    - **Negative:** {_n_negative:,} events ({_n_negative / _n_total:.1%}),
      meaning the case looks overpaid at that point. Probably a mix of
      actual overpayments and the same kind of payment-recording issues
      found in Task 2.2.4b (same-day ordering, payments missing from the
      log).
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

    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(f"""
    **Two things stand out here**, and both confirm the hypothesis above:
    1. The distribution really is **discrete and spiky**, not continuous.
       The 5 most common exact amounts ({', '.join(f'{a:g} ({n:,} cases)' for a, n in _top_values.items())}) alone cover
       {_top_share:.1%} of all {len(case_log):,} cases, a pretty clear sign
       of a small set of statutory tariffs rather than amounts that vary
       freely.
    2. It's also **strongly right-skewed**, with a long tail. The mean
       ({case_log['initial_fine_amount'].mean():.1f}) sits well above the
       median ({case_log['initial_fine_amount'].median():.1f}), because of a
       thin trail of large fines reaching all the way up to
       {case_log['initial_fine_amount'].max():,.0f}. You can see that in the
       log-scaled histogram as a sparse scatter of bars far to the right of
       the main mass.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(case_log, mo, px):
    # Task 2.3.6: relate initial_fine_amount and final_fine_amount per case
    _fig = px.scatter(
        case_log, x='initial_fine_amount', y='final_fine_amount',
        opacity=0.15, title='Final vs. initial fine amount per case',
    )
    # diagonal reference line must span the actual data range (final_fine_amount
    # reaches 8,000, well beyond initial_fine_amount's max of 4,351) or it
    # would visibly stop short of the top of the chart
    _axis_max = max(case_log['initial_fine_amount'].max(), case_log['final_fine_amount'].max())
    _fig.add_shape(type='line', x0=0, y0=0, x1=_axis_max, y1=_axis_max, line=dict(color='gray', dash='dot'))

    _no_penalty_share = (case_log['final_fine_amount'] == case_log['initial_fine_amount']).mean()
    _penalty_share = (case_log['final_fine_amount'] > case_log['initial_fine_amount']).mean()
    _below_share = (case_log['final_fine_amount'] < case_log['initial_fine_amount']).mean()

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

    A handful of points sit even further above the doubling line, cases
    with an apparently higher penalty multiplier. Might be worth a closer
    look if you want to chase outliers further.
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

    These can genuinely co-occur (a case can be paid and still appealed, or
    sent to collection and later appealed), and plenty of cases in the log
    end without reaching any of them, so it's worth checking the overlaps
    and the "no outcome" bucket rather than assuming the three partition the
    cases cleanly.
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

    _n_none = int((~case_log_outcomes[_outcomes[0]] & ~case_log_outcomes[_outcomes[1]] & ~case_log_outcomes[_outcomes[2]]).sum())

    # edge cases of the definitions: zero-amount fines count as "paid" without any
    # payment, and dismissed fines (dismissal other than NIL) have no outcome of their own
    _has_payment = df_task5.groupby('case:concept:name')['concept:name'].apply(lambda s: 'Payment' in set(s))
    _n_paid_without_payment = int((case_log_outcomes['outcome_paid'] & ~_has_payment).sum())
    _is_dismissed = df_task5.groupby('case:concept:name')['dismissal'].apply(lambda s: s.dropna().ne('NIL').any())
    _n_dismissed = int(_is_dismissed.sum())

    mo.vstack([
        mo.md("**Cases per outcome:**"),
        mo.ui.table(_single_counts),
        mo.md("**Cases per pairwise outcome combination:**"),
        mo.ui.table(_pair_counts),
        mo.md(f"""
    **Cases with none of the three outcomes:** {_n_none:,} out of {_n_total:,}
    ({_n_none / _n_total:.1%}). In these cases the fine was created and
    maybe sent, but the log never records a full payment, an escalation to
    collection or an appeal. Many of them stop years before the log ends
    in 2013, so it's not just that the recording period ran out. More
    likely explanations are a payment that was never logged, a dismissal,
    or an offender who couldn't be reached (see Task 3.1d).

    **Two edge cases of our definitions:**
    - {_n_paid_without_payment} cases count as paid without a single
      `Payment` event. These are the zero-amount fines from Task 1.1c:
      nothing is owed, so `outstanding_amount` is 0 right away. That's
      technically correct, but worth knowing.
    - {_n_dismissed:,} cases have a `dismissal` value other than "NIL" at
      some point, i.e. the fine was dismissed (e.g. "#" by the prefecture,
      "G" by the judge, plus several undocumented codes). None of our three
      outcomes covers a dismissal on its own, so "dismissed" would be a
      natural fourth outcome. The undocumented codes (e.g. "A", "T", "D")
      should be documented, since right now we can't say what they mean.
    """),
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
        mo.md("""
    Here the fine is created, sent, and a penalty gets added once the
    notification deadline passes, but no payment ever comes in. More than
    two years later (2009-03-29), the case gets escalated to
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
    positive (the enrichment doesn't know about dismissals).
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
    _cols = ['time:timestamp', 'concept:name', 'amount_due_so_far', 'expense_so_far', 'payment_cumsum', 'outstanding_amount']
    _case_id = 'A10125'
    _case_table = df_task5.loc[df_task5['case:concept:name'] == _case_id, _cols].reset_index(drop=True)
    for _col in _outcome_cols:
        _case_table[_col] = case_log_outcomes.loc[_case_id, _col]

    mo.vstack([
        mo.md(f"""
    {_n_multi:,} cases have more than one outcome at once. Here's one of
    them, case `{_case_id}` (paid *and* appealed):
    """),
        mo.ui.table(_case_table),
        mo.md("""
    This case shows why "paid" and "appealed" aren't mutually exclusive: the
    offender appeals the fine, then pays off exactly what was owed at that
    point (36 + 13 expense = 49), bringing `outstanding_amount` to 0. But
    the penalty still gets applied afterward anyway (the appeal evidently
    didn't stop it in time), pushing the amount owed back up to 38, on the
    very same day the appeal is actually sent off. So the case counts as
    both paid (it did reach 0 at some point) and appealed, even though it
    isn't fully resolved by the end of what we see in the log. A good
    reminder that "paid" here means "settled at some point", not
    necessarily "the final state of the case".
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
    _cols = ['time:timestamp', 'concept:name', 'amount_due_so_far', 'expense_so_far', 'payment_cumsum', 'outstanding_amount']
    _case_id = 'A1'
    _case_table = df_task5.loc[df_task5['case:concept:name'] == _case_id, _cols].reset_index(drop=True)
    for _col in _outcome_cols:
        _case_table[_col] = case_log_outcomes.loc[_case_id, _col]

    mo.vstack([
        mo.md(f"""
    {_n_none:,} cases have none of the three outcomes. Here's one of them,
    case `{_case_id}`:
    """),
        mo.ui.table(_case_table),
        mo.md("""
    This case only has two events: the fine gets created, then it gets
    sent to the offender in December 2006, and that's it. No payment, no
    penalty, no escalation to collection, no appeal, and `dismissal` stays
    "NIL". The log runs until 2013, so the case wasn't simply cut off by
    the end of the recording period; it just stops more than six years
    earlier. Notably, `Insert Fine Notification` never happens, so the
    offender apparently never received the fine. That would explain why
    no penalty follows, since the payment deadline only starts with the
    notification. Possible reasons are an offender who couldn't be reached
    (e.g. a wrong address), or a payment that happened outside the system
    and was never logged. Either way, the log leaves this case unresolved.

    Case `A1` isn't an exception: around 20,000 cases follow exactly this
    `Create Fine -> Send Fine` pattern (variant 3 in Task 4.1.1b). An open
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
    This surprised us a bit, since the 231 distinct variants suggest a
    much messier process than it actually is.
    """)
    return


@app.cell(hide_code=True)
def _(mo, variant_counts):
    # Task 4.1.1b: summarize each of the top 4 sequential variants in one sentence
    _n_cases = int(variant_counts.sum())
    _top4 = variant_counts.head(4)
    _rows = [f"- `{' -> '.join(v)}` ({c:,} cases, {c / _n_cases:.1%})" for v, c in _top4.items()]

    mo.md(f"""
    **The top 4 variants:**

    {chr(10).join(_rows)}

    In one sentence each:
    1. `{' -> '.join(_top4.index[0])}`: the fine is created, sent, formally
       notified, hit with a late-payment penalty, and finally escalated to
       credit collection without ever being paid.
    2. `{' -> '.join(_top4.index[1])}`: the fine is created and paid
       immediately, without any of the sending or notification steps ever
       happening.
    3. `{' -> '.join(_top4.index[2])}`: the fine is created and sent, but
       no notification is ever recorded as received and nothing else
       happens (these cases stop in every year from 2000 to 2013, so
       it's not just the end of the log, cf. Task 3.1d).
    4. `{' -> '.join(_top4.index[3])}`: the fine goes through the full
       notify-and-penalize cycle, but this time it does get paid off
       afterward, so no escalation is needed.
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

    mo.md(f"""
    Filtering the event log down to just the fine object's 6 activities
    (`{fine_activities}`) keeps all {len(_fine_variants):,} cases (every
    case starts with `Create Fine`, cf. Task 2.3.5), but the number of
    distinct sequential variants drops from **{_full_variants.nunique()} to
    {_fine_variants.nunique()}**. Removing the 5 appeal-related activities
    collapses a lot of near-duplicate variants into the same shorter
    sequence: those extra activities were responsible for most of the
    variant diversity in the full log, even though they only occur in a
    small minority of cases (cf. `outcome_appealed`, 3.0% of cases, in
    Task 3.1a).
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
      the deadline, the fine goes to `Payment` without any penalty.
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

    The model is a proper workflow graph: one start event, one end event,
    only XOR gateways (each one either a split or a join), every task with
    exactly one incoming and one outgoing flow, and every node lies on a
    path from start to end. Because it uses only XOR gateways, there's
    never more than one token in the net, so a lack of synchronization
    can't happen. And since there's no AND-join, it can't deadlock either,
    so the model is **sound**. The cell below double-checks this by
    converting the BPMN file into a Petri net with pm4py and running its
    Woflan soundness check.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo, pm4py):
    # Task 4.2.3: verify soundness of the BPMN model (BPMN -> Petri net -> Woflan)
    _bpmn = pm4py.read_bpmn('bpmn/fine_object.bpmn')
    _net, _im, _fm = pm4py.convert_to_petri_net(_bpmn)
    _is_sound = pm4py.check_soundness(_net, _im, _fm)[0]

    mo.md(f"""
    **Soundness check (pm4py, Woflan) on `bpmn/fine_object.bpmn`:**
    the converted Petri net has {len(_net.places)} places and
    {len(_net.transitions)} transitions, and the model is
    **{'sound' if _is_sound else 'NOT sound'}**.
    """)
    return


if __name__ == "__main__":
    app.run()
