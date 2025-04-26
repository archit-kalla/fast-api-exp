

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import Session

from doc_ingest_app.models.sql_models import Base

url = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="admin",
    host="localhost",
    port=5432,
    database="postgres"
)
engine = create_engine(url, echo=True)

def create_tables():
    #create session
    with Session(engine) as session:
        session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        session.commit()

    Base.metadata.create_all(engine)

def drop_tables():
    #create session
    Base.metadata.drop_all(engine)
    with Session(engine) as session:
        session.execute(text('DROP EXTENSION IF EXISTS vector'))
        session.commit()

if __name__ == "__main__":
    drop_tables()