#!/usr/bin/env bash
# Ubuntu 24.04 amd64 only. Downloads and extracts; never installs a service.
set -euo pipefail
here=$(cd -- "$(dirname -- "$0")" && pwd)
cache=${PG_CACHE:-"$HOME/.cache/shop-pg16"}
mkdir -p "$cache/debs" "$cache/root"
cd "$cache/debs"
apt-get download postgresql-16=16.15-0ubuntu0.24.04.1 postgresql-client-16=16.15-0ubuntu0.24.04.1 libpq5=16.15-0ubuntu0.24.04.1
sha256sum -c "$here/pg-packages.sha256"
for file in libpq5_16.15-0ubuntu0.24.04.1_amd64.deb postgresql-16_16.15-0ubuntu0.24.04.1_amd64.deb postgresql-client-16_16.15-0ubuntu0.24.04.1_amd64.deb; do
    dpkg-deb -x "$file" "$cache/root"
done
"$cache/root/usr/lib/postgresql/16/bin/postgres" --version
