"""
Insert sample data into the Railway database (so you can include screenshots in your report).

Usage:
  - Ensure `DATABASE_URL` is set (Railway will provide it).
  - Run: python seed.py
"""

from sqlalchemy import func, select

from main import SessionLocal, UploadedFile


def seed_demo() -> None:
    sample_text = "Sample data created by seed.py\n"
    sample_bytes = sample_text.encode("utf-8")

    with SessionLocal() as session:
        existing = session.execute(
            select(func.count()).select_from(UploadedFile)
        ).scalar_one()
        if existing != 0:
            return

        session.add(
            UploadedFile(
                filename="sample.txt",
                content_type="text/plain",
                data=sample_bytes,
            )
        )
        session.commit()


if __name__ == "__main__":
    seed_demo()
    print("Seed complete.")

