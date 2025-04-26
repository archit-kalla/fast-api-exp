# An experiment in FastAPI, SQLAlchemy, Docker, and pgvector

## run docker

```bash
docker pull pgvector/pgvector:pg17

docker run -d -p 5432:5432 --name postgres_pgvec -e POSTGRES_PASSWORD=admin pgvector/pgvector:pg17

docker pull redis 

docker run -d -p 6379:6379 redis  

docker pull localstack/localstack

docker run --rm -it -p 4566:4566 -p 4510-4559:4510-4559 -d localstack/localstack
```

## run app

```bash
fastapi dev doc_ingest_app/main.py     

celery -A doc_ingest_app.tasks worker --loglevel=info --pool=solo

```
