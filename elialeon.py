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


@app.cell
def _(pm4py):
    event_log_from_disk =  pm4py.read_xes('Road_Traffic_Fine_Management_Process.xes', variant="rustxes")
    # The XES file stores local (Italian) midnight as 22:00/23:00 UTC (cf. Session 2, Task 1).
    # We work in local time throughout so that calendar dates are correct.
    event_log_from_disk["time:timestamp"] = event_log_from_disk["time:timestamp"].dt.tz_convert("Europe/Rome")

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


@app.cell
def _(event_log_from_disk):
    # a) Time interval covered by the log
    log_start = event_log_from_disk["time:timestamp"].min()
    log_end = event_log_from_disk["time:timestamp"].max()
    print("Log start:", log_start)
    print("Log end:", log_end)
    _events_per_day = event_log_from_disk["time:timestamp"].dt.date.value_counts().sort_index()
    print("Events on the first days:", _events_per_day.head(5).to_dict())
    print("Events on the last days:", _events_per_day.tail(3).to_dict())
    return


@app.cell
def _(event_log_from_disk):
    # b) Distinct values of the attribute vehicleClass
    vehicle_classes = event_log_from_disk["vehicleClass"].dropna().unique()
    n_vehicle_classes = event_log_from_disk["vehicleClass"].nunique(dropna=True)
    print("Distinct vehicleClass values:", sorted(vehicle_classes))
    print("Number of distinct vehicleClass values:", n_vehicle_classes)
    return


@app.cell
def _(event_log_from_disk):
    # c) min, median, max of the initial `amount` (at Create Fine events)
    create_fine_events = event_log_from_disk[
        event_log_from_disk["concept:name"] == "Create Fine"
    ]
    initial_amount = create_fine_events["amount"]

    print("min amount:", initial_amount.min())
    print("median amount:", initial_amount.median())
    print("max amount:", initial_amount.max())
    print(initial_amount.describe())
    return


@app.cell
def _(event_log_from_disk):
    # d) Events with points > 0: which activities, how many cases affected
    events_with_points = event_log_from_disk[event_log_from_disk["points"] > 0]

    print("Number of events with points > 0:", len(events_with_points))
    print("Associated activities:", events_with_points["concept:name"].unique())
    print("Activity value counts:")
    print(events_with_points["concept:name"].value_counts())
    print("Number of cases affected:", events_with_points["case:concept:name"].nunique())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a) What time interval does the log cover?**

    The log spans from **2000-01-01** to **2013-06-18** (local Italian time), i.e. about 13.5 years. This matches the `log_start_time` `2000-01-01T00:00:00+01:00` given in `DATA.xml`. In raw UTC the first event would appear as 1999-12-31 23:00, which is only the time-zone offset. The first day (a public holiday) has a single event, followed by a normal ramp-up (4, 39, 51, 61 events on the next days), so the start looks like a genuine cut-off of the extraction rather than a data quality problem.

    **b) How many distinct values for the attribute `vehicleClass` does the log have?**

    There are **4** distinct values: `A`, `C`, `M`, `R`.

    **c) What are min, median, max of the initial value of `amount` (at Create Fine events)?**

    - min = **0.0**
    - median = **35.0**
    - max = **4351.0**

    *Reflection:* A fine `amount` of **0** (36 cases) is suspicious — a traffic fine with no monetary value seems like a data quality issue or a special dismissal/exemption case that should be investigated further (e.g., is it linked to a specific `article` or `dismissal` value?). Likewise, the **max of 4351** is far above the 75th percentile (~38) and the next-highest values (798, 1626, 1725, 1842, 1886, 4000) — these outliers should be checked for correctness (e.g., possible data entry errors, or legitimately severe/aggravated offenses combining multiple penalties) before being used in further analysis such as averages.

    **d) How many events have `points` > 0? Which activities? How many cases are affected?**

    - **3,548** events have `points > 0`.
    - They are **all** associated with the **`Create Fine`** activity (i.e., point deductions are recorded at fine creation, consistent with the process description).
    - **3,548** distinct cases are affected — i.e., exactly one `points`-bearing event per case, meaning each affected case has its penalty points recorded only once (at creation), not repeated at later activities.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 2

    ## Part 1: Schema Analysis, Case Inspection

    ### 1. Timestamp granularity
    """)
    return


@app.cell
def _(event_log_from_disk):
    # 1) Check timestamp granularity: compare the raw UTC representation with local Italian time
    # (the log was converted to Europe/Rome right after loading).
    ts_local = event_log_from_disk["time:timestamp"]
    ts = ts_local.dt.tz_convert("UTC")

    print("Distinct hour values (UTC, as stored in the XES file):", sorted(ts.dt.hour.unique()))
    print("Distinct second values (UTC):", ts.dt.second.unique())
    print("Distinct microsecond values (UTC):", ts.dt.microsecond.unique())

    print("Distinct local (Europe/Rome) hour values:", ts_local.dt.hour.unique())
    print("Distinct local (Europe/Rome) minute values:", ts_local.dt.minute.unique())
    print("Distinct local (Europe/Rome) second values:", ts_local.dt.second.unique())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **1) Which granularity do the timestamps of the log have?**

    At first glance the timestamps look like they have minute-level granularity (times like `22:00:00` or `23:00:00` UTC). But converting to the local Italian timezone (`Europe/Rome`) shows that **every single timestamp falls exactly on local midnight** (hour=0, minute=0, second=0). This means the log actually only has **daily granularity**: the time-of-day component carries no information, and the apparent `22:00`/`23:00` UTC values are simply midnight in CET/CEST shifted into UTC (depending on whether daylight saving time applies).

    **Consequence for the rest of the notebook:** we convert all timestamps to `Europe/Rome` directly after loading, so that dates are correct (in UTC every date would be one day too early). For day differences we compare calendar dates, because absolute durations across a daylight-saving switch are one hour short (59 days 23 h instead of 60 days).

    *Reflection:* This matters for later analysis — e.g. when computing durations in hours or comparing events that occur "on the same day", and it already foreshadows the `totalPaymentAmount` ordering issue we find in Task 4 below (same-day events have no reliable sub-day order).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2. Activity schema analysis
    """)
    return


@app.cell
def _(event_log_from_disk):
    # 2) Build the schema (set of attributes with at least one non-null value) for each activity.
    MANDATORY_COLS = ["case:concept:name", "time:timestamp", "concept:name"]
    GLOBAL_COLS = MANDATORY_COLS + ["lifecycle:transition"]  # constant 'complete' for every event
    local_attribute_cols = [c for c in event_log_from_disk.columns if c not in GLOBAL_COLS]

    activities = event_log_from_disk["concept:name"].unique()
    schema = {}
    missing_counts = {}
    for _act in activities:
        _sub = event_log_from_disk[event_log_from_disk["concept:name"] == _act]
        _cols_in_schema = [c for c in local_attribute_cols if _sub[c].notna().any()]
        schema[_act] = _cols_in_schema
        missing_counts[_act] = {c: int(_sub[c].isna().sum()) for c in _cols_in_schema}

    for _act in sorted(schema, key=lambda a: -len(event_log_from_disk[event_log_from_disk["concept:name"] == a])):
        print(f"{_act}: {schema[_act]}")
    return missing_counts, schema


