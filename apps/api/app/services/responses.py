from sqlalchemy.orm import Session

from app.repositories.responses import ResponsesRepository
from app.schemas.common import ResponseActionListResponse
from app.schemas.listing import ListMetaResponse, ResponseListQuery
from app.services.serializers import to_response_action_summary_response


def list_response_actions(
    session: Session, query: ResponseListQuery
) -> ResponseActionListResponse:
    actions, total = ResponsesRepository(session).list_response_actions(query)
    total_pages = max(1, (total + query.page_size - 1) // query.page_size)
    page = min(query.page, total_pages)

    return ResponseActionListResponse(
        items=[to_response_action_summary_response(action) for action in actions],
        meta=ListMetaResponse(
            page=page,
            page_size=query.page_size,
            total=total,
            total_pages=total_pages,
            sort_by=query.sort_by.value,
            sort_direction=query.sort_direction,
            warnings=[],
        ),
    )
