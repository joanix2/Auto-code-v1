import logging
from typing import Any, Callable, Coroutine, TypeVar

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def handle_operation(
    operation: str,
    callback: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    **kwargs: Any,
) -> T:
    try:
        return await callback(*args, **kwargs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{operation.capitalize()} error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {operation}: {str(e)}",
        )


async def handle_create(
    callback: Callable[..., Coroutine[Any, Any, T]], *args: Any, **kwargs: Any
) -> T:
    return await handle_operation("create", callback, *args, **kwargs)


async def handle_update(
    callback: Callable[..., Coroutine[Any, Any, T]], *args: Any, **kwargs: Any
) -> T:
    return await handle_operation("update", callback, *args, **kwargs)


async def handle_delete(
    callback: Callable[..., Coroutine[Any, Any, T]], *args: Any, **kwargs: Any
) -> T:
    return await handle_operation("delete", callback, *args, **kwargs)


async def handle_get(
    callback: Callable[..., Coroutine[Any, Any, T]], *args: Any, **kwargs: Any
) -> T:
    return await handle_operation("get", callback, *args, **kwargs)
