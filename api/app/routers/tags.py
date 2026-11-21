from fastapi import APIRouter

from app.dependencies import SessionDep
from app.schemas import TagOut
from app.services import tags as service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
def list_tags(session: SessionDep) -> list[TagOut]:
    return [TagOut.model_validate(tag) for tag in service.list_tags(session)]
