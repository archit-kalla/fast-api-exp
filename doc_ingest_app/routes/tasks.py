from fastapi import APIRouter

from ..tasks import fake_task_remote, celery


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)

@router.post("/fakeTask", tags=["Tasks"])
async def fake_task():
    task = fake_task_remote.delay()
    return {"status": task.status, "task_id": task.id}

@router.get("/status/{task_id}", tags=["Tasks"])
async def get_status(task_id: str):
    task = celery.AsyncResult(task_id)
    if task.state == "PENDING":
        response = {
            "state": task.state,
            "status": "Pending...",
        }
    elif task.state != "FAILURE":
        response = {
            "state": task.state,
            "result": task.result,
        }
    else:
        response = {
            "state": task.state,
            "status": str(task.info),  # this is the exception raised
        }
    return response