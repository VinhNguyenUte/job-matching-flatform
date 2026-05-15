from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID


def public_id_column():
    return Column(UUID(as_uuid=True), server_default=text("gen_random_uuid()"), unique=True)
