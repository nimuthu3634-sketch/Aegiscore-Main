from sqlalchemy.orm import Session

from app.repositories.responses import ResponsesRepository
from app.schemas.common import ResponseActionListResponse
from app.services.serializers import to_response_action_summary_response


def list_response_actions(session: Session) -> ResponseActionListResponse:
    actions = ResponsesRepository(session).list_response_actions()
    return ResponseActionListResponse(
        items=[to_response_action_summary_response(action) for action in actions]
    )