@app.cell
def _(missing_counts, schema):
    # 2a) Which activity schemas have attributes with missing values?
    for _act, _cols in schema.items():
        for _col in _cols:
            _n_missing = missing_counts[_act][_col]
            if _n_missing > 0:
                print(f"{_act}.{_col}: {_n_missing} missing values")
    return


@app.cell
def _(schema):
    # 2b) Which non-global attributes are shared across more than one activity schema?
    from collections import defaultdict

    col_to_activities = defaultdict(list)
    for _act, _cols in schema.items():
        for _col in _cols:
            col_to_activities[_col].append(_act)

    shared_cols = {c: acts for c, acts in col_to_activities.items() if len(acts) > 1}
    for _col, _acts in shared_cols.items():
        print(f"{_col}: shared by {_acts}")
    return


@app.cell
def _(event_log_from_disk):
    # 2b continued) Inspect a case with both 'Add penalty' and 'Payment' to classify
    # 'amount' and 'totalPaymentAmount' as cumulative or incremental.
    sample_cols = [
        "time:timestamp", "concept:name", "amount", "totalPaymentAmount", "paymentAmount",
    ]
    sample_case_24 = event_log_from_disk[event_log_from_disk["case:concept:name"] == "A10000"]
    sample_case_24 = sample_case_24.sort_values("time:timestamp")
    sample_case_24[sample_cols]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **2) Inspect the schemas of all activities.**

    **a) Which activity schemas have attributes with missing values?**

    Only one attribute is incomplete: `lastSent` at activity **`Insert Fine Notification`**, which is missing for **1,631** of its 79,860 events. Every other local attribute is complete (no missing values) within the schema of the activity it belongs to.

    **b) Which non-global attributes are shared across more than one activity schema?**

    Four non-global attributes are shared:

    - **`amount`** — shared by `Create Fine` and `Add penalty`.
    - **`dismissal`** — shared by `Create Fine`, `Send Appeal to Prefecture`, and `Appeal to Judge`.
    - **`org:resource`** — shared by `Create Fine` and `Appeal to Judge`.
    - **`totalPaymentAmount`** — shared by `Create Fine` and `Payment`.

    Of these, `amount` and `totalPaymentAmount` are numerical. Looking at a sample case (`A10000`) that has both an `Add penalty` and a `Payment` event:

    - **`amount`** goes `36.0` (at Create Fine) → `74.0` (at Add penalty). This is **not** additive — it is a **restated value** representing the current total fine amount at that point in the case. We classify it as **case-cumulative** (a running *state*, re-written rather than summed).
    - **`totalPaymentAmount`** goes `0.0` (at Create Fine) → `87.0` (after a payment of `87.0`). This matches the sum of payments made so far in the case, so it is also **case-cumulative** (specifically a cumulative sum).

    Neither attribute is purely *incremental* (a standalone per-event number) — both carry forward a running value across events of the same case.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3. Case inspection
    """)
    return


@app.cell
def _(event_log_from_disk):
    # 3) Select a case with more than three events and inspect it event by event.
    inspection_cols = [
        "time:timestamp", "concept:name", "amount", "totalPaymentAmount", "paymentAmount",
        "expense", "dismissal", "points", "article", "vehicleClass", "notificationType",
        "org:resource", "matricola", "lastSent",
    ]
    case_A14727 = event_log_from_disk[event_log_from_disk["case:concept:name"] == "A14727"]
    case_A14727 = case_A14727.sort_values("time:timestamp")
    case_A14727[inspection_cols]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **3) Case A14727 (6 events) — event-by-event summary:**

    - **2007-06-27 — Create Fine**: Fine created for article 157 (stopping/parking), vehicle class `A`, initial `amount` = 36.0, 0 penalty points, `dismissal` initialized to `NIL` (not dismissed), handled by resource 557.
    - **2007-09-13 — Send Fine**: Notification sent to the offender; a postal `expense` of 13.0 is recorded (not yet reflected in `amount`).
    - **2007-10-04 — Insert Fine Notification**: Notification registered as received; `notificationType` = `P` (addressed to the car owner).
    - **2007-10-09 — Appeal to Judge**: The offender appeals to a judge; `dismissal` is (re-)set to `NIL` and `org:resource`/`matricola` are recorded as `0`, suggesting these fields are not meaningfully populated for this activity in this case (possibly a default/placeholder rather than a real resource).
    - **2007-12-03 — Add penalty**: Despite the pending appeal, a penalty is added and `amount` increases from 36.0 to 74.0.
    - **2009-08-17 — Payment**: Nearly two years after fine creation, a payment of 87.0 is registered, and `totalPaymentAmount` reaches 87.0 — exactly matching `amount` (74.0) plus the `expense` (13.0), i.e., the fine is now fully paid.

    *Reflection:* It is interesting that a penalty was added (2007-12-03) *after* an appeal to a judge was already filed (2007-10-09) and apparently not yet resolved — the log has no "Appeal to Judge" outcome activity, so we cannot tell from this log alone whether the appeal was rejected before the penalty was added, or whether the appeal and penalty tracks ran independently. This would be worth raising as an open question.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Part 2: Event Enrichment

    ### 4. Cumulative sum of payment amounts
    """)
    return


@app.cell
def _(event_log_from_disk):
    # 4) Add an attribute representing, for each case, the cumulative sum of payment
    # amounts after each event. We first make sure events are sorted by case and time
    # (sequential aggregation relies on this), then cumsum 'paymentAmount' per case,
    # treating missing payments as 0 so the running total starts at 0 like totalPaymentAmount does.
    event_log_enriched = event_log_from_disk.sort_values(
        ["case:concept:name", "time:timestamp"], kind="stable"
    ).reset_index(drop=True)

    # Sanity check required by sequential aggregation: timestamps must be non-decreasing per case.
    monotonic_ok = event_log_enriched.groupby("case:concept:name")[
        "time:timestamp"
    ].apply(lambda s: s.is_monotonic_increasing).all()
    print("Timestamps monotonic increasing within every case:", monotonic_ok)

    event_log_enriched["payment_amount_running_total"] = event_log_enriched.groupby(
        "case:concept:name"
    )["paymentAmount"].transform(lambda s: s.fillna(0).cumsum())
    return (event_log_enriched,)


