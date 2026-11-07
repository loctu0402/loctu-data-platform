import argparse
import json
import os
import smtplib
import sys
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd
import requests
from expected_value import expected_difference, expected_value
from jinja2 import Environment, FileSystemLoader


HERE = Path(__file__).parent


def fetch(project, gold, as_of):
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    start = as_of - timedelta(days=200)
    q = {
        "savings": f"select * from `{gold}.fct_savings_daily` where date_day between '{start}' and '{as_of}' order by date_day",
        "kitchen": f"select * from `{gold}.agg_kitchen_daily` where date_day between '{as_of - timedelta(days=60)}' and '{as_of}' order by date_day",
        "funnel": f"select * from `{gold}.fct_deposit_funnel_daily` where date_day between '{as_of - timedelta(days=30)}' and '{as_of}'",
    }
    return {k: client.query(sql).to_dataframe() for k, sql in q.items()}


def is_ready(frames, as_of):
    return all(not df.empty and pd.to_datetime(df["date_day"]).max().date() >= as_of for df in frames.values())


def pct(a, b):
    return None if not b else a / b - 1


def build_context(frames, as_of):
    s = frames["savings"].assign(date_day=lambda d: pd.to_datetime(d["date_day"])).set_index("date_day").sort_index()
    s = s.apply(pd.to_numeric, errors="coerce")
    today, week_ago = s.loc[pd.Timestamp(as_of)], s.loc[pd.Timestamp(as_of - timedelta(days=7))]
    cash_in = expected_value(s["cash_in_amount"], as_of)
    cash_out = expected_value(s["cash_out_amount"], as_of)
    net = expected_difference(cash_in, cash_out)
    flows = []
    for label, ev, ratio in (("Cash in", cash_in, True), ("Cash out", cash_out, True), ("Net flow", net, False)):
        last = ev.iloc[-1]
        flows.append({"label": label, "actual": last["actual"], "expected": last["expected"],
                      "gap": pct(last["actual"], last["expected"]) if ratio else None, "verdict": last["verdict"]})
    k = frames["kitchen"]
    k = k[(k["kitchen_id"] == "all") & (k["platform"] == "all")].assign(date_day=lambda d: pd.to_datetime(d["date_day"])).set_index("date_day")
    k = k.apply(pd.to_numeric, errors="coerce")
    last7 = k.loc[pd.Timestamp(as_of - timedelta(days=6)):pd.Timestamp(as_of)].sum()
    prev7 = k.loc[pd.Timestamp(as_of - timedelta(days=13)):pd.Timestamp(as_of - timedelta(days=7))].sum()
    f = frames["funnel"].assign(date_day=lambda d: pd.to_datetime(d["date_day"])).set_index("date_day").loc[pd.Timestamp(as_of)]
    return {
        "as_of": as_of.isoformat(),
        "balance": {"value": today["aum_end"], "vs_week": pct(today["aum_end"], week_ago["aum_end"])},
        "funded": {"value": int(today["funded_accounts"]), "new": int(today["new_funded_accounts"]), "churned": int(today["churned_accounts"])},
        "flows": flows,
        "deposit_conversion": f["users_deposited"] / f["users_opened"] if f["users_opened"] else None,
        "kitchen": {
            "orders": int(last7["orders"]),
            "orders_vs_prev": pct(last7["orders"], prev7["orders"]),
            "on_time_rate": last7["on_time_orders"] / last7["completed_orders"],
            "on_time_prev": prev7["on_time_orders"] / prev7["completed_orders"],
            "cancel_rate": 1 - last7["completed_orders"] / last7["orders"],
            "avg_delivery_minutes": last7["delivery_minutes_sum"] / last7["completed_orders"],
            "avg_rating": last7["rating_sum"] / last7["rating_count"],
        },
    }


def render_html(ctx):
    env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=True)
    env.filters["money"] = lambda v: f"{v / 1e9:,.2f}B" if abs(v) >= 1e9 else f"{v / 1e6:,.1f}M"
    env.filters["signed_pct"] = lambda v: "n/a" if v is None else f"{v:+.1%}"
    return env.get_template("daily_report.html").render(**ctx)


def chat_card(ctx):
    flags = [f"{f['label']} is {f['verdict']} expected" for f in ctx["flows"] if f["verdict"] != "normal"]
    k = ctx["kitchen"]
    lines = [
        f"*Savings {ctx['as_of']}*  balance {ctx['balance']['value'] / 1e9:,.2f}B ({ctx['balance']['vs_week']:+.1%} w/w), "
        f"funded {ctx['funded']['value']:,} (+{ctx['funded']['new']} new, -{ctx['funded']['churned']} churned)",
        f"*Kitchens, last 7 days*  {k['orders']:,} orders ({k['orders_vs_prev']:+.1%}), on time {k['on_time_rate']:.1%} "
        f"({(k['on_time_rate'] - k['on_time_prev']) * 100:+.1f} pts), cancelled {k['cancel_rate']:.1%}",
    ]
    if flags:
        lines.append("Watch: " + "; ".join(flags))
    return {"text": "\n".join(lines)}


def deliver(html, card, as_of):
    webhook = os.environ.get("CHAT_WEBHOOK_URL")
    if webhook:
        requests.post(webhook, data=json.dumps(card), headers={"Content-Type": "application/json"}, timeout=10).raise_for_status()
    if os.environ.get("SMTP_HOST"):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Platform daily, {as_of}"
        msg["From"] = os.environ["SMTP_USER"]
        msg["To"] = os.environ["REPORT_RECIPIENTS"]
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587))) as s:
            s.starttls()
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            s.send_message(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    ap.add_argument("--project", default=os.environ.get("GCP_PROJECT_ID"))
    ap.add_argument("--gold-dataset", default=os.environ.get("GOLD_DATASET", "gold"))
    ap.add_argument("--send", action="store_true")
    args = ap.parse_args()

    frames = fetch(args.project, args.gold_dataset, args.as_of)
    if not is_ready(frames, args.as_of):
        sys.exit(f"gold tables are not loaded through {args.as_of} yet")
    ctx = build_context(frames, args.as_of)
    html, card = render_html(ctx), chat_card(ctx)
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    (out / f"daily_{args.as_of}.html").write_text(html, encoding="utf-8")
    (out / f"chat_{args.as_of}.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    if args.send:
        deliver(html, card, args.as_of)


if __name__ == "__main__":
    main()
