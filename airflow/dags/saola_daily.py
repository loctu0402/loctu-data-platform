import json
import os
from datetime import datetime, timedelta

import requests
from airflow import DAG

try:
    from airflow.providers.standard.operators.bash import BashOperator
except ImportError:
    from airflow.operators.bash import BashOperator

REPO = os.environ.get("SAOLA_REPO", "/opt/airflow/repo")
DBT = f"cd {REPO}/dbt && dbt {{cmd}} --target prod --profiles-dir ."


def alert_chat(context):
    webhook = os.environ.get("SAOLA_CHAT_WEBHOOK")
    if not webhook:
        return
    ti = context["task_instance"]
    text = f"*{ti.dag_id}.{ti.task_id}* failed for {context['ds']} (try {ti.try_number}). Log: {ti.log_url}"
    requests.post(webhook, data=json.dumps({"text": text}), headers={"Content-Type": "application/json"}, timeout=10)


default_args = {
    "owner": "analytics-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=15),
    "on_failure_callback": alert_chat,
}

with DAG(
    dag_id="saola_daily",
    start_date=datetime(2026, 1, 1),
    schedule="30 0 * * *",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["gold", "report", "agent"],
) as dag:
    freshness = BashOperator(task_id="source_freshness", bash_command=DBT.format(cmd="source freshness"))
    silver = BashOperator(task_id="build_silver", bash_command=DBT.format(cmd="build --select silver utilities"))
    gold = BashOperator(task_id="build_gold", bash_command=DBT.format(cmd="build --select gold"))
    golden = BashOperator(task_id="golden_eval", bash_command=f"cd {REPO} && python agent/eval_golden.py --live --target prod")
    report = BashOperator(
        task_id="daily_report",
        bash_command=f"cd {REPO} && python report/daily_report.py --as-of {{{{ ds }}}} --send",
        retries=6,
        retry_delay=timedelta(minutes=20),
    )

    freshness >> silver >> gold >> [golden, report]