@app.cell
def _(event_log_enriched):
    # 4a) Inspect a case to verify the enrichment.
    verify_cols = [
        "time:timestamp", "concept:name", "paymentAmount",
        "payment_amount_running_total", "totalPaymentAmount",
    ]
    event_log_enriched[event_log_enriched["case:concept:name"] == "A10000"][verify_cols]
    return


@app.cell
def _(event_log_enriched):
    # 4b) Compare our enrichment against the pre-existing totalPaymentAmount attribute,
    # restricted to rows where totalPaymentAmount is actually populated.
    comparison = event_log_enriched.dropna(subset=["totalPaymentAmount"]).copy()
    comparison["deviation"] = (
        comparison["totalPaymentAmount"] - comparison["payment_amount_running_total"]
    )
    deviating_rows = comparison[comparison["deviation"].abs() > 1e-6]

    print("Rows where totalPaymentAmount is populated:", len(comparison))
    print("Deviating rows:", len(deviating_rows))
    print("Distinct cases affected:", deviating_rows["case:concept:name"].nunique())
    print("Deviating activities:", deviating_rows["concept:name"].unique())
    print("Deviation sign: min =", round(deviating_rows["deviation"].min(), 2),
          ", max =", round(deviating_rows["deviation"].max(), 2),
          ", total =", round(deviating_rows["deviation"].sum(), 2))

    # Does the deviation persist until the last payment of the case?
    _last_payment = comparison[comparison["concept:name"] == "Payment"].groupby(
        "case:concept:name"
    ).tail(1)
    _persisting = _last_payment[_last_payment["deviation"].abs() > 1e-6]
    print("Cases whose deviation persists at the last payment:", len(_persisting))

    # Is the deviation equal to the amount of some payment of the same case
    # (i.e. one payment seems to be counted twice / missing as an event)?
    _first_dev = deviating_rows.groupby("case:concept:name").head(1)
    _payments_per_case = event_log_enriched[
        event_log_enriched["concept:name"] == "Payment"
    ].groupby("case:concept:name")["paymentAmount"].apply(lambda s: set(s.round(2)))
    _dev_equals_payment = _first_dev.apply(
        lambda r: round(r["deviation"], 2) in _payments_per_case[r["case:concept:name"]], axis=1
    )
    print("Cases where the deviation equals one of the case's payment amounts:",
          _dev_equals_payment.sum(), "of", len(_first_dev))
    return


@app.cell
def _(event_log_enriched):
    # 4b continued) Inspect one deviating case in detail.
    deviation_cols = [
        "time:timestamp", "concept:name", "paymentAmount",
        "payment_amount_running_total", "totalPaymentAmount",
    ]
    for _case in ["A22233", "C17607", "A12292"]:
        print("Case", _case)
        print(event_log_enriched[event_log_enriched["case:concept:name"] == _case][deviation_cols].to_string())
        print()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **4) Cumulative sum of payment amounts.**

    **a)** The enrichment `payment_amount_running_total` matches `totalPaymentAmount` on the inspected case `A10000`: both reach `87.0` after the single payment event.

    **b)** *Hypothesis before running the check:* `totalPaymentAmount` should match our enrichment everywhere it is populated (at `Create Fine` and `Payment`).

    The comparison (at the 227,971 events where `totalPaymentAmount` is populated) shows **95 deviating rows in 77 cases**, all at `Payment` events. That is rare (77 of ~69,700 cases with payments, ≈ 0.1 %) but systematic:

    - The deviation is **always positive** (`totalPaymentAmount` is higher than the sum of the recorded payments), between €1.98 and €180, €5,322 in total over all deviating rows.
    - In **75 of 77 cases** the deviation is exactly equal to the amount of a payment that occurs in the same case.

    Inspecting the deviating cases shows two different patterns:

    1. **Same-day payments (case `A12292`)**: two payments (49 + 87) are registered on the same day. `totalPaymentAmount` shows the end-of-day total (136) on *both* events, while our running total credits them one after the other. Because timestamps only have daily granularity (Task 1), the order of same-day events is unknown, so here the deviation is a temporary artefact and disappears at the last payment. This happens in 27 cases.
    2. **Persistent deviation (cases `C17607`, `A22233`)**: in **50 cases** the deviation never goes away. In `C17607` the offender pays €50 in monthly instalments; at the 11th instalment `totalPaymentAmount` jumps by €100 instead of €50 and ends at 687.75, while the recorded payments sum to 637.75. Neither value settles the fine: after the penalty the amount due is 1,377.07, so roughly €690–740 remain open either way. In `A22233` €87 are due (€74 + €13 expense); the recorded payments sum exactly to €87, whereas `totalPaymentAmount` shows €136.

    *Plausible explanation (hypothesis, not verified):* since the deviation almost always equals an existing payment amount of the case, a second payment with identical case, day and amount may have been lost from the event list (e.g. through de-duplication during log preparation; daily timestamps make such events indistinguishable). If so, `A22233` would contain an overpayment of €49 that is not visible in the event list (our `outstanding_amount` in Task 5a shows 0). Equally possible is that `totalPaymentAmount` itself was computed incorrectly, e.g. by counting a payment twice. The log alone cannot decide between the two; this would need to be clarified with the data provider.

    *Finding / recommendation:* record timestamps with full time-of-day precision and a unique payment/transaction ID per payment, so that repeated payments can be distinguished and `totalPaymentAmount` can be verified against individual payments. For these ~50 cases, analyses based on summing `paymentAmount` (such as our `outstanding_amount` below) and analyses based on `totalPaymentAmount` give different results.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 5. Outstanding amount
    """)
    return


@app.cell
def _(event_log_enriched):
    # 5) outstanding_amount = (latest fine amount + cumulative expenses) - cumulative payments.
    # 'amount' is case-cumulative/restated (cf. Task 2), so we forward-fill its latest value.
    # 'expense' is incremental and only occurs once (at Send Fine), so we cumsum it.
    # Money is rounded to 2 decimals after each arithmetic step (cf. lecture coding recommendations).
    event_log_outstanding = event_log_enriched.copy()
    _by_case = event_log_outstanding.groupby("case:concept:name")
    event_log_outstanding["amount_latest"] = _by_case["amount"].ffill()
    event_log_outstanding["expense_running_total"] = _by_case["expense"].transform(
        lambda s: s.fillna(0).cumsum()
    ).round(2)

    event_log_outstanding["total_owed"] = (
        event_log_outstanding["amount_latest"].fillna(0)
        + event_log_outstanding["expense_running_total"]
    ).round(2)
    event_log_outstanding["outstanding_amount"] = (
        event_log_outstanding["total_owed"]
        - event_log_outstanding["payment_amount_running_total"]
    ).round(2)
    return (event_log_outstanding,)


@app.cell
def _(event_log_outstanding):
    # 5a) Inspect a case to verify the enrichment.
    outstanding_cols = [
        "time:timestamp", "concept:name", "amount_latest", "expense_running_total",
        "payment_amount_running_total", "total_owed", "outstanding_amount",
    ]
    event_log_outstanding[event_log_outstanding["case:concept:name"] == "A22233"][outstanding_cols]
    return (outstanding_cols,)


@app.cell
def _(event_log_outstanding):
    # 5b) Number of events with outstanding_amount > 0.
    n_outstanding = (event_log_outstanding["outstanding_amount"] > 0).sum()
    print("Number of events with outstanding_amount > 0:", n_outstanding)

    _negative = event_log_outstanding[event_log_outstanding["outstanding_amount"] < 0]
    print("Events with NEGATIVE outstanding_amount (overpayment):", len(_negative),
          "in", _negative["case:concept:name"].nunique(), "cases")
    _neg_cases = _negative["case:concept:name"].unique()
    _neg_case_events = event_log_outstanding[event_log_outstanding["case:concept:name"].isin(_neg_cases)]
    _paid_before_send = _neg_case_events.groupby("case:concept:name")["concept:name"].apply(
        lambda s: "Send Fine" not in set(s)
        or s.tolist().index("Payment") < s.tolist().index("Send Fine")
        if "Payment" in set(s) else False
    )
    print("...of which the (first) payment happens before any Send Fine:", _paid_before_send.sum())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **5) Outstanding amount.**

    We define `outstanding_amount = (latest amount + cumulative expense) - cumulative paymentAmount`, where `amount` is forward-filled (it is a case-cumulative *state*, cf. Task 2) and `expense`/`paymentAmount` are cumulatively summed (they are incremental, one-time or repeatable charges/payments).

    **a)** On case `A22233`, after Create Fine the outstanding amount is `36.0`; after Send Fine (expense 13.0) it rises to `49.0`; after Add penalty it rises to `87.0`; after the first payment of `49.0` it drops to `38.0`; after the second payment of `38.0` it correctly reaches `0.0` — matching our manual expectation.

    **b)** **500,406** events (≈ 89 % of all events) have `outstanding_amount > 0`. *Hypothesis:* the majority of events should be positive, because every case starts with an unpaid fine and ~40 % of cases end in credit collection. The result matches this.

    *Side-finding:* **1,271 events in 1,238 cases** have a **negative** outstanding amount, i.e. more was paid than was due according to the log. Most of these differences are small: 365 are below €1 (e.g. `N35881`: €79.30 paid for €79.03 due, which looks like transposed digits or a rounding difference), and about 350 are almost exactly €5. The recurring €5 suggests an extra fee (e.g. an administrative or bank fee) that offenders pay but that is never recorded as `expense`. 325 of these cases paid before any `Send Fine`, i.e. before the postal expense was even recorded. 1,186 cases still end with a negative balance, and the log contains no refund activity.

    *Finding / recommendation:* record all cost components (fees) explicitly as attributes and add a refund activity, so that the balance of a fine can be reconstructed from the log.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Part 3: Case Enrichment

    ### 5. Case log with initial fine amount
    """)
    return


