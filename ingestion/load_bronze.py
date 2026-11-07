import argparse
import os
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

END = date.today() - timedelta(days=1)
START = END - timedelta(days=213)
RATE_CUT_DAY = END - timedelta(days=78)
CAMPAIGN_DAYS = (END - timedelta(days=53), END - timedelta(days=47))
FLEET_SWITCH_DAY = END - timedelta(days=122)
TZ = timezone(timedelta(hours=7))


def calendar():
    return pd.date_range(START, END, freq="D")


def ts(day, minutes):
    return (day + timedelta(minutes=int(minutes))).tz_localize(TZ).tz_convert("UTC")


def wallet(rng):
    signups, acc_id = [], 0
    for day in calendar():
        base = (18 + 6 * (day.weekday() < 5)) * (3.2 if CAMPAIGN_DAYS[0] <= day.date() <= CAMPAIGN_DAYS[1] else 1)
        for _ in range(rng.poisson(base)):
            acc_id += 1
            in_campaign = CAMPAIGN_DAYS[0] <= day.date() <= CAMPAIGN_DAYS[1]
            signups.append({
                "account_id": f"A{acc_id:06d}",
                "user_id": f"U{rng.integers(1, 400000):06d}",
                "opened_at": ts(day, rng.integers(0, 1440)),
                "acquisition_channel": "campaign" if in_campaign else rng.choice(["app_home", "referral", "campaign", "partner_bank"], p=[0.5, 0.2, 0.2, 0.1]),
                "segment": rng.choice(["mass", "affluent", "student"], p=[0.7, 0.1, 0.2]),
            })
    accounts = pd.DataFrame(signups)

    rows, txn = [], 0
    channels = ["bank_transfer", "wallet_balance", "linked_card", "virtual_account"]
    for a in accounts.itertuples():
        balance = 0.0
        open_day = a.opened_at.tz_convert(TZ).tz_localize(None).normalize()
        affinity = {"affluent": 4.0, "mass": 1.0, "student": 0.4}[a.segment]
        leave_day = open_day + timedelta(days=int(rng.exponential(220)))
        for day in pd.date_range(open_day, END, freq="D"):
            if day > leave_day:
                if balance > 0:
                    txn += 1
                    rows.append((f"T{txn:08d}", a.account_id, "cash_out", round(balance, 2), rng.choice(channels[:3]), "success", ts(day, 600)))
                break
            payday = day.day in (1, 2, 3, 15, 16)
            p_in = 0.06 * (2.2 if payday else 1.0) * (1.3 if day.weekday() < 5 else 0.8)
            if day == open_day or rng.random() < p_in:
                amount = float(np.round(rng.lognormal(13.2, 0.9) * affinity / 1000) * 1000)
                status = "success" if rng.random() > 0.03 else "failed"
                txn += 1
                rows.append((f"T{txn:08d}", a.account_id, "cash_in", amount, rng.choice(channels, p=[0.45, 0.3, 0.15, 0.1]), status, ts(day, rng.integers(360, 1380))))
                if status == "success":
                    balance += amount
            after_cut = 0 <= (day.date() - RATE_CUT_DAY).days < 21
            if balance > 0 and rng.random() < 0.035 * (2.6 if after_cut else 1.0):
                amount = float(min(balance, np.round(balance * rng.uniform(0.2, 1.0) / 1000) * 1000))
                if amount > 0:
                    txn += 1
                    rows.append((f"T{txn:08d}", a.account_id, "cash_out", amount, rng.choice(channels[:3]), "success", ts(day, rng.integers(360, 1380))))
                    balance -= amount
            if balance > 0:
                interest = round(balance * (0.045 if day.date() < RATE_CUT_DAY else 0.038) / 365, 2)
                if interest >= 1:
                    txn += 1
                    rows.append((f"T{txn:08d}", a.account_id, "interest", interest, "system", "success", ts(day, 1439)))
                    balance += interest
    transactions = pd.DataFrame(rows, columns=["txn_id", "account_id", "txn_type", "amount", "channel", "status", "created_at"])
    days = calendar().date
    rates = pd.DataFrame({"rate_date": days, "annual_rate": np.where(days < RATE_CUT_DAY, 0.045, 0.038)})
    return accounts, transactions, rates


