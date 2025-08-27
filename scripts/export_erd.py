# scripts/export_erd.py
# Run:  python -m scripts.export_erd
import os, sys, shutil, subprocess
from pathlib import Path

# ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy_schemadisplay import create_schema_graph

from src.utils.db_utils import Base
try:
    from src.models import Books, Users, Rental  
except Exception:
    from src.models.Books import Books
    from src.models.Users import Users
    from src.models.RentalReq import Rental

def resolve_dot() -> str:
    """
    Return a full path to Graphviz 'dot' executable, even if PATH is broken.
    Order:
      1) GRAPHVIZ_DOT env var (if user set it)
      2) 'dot' found on PATH (works in some shells)
      3) Common Windows install locations
    """
    # 1) explicit env var
    env_dot = os.environ.get("GRAPHVIZ_DOT")
    if env_dot and Path(env_dot).exists():
        return env_dot

    # 2) on PATH?
    found = shutil.which("dot")
    if found:
        return found

    # 3) typical Windows locations
    candidates = [
        r"C:\Program Files\Graphviz\bin\dot.exe",
        r"C:\Program Files (x86)\Graphviz\bin\dot.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    # last resort: try appending common path and retry
    os.environ["PATH"] = os.environ.get("PATH", "") + r";C:\Program Files\Graphviz\bin"
    found = shutil.which("dot")
    if found:
        return found

    raise FileNotFoundError(
        'Graphviz "dot" not found. Install Graphviz and/or set env var GRAPHVIZ_DOT, e.g.: '
        r'GRAPHVIZ_DOT="C:\Program Files\Graphviz\bin\dot.exe"'
    )

def build_sync_url() -> str:
    # Prefer DATABASE_URL env
    url = os.environ.get("DATABASE_URL")
    if not url:
        # fallback: borrow async engine URL from db_utils.engine if you keep it there
        from src.utils.db_utils import engine as async_engine
        url = str(async_engine.url)
    # convert async drivers to sync for reflection
    return url.replace("+asyncpg", "+psycopg").replace("+aiopg", "+psycopg2")

if __name__ == "__main__":
    sync_url = build_sync_url()
    engine = create_engine(sync_url)

    graph = create_schema_graph(
        engine=engine,
        metadata=Base.metadata,  
        show_datatypes=True,
        show_indexes=True,
        rankdir="LR",
        concentrate=False
    )

    dot_path = resolve_dot()
    # optional: show which dot we’re using
    try:
        v = subprocess.check_output([dot_path, "-V"], stderr=subprocess.STDOUT, text=True)
        print("Using Graphviz:", v.strip())
    except Exception:
        print("Using Graphviz:", dot_path)

    out = ROOT / "erd.png"
    graph.write_png(str(out), prog=dot_path)
    print(f"✅ ERD exported to {out}")