@app.cell
def _(event_log_enriched):
    # Identify true case attributes: columns with at most one distinct non-null value per case.
    candidate_cols = [
        "paymentAmount", "amount", "notificationType", "dismissal", "vehicleClass",
        "matricola", "expense", "article", "lastSent", "points", "org:resource",
        "totalPaymentAmount",
    ]
    nunique_per_case = event_log_enriched.groupby("case:concept:name")[candidate_cols].nunique()
    case_attribute_cols = nunique_per_case.columns[(nunique_per_case.max() <= 1)].tolist()
    print("Case attributes (<=1 distinct non-null value per case):", case_attribute_cols)
    return (case_attribute_cols,)


@app.cell
def _(case_attribute_cols, event_log_enriched, pd):
    # Build the case log: mandatory case-level fields, the identified case attributes,
    # and the initial fine amount (amount at the Create Fine event of each case).
    cases = event_log_enriched.groupby("case:concept:name")

    case_log = cases.agg(
        start_time=("time:timestamp", "first"),
        end_time=("time:timestamp", "last"),
        no_of_events=("concept:name", "count"),
    )
    for col in case_attribute_cols:
        case_log[col] = cases[col].apply(
            lambda s: s.dropna().iloc[0] if s.notna().any() else pd.NA
        )

    initial_fine_amount = event_log_enriched[
        event_log_enriched["concept:name"] == "Create Fine"
    ].set_index("case:concept:name")["amount"]
    case_log["initial_fine_amount"] = initial_fine_amount

    case_log[["start_time", "end_time", "no_of_events", "initial_fine_amount"]]
    return case_log, cases


@app.cell
def _(case_log):
    case_log["initial_fine_amount"].describe()
    return


