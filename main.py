import os
from datetime import datetime

from flask import Flask, Response, abort, redirect, render_template, request, url_for
from sqlalchemy import DateTime, Integer, LargeBinary, String, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///local.db"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class UploadedFile(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(256), nullable=True)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# Create the schema automatically on first run.
Base.metadata.create_all(engine)


@app.get("/")
def index():
    with SessionLocal() as session:
        rows = session.execute(
            select(
                UploadedFile.id,
                UploadedFile.filename,
                UploadedFile.uploaded_at,
                func.octet_length(UploadedFile.data).label("size"),
            ).order_by(UploadedFile.uploaded_at.desc())
        )
        files = [
            {
                "id": f.id,
                "name": f.filename,
                "size": f.size,
                "uploaded_at": f.uploaded_at,
            }
            for f in rows
        ]
    return render_template("index.html", files=files)


@app.post("/upload")
def upload():
    if "file" not in request.files:
        return redirect(url_for("index"))

    f = request.files["file"]
    if not f or not f.filename:
        return redirect(url_for("index"))

    filename = secure_filename(f.filename)
    if not filename:
        return redirect(url_for("index"))

    data = f.read()
    if not data:
        return redirect(url_for("index"))

    uf = UploadedFile(
        filename=filename,
        content_type=f.mimetype or "application/octet-stream",
        data=data,
    )
    with SessionLocal() as session:
        session.add(uf)
        session.commit()

    return redirect(url_for("index"))


@app.get("/download/<int:file_id>")
def download(file_id: int):
    with SessionLocal() as session:
        uf = session.get(UploadedFile, file_id)
        if not uf:
            abort(404, description="File not found.")

        safe_name = os.path.basename(uf.filename) or "download"
        return Response(
            uf.data,
            mimetype=uf.content_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
        )


@app.post("/rename/<int:file_id>")
def rename(file_id: int):
    new_name = (request.form.get("new_name") or "").strip()
    new_name = secure_filename(new_name)
    if not new_name:
        abort(400, description="Missing new_name.")

    with SessionLocal() as session:
        uf = session.get(UploadedFile, file_id)
        if not uf:
            abort(404, description="File not found.")
        uf.filename = new_name
        session.commit()

    return redirect(url_for("index"))


@app.post("/delete/<int:file_id>")
def delete(file_id: int):
    with SessionLocal() as session:
        uf = session.get(UploadedFile, file_id)
        if not uf:
            abort(404, description="File not found.")
        session.delete(uf)
        session.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
