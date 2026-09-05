"""Simple sequential document-number generator per prefix, backed by a counter table.

Uses SELECT ... FOR UPDATE style row locking (via a dedicated counters table) so
concurrent requests do not generate duplicate numbers.
"""
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import Session

from app.db.session import Base


class DocumentCounter(Base):
    __tablename__ = "document_counters"

    prefix = Column(String(20), primary_key=True)
    last_value = Column(Integer, nullable=False, default=0)


def next_number(db: Session, prefix: str) -> str:
    counter = (
        db.query(DocumentCounter)
        .filter(DocumentCounter.prefix == prefix)
        .with_for_update()
        .first()
    )
    if counter is None:
        counter = DocumentCounter(prefix=prefix, last_value=0)
        db.add(counter)
        db.flush()
        counter = (
            db.query(DocumentCounter)
            .filter(DocumentCounter.prefix == prefix)
            .with_for_update()
            .first()
        )
    counter.last_value += 1
    db.flush()
    return f"{prefix}-{counter.last_value:06d}"
