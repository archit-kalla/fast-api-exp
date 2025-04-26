# An experiment in FastAPI, SQLAlchemy, Docker, and pgvector

## run docker

```bash
docker pull pgvector/pgvector:pg17

docker run -d -p 5432:5432 --name postgres_pgvec -e POSTGRES_PASSWORD=admin sha256:438a79880cd2559658c49ac807386179c036204411ceff761c98b947628aabdb

docker pull redis 

docker run -d -p 6379:6379 redis  
```

## run app

```bash
fastapi dev doc_ingest_app/main.py     

celery -A doc_ingest_app.tasks worker --loglevel=info --pool=solo

```
