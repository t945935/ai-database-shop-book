"""Run tests against an externally supplied PostgreSQL DSN on any OS."""
import os
import subprocess
import sys

if not os.environ.get('SHOP_DSN'):
    raise SystemExit('SHOP_DSN is required; start PostgreSQL separately or use bootstrap_pg.sh on Ubuntu')
raise SystemExit(subprocess.call([sys.executable, '-m', 'pytest', '-v', '-s', *sys.argv[1:]]))