def app_events(rng):
    rows, eid = [], 0
    for day in calendar():
        for user in rng.integers(1, 400000, rng.poisson(900 * (1.25 if day.weekday() < 5 else 0.9))):
            minute = rng.integers(300, 1400)
            steps = ["open_savings_tab"]
            if rng.random() < 0.42:
                steps.append("start_deposit")
                if rng.random() < 0.58:
                    steps.append("deposit_success")
            for i, name in enumerate(steps):
                eid += 1
                rows.append((f"E{eid:09d}", f"U{user:06d}", name, ts(day, minute) + timedelta(seconds=45 * i)))
    return pd.DataFrame(rows, columns=["event_id", "user_id", "event_name", "event_ts"])


def kitchen(rng):
    kitchens = pd.DataFrame({
        "kitchen_id": [f"K{i:02d}" for i in range(1, 6)],
        "city_zone": ["north", "central", "east", "west", "south"],
        "opened_on": [START - timedelta(days=300), START - timedelta(days=200), START - timedelta(days=60), START, START + timedelta(days=50)],
    })
    hours = [11, 12, 13, 15, 18, 19, 20, 21]
    weights = [0.12, 0.2, 0.1, 0.04, 0.14, 0.2, 0.14, 0.06]
    orders, deliveries, oid = [], [], 0
    for day in calendar():
        for k in kitchens.itertuples():
            if day.date() < k.opened_on:
                continue
            for _ in range(rng.poisson(120 * (1.35 if day.weekday() >= 5 else 1.0))):
                oid += 1
                ordered = ts(day, int(rng.choice(hours, p=weights)) * 60 + rng.integers(0, 60))
                subtotal = float(np.round(rng.lognormal(12.1, 0.35) / 1000) * 1000)
                cancelled = rng.random() < 0.04
                orders.append((f"O{oid:08d}", k.kitchen_id, rng.choice(["bowl_house", "grill_lab", "green_kitchen", "noodle_bar"]),
                               rng.choice(["own_app", "aggregator_a", "aggregator_b"], p=[0.35, 0.4, 0.25]), ordered, subtotal,
                               float(round(subtotal * rng.choice([0, 0, 0.1, 0.2]), -3)), "cancelled" if cancelled else "completed"))
                if not cancelled:
                    fleet = day.date() >= FLEET_SWITCH_DAY
                    picked = ordered + timedelta(minutes=float(rng.gamma(4, 3.2)))
                    deliveries.append((f"O{oid:08d}", "fleet" if fleet else "third_party", picked,
                                       picked + timedelta(minutes=float(rng.gamma(5, 3.4 if fleet else 4.3))),
                                       round(float(rng.gamma(3, 1.4)), 1), int(np.clip(round(rng.normal(4.4 if fleet else 4.1, 0.7)), 1, 5))))
    orders = pd.DataFrame(orders, columns=["order_id", "kitchen_id", "brand", "platform", "ordered_at", "subtotal", "discount", "status"])
    deliveries = pd.DataFrame(deliveries, columns=["order_id", "courier_type", "picked_up_at", "delivered_at", "distance_km", "rating"])
    return kitchens, orders, deliveries


def build(seed=7):
    rng = np.random.default_rng(seed)
    accounts, transactions, rates = wallet(rng)
    kitchens, orders, deliveries = kitchen(rng)
    return {
        "bronze_wallet.accounts": accounts,
        "bronze_wallet.transactions": transactions,
        "bronze_wallet.daily_rates": rates,
        "bronze_app.events": app_events(rng),
        "bronze_kitchen.kitchens": kitchens,
        "bronze_kitchen.orders": orders,
        "bronze_kitchen.deliveries": deliveries,
    }


def load_bigquery(tables, project, location):
    from google.cloud import bigquery

    client = bigquery.Client(project=project, location=location)
    loaded_at = datetime.now(timezone.utc)
    for name, df in tables.items():
        dataset = name.split(".")[0]
        client.create_dataset(bigquery.Dataset(f"{project}.{dataset}"), exists_ok=True)
        job = client.load_table_from_dataframe(
            df.assign(_loaded_at=loaded_at),
            f"{project}.{name}",
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"),
        )
        job.result()
        print(f"{name:30s} {len(df):>9,d} rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=os.environ.get("SAOLA_GCP_PROJECT"))
    ap.add_argument("--location", default="asia-southeast1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    data = build()
    if args.dry_run:
        for table, frame in data.items():
            print(f"{table:30s} {len(frame):>9,d} rows")
    else:
        load_bigquery(data, args.project, args.location)
