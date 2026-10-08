import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Assignment 1, Part 2: Road Traffic Fine Management Process
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import pm4py
    import plotly.express as px
    import plotly.graph_objects as go

    return go, mo, pd, pm4py, px


@app.cell(hide_code=True)
def _(pm4py):
    event_log_from_disk =  pm4py.read_xes('data/Road_Traffic_Fine_Management_Process.xes', variant="rustxes")

    print(len(event_log_from_disk), 'events read.')
    event_log_from_disk
    return (event_log_from_disk,)


@app.cell(hide_code=True)
def _(event_log_from_disk, pm4py):
    # events of each case in log order (stable sort keeps the order of same-day events)
    df = pm4py.convert_to_dataframe(event_log_from_disk) \
             .sort_values(['case:concept:name', 'time:timestamp'], kind='stable')
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 5

    ## Task 5.1
    """)
    return


@app.cell(hide_code=True)
def _(df, mo):
    # Task 5.1a: rework = an activity that occurs more than once in the same case
    _occ = df.groupby(['case:concept:name', 'concept:name']).size().rename('occurrences').reset_index()
    _rep = _occ[_occ['occurrences'] > 1]

    _per_activity = _rep.groupby('concept:name')['occurrences'].agg(
        cases_with_rework='size',
        rework_events=lambda s: int((s - 1).sum()),
        max_occurrences_in_a_case='max',
    ).reset_index().rename(columns={'concept:name': 'activity'})
    _distribution = _rep['occurrences'].value_counts().sort_index() \
                        .rename_axis('occurrences_in_the_case').reset_index(name='no_of_cases')

    _n_cases = df['case:concept:name'].nunique()
    _n_rework = _rep['case:concept:name'].nunique()
    _n_two = int((_rep['occurrences'] == 2).sum())

    mo.vstack([
        mo.md(f"""
    Only {len(_per_activity)} activity is ever repeated within a case: {', '.join(f'`{a}`' for a in _per_activity['activity'])}. In
    total, {_n_rework:,} of the {_n_cases:,} cases
    ({_n_rework / _n_cases:.1%}) contain rework, with
    {_per_activity['rework_events'].sum():,} extra events. Most of these
    cases repeat the activity only once ({_n_two:,} cases, i.e.
    {_n_two / _n_rework:.1%}, have exactly 2 payments), and only a few
    cases have many repetitions (up to
    {_per_activity['max_occurrences_in_a_case'].max()} payments in one
    case).
    """),
        mo.ui.table(_per_activity),
        mo.ui.table(_distribution),
    ])
    return


@app.cell(hide_code=True)
def _(df, mo):
    # Task 5.1b: inspect cases with few and with many repetitions
    _cols = ['time:timestamp', 'concept:name', 'amount', 'expense', 'paymentAmount', 'article']
    _small_1 = df.loc[df['case:concept:name'] == 'A10434', _cols].reset_index(drop=True)
    _small_2 = df.loc[df['case:concept:name'] == 'A1098', _cols].reset_index(drop=True)
    _high = df.loc[df['case:concept:name'] == 'C20817', _cols].reset_index(drop=True)

    _a_fine = _small_1['amount'].iloc[0]
    _a_penalized = _small_1['amount'].dropna().iloc[-1]
    _a_expense = _small_1['expense'].sum()
    _a_p1, _a_p2 = _small_1.loc[_small_1['concept:name'] == 'Payment', 'paymentAmount'].tolist()

    _s_fine = _small_2['amount'].iloc[0]
    _s_penalized = _small_2['amount'].dropna().iloc[-1]
    _s_expense = _small_2['expense'].sum()
    _s_p1, _s_p2 = _small_2.loc[_small_2['concept:name'] == 'Payment', 'paymentAmount'].tolist()

    _h_pay = _high[_high['concept:name'] == 'Payment']
    _h_gap = _h_pay['time:timestamp'].diff().dt.days.median()
    _median_fine = df.loc[df['concept:name'] == 'Create Fine', 'amount'].median()

    mo.vstack([
        mo.md("**Few repetitions: case `A10434` (2 payments)**"),
        mo.ui.table(_small_1),
        mo.md(f"""
    The fine of {_a_fine:g} is sent with an expense of {_a_expense:g}, and
    the penalty raises `amount` to {_a_penalized:g}. Only after the penalty
    does the offender pay {_a_p1:g}, which is exactly fine + expense
    ({_a_fine:g} + {_a_expense:g}). Later they pay {_a_p2:g}, exactly the
    penalty part ({_a_penalized:g} - {_a_fine:g}).

    *Hypothesis:* The offender paid too late, using the amount from the
    original fine notice, because they didn't know the penalty had
    already been added. After a request for the rest, they paid the
    penalty separately.
    """),
        mo.md("**Few repetitions: case `A1098` (2 payments)**"),
        mo.ui.table(_small_2),
        mo.md(f"""
    The offender has to pay the fine of {_s_fine:g} plus an expense
    of {_s_expense:g}. Within the deadline they pay only {_s_p1:g}. Still,
    the penalty is added (`amount` goes up to {_s_penalized:g}), as it is
    for every notified case (Part 1, Task 3.1c). Afterwards they pay
    {_s_p2:g}, which is exactly the missing expense, and the case ends
    without the penalty being paid.

    *Hypothesis:* The offender didn't know that the postal expense also
    has to be paid. After a reminder they paid the missing part, and the
    penalty was waived because the fine itself was paid on time.
    """),
        mo.md(f"**Many repetitions: case `C20817` ({len(_h_pay)} payments)**"),
        mo.ui.table(_high),
        mo.md(f"""
    The fine of {_high['amount'].iloc[0]:g} is
    {_high['amount'].iloc[0] / _median_fine:.0f} times the median initial
    fine of all cases ({_median_fine:g}). The offender appeals to a judge,
    and the penalty raises `amount` to
    {_high['amount'].dropna().iloc[-1]:g}. Then they pay {len(_h_pay)} times
    {_h_pay['paymentAmount'].mode().iloc[0]:g}, about every {_h_gap:.0f}
    days, in total {_h_pay['paymentAmount'].sum():g}, i.e. about the initial
    fine.

    *Hypothesis:* The fine was too high to pay at once, so the offender
    got an installment plan with monthly payments, and the penalty was
    dropped as part of it. The repetition is planned, not caused by an
    error.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 5.2
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, pd, px):
    # Task 5.2a: arrival of cases over time (arrival = Create Fine), in Italian
    # local time because the log stores UTC (cf. Part 1, Task 2.1.1)
    _arrival = df.loc[df['concept:name'] == 'Create Fine', 'time:timestamp'].dt.tz_convert('Europe/Rome')
    _year = _arrival.dt.year.rename('year')
    _month = _arrival.dt.month.rename('month')

    # seasonality per month and drift per year in one heatmap
    # months without data (after the end of the log in June 2013) stay empty, not 0
    _heat = _arrival.groupby([_year, _month]).size().unstack()
    _fig_heat = px.imshow(
        _heat, color_continuous_scale='Blues', aspect='auto',
        labels=dict(x='Month', y='Year', color='Arrived cases'),
        title='Arrived cases per month and year',
    )
    _fig_heat.update_xaxes(tickvals=list(range(1, 13)))
    _fig_heat.update_yaxes(tickvals=list(_heat.index))

    # seasonality per day of the week
    _weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    _per_weekday = _arrival.dt.dayofweek.value_counts().sort_index()
    _fig_week = px.bar(
        pd.DataFrame({'weekday': _weekdays, 'arrived_cases': _per_weekday.values}),
        x='weekday', y='arrived_cases', title='Arrived cases per day of the week (all years)',
    )

    _summer_share = _month.isin([7, 8]).mean()
    _full_years = _heat.loc[:2012]  # the log ends in June 2013
    _summer_share_per_year = _full_years[[7, 8]].sum(axis=1) / _full_years.sum(axis=1)
    _per_year = _full_years.sum(axis=1)
    _weekend_ratio = _per_weekday.iloc[5:].mean() / _per_weekday.iloc[:5].mean()

    # is the drop in 2012 the same for all cases? share of new cases that get a fine letter
    _sent_cases = set(df.loc[df['concept:name'] == 'Send Fine', 'case:concept:name'])
    _case_year = pd.Series(_year.values, index=df.loc[_arrival.index, 'case:concept:name'])
    _sent_share = pd.Series(_case_year.index.isin(_sent_cases), index=_case_year.index).groupby(_case_year).mean()

    mo.vstack([
        mo.md(r"""
    **Hypotheses:** (1) More fines are created in summer, because of
    tourists and more traffic. (2) Fewer fines are created at weekends,
    because fewer police officers work. (3) The number of fines per year
    stays roughly constant. The log only has day-level timestamps, so we
    can't look at the hours of the day.
    """),
        mo.ui.plotly(_fig_heat),
        mo.ui.plotly(_fig_week),
        mo.md(f"""
    **Finding 1, strong summer peak (heatmap):** July and August alone
    contain {_summer_share:.1%} of all arrivals, whereas a uniform
    distribution would give two months only 16.7%. The summer peak appears
    in every full year, but its strength varies: the summer share lies
    between {_summer_share_per_year.min():.0%}
    ({_summer_share_per_year.idxmin()}) and
    {_summer_share_per_year.max():.0%} ({_summer_share_per_year.idxmax()}).
    So hypothesis (1) is confirmed. *Interpretation:* the town is probably a tourist
    destination, so many more cars are parked (and fined) during the summer
    holidays. The police should plan more capacity for creating and
    sending fines in the months after the summer.

    **Finding 2, more fines at weekends (bar chart):** On average,
    Saturdays and Sundays have {_weekend_ratio:.2f} times as many arrivals
    as a weekday. So hypothesis (2) is wrong. *Interpretation:* this fits
    the tourism explanation: visitors and leisure traffic come mainly at
    weekends.

    **Finding 3, drift in volume (heatmap rows):** Between 2000 and 2012
    the number of arrivals per year varies between {_per_year.min():,.0f}
    ({_per_year.idxmin()}) and {_per_year.max():,.0f} ({_per_year.idxmax()}),
    so hypothesis (3) is wrong. The volume goes up and down, and it drops
    sharply in {_per_year.idxmin()}. In that year only
    {_sent_share.loc[_per_year.idxmin()]:.0%} of the new cases get a `Send Fine` letter,
    compared with {_sent_share.loc[2005:2011].min():.0%} to
    {_sent_share.loc[2005:2011].max():.0%} in 2005 to 2011. So the drop
    is mostly in fines that were not paid directly. *Interpretation:* we
    don't think fewer fines were really issued. More likely, part of the
    2012 fines are missing from the log, e.g. because of how the log was
    extracted. This is an open question for the data providers.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(df, mo, px):
    # Task 5.2b: closure of cases over time (closure = last event of the case)
    _last = df.groupby('case:concept:name').tail(1).copy()
    _last['local_day'] = _last['time:timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize()
    _main = ['Payment', 'Send for Credit Collection', 'Send Fine']
    _last['closing_activity'] = _last['concept:name'].where(_last['concept:name'].isin(_main), 'other (appeal activities)')
    _last['month'] = _last['local_day'].dt.to_period('M').dt.to_timestamp()

    _monthly = _last.groupby(['month', 'closing_activity']).size().reset_index(name='closed_cases')
    _fig = px.bar(
        _monthly, x='month', y='closed_cases', facet_row='closing_activity', height=800,
        category_orders={'closing_activity': _main + ['other (appeal activities)']},
        title='Closed cases per month, split by the activity that closes the case (own y-axis per row)',
    )
    _fig.update_yaxes(matches=None, title='')
    _fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))

    # finding 1: how many closures happen on credit collection days?
    _cc_days = set(_last.loc[_last['concept:name'] == 'Send for Credit Collection', 'local_day'])
    _share_on_cc_days = _last['local_day'].isin(_cc_days).mean()

    # finding 2: payment closures in summer
    _paid = _last[_last['concept:name'] == 'Payment']
    _paid_jul_sep = _paid['local_day'].dt.month.isin([7, 8, 9]).mean()

    # finding 3: cases that "close" with Send Fine at the end of the log
    _sent = _last[_last['concept:name'] == 'Send Fine'].groupby('month').size()
    _last_two = _sent.iloc[-2:]
    _median_before = _sent.iloc[:-2].median()

    mo.vstack([
        mo.md(r"""
    **Hypothesis:** Cases are closed some time after they arrive, and
    their duration varies. So we expect the closures to follow the summer
    peak of the arrivals with a delay, but with a smoother curve.
    """),
        mo.ui.plotly(_fig),
        mo.md(f"""
    **Finding 1, closures come in huge spikes:** {_share_on_cc_days:.1%}
    of all {len(_last):,} closures happen on just {len(_cc_days)} days,
    namely the days on which cases are sent for credit collection (spikes
    in the second row). So our hypothesis of a smooth curve is wrong. *Interpretation:*
    {(_last['concept:name'] == 'Send for Credit Collection').mean():.0%} of
    the cases end with `Send for Credit Collection`, and this activity is
    done in batches (see Task 5.2c). So the closure date of these cases
    depends on when the next batch is run, not on the case itself.

    **Finding 2, closures by payment follow the arrivals:**
    {_paid_jul_sep:.0%} of the cases that end with `Payment` are closed in
    July to September (25% if uniform). *Interpretation:* many fines are
    paid within a few days of the offence (variant `Create Fine -> Payment`,
    Part 1, Task 4.1.1b), so these closures copy the summer peak of the
    arrivals with almost no delay.

    **Finding 3, end-of-log effect:** cases whose last event is
    `Send Fine` jump to {_last_two.iloc[0]:,} and {_last_two.iloc[1]:,} in the
    last two months of the log ({_last_two.index[0]:%Y-%m} and
    {_last_two.index[1]:%Y-%m}), compared with a median of
    {_median_before:.0f} per month before. *Interpretation:* these cases
    are not really closed. They were still running when the log was
    extracted. When we analyse closures or cycle times, we should leave
    out the cases from the last months of the log.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(df, mo, px):
    # Task 5.2c: activity load of Send for Credit Collection and Send Appeal to Prefecture
    _acts = ['Send for Credit Collection', 'Send Appeal to Prefecture']
    _ev = df[df['concept:name'].isin(_acts)].copy()
    _ev['day'] = _ev['time:timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize()
    _daily = _ev.groupby(['concept:name', 'day']).size().reset_index(name='events')

    _fig = px.scatter(
        _daily, x='day', y='events', facet_row='concept:name', height=600,
        category_orders={'concept:name': _acts},
        title='Events per day (one dot per day with at least one event, own y-axis per row)',
    )
    _fig.update_yaxes(matches=None, title='')
    _fig.update_traces(marker_size=8)
    _fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))

    # Send for Credit Collection
    _cc = _daily[_daily['concept:name'] == 'Send for Credit Collection'].set_index('day')['events']
    _cc_years = set(_cc.index.year)
    _no_cc_years = [y for y in range(_ev['day'].dt.year.min(), _ev['day'].dt.year.max() + 1) if y not in _cc_years]
    _cc_christmas = _cc[(_cc.index.month == 12) & (_cc.index.day == 25)]

    # Send Appeal to Prefecture
    _ap = _daily[_daily['concept:name'] == 'Send Appeal to Prefecture'].set_index('day')['events']
    _ap_max_day = _ap.idxmax()
    _ap_without_max = _ap.drop(_ap_max_day)
    _ap_sundays_other = int(_ap_without_max[_ap_without_max.index.dayofweek == 6].sum())

    mo.vstack([
        mo.md(r"""
    **Hypotheses:** (1) `Send for Credit Collection` hands cases over to an
    external agency, so we expect it to be done in batches (e.g. a few
    times per year) rather than every day. (2) `Send Appeal to Prefecture`
    depends on individual offenders, so we expect a continuous load with
    a few appeals on most days.
    """),
        mo.ui.plotly(_fig),
        mo.md(f"""
    **Finding 1, credit collection happens on only {len(_cc)} days:** all
    {_cc.sum():,} `Send for Credit Collection` events are recorded on just
    {len(_cc)} days in {_ev['day'].dt.year.nunique()} years, with up to
    {_cc.max():,} cases on one day. In {', '.join(str(y) for y in _no_cc_years)}
    there is no batch at all. So hypothesis (1) is confirmed, and the
    batching is even more extreme than we expected: about one batch per
    year. The batch of {', '.join(f'{d:%Y-%m-%d}' for d in _cc_christmas.index)}
    is dated on Christmas Day.
    *Interpretation:* unpaid fines wait until the next yearly batch, so
    the time until credit collection depends mostly on the batch dates.
    This causes long and very different waiting times. A batch on
    Christmas Day is unlikely to be real work, so the date may be a
    placeholder from a data migration. We would ask the data providers.

    **Finding 2, appeals are continuous, with one outlier day:**
    `Send Appeal to Prefecture` occurs on {len(_ap):,} different days, so
    hypothesis (2) is confirmed. But on {_ap_max_day:%Y-%m-%d} (a {_ap_max_day:%A}, Christmas Day)
    there are {_ap.max():,} appeals sent in one day, which is
    {_ap.max() / _ap.sum():.0%} of all appeals in the log. Apart from this
    day, only {_ap_sundays_other} appeals are recorded on a Sunday at all.
    *Interpretation:* this is very likely not real work but a bulk entry
    of older appeals, e.g. a backlog that was recorded in one go. Again a
    Christmas date, like one of the credit collection batches. For the
    data collection, we would suggest recording the real date of each
    activity and not the date of data entry.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 5.3
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, pd, px):
    # Task 5.3: cycle time (first to last event, in days, Italian local dates)
    _local = df.assign(local_day=df['time:timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize())
    _cases = _local.groupby('case:concept:name')
    _cycle_time = (_cases['local_day'].max() - _cases['local_day'].min()).dt.days
    _activities = _cases['concept:name'].apply(set)

    _sent_to_cc = _activities.apply(lambda s: 'Send for Credit Collection' in s)
    # fully paid = at least one payment, and the payments cover the final amount
    # plus all expenses (outstanding amount <= 0 at the end, cf. Part 1, Task 2.2.5)
    _fully_paid = _activities.apply(lambda s: 'Payment' in s) & \
        (_cases['paymentAmount'].sum() >= _cases['amount'].last() + _cases['expense'].sum() - 0.01)

    _a = _cycle_time[_sent_to_cc]
    _b = _cycle_time[_fully_paid]
    _plot = pd.concat([
        pd.DataFrame({'group': '(a) sent to credit collection', 'cycle_time_days': _a}),
        pd.DataFrame({'group': '(b) fully paid', 'cycle_time_days': _b}),
    ])
    _fig = px.histogram(
        _plot, x='cycle_time_days', facet_row='group', height=550,
        title='Cycle time per case (bins of 30 days, own y-axis per row)',
    )
    _fig.update_traces(xbins=dict(start=0, size=30))
    _fig.update_yaxes(matches=None, title='')
    _fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))

    _stats = pd.DataFrame({
        '(a) sent to credit collection': _a.describe(percentiles=[.1, .5, .9]),
        '(b) fully paid': _b.describe(percentiles=[.1, .5, .9]),
    }).T.round(0).rename_axis('cycle time in days').reset_index()

    mo.vstack([
        mo.md(r"""
    **Definitions:** The *cycle time* of a case is the number of days
    between its first and its last event (Italian local dates). A case is
    *sent to credit collection* if it contains `Send for Credit Collection`.
    A case is *fully paid* if it has at least one `Payment` and the
    payments cover the final `amount` plus all expenses, i.e. nothing is
    owed at the end of the case. This is stricter than the "paid" outcome
    of Part 1 (Task 3.1), which also counted cases that were paid off at
    some point but owed money again later.
    """),
        mo.ui.plotly(_fig),
        mo.ui.table(_stats),
        mo.md(f"""
    **(a) Cases sent to credit collection ({len(_a):,} cases):** these
    cases are very slow. The median cycle time is {_a.median():.0f} days
    (about {_a.median() / 365:.1f} years), and no case is faster than
    {_a.min():.0f} days, because a case must first be sent, notified and
    penalized before it can go to credit collection. The histogram has
    several separate peaks instead of one smooth hump. This fits the
    yearly credit collection batches (Task 5.2c): the cycle time depends
    on which batch a case falls into.

    **(b) Fully paid cases ({len(_b):,} cases):** most of these cases are
    very fast. The median is only {_b.median():.0f} days, and
    {(_b <= 30).mean():.0%} are closed within 30 days. These are the fines
    paid directly after `Create Fine`. But the distribution has a long
    tail: {(_b > 365).mean():.0%} take more than a year, up to
    {_b.max():,.0f} days. These are cases that are paid only after the
    penalty or in installments (Task 5.1b).
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 5.4
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, pd, px):
    # Task 5.4a: delay (in days) between each pair of subsequent activities of S,
    # using the first occurrence of each activity per case and Italian local dates
    _S = ['Create Fine', 'Send Fine', 'Insert Fine Notification', 'Add penalty', 'Send for Credit Collection']
    _local = df.assign(local_day=df['time:timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize())
    _first = _local[_local['concept:name'].isin(_S)] \
                 .groupby(['case:concept:name', 'concept:name'])['local_day'].first().unstack()
    s_delays = pd.DataFrame({f'{a} -> {b}': (_first[b] - _first[a]).dt.days for a, b in zip(_S, _S[1:])})

    _figs = []
    for _pair, _bin in zip(s_delays.columns, [1, 1, 1, 7]):
        _d = s_delays[_pair].dropna()
        _f = px.histogram(x=_d, height=300, title=f'{_pair} ({len(_d):,} cases, bins of {_bin} day(s))')
        _f.update_traces(xbins=dict(size=_bin))
        _f.update_xaxes(title='delay in days')
        _f.update_yaxes(title='cases')
        _figs.append(mo.ui.plotly(_f))

    _d1, _d2, _d3, _d4 = (s_delays[c].dropna() for c in s_delays.columns)

    mo.vstack([mo.md(r"""
    **Definition:** For each case we take the date of the *first*
    occurrence of each activity of S (Italian local dates) and compute
    the delay in days between two subsequent activities. A case only
    counts for a pair if it contains both activities.
    """)] + _figs + [mo.md(f"""
    **Observations, one per distribution:**

    1. **Create Fine -> Send Fine:** the median delay is {_d1.median():.0f}
       days. The number of letters per day stays high up to about 145
       days and then suddenly drops: {(_d1 <= 150).mean():.1%} of the letters are
       sent within 150 days. So the letters seem to be sent just before a
       deadline (see Task 5.4c).
    2. **Send Fine -> Insert Fine Notification:** the median transit time
       of the letter is {_d2.median():.0f} days, but the distribution has
       several separate peaks (see Task 5.4d).
    3. **Insert Fine Notification -> Add penalty:** the delay is exactly
       {_d3.min():.0f} days in all {len(_d3):,} cases (min = max =
       {_d3.max():.0f}). The penalty is added automatically on the day the
       60-day payment deadline ends, without any exception.
    4. **Add penalty -> Send for Credit Collection:** the shortest delay is
       {_d4.min():.0f} days, the median {_d4.median():.0f} days and the
       maximum {_d4.max():,.0f} days. The histogram has several separate
       peaks, because credit collection is done in batches (Task 5.2c):
       an unpaid case waits for the next batch, more than a year in the
       median.
    """)])
    return (s_delays,)


@app.cell(hide_code=True)
def _(mo, s_delays):
    # Task 5.4b: proposals to improve the performance of the subprocess
    _send = s_delays['Create Fine -> Send Fine'].dropna()
    _cc = s_delays['Add penalty -> Send for Credit Collection'].dropna()

    mo.md(f"""
    **Proposed changes:**

    1. **Send the fine letter earlier.** `Create Fine -> Send Fine` takes
       {_send.median():.0f} days in the median, so the offender only learns
       about the fine after about {_send.median() / 30:.0f} months. We see
       no reason in the process for this wait: the letters seem to be sent just before the
       legal deadline (Task 5.4c). Sending them e.g. every week would
       shorten every case that gets a letter by weeks, and it removes the
       risk that a fine becomes invalid because the deadline is missed.
    2. **Send unpaid fines for credit collection more often.**
       `Add penalty -> Send for Credit Collection` takes
       {_cc.median():.0f} days in the median, mainly because there is only
       about one batch per year (Task 5.2c), and each batch only takes
       fines that are already several months old (Task 5.5). A monthly or
       quarterly batch without such an early cut-off would cut
       this waiting time to a few months. The older a debt is, the harder
       it usually is to collect, so this should also bring in more money.
    3. **Keep the 60-day deadline, but check payments first.** The delay
       `Insert Fine Notification -> Add penalty` is fixed by law, so it
       can't be shortened. But the penalty is added automatically even
       when the fine was already paid (Part 1, Task 3.1c). A check before
       `Add penalty` would avoid unnecessary penalties and the extra
       payments and rework they cause (Task 5.1b).
    4. **Notify electronically where possible.** The transit time of the
       letter has a second peak when the offender is not at home (Task
       5.4d). An electronic notification (e.g. by certified e-mail) would
       avoid this delay and the postal expense.
    """)
    return


@app.cell(hide_code=True)
def _(mo, px, s_delays):
    # Task 5.4c: which deadline for Send Fine does the distribution suggest?
    _d = s_delays['Create Fine -> Send Fine'].dropna()
    _fig = px.histogram(x=_d[_d <= 400], height=350,
                        title='Create Fine -> Send Fine, zoomed to 0-400 days (bins of 1 day)')
    _fig.update_traces(xbins=dict(size=1))
    _fig.add_vline(x=150, line_dash='dot', line_color='gray', annotation_text='150 days')
    _fig.update_xaxes(title='delay in days')
    _fig.update_yaxes(title='cases')

    _per_day = _d.value_counts().sort_index()
    _before = _per_day.loc[130:145].mean()
    _after = _per_day.loc[151:165].mean()
    _late = _d[_d > 150]

    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(f"""
    The distribution suggests a deadline of **150 days** after the fine
    was created. Up to about 145 days the number of letters per day stays
    high (on average {_before:.0f} per day for 130 to 145 days), and then
    it drops sharply to {_after:.0f} per day for 151 to 165 days. In total,
    {(_d <= 150).mean():.1%} of the letters are sent within 150 days. Such
    a cliff only makes sense if there is a hard limit that the police
    tries not to exceed. They send many letters as late as possible, but
    almost never after day 150. The few later letters
    ({len(_late):,} cases, {len(_late) / len(_d):.1%}) are probably the
    letters sent abroad, which have a longer deadline.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(df, mo, px, s_delays):
    # Task 5.4d: peaks in the transit time of the Send Fine letter
    _d = s_delays['Send Fine -> Insert Fine Notification'].dropna()
    _fig = px.histogram(x=_d[_d <= 60], height=350,
                        title='Send Fine -> Insert Fine Notification, zoomed to 0-60 days (bins of 1 day)')
    _fig.update_traces(xbins=dict(size=1))
    _fig.update_xaxes(title='transit time in days')
    _fig.update_yaxes(title='cases')

    _per_day = _d.value_counts().sort_index()
    _peak_1 = _per_day.loc[3:12].idxmax()
    _peak_2 = _per_day.loc[13:30].idxmax()

    # the 0-day peak: is there a postal expense at all?
    _send = df[df['concept:name'] == 'Send Fine'].set_index('case:concept:name')['expense']
    _no_expense_0 = (_send.reindex(_d[_d == 0].index) == 0).mean()
    _no_expense_other = (_send.reindex(_d[_d > 0].index) == 0).mean()

    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(f"""
    We see **three major peaks**:

    1. **At 0 days ({_per_day.loc[0]:,} cases):** the fine is sent and
       received on the same day. In {_no_expense_0:.0%} of these cases the
       `expense` of `Send Fine` is 0, compared with {_no_expense_other:.1%}
       of the other cases. So no letter was mailed. We think the fine was
       handed directly to the offender, e.g. on the spot.
    2. **At about {_peak_1:.0f} days ({_per_day.loc[_peak_1]:,} cases on the
       highest day):** the normal case, in which the registered letter is
       delivered to the offender about one week after it was sent.
    3. **At about {_peak_2:.0f} days ({_per_day.loc[_peak_2]:,} cases on the
       highest day):** about {_peak_2 - _peak_1:.0f} days after the first
       postal peak. We think the offender was not at home when the
       letter was delivered, so it was left at the post office and only
       picked up (or counted as received) later. Because this extra
       waiting time is similar for many offenders, it creates a second,
       separate peak instead of just a longer tail.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 5.5
    """)
    return


@app.cell(hide_code=True)
def _(df, go, mo):
    # Task 5.5: performance spectrum for the two activities of Task 5.2c.
    # Each line is one case, from the date of the first activity (top) to the
    # date of the second activity (bottom), in Italian local time.
    _local = df.assign(local_day=df['time:timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize())
    _first = _local.groupby(['case:concept:name', 'concept:name'])['local_day'].first().unstack()

    def _spectrum(a, b, groups, title):
        _fig = go.Figure()
        for _name, _sub in groups:
            _xs, _ys = [], []
            for _s, _e in zip(_sub[a], _sub[b]):
                _xs += [_s, _e, None]
                _ys += [1, 0, None]
            _fig.add_trace(go.Scattergl(x=_xs, y=_ys, mode='lines', name=_name, opacity=0.3, line=dict(width=1)))
        _fig.update_yaxes(tickvals=[1, 0], ticktext=[a, b], range=[-0.1, 1.1])
        _fig.update_layout(title=title, height=350)
        return _fig

    # segment 1: Add penalty -> Send for Credit Collection (random sample of cases to keep the chart light)
    _cc = _first.dropna(subset=['Add penalty', 'Send for Credit Collection'])
    _cc_sample = _cc.sample(3000, random_state=0)
    _fig_cc = _spectrum('Add penalty', 'Send for Credit Collection',
                        [('sample of 3,000 cases', _cc_sample)],
                        'Performance spectrum: Add penalty -> Send for Credit Collection')

    # which fines does each batch contain?
    _batches = _cc.groupby('Send for Credit Collection').agg(
        no_of_cases=('Add penalty', 'size'),
        latest_create_fine=('Create Fine', 'max'),
        earliest_penalty=('Add penalty', 'min'),
        latest_penalty=('Add penalty', 'max'),
    ).rename_axis('batch').reset_index()
    _batches['days_from_latest_fine_to_batch'] = (_batches['batch'] - _batches['latest_create_fine']).dt.days
    # stragglers: cases whose penalty is older than the newest penalty of the previous batch
    _prev_latest = _batches['latest_penalty'].shift()
    _cc_with_prev = _cc.merge(_batches[['batch']].assign(prev_latest_penalty=_prev_latest),
                              left_on='Send for Credit Collection', right_on='batch')
    _n_stragglers = int((_cc_with_prev['Add penalty'] <= _cc_with_prev['prev_latest_penalty']).sum())

    # segment 2: Insert Date Appeal to Prefecture -> Send Appeal to Prefecture
    _ap = _first.dropna(subset=['Insert Date Appeal to Prefecture', 'Send Appeal to Prefecture'])
    _outlier_day = _ap['Send Appeal to Prefecture'].value_counts().idxmax()
    _on_outlier = _ap['Send Appeal to Prefecture'] == _outlier_day
    _fig_ap = _spectrum('Insert Date Appeal to Prefecture', 'Send Appeal to Prefecture',
                        [('other days', _ap[~_on_outlier]), (f'sent on {_outlier_day:%Y-%m-%d}', _ap[_on_outlier])],
                        'Performance spectrum: Insert Date Appeal to Prefecture -> Send Appeal to Prefecture')
    _ap_delay = (_ap['Send Appeal to Prefecture'] - _ap['Insert Date Appeal to Prefecture']).dt.days
    _n_inserted_after = int((_ap_delay[_on_outlier] < 0).sum())

    mo.vstack([
        mo.ui.plotly(_fig_cc),
        mo.ui.table(_batches),
        mo.md(f"""
    **Refined finding 1, how the credit collection batches work:** in the
    spectrum, the lines of many different penalty dates come together in
    a few batch dates. To keep the chart readable, it shows a random sample
    of {len(_cc_sample):,} of the {len(_cc):,} cases; the table and all
    numbers below use all cases. The table shows which fines each batch contains:
    the newest fine in a batch was created
    {_batches['days_from_latest_fine_to_batch'].min()} to
    {_batches['days_from_latest_fine_to_batch'].max()} days before the
    batch (median {_batches['days_from_latest_fine_to_batch'].median():.0f}).
    So a batch only contains fines that are already several months old,
    which looks like a cut-off date set well before each batch. The lines also cross: {_n_stragglers:,} cases
    ({_n_stragglers / len(_cc):.1%}) have a penalty older than the newest
    penalty of the *previous* batch, i.e. they were skipped once and only
    collected in a later batch. So the batches are mostly, but not
    strictly, first-in-first-out (FIFO). This refines Task 5.2c: the
    yearly batch is not only rare, it also leaves out all fines newer than
    the cut-off, which adds to the long waiting time.
    """),
        mo.ui.plotly(_fig_ap),
        mo.md(f"""
    **Refined finding 2, the outlier day of the appeals is a backlog:** for
    normal appeals the lines are short and almost vertical: the median
    delay between insertion and sending is
    {_ap_delay[~_on_outlier].median():.0f} days. The
    {int(_on_outlier.sum())} appeals sent on {_outlier_day:%Y-%m-%d} are very
    different. Their lines come from all over the time axis: they were
    inserted between {_ap.loc[_on_outlier, 'Insert Date Appeal to Prefecture'].min():%Y-%m-%d}
    and {_ap.loc[_on_outlier, 'Insert Date Appeal to Prefecture'].max():%Y-%m-%d}
    (median delay {_ap_delay[_on_outlier].median():,.0f} days). {_n_inserted_after}
    of them were even inserted *after* they were supposedly sent, which
    is impossible. This confirms our guess from Task 5.2c: the date is not
    the real sending date. It looks like many old appeals were recorded in
    one go with a placeholder date. For the analysis, the
    `Send Appeal to Prefecture` timestamps of these cases should not be
    used.
    """),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 5.6
    """)
    return


@app.cell(hide_code=True)
def _(df, mo):
    # Task 5.6: article chooser for the interactive visualization (most frequent articles first)
    _counts = df.loc[df['concept:name'] == 'Create Fine', 'article'].value_counts()
    article_dropdown = mo.ui.dropdown(
        options={f'{a:g} ({n:,} cases)': a for a, n in _counts.items()},
        value=f'{_counts.index[0]:g} ({_counts.iloc[0]:,} cases)',
        label='Choose an article of the traffic law:',
    )
    article_dropdown
    return (article_dropdown,)


@app.cell(hide_code=True)
def _(article_dropdown, df, mo, px):
    # Task 5.6: initial fine amount over time for the chosen article
    _article = article_dropdown.value
    _cf = df[(df['concept:name'] == 'Create Fine') & (df['article'] == _article)].copy()
    _cf['creation_date'] = _cf['time:timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize()

    # one dot per day and amount (instead of one per case) keeps the chart light
    _points = _cf.groupby(['creation_date', 'amount']).size().reset_index(name='no_of_cases')
    _fig = px.scatter(
        _points, x='creation_date', y='amount', hover_data=['no_of_cases'], opacity=0.5,
        title=f'Initial fine amount over time for article {_article:g} (one dot per day and amount)',
    )
    _fig.update_traces(marker_size=5)
    _fig.update_xaxes(title='date of Create Fine')
    _fig.update_yaxes(title='initial fine amount')

    _per_year = _cf.groupby(_cf['creation_date'].dt.year.rename('year'))['amount'].agg(
        no_of_cases='size',
        most_frequent_amount=lambda s: s.mode().iloc[0],
        share_of_most_frequent=lambda s: f'{(s == s.mode().iloc[0]).mean():.1%}',
        no_of_distinct_amounts='nunique',
    ).reset_index()

    mo.vstack([mo.ui.plotly(_fig), mo.ui.table(_per_year)])
    return


@app.cell(hide_code=True)
def _(df, go, mo):
    # Task 5.6: the same chart with a dropdown built into the plotly figure, so it
    # also works in the static HTML export (the marimo dropdown needs a running notebook)
    _cf = df[df['concept:name'] == 'Create Fine'].copy()
    _cf['creation_date'] = _cf['time:timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize()
    _points = _cf.groupby(['article', 'creation_date', 'amount']).size().reset_index(name='no_of_cases')
    _articles = _cf['article'].value_counts()  # most frequent article first

    _fig = go.Figure()
    for _i, _art in enumerate(_articles.index):
        _p = _points[_points['article'] == _art]
        _fig.add_trace(go.Scatter(
            x=_p['creation_date'], y=_p['amount'], customdata=_p['no_of_cases'],
            mode='markers', marker=dict(size=5, opacity=0.5), visible=(_i == 0),
            name=f'{_art:g}', hovertemplate='%{x|%Y-%m-%d}<br>amount: %{y}<br>cases: %{customdata}<extra></extra>',
        ))

    _n_articles = len(_articles)
    _buttons = [
        dict(
            label=f'{art:g} ({n:,} cases)', method='update',
            args=[{'visible': [j == i for j in range(_n_articles)]},
                  {'title': f'Initial fine amount over time for article {art:g} (one dot per day and amount)'}],
        )
        for i, (art, n) in enumerate(_articles.items())
    ]
    _fig.update_layout(
        updatemenus=[dict(buttons=_buttons, direction='down', x=0, xanchor='left', y=1.18, yanchor='top')],
        title=dict(text=f'Initial fine amount over time for article {_articles.index[0]:g} (one dot per day and amount)', y=0.97),
        margin=dict(t=110), height=450, showlegend=False,
        xaxis_title='date of Create Fine', yaxis_title='initial fine amount',
    )

    mo.vstack([
        mo.md("""
    **Static version for the HTML export:** the marimo dropdown above only
    updates the chart while the notebook is running. This chart has its
    own dropdown (top left), which also works in the exported HTML file.
    """),
        mo.ui.plotly(_fig),
    ])
    return


@app.cell(hide_code=True)
def _(df, mo):
    # Task 5.6: findings for the example article 157 (independent of the dropdown)
    _cf = df[(df['concept:name'] == 'Create Fine') & (df['article'] == 157)].copy()
    _cf['creation_date'] = _cf['time:timestamp'].dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize()
    _year = _cf['creation_date'].dt.year

    _share_mode = _cf.groupby(_year)['amount'].agg(lambda s: (s == s.mode().iloc[0]).mean())
    # month in which the most frequent amount changes
    _monthly = _cf.groupby(_cf['creation_date'].dt.to_period('M'))['amount'].agg(lambda s: s.mode().iloc[0])
    _changes = _monthly[_monthly != _monthly.shift()]
    _decreases = _changes[_changes < _changes.shift()]

    mo.md(f"""
    **Findings for the example article 157 (stopping and parking):**

    - **One amount per period:** in every year, at least
      {_share_mode.min():.1%} of the article 157 fines have the same
      initial amount. In the chart this gives horizontal lines that change
      in steps, so the amount depends only on the article and on the
      date, not on the individual case.
    - **Changes in January:** the amount changes in
      {', '.join(f"{p.strftime('%Y-%m')} (to {a:g})" for p, a in _changes.iloc[1:].items())}.
      From 2003 on this happens every two years, always in January. Such
      a regular pattern looks like a planned adjustment of all fine
      amounts, e.g. to inflation, and not like individual decisions. In
      total, the fine rises from
      {_changes.iloc[0]:g} to {_changes.iloc[-1]:g}
      (+{_changes.iloc[-1] / _changes.iloc[0] - 1:.0%}).
    - **One decrease:** the only step down is in
      {', '.join(p.strftime('%Y-%m') for p in _decreases.index)} (to
      {', '.join(f'{a:g}' for a in _decreases.values)}). This is when Italy
      switched from lira to euro, so we think the amount was rounded when
      it was converted.

    *Interpretation:* this is a clear concept drift. The same offence
    costs different amounts at different times, so amounts should only be
    compared within the same tariff period. For the data collection, we
    would suggest recording the tariff version used for each fine.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 5.7
    """)
    return


@app.cell(hide_code=True)
def _(df, mo, pd, px, s_delays):
    # Task 5.7: Create Fine -> Send Fine for cases starting after Sept 1, 2010 vs. the full log (Task 5.4)
    _start = df[df['concept:name'] == 'Create Fine'].set_index('case:concept:name')['time:timestamp'] \
                 .dt.tz_convert('Europe/Rome').dt.tz_localize(None).dt.normalize()
    _n_cases_after = int((_start > pd.Timestamp('2010-09-01')).sum())
    _full = s_delays['Create Fine -> Send Fine'].dropna()
    _after = _full[_start.reindex(_full.index) > pd.Timestamp('2010-09-01')]

    _plot = pd.concat([
        pd.DataFrame({'cases': 'full log (Task 5.4)', 'delay_days': _full}),
        pd.DataFrame({'cases': 'cases starting after 2010-09-01', 'delay_days': _after}),
    ])
    _fig = px.histogram(
        _plot[_plot['delay_days'] <= 300], x='delay_days', color='cases', histnorm='percent',
        barmode='overlay', opacity=0.6, height=400,
        title='Create Fine -> Send Fine (share of cases per bin of 5 days, up to 300 days)',
    )
    _fig.update_traces(xbins=dict(start=0, size=5))
    _fig.update_xaxes(title='delay in days')
    _fig.update_yaxes(title='% of cases')

    _per_day = _after.value_counts().sort_index()
    _before_drop = _per_day.reindex(range(45, 60), fill_value=0).mean()
    _after_drop = _per_day.reindex(range(65, 80), fill_value=0).mean()

    # robustness: cases from the last 150 days of the log might not have their
    # Send Fine yet, which would favour short delays, so check without them
    _log_end = df['time:timestamp'].max().tz_convert('Europe/Rome').tz_localize(None).normalize()
    _complete = _after[_start.reindex(_after.index) <= _log_end - pd.Timedelta(days=150)]

    mo.vstack([
        mo.ui.plotly(_fig),
        mo.md(f"""
    After filtering, {_n_cases_after:,} cases remain, and {len(_after):,} of
    them have a `Send Fine`. Compared with the full log, the distribution
    is very different:

    - **Letters are sent much earlier:** the median delay is
      {_after.median():.0f} days instead of {_full.median():.0f} days.
    - **The cliff at 150 days is gone.** Instead, most letters are sent
      within about two months: {(_after <= 60).mean():.0%} within 60 days
      (full log: {(_full <= 60).mean():.0%}). After about 60 days the number
      of letters per day drops from {_before_drop:.0f} (45 to 59 days) to
      {_after_drop:.0f} (65 to 79 days), and {(_after <= 90).mean():.0%} are
      sent within 90 days.

    **Check for an end-of-log effect:** cases that start in the last 150
    days of the log might not have their `Send Fine` yet, which would favour
    short delays. Without these cases ({len(_complete):,} cases left), the
    result is the same: median {_complete.median():.0f} days,
    {(_complete <= 60).mean():.0%} within 60 days and
    {(_complete <= 90).mean():.0%} within 90 days. So the shift is real and
    not caused by the end of the log.

    *Interpretation:* such a sudden and lasting change in the sending
    behaviour suggests that the legal deadline for the fine was shortened
    around 2010. The letter still needs one to three weeks to be
    delivered (Task 5.4d), so the police now seems to send most letters
    within about 60 days, so that they still arrive in time. The
    {(_after > 90).mean():.0%} of letters sent after 90 days could be
    letters sent abroad or letters that were sent too late. This is a clear concept drift:
    the full-log distribution in Task 5.4 mixes two different periods, so
    the 150-day deadline from Task 5.4c only holds for cases before the
    change.
    """),
    ])
    return


if __name__ == "__main__":
    app.run()
