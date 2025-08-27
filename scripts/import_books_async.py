# ── run:  python -m scripts.import_books_async test_data/books.csv
import sys, asyncio
from pathlib import Path
import csv
from typing import Optional


# Windows event loop policy for psycopg3 async
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Ensure project root in sys.path when running as a script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.db_utils import engine, Base, create_database_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# try both import paths for your model
try:
    from src.models import Books, Users, Rental
except ModuleNotFoundError:
    from src.models import Books, Users, Rental  # fallback if you don't use "src."


# --- header mapping: Book-Crossing & our schema ---
HEADER_MAP = {
    "isbn": {"isbn", "ISBN"},
    "title": {"title", "Book-Title"},
    "author": {"author", "Book-Author"},
    "published_year": {"published_year", "Year-Of-Publication", "year"},
    "publisher": {"publisher", "Publisher"},
    "image_url_s": {"image_url_s", "Image-URL-S"},
    "image_url_m": {"image_url_m", "Image-URL-M"},
    "image_url_l": {"image_url_l", "Image-URL-L"},
    "total_copies": {"total_copies", "so_luong", "ton_kho"},
}

def _to_int(v: Optional[str], default: Optional[int]=None) -> Optional[int]:
    try:
        return int(v) if v not in (None, "") else default
    except ValueError:
        return default

def _pick(d: dict, keys: set[str], default=None):
    # keys can include quotes in Book-Crossing; strip quotes for matching
    keyset = {k.strip('"') for k in d.keys()}
    for k in keys:
        if k in d:
            val = d[k]
            return val if val != "" else default
        if k in keyset:
            # try unquoted lookup
            for raw in d.keys():
                if raw.strip('"') == k:
                    val = d[raw]
                    return val if val != "" else default
    return default

def _sniff_delimiter(p: Path) -> str:
    # detect ; vs , using first non-empty line
    with p.open("r", encoding="utf-8", newline="") as f:
        sample = ""
        for line in f:
            if line.strip():
                sample = line
                break
    return ";" if sample.count(";") > sample.count(",") else ","


async def upsert_book(db: AsyncSession, row: dict) -> bool:
    # normalize one row to our fields
    title = (_pick(row, HEADER_MAP["title"]) or "").strip()
    author = (_pick(row, HEADER_MAP["author"]) or "").strip()
    year = _to_int(_pick(row, HEADER_MAP["published_year"]))
    publisher = (_pick(row, HEADER_MAP["publisher"]) or None)
    isbn = (_pick(row, HEADER_MAP["isbn"]) or None)
    image_url_s = (_pick(row, HEADER_MAP["image_url_s"]) or None)
    image_url_m = (_pick(row, HEADER_MAP["image_url_m"]) or None)
    image_url_l = (_pick(row, HEADER_MAP["image_url_l"]) or None)
    total_copies = _to_int(_pick(row, HEADER_MAP["total_copies"]), 1) or 1

    # minimal required
    if not title or not author or year is None:
        return False

    # upsert by ISBN then by (title, author)
    book = None
    if isbn:
        res = await db.execute(select(Books).where(Books.isbn == isbn))
        book = res.scalars().first()
    if not book:
        res = await db.execute(select(Books).where(Books.title == title, Books.author == author))
        book = res.scalars().first()

    if book:
        diff = total_copies - (book.total_copies or 0)
        book.title = title
        book.author = author
        book.published_year = year
        book.publisher = publisher
        book.isbn = isbn
        book.image_url_s = image_url_s
        book.image_url_m = image_url_m
        book.image_url_l = image_url_l
        book.total_copies = total_copies
        book.available_copies = max(0, (book.available_copies or 0) + diff)
        db.add(book)
    else:
        db.add(Books(
            title=title,
            author=author,
            published_year=year,
            publisher=publisher,
            isbn=isbn,
            image_url_s=image_url_s,
            image_url_m=image_url_m,
            image_url_l=image_url_l,
            total_copies=total_copies,
            available_copies=total_copies,
        ))
    return True


async def main(csv_path: str):
    p = Path(csv_path)
    if not p.exists():
        raise SystemExit(f"File not found: {csv_path}")

    delim = _sniff_delimiter(p)
    print(">>> Using DB:", engine.url)
    print(">>> CSV delimiter detected:", repr(delim))

    # create tables if needed
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # read rows
    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delim)
        rows = list(reader)
    print(">>> CSV rows detected:", len(rows))

    processed = 0
    written = 0
    async for db in create_database_session():
        async with db.begin():
            for row in rows:
                processed += 1
                ok = await upsert_book(db, row)
                if ok:
                    written += 1
        # post-commit sanity count
        res = await db.execute(select(Books))
        total = len(res.scalars().all())
        print(f">>> Rows processed: {processed}, written: {written}, total in DB now: {total}")
        break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.import_books_async <path_to_csv>")
        raise SystemExit(1)
    asyncio.run(main(sys.argv[1]))
