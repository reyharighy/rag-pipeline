from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.prompt_templates import (
    TEMPLATE_KEYS,
    list_prompt_templates,
    set_template_body,
)

router = APIRouter()


class PromptTemplateUpdate(BaseModel):
    body: str = Field(..., min_length=1)


@router.get("/prompt-templates")
def get_prompt_templates() -> dict[str, list[dict[str, str]]]:
    return {"templates": list_prompt_templates()}


@router.put("/prompt-templates/{key}")
def put_prompt_template(
    key: str, payload: PromptTemplateUpdate
) -> dict[str, str | bool]:
    if key not in TEMPLATE_KEYS:
        raise HTTPException(status_code=404, detail="Unknown template key")

    try:
        set_template_body(key, payload.body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return {"ok": True, "key": key}
