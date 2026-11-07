#!/usr/bin/env bash
set -euo pipefail

: "${RUNNER_TOKEN:?registration token from Settings > Actions > Runners > New self-hosted runner}"
repo_url="${REPO_URL:-https://github.com/loctu0402/loctu-data-platform}"
dir=/opt/actions-runner
version="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest | grep -oP '"tag_name":\s*"v\K[^"]+')"

id -u runner >/dev/null 2>&1 || sudo useradd -m -s /bin/bash runner
sudo mkdir -p "$dir" /opt/airflow/repo
sudo chown runner "$dir" /opt/airflow/repo

cd "$dir"
sudo -u runner curl -fsSL -o runner.tgz "https://github.com/actions/runner/releases/download/v${version}/actions-runner-linux-x64-${version}.tar.gz"
sudo -u runner tar xzf runner.tgz
sudo -u runner ./config.sh --unattended --url "$repo_url" --token "$RUNNER_TOKEN" \
  --name "$(hostname)" --labels airflow-vm --work _work --replace
sudo ./svc.sh install runner
sudo ./svc.sh start
echo "runner $(hostname) registered with label airflow-vm, version $version"
