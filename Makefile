DBT = cd dbt && dbt
TARGET ?= dev

install:
	pip install -r requirements.txt

bronze:
	python ingestion/load_bronze.py

build:
	$(DBT) source freshness --profiles-dir . --target $(TARGET)
	$(DBT) build --profiles-dir . --target $(TARGET)

check:
	$(DBT) parse --profiles-dir .
	sqlfluff lint dbt/models dbt/tests
	python tools/gate.py
	python tools/ground.py
	python tools/eval_golden.py
	pytest -q
	python -m py_compile airflow/dags/saola_daily.py

golden:
	python tools/eval_golden.py --live --target $(TARGET)

report:
	python report/daily_report.py

lineage:
	python docs/render_lineage.py

.PHONY: install bronze build check golden report lineage