@app.cell
def _(case_log):
    import plotly.express as px

    fig_initial_amount = px.histogram(
        case_log, x="initial_fine_amount", nbins=200, log_y=True, marginal="rug",
        title="Distribution of initial fine amount",
    )
    fig_initial_amount.update_layout(bargap=0.2)
    fig_initial_amount
    return (px,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **5) Initial fine amount.**

    **a) Hypothesis:** Traffic fines in most countries are set from a small catalogue of standard amounts tied to specific articles/offenses (e.g., illegal parking vs. speeding have fixed fine levels). We therefore expect the distribution to be **highly concentrated on a handful of discrete values** (a few spikes) rather than smoothly spread out, with a long thin tail of rare, much higher amounts (aggravated or combined offenses).

    **b) Observations:** The histogram (log-scaled y-axis, with a rug plot for the tail) confirms the hypothesis:

    1. The distribution is extremely **peaked around €35–38** (matching the median of €35 found in Task 1.1c), consistent with a small number of standard fine amounts for the most common articles (e.g., article 157 for parking, which alone accounts for ~45% of all fines).
    2. There is a **long right tail** of rare, high-value fines up to €4,351, visible only thanks to the rug plot and log scale — on a plain linear histogram these outliers would be essentially invisible (as warned on the lecture slide "outliers might be overlooked").
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 6. Initial vs. final fine amount
    """)
    return


@app.cell
def _(case_log, cases, pd):
    # final fine amount = last non-null value of 'amount' per case
    final_fine_amount = cases["amount"].apply(
        lambda s: s.dropna().iloc[-1] if s.notna().any() else pd.NA
    )
    case_log["final_fine_amount"] = final_fine_amount
    case_log[["initial_fine_amount", "final_fine_amount"]]
    return (final_fine_amount,)


@app.cell
def _(case_log, final_fine_amount, pd, px):
    # Log-log scale with equal axis scaling: lines y = k*x become parallel diagonals,
    # so bands with a constant ratio final/initial are easy to tell apart.
    # (36 cases with an initial amount of 0 cannot be shown on a log scale.)
    _df = case_log.assign(final_fine_amount=final_fine_amount.astype(float))
    _df = _df[_df["initial_fine_amount"] > 0]
    _df["ratio"] = _df["final_fine_amount"] / _df["initial_fine_amount"]
    _df["ratio_band"] = pd.cut(
        _df["ratio"], [0, 1.0001, 1.9, 2.1, 3, 5],
        labels=["x1 (no penalty)", "x1.8 (outlier)", "x2", "x2.5", "x3.7-x4"],
    ).astype(str)

    fig_initial_vs_final = px.scatter(
        _df, x="initial_fine_amount", y="final_fine_amount", color="ratio_band",
        hover_data=["article", "ratio"], log_x=True, log_y=True, render_mode="webgl",
        title="Initial vs. final fine amount per case (log-log, dashed: y = x and y = 2x)",
        width=750, height=650,
    )
    for _k in [1, 2]:
        fig_initial_vs_final.add_shape(
            type="line", x0=1, y0=_k, x1=10000, y1=10000 * _k,
            line=dict(dash="dash", color="grey", width=1),
        )
    fig_initial_vs_final.update_xaxes(range=[0, 4])
    fig_initial_vs_final.update_yaxes(range=[0, 4], scaleanchor="x", scaleratio=1)

    print("Cases with final < initial:", int((_df["ratio"] < 1).sum()))
    print("Cases per band:", _df["ratio_band"].value_counts().to_dict())
    print("Median ratio of penalised cases:", round(_df.loc[_df["ratio"] > 1.0001, "ratio"].median(), 3))
    for _band in ["x1.8 (outlier)", "x2.5", "x3.7-x4"]:
        print(f"Articles in band {_band}:", _df.loc[_df["ratio_band"] == _band, "article"].value_counts().to_dict())
    fig_initial_vs_final
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **6) Initial vs. final fine amount.**

    *Note on the visualisation:* in a plain linear scatter plot the axes have different ranges (initial up to €4,351, final up to €8,000). The line y = x then does not coincide with the visual diagonal of the chart, so points seem to lie both above and below "the diagonal". We therefore use a log-log plot with equal axis scaling: every constant ratio final/initial becomes a parallel diagonal line.

    **Observations:**

    - **No case lies below y = x**: the final amount is never smaller than the initial amount. This is consistent with the process description, where `Add penalty` only increases the amount and no activity reduces it.
    - **Band y = x (70,492 cases, ≈ 47 %)**: no penalty was added; the amount stays unchanged.
    - **Band y ≈ 2x (79,810 cases, ≈ 53 %)**: the main penalty band. The median ratio is 2.04; the small surplus over exactly 2 (ratios 2.00–2.06) is a rounding/fee component. **The penalty doubles the fine**, consistent with the Italian rule that the fine doubles if it is not paid within 60 days (cf. the exact 60-day delay in Task 4.2).
    - **Small additional bands**, visible only thanks to the colouring:
      - **×2.5 (20 cases)**: all for **article 94**.
      - **×3.7–×4 (10 cases)**: articles 116, 189 and 213, mostly from 2010–2012.
      - **Two outliers below ×2** (×1.77 and ×1.84), including the largest fine in the log (€4,351 → €8,000). Here the final amount looks capped (€8,000 is the maximum of `amount` in the whole log).

    **Interpretation:** the penalty is not a free decision but a fixed multiplier of the initial fine, ×2 for almost all offences. A few specific articles carry a higher multiplier. The handful of deviations from these multipliers (e.g. a possible cap at €8,000) should be checked with the domain experts.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 7. Noteworthy fact: `dismissal`
    """)
    return


