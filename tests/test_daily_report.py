from datetime import date

import numpy as np
import pandas as pd
from daily_report import build_context, chat_card, is_ready, render_html

AS_OF = date(2026, 10, 31)


def frames():
    days = pd.date_range(end=AS_OF, periods=200, freq="D")
    rng = np.random.default_rng(3)
    cash_in = 4e9 * np.where(days.day_of_week < 5, 1.2, 0.7) * rng.normal(1, 0.04, len(days))
    cash_out = 3.6e9 * rng.normal(1, 0.05, len(days))
    savings = pd.DataFrame({
        "date_day": days.date,
        "aum_end": 2e11 + np.cumsum(cash_in - cash_out),
        "cash_in_amount": cash_in,
        "cash_out_amount": cash_out,
        "net_flow_amount": cash_in - cash_out,
        "funded_accounts": 4000,
        "new_funded_accounts": 20,
        "churned_accounts": 12,
    })
    kdays = days[-60:]
    kitchen = pd.DataFrame({
        "date_day": kdays.date, "kitchen_id": "all", "platform": "all", "orders": 600, "completed_orders": 576,
        "on_time_orders": 470, "delivery_minutes_sum": 576 * 29.5, "rating_sum": 576 * 4, "rating_count": 576,
    })
    funnel = pd.DataFrame({"date_day": days[-30:].date, "users_opened": 1000, "users_started_deposit": 420, "users_deposited": 240})
    return {"savings": savings, "kitchen": kitchen, "funnel": funnel}


def test_report_renders_every_section():
    ctx = build_context(frames(), AS_OF)
    html = render_html(ctx)
    assert "Saola daily" in html and "Kitchens, last 7 days" in html
    assert [f["label"] for f in ctx["flows"]] == ["Cash in", "Cash out", "Net flow"]
    assert abs(ctx["deposit_conversion"] - 0.24) < 1e-9
    assert abs(ctx["kitchen"]["cancel_rate"] - 0.04) < 1e-9


def test_chat_card_is_one_summary_block():
    card = chat_card(build_context(frames(), AS_OF))
    assert set(card) == {"text"} and card["text"].startswith("*Savings 2026-10-31*")


def test_report_waits_for_late_data():
    f = frames()
    f["savings"] = f["savings"].iloc[:-1]
    assert not is_ready(f, AS_OF)
