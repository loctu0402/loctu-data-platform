DBT = cd dbt && dbt
TARGET ?= dev
BASE ?= origin/main
VM_ROOT ?= /tmp/airflow-vm

install:
	pip install -r requirements.txt

parse:
	$(DBT) parse --profiles-dir .

lint:
	python tools/lint.py

test:
	pytest -q

gate:
	python tools/gate.py

ground:
	python tools/ground.py

eval:
	python tools/eval_golden.py

check: parse lint test gate ground eval

plan: parse
	python tools/detect.py --base $(BASE) --head HEAD

simulate:
	bash deploy/sync_release.sh $(VM_ROOT)
	bash deploy/sync_release.sh $(VM_ROOT)
	bash deploy/smoke_check.sh $(VM_ROOT)

bronze:
	python ingestion/load_bronze.py

build:
	$(DBT) source freshness --profiles-dir . --target $(TARGET)
	$(DBT) build --profiles-dir . --target $(TARGET)

golden:
	python tools/eval_golden.py --live --target $(TARGET)

report:
	python report/daily_report.py

lineage:
	python docs/render_lineage.py

.PHONY: install parse lint test gate ground eval check plan simulate bronze build golden report lineage