@app.cell
def _(event_log_from_disk):
    # 7) Noteworthy fact about `dismissal`: the process description (Session 1) only
    # documents two non-trivial codes, 'G' (dismissed by judge) and '#' (dismissed by
    # prefecture). Let's check what other values actually occur in the log.
    dismissal_counts = event_log_from_disk["dismissal"].value_counts(dropna=False)
    print(dismissal_counts)

    documented = {"NIL", "#", "G"}
    undocumented_codes = sorted(
        event_log_from_disk.loc[
            event_log_from_disk["dismissal"].notna()
            & ~event_log_from_disk["dismissal"].isin(documented),
            "dismissal",
        ].unique()
    )
    print()
    print("Number of undocumented non-null dismissal codes:", len(undocumented_codes))
    print("Undocumented codes:", undocumented_codes)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **7) Noteworthy fact about `dismissal`.**

    The process/attribute description (Session 1) only explains three values for `dismissal`: `NIL` (not dismissed, the initial value), `G` (dismissed by the judge), and `#` (dismissed by the prefecture). However, the log actually contains **23 additional, undocumented single-character/digit codes** (`A`, `T`, `D`, `I`, `N`, `U`, `5`, `V`, `@`, `C`, `E`, `Z`, `M`, `F`, `R`, `K`, `3`, `B`, `2`, `4`, `Q`, `$`, `J`), each occurring only a handful of times (2 to 213 occurrences).

    These codes are all set at `Create Fine`, and **486 of the 504 affected cases follow the variant *Create Fine → Send Fine* and then stop** (no notification, payment or collection; see Task 3.1 d). This strongly suggests that the codes mark fines that were dropped by the police itself, e.g. for formal reasons.

    *Reflection:* These look like they could be additional dismissal-reason codes from the source system (e.g., different legal grounds for dismissal, or administrative outcome codes) that were never explained in the published data dictionary. Since they are rare and undocumented, any downstream analysis that treats "dismissed" as simply `dismissal != NIL` should explicitly decide whether to include these codes, and this gap should be flagged as a **data documentation improvement** to request from the data provider.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 3

    ## Task 3.1 – Outcome analysis

    We define three business-level outcomes of a fine:

    | Outcome | Definition (case level) | Business meaning |
    |---|---|---|
    | `paid_in_full` | at least one `Payment` and the final `outstanding_amount` (Session 2, Task 5 in Part 2) is ≤ 0 | the state collected the money itself |
    | `sent_to_credit_collection` | the case contains `Send for Credit Collection` | collection failed and was handed over to an external agency |
    | `dismissed` | `dismissal` is `G` (judge) or `#` (prefecture) at some event | the obligation to pay was cancelled |

    Only the two documented dismissal codes count as `dismissed`; the undocumented codes (Session 2, Task 7) are not used because their meaning is unknown.

    *Hypothesis:* the three outcomes should be (almost) mutually exclusive. Paid and credit collection should together cover the vast majority of cases, and dismissals should be rare (a few %), since few offenders appeal.
    """)
    return


@app.cell
def _(case_log, event_log_outstanding):
    # a) Boolean outcome indicators on the case log.
    _ev = event_log_outstanding.assign(
        _is_payment=event_log_outstanding["concept:name"] == "Payment",
        _is_credit=event_log_outstanding["concept:name"] == "Send for Credit Collection",
        _is_dismissed=event_log_outstanding["dismissal"].isin(["G", "#"]),
    )
    _by_case = _ev.groupby("case:concept:name")
    outcome_log = case_log.copy()
    outcome_log["final_outstanding"] = _by_case["outstanding_amount"].last()
    outcome_log["paid_in_full"] = _by_case["_is_payment"].any() & (outcome_log["final_outstanding"] <= 0)
    outcome_log["sent_to_credit_collection"] = _by_case["_is_credit"].any()
    outcome_log["dismissed"] = _by_case["_is_dismissed"].any()
    outcome_log[["final_outstanding", "paid_in_full", "sent_to_credit_collection", "dismissed"]]
    return (outcome_log,)


@app.cell
def _(outcome_log, pd):
    # a) Number of cases per outcome, per pair of outcomes, and without any outcome.
    from itertools import combinations

    OUTCOMES = ["paid_in_full", "sent_to_credit_collection", "dismissed"]
    _rows = [{"outcome(s)": _o, "cases": int(outcome_log[_o].sum())} for _o in OUTCOMES]
    for _a, _b in combinations(OUTCOMES, 2):
        _rows.append({"outcome(s)": f"{_a} AND {_b}", "cases": int((outcome_log[_a] & outcome_log[_b]).sum())})
    _rows.append({"outcome(s)": "all three", "cases": int(outcome_log[OUTCOMES].all(axis=1).sum())})
    _rows.append({"outcome(s)": "no outcome", "cases": int((~outcome_log[OUTCOMES].any(axis=1)).sum())})
    outcome_counts = pd.DataFrame(_rows)
    outcome_counts["share_of_cases_%"] = (100 * outcome_counts["cases"] / len(outcome_log)).round(2)
    outcome_counts
    return (OUTCOMES,)


@app.cell
def _(event_log_outstanding):
    def show_case(case_id):
        _cols = [
            "time:timestamp", "concept:name", "amount", "expense", "paymentAmount",
            "payment_amount_running_total", "outstanding_amount", "dismissal",
        ]
        return event_log_outstanding[event_log_outstanding["case:concept:name"] == case_id][_cols]

    return (show_case,)


@app.cell
def _(OUTCOMES, mo, outcome_log, show_case):
    # b) One example case per outcome (first case id that has exactly this one outcome).
    _examples = []
    for _o in OUTCOMES:
        _only = outcome_log[outcome_log[_o] & (outcome_log[OUTCOMES].sum(axis=1) == 1)]
        _cid = _only.index[0]
        _examples += [mo.md(f"**{_o}** – case `{_cid}`"), show_case(_cid)]
    mo.vstack(_examples)
    return


@app.cell
def _(OUTCOMES, mo, outcome_log, show_case):
    # c) Cases with more than one outcome.
    _multi = outcome_log[outcome_log[OUTCOMES].sum(axis=1) > 1]
    _items = []
    for _cid in _multi.index:
        _flags = [o for o in OUTCOMES if _multi.loc[_cid, o]]
        _items += [mo.md(f"case `{_cid}`: {', '.join(_flags)}"), show_case(_cid)]
    mo.vstack(_items)
    return


@app.cell
def _(OUTCOMES, event_log_outstanding, mo, outcome_log, show_case):
    # d) Cases without any outcome: example + which variants they follow.
    _no_outcome = outcome_log.index[~outcome_log[OUTCOMES].any(axis=1)]
    _variants = event_log_outstanding[
        event_log_outstanding["case:concept:name"].isin(_no_outcome)
    ].groupby("case:concept:name")["concept:name"].agg(" → ".join)
    mo.vstack([
        mo.md("**Most frequent variants of cases without outcome**"),
        _variants.value_counts().head(6).rename("cases").to_frame(),
        mo.md("**Example: case `A1`**"),
        show_case("A1"),
        mo.md("**Example: case `A10798`**"),
        show_case("A10798"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a) Results.** `paid_in_full`: **60,287** cases (40.1 %), `sent_to_credit_collection`: **59,013** (39.2 %), `dismissed`: **2,073** (1.4 %). Pairs: paid & credit collection **2**, paid & dismissed **1**, credit collection & dismissed **0**; all three: 0. **29,000** cases (19.3 %) have no outcome. As expected, the outcomes are practically mutually exclusive. Surprisingly, however, almost a fifth of all fines end without any of the three outcomes.

    **b) One case per outcome:**

    - *Paid – `A10000`:* €36 fine, €13 postal expense, the offender misses the 60-day deadline, so the penalty raises the fine to €74. One payment of €87 (= 74 + 13) a year later settles it exactly; outstanding = 0.
    - *Credit collection – `A100`:* fine notified, no payment within 60 days, penalty added (€82.50 outstanding). Two years later the fine is handed over to credit collection with the full amount still open.
    - *Dismissed – `A10001`:* the offender appeals to the prefecture shortly after the notification. While the appeal is pending, the automatic penalty is still added. The dismissal flag `#` (dismissed by the prefecture) is recorded at `Send Appeal to Prefecture`, so the obligation to pay is cancelled, although the log still shows €87 as "outstanding". The dismissal is recorded on the event where the appeal is *sent*, not when the result is received, which is a data representation issue.

    **c) Cases with more than one outcome (3 cases):**

    - *`S66168` (paid & credit collection):* the fine incl. penalty and expense (€144.63) is paid in full in August 2002, yet the case is sent for credit collection in January 2004. This is a clear process error, probably caused by the periodic batch run of credit collection (see Task 4.2) not checking the payment status.
    - *`N35881` (paid & credit collection):* €79.30 paid for €79.03 due (digits transposed?), still sent to credit collection. The same batch problem applies here.
    - *`S188064` (paid & dismissed):* the prefecture dismissed the fine (`#`), but the penalty was still added and the offender paid the full €174. Either the dismissal was later reversed or the offender paid a cancelled fine and should get a refund.

    **d) Cases without an outcome (29,000):** the dominant variant is *Create Fine → Send Fine* (20,385 cases, e.g. `A1`): the fine was sent but the notification was never registered as received, and nothing else happened, even for fines from 2000–2010. Possible explanations are notifications that could not be delivered (unknown or foreign address), fines dropped by the police without a documented reason (the undocumented dismissal codes `A`, `T`, `D`, `I`, … occur almost exclusively in this variant), or a missing "fine archived/expired" activity in the log. The second group (e.g. `A10798`, 3,239 cases of the same variant) are **partial payments**: the offender paid, but a small remainder (often the penalty or the postal expense) is still open and was never sent to credit collection.

    *Finding / recommendation:* add an explicit final activity (e.g. "Fine closed" with a reason: paid, dismissed, collected, expired, not deliverable), check the payment status before handing over to credit collection, and handle small residual amounts consistently.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Session 4

    ## Task 4.1 – Sequential variants
    """)
    return


