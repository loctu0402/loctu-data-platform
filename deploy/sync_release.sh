#!/usr/bin/env bash
set -euo pipefail

target="${1:?usage: deploy/sync_release.sh <target-root>}"
sha="$(git rev-parse --short HEAD)"
release="$target/releases/$sha"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$release" "$target/deploys"
rsync -a --checksum --delete --exclude-from=deploy/sync.exclude ./ "$release/"
echo "$sha" > "$release/DEPLOYED_SHA"

ln -sfn "$release" "$target/current.next"
mv -Tf "$target/current.next" "$target/current"

changed="$(git diff --name-only HEAD~1 HEAD 2>/dev/null | sed 's/.*/"&"/' | paste -sd, - || true)"
cat > "$target/deploys/${stamp}_${sha}.json" <<JSON
{"_meta": {"schema_version": 1, "key": "${stamp}_${sha}", "as_of": "${stamp}", "source": "deploy/sync_release.sh"},
 "sha": "${sha}", "release": "${release}", "changed": [${changed}]}
JSON

ls -1dt "$target"/releases/* | tail -n +6 | xargs -r rm -rf
echo "deployed $sha to $target/current"
