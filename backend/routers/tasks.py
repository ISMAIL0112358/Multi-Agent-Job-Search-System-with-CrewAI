from fastapi import APIRouter, Depends, HTTPException, status
from celery.result import AsyncResult
from backend.deps import get_current_user
from backend.models.user import User
from backend.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    """Check the status of a background task asynchronously."""
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        # Determine if finished
        if task_result.state == 'PENDING':
            response = {
                "state": task_result.state,
                "status": "Task is pending..."
            }
        elif task_result.state == 'FAILURE':
            response = {
                "state": task_result.state,
                "status": "Task failed",
                "error": str(task_result.info)
            }
        elif task_result.state == 'SUCCESS':
            response = {
                "state": task_result.state,
                "status": "Task completed successfully",
                "result": task_result.result
            }
        else:
            response = {
                "state": task_result.state,
                "status": "Task is in progress..."
            }
            
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve task status: {str(e)}"
        )