@app.cell
def _(event_log_enriched):
    case_variants = event_log_enriched.groupby("case:concept:name")["concept:name"].agg(" → ".join)
    variant_table = case_variants.value_counts().rename("cases").to_frame()
    variant_table["share_%"] = (100 * variant_table["cases"] / len(case_variants)).round(2)
    variant_table["cumulative_%"] = (100 * variant_table["cases"].cumsum() / len(case_variants)).round(2)
    n_variants_80 = int((variant_table["cases"].cumsum() / len(case_variants) < 0.8).sum() + 1)

    print("Number of sequential variants:", len(variant_table))
    print("Minimum number of variants covering 80% of cases:", n_variants_80)
    variant_table.head(10)
    return


@app.cell
def _(event_log_enriched):
    # c) Fine object sub-log
    FINE_OBJECT_ACTIVITIES = [
        "Create Fine", "Send Fine", "Insert Fine Notification",
        "Add penalty", "Send for Credit Collection", "Payment",
    ]
    fine_object_log = event_log_enriched[
        event_log_enriched["concept:name"].isin(FINE_OBJECT_ACTIVITIES)
    ]
    fine_object_variants = fine_object_log.groupby("case:concept:name")["concept:name"].agg(" → ".join)
    print("Events before / after filtering:", len(event_log_enriched), "/", len(fine_object_log))
    print("Cases after filtering:", fine_object_variants.size)
    print("Sequential variants after filtering:", fine_object_variants.nunique())
    fine_object_variants.value_counts().head(10).rename("cases").to_frame()
    return fine_object_log, fine_object_variants


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a)** The log has **231** sequential variants, but the distribution is extremely skewed: the **3 most frequent variants already cover 81.96 %** of the cases (37.56 + 30.84 + 13.56 %), so **3 variants** are needed to cover 80 %.

    **b) Top 4 variants:**

    1. *Create Fine → Send Fine → Insert Fine Notification → Add penalty → Send for Credit Collection* (37.6 %): the offender is notified, does not pay within 60 days, the penalty is added and the unpaid fine is handed over to credit collection.
    2. *Create Fine → Payment* (30.8 %): the offender pays immediately (e.g. on the spot or right after the fine is issued), so no notification is ever sent.
    3. *Create Fine → Send Fine* (13.6 %): the fine is sent but nothing else is recorded afterwards; neither notification, payment nor collection (see Task 3.1 d).
    4. *Create Fine → Send Fine → Insert Fine Notification → Add penalty → Payment* (6.3 %): the offender pays only after the 60-day deadline, i.e. the full amount including the penalty.

    **c)** Keeping only the six fine-object activities reduces the number of sequential variants from **231 to 48** (all 150,370 cases keep at least `Create Fine`). The many variants of the full log are mostly caused by the appeal activities (prefecture/judge), which are interleaved in different orders with the fine activities. Still, 3 variants cover 80 % of the fine-object cases.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 4.2 – Process map of the fine object

    Process map from **Disco** (screenshot `fine_object_disco.png`): attribute filter on the six fine-object activities (*keep selected*), absolute frequencies, 100 % activities and 100 % paths. The table below the map reproduces the same directly-follows frequencies in Python, and the following cell contains the checks that support our observations.
    """)
    return


@app.cell
def _(mo):
    mo.image("fine_object_disco.png")
    return


@app.cell
def _(fine_object_log):
    # Directly-follows relations as a table (same numbers as on the process map).
    _df = fine_object_log[["case:concept:name", "concept:name"]].copy()
    _df["next activity"] = _df.groupby("case:concept:name")["concept:name"].shift(-1)
    _df.dropna(subset=["next activity"]).groupby(["concept:name", "next activity"]).size().sort_values(
        ascending=False
    ).rename("frequency").to_frame()
    return


@app.cell
def _(event_log_outstanding):
    # Supporting checks for the observations below.
    _el = event_log_outstanding.copy()
    _by_case = _el.groupby("case:concept:name")
    _el["previous activity"] = _by_case["concept:name"].shift(1)
    _el["outstanding_before"] = _by_case["outstanding_amount"].shift(1)

    _notif = _el[_el["concept:name"] == "Insert Fine Notification"].set_index("case:concept:name")["time:timestamp"]
    _pen = _el[_el["concept:name"] == "Add penalty"].set_index("case:concept:name")["time:timestamp"]
    # calendar days in local time (tz_localize(None) avoids the one-hour DST offset of absolute durations)
    _days = _pen.dt.tz_localize(None).dt.normalize() - _notif.reindex(_pen.index).dt.tz_localize(None).dt.normalize()
    print("Calendar days between Insert Fine Notification and Add penalty:")
    print(_days.dt.days.value_counts().to_dict())

    _pen_after_pay = _el[(_el["concept:name"] == "Add penalty") & (_el["previous activity"] == "Payment")]
    print("Add penalty directly after Payment:", len(_pen_after_pay),
          "| amount still outstanding before the penalty:", int((_pen_after_pay["outstanding_before"] > 0).sum()),
          "| median outstanding:", _pen_after_pay["outstanding_before"].median())

    _cc_after_pay = _el[(_el["concept:name"] == "Send for Credit Collection") & (_el["previous activity"] == "Payment")]
    print("Credit collection directly after Payment:", len(_cc_after_pay),
          "| amount still outstanding:", int((_cc_after_pay["outstanding_before"] > 0).sum()))

    _send_after_pay = _el[(_el["concept:name"] == "Send Fine") & (_el["previous activity"] == "Payment")]
    print("Send Fine directly after Payment:", len(_send_after_pay),
          "| fine already fully paid before sending:", int((_send_after_pay["outstanding_before"] <= 0).sum()))

    print("Send for Credit Collection events per year:")
    print(_el[_el["concept:name"] == "Send for Credit Collection"]["time:timestamp"].dt.year.value_counts().sort_index().to_dict())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **a) Unexpected observations (to be investigated further):**

    1. **`Add penalty` directly after `Payment` (3,902 times).** A paying offender should not get a penalty. The checks above show that in 3,866 of these cases an amount was still outstanding (median ≈ €5, i.e. roughly the postal expense). The offender paid the fine but not the postal expense, so the payment was incomplete and the penalty was still triggered.
    2. **`Send for Credit Collection` after `Payment` (1,538 times).** Handing over a fine that has been (partly) paid is surprising. Almost all (1,536) still have an outstanding amount, so collection is for the remainder. However, collection events only occur in certain years, in large batches (e.g. 9,136 in 2002 and none in 2005, 2008 or 2011). This suggests a periodic batch run, which may send fines that have meanwhile been paid in full (cf. case `S66168` in Task 3.1).
    3. **`Send Fine` after `Payment` (569 times).** Sending the fine after it has been paid is wasteful: in 540 of these cases the fine was already fully paid, yet a notification was sent and a postal expense added.
    4. **20,897 cases end with `Send Fine`**, i.e. the notification was never registered as received and nothing else happened (see Task 3.1 d).
    5. **`Insert Fine Notification → Add penalty` dominates (75,958 of 79,860).** The penalty is added exactly **60 calendar days** after the notification in all 79,860 cases. It is an automatic deadline (60 days to pay) rather than a manual decision.

    **b) Unexpected variant.** From the process map we chose the most frequent unexpected edge, **`Payment → Add penalty` (3,902)**. In Disco we clicked this edge and applied *"Filter this path…"*, i.e. a **Follower filter** (reference event `Payment`, follower `Add penalty`, *directly followed*) on top of the fine-object attribute filter. The filtered log contains 3,902 cases in 14 variants (first screenshot below). The most frequent of them (**Variant 1, 3,305 cases = 84.7 %**, second screenshot) is:

    **Create Fine → Send Fine → Insert Fine Notification → Payment → Add penalty → Payment**

    It is the 6th most frequent variant of the whole fine-object sub-log.
    """)
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md("*Disco: process map after the follower filter `Payment → Add penalty` (3,902 cases)*"),
        mo.image("fine_object_follower_filter.png", width=500),
        mo.md("*Disco: variants of the filtered log, Variant 1 selected (3,305 cases)*"),
        mo.image("fine_object_variant_disco.png"),
    ])
    return


