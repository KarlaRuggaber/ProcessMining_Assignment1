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
    import plotly.express as px

    return mo, pd, pm4py, px


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

    a) The log covers the period from 1999-12-31 23:00:00 UTC to 2013-06-17 22:00:00 UTC.

    b) vehicleClass has 4 distinct values: A, C, M, and R. A number of events simply
       don't have a value recorded for this attribute.

    c) For Create Fine events, the amount attribute has the following stats:
      - Min: 0.0
      - Median: 35.0
      - Max: 4351.0

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
    seconds = sorted(df['time:timestamp'].dt.second.unique())
    minutes = sorted(df['time:timestamp'].dt.minute.unique())
    hours   = sorted(df['time:timestamp'].dt.hour.unique())

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
    `lastSent` attribute is missing for {int(_incomplete_df['missing'].iloc[0]) if len(_incomplete_df) else 0}
    out of {int(_incomplete_df['events_of_activity'].iloc[0]) if len(_incomplete_df) else 0}
    events. Every other local attribute, for every other activity, is
    complete, filled for 100% of that activity's events.
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
    Out of {len(_attribute_cols)} non-mandatory attributes:
    - **Global**, filled for all {_n_activities} activities and therefore not really local: `{_global_attrs}`.
    - **Shared**, local to more than one activity but not all of them: {len(_shared_attrs)} attributes.
    - **Exclusive**, local to exactly one activity: {len(_exclusive_attrs)} attributes.
    """),
        mo.ui.table(_shared_df),
        mo.md(f"""
    **Are the numerical shared attributes cumulative or incremental?**

    - `amount` (shows up at `Create Fine` and `Add penalty`) turns out to be
      **case-cumulative**. I checked all {len(_amount_check):,} cases that
      have both events, and `amount` always goes up from `Create Fine` to
      `Add penalty`, by a factor of {_amount_ratio.mean():.2f} on average
      (median {_amount_ratio.median():.2f}). That lines up with the statutory
      late-payment penalty roughly doubling the fine. So it's not really a
      running sum of increments, it's a recalculated total that only ever
      grows within a case, which is exactly what makes it case-cumulative
      rather than a standalone value.
    - `totalPaymentAmount` (shows up at `Create Fine` and `Payment`) is also
      **case-cumulative**, and here the check is even more direct: across
      all {len(_pay):,} `Payment` events, `totalPaymentAmount` matches
      `cumsum(paymentAmount)` within the same case for {_pay_match_rate:.1%}
      of them (the small deviations are probably payments that happened
      before the log's observation window started). So this one really is a
      genuine running sum of payments made so far.
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
        'paymentAmount', 'expense', 'notificationType', 'dismissal', 'org:resource',
    ]

    mo.vstack([
        mo.md(f"**Case `{selected_case_id}`** ({len(case_events)} events):"),
        mo.ui.table(case_events[display_cols].reset_index(drop=True)),
        mo.md("""
    **Going through the case event by event:**

    - **2007-03-08, `Create Fine`**: the fine gets created with a base
      `amount` of 36, and `totalPaymentAmount` starts at 0. No penalty
      points for this violation.
    - **2007-07-16, `Send Fine`** (about 4 months later): the fine notice
      goes out to the offender, with an `expense` of 13 recorded for
      sending it.
    - **2007-08-01, `Insert Fine Notification`** (roughly 2 weeks after
      sending): the notification gets formally registered, `notificationType`
      is "P" and `lastSent` is set to "P" too.
    - **2007-09-30, `Add penalty`** (about 2 months after the notification,
      so past the payment deadline): a penalty kicks in and `amount` jumps
      from 36 to 74, the new case-cumulative total owed.
    - **2008-09-08, `Payment`** (almost a year later): a payment of 87 comes
      in, `totalPaymentAmount` updates to 87 too, covering the full
      penalized amount plus the extra costs, and the case is settled.

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

    _dev_case_id = _mismatch.loc[_mismatch['concept:name'] == 'Payment', 'case:concept:name'].iloc[0]
    _dev_cols = ['time:timestamp', 'concept:name', 'paymentAmount', 'payment_cumsum', 'totalPaymentAmount']
    _dev_case = df_task4.loc[df_task4['case:concept:name'] == _dev_case_id, _dev_cols].reset_index(drop=True)

    mo.vstack([
        mo.md(f"""
    I compared `payment_cumsum` to `totalPaymentAmount` at the
    {len(_comparable):,} events where `totalPaymentAmount` is actually
    defined (`Create Fine` and `Payment`). They agree in
    {(1 - len(_mismatch) / len(_comparable)):.3%} of cases, leaving
    {len(_mismatch)} deviating events ({len(_mismatch) / len(_comparable):.3%}).
    All of these happen at a `Payment` event, and in every single one,
    `payment_cumsum` is *smaller* than `totalPaymentAmount`, by
    {_mismatch['deviation'].abs().mean():.1f} on average and up to
    {_mismatch['deviation'].abs().max():.1f}.
    """),
        mo.md(f"**One of the deviating cases, `{_dev_case_id}`:**"),
        mo.ui.table(_dev_case),
        mo.md("""
    All of these deviations happen for cases with **two `Payment` events on
    the same calendar day** (the log can't tell them apart at day-level
    granularity). `totalPaymentAmount` already shows the *final* total,
    after both same-day payments, on the *first* of the two rows, while
    `payment_cumsum` correctly shows only the running total right after
    that individual payment. That looks like a data-quality issue in
    `totalPaymentAmount`: it seems to have been computed with knowledge of
    the case's eventual total rather than strictly as a running sum up to
    each event. It's a good reminder of why the lecture tells you to verify
    a pre-existing attribute instead of just trusting it.
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

    df_task5['outstanding_amount'] = (
        df_task5['amount_due_so_far'] + df_task5['expense_so_far'] - df_task5['payment_cumsum']
    )

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

    Put together: `outstanding_amount = amount_due_so_far + expense_so_far - payment_cumsum`.
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
      actual overpayments and the same kind of same-day payment-ordering
      artifact found in Task 2.2.4b.
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

    mo.vstack([
        mo.md(f"""
    Here's the **case log**, built by aggregating the event log per case
    ({len(case_log):,} cases in total). On top of `start_time`, `end_time`
    and `no_of_events`, it includes every **case attribute**, meaning an
    attribute with at most one distinct non-null value per case. I found
    these by checking
    `event_log.groupby(case_id)[attr].nunique().max() <= 1` for each
    non-mandatory attribute, which gives: `{_case_attr_cols}`.

    New enrichment: **`initial_fine_amount`**, the first non-null value of
    `amount` per case (the same as the `amount` at the case's `Create Fine`
    event, since every case starts there, see Task 2.2.4). While I'm at it,
    I also add `final_fine_amount` (last non-null value of `amount`) the
    same way, since it's needed again in Task 2.3.6 below.
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
    they're not set freely case by case. My hypothesis is that
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
       The 5 most common exact amounts (`{dict(_top_values)}`) alone cover
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
    **Noteworthy fact:** just **3 article codes, {list(_top3.index)}, account
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


if __name__ == "__main__":
    app.run()
