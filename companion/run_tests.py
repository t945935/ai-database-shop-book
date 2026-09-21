"""Create a disposable PostgreSQL cluster; never use an existing database."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

pg = Path(os.environ.get("PG_BIN", str(Path.home() / ".cache/shop-pg16/root/usr/lib/postgresql/16/bin")))
with tempfile.TemporaryDirectory(prefix="shop-p1-") as tmp:
    root = Path(tmp)
    data = root / "data"
    subprocess.run([pg / "initdb", "-D", data, "--no-locale", "--encoding=UTF8", "--auth-local=trust", "--auth-host=reject"], check=True)
    started = False
    try:
        # Private 0700 directory and no TCP: same port can coexist safely.
        subprocess.run([pg / "pg_ctl", "-D", data, "-l", root / "server.log", "-o", f"-k {root} -p 55439 -c listen_addresses=''", "-w", "start"], check=True)
        started = True
        env = dict(os.environ, SHOP_DSN=f"host={root} port=55439 dbname=postgres")
        import psycopg
        with psycopg.connect(env["SHOP_DSN"]) as conn:
            print("SERVER:", conn.execute("select version()").fetchone()[0], flush=True)
        print("PYTHON:", sys.version, "PSYCOPG:", psycopg.__version__, flush=True)
        result = subprocess.run([sys.executable, "-m", "pytest", "-v", "-s", *sys.argv[1:]], env=env)
    finally:
        if started:
            subprocess.run([pg / "pg_ctl", "-D", data, "-m", "fast", "-w", "stop"], check=True)
    sys.exit(result.returncode)