@app.cell
def _(fine_object_variants, mo, show_case):
    _variant = "Create Fine → Send Fine → Insert Fine Notification → Payment → Add penalty → Payment"
    _cases = fine_object_variants[fine_object_variants == _variant]
    mo.vstack([
        mo.md(f"*Cross-check in Python: {len(_cases)} cases follow this variant (same as in Disco).*"),
        mo.md("**c) Case `A10798`** (first case of Variant 1 in Disco), table view in Disco:"),
        mo.image("A10798_case_disco.png"),
        mo.md("Same case with our enrichments (running payment total and outstanding amount):"),
        show_case("A10798"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **c) Explanation (case `A10798`):** the fine of €22 is created; after `Send Fine` the offender owes €35 (fine + €13 postal expense). Within the 60-day period the offender pays **only €22**, i.e. the fine without the postal expense, so €13 remain outstanding. Exactly 60 days after the notification the system automatically applies the penalty (`amount` 22 → 44), which raises the outstanding amount to €35. The offender then pays the missing €13, after which €22 (the penalty) remain open. The case nevertheless ends there, without credit collection.

    So the unexpected "penalty after payment" is not an error. The deadline rule is applied to the *balance* and does not care whether a payment was made. Most such offenders probably believed they had paid in full.

    *Recommendation:* communicate the total amount due (fine + postal expense) clearly on the notification, e.g. with a pre-filled payment slip. *Open question:* why are some residual amounts (like the €22 here) never sent to credit collection?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Task 4.3 – BPMN model of the fine object

    The model captures our preliminary understanding of how the fine object *should* behave:

    - After `Create Fine` the offender may pay immediately; then no notification is necessary.
    - Otherwise the fine is sent. If the notification cannot be delivered or the fine is dropped (cf. Task 3.1 d: 13.6 % of the cases end after `Send Fine`), the case ends.
    - Otherwise the notification is registered. If the offender pays within 60 days, the fine is paid without penalty.
    - Otherwise `Add penalty` is applied (automatically after 60 days, Task 4.2). The offender can then still pay; if not, the fine is sent for credit collection or, in exceptional cases, not pursued further (3,252 cases end after `Add penalty`).
    - Payments can be made in instalments (loop back to `Payment` until the fine is fully paid).

    The model uses only exclusive gateways. Every path from the start event reaches the end event, and the instalment loop can always be left. It is therefore sound, which the Woflan check below confirms.

    **How much of the log does the model replay?** Using alignments on the fine-object sub-log, the model fits **17 of 48 variants, i.e. 141,131 of 150,370 cases (93.9 %)**. The first version of the model (without the two exits) fitted only 117,363 cases (78.0 %); the third most frequent variant *Create Fine → Send Fine* was not possible. The remaining deviations are exactly the behaviour we consider undesired or need clarifying (Task 4.2): penalties after partial payments, credit collection after a payment, `Send Fine` after `Payment`, and payments before the notification is registered. These are deliberately not part of this normative model.
    """)
    return


@app.cell
def _(mo):
    from pathlib import Path

    mo.Html(Path("Fine-Object-Model.svg").read_text())
    return


@app.cell
def _(pm4py):
    from pm4py.algo.analysis.woflan import algorithm as woflan

    _bpmn = pm4py.read_bpmn("Fine-Object-Model.bpmn")
    _net, _im, _fm = pm4py.convert_to_petri_net(_bpmn)
    print("Activities in model:", sorted(t.label for t in _net.transitions if t.label))
    print("Sound (Woflan):", woflan.apply(_net, _im, _fm, parameters={"print_diagnostics": False}))
    return


@app.cell
def _(fine_object_log, pm4py):
    # Alignment-based fitness per variant of the fine-object sub-log.
    from pm4py.objects.log.obj import EventLog, Event, Trace
    from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments

    _fo_net, _fo_im, _fo_fm = pm4py.convert_to_petri_net(pm4py.read_bpmn("Fine-Object-Model.bpmn"))
    _variants = fine_object_log.groupby("case:concept:name")["concept:name"].agg(tuple).value_counts()
    _traces = EventLog([Trace([Event({"concept:name": _a}) for _a in _v]) for _v in _variants.index])
    _fits = [_r["fitness"] == 1.0 for _r in alignments.apply(_traces, _fo_net, _fo_im, _fo_fm)]
    print(f"Fitting variants: {sum(_fits)} of {len(_variants)}")
    print(f"Fitting cases: {_variants[_fits].sum()} of {_variants.sum()} "
          f"({100 * _variants[_fits].sum() / _variants.sum():.1f} %)")
    _variants[[not _f for _f in _fits]].head(5).rename("cases (not fitting)").to_frame()
    return


if __name__ == "__main__":
    app.run()
