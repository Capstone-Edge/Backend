import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db

router = APIRouter(prefix="/api/v1/routines", tags=["Routines"])


@router.get("")
def get_routines(
    is_active: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    query = """
        SELECT
            name AS routine_name,
            display_name AS routine_display_name,
            description,
            is_active
        FROM routines
        WHERE is_active = :is_active
        ORDER BY name
    """

    rows = db.execute(text(query), {"is_active": is_active}).mappings().all()

    return {
        "routines": [
            {
                "routine_name": row["routine_name"],
                "routine_display_name": row["routine_display_name"],
                "description": row["description"],
                "is_active": bool(row["is_active"]),
            }
            for row in rows
        ]
    }


@router.get("/{routine_name}")
def get_routine_detail(
    routine_name: str,
    db: Session = Depends(get_db),
):
    routine_query = """
        SELECT
            id,
            name AS routine_name,
            display_name AS routine_display_name,
            description,
            is_active
        FROM routines
        WHERE name = :routine_name
          AND is_active = true
        LIMIT 1
    """

    routine = db.execute(
        text(routine_query),
        {"routine_name": routine_name}
    ).mappings().first()

    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")

    steps_query = """
        SELECT
            rs.step_order AS step_order,
            d.name AS device_name,
            dt.name AS device_type,
            c.tool_name AS tool_name,
            rs.input_params AS parameters,
            rs.delay_seconds AS delay_seconds
        FROM routine_steps rs
        JOIN devices d ON rs.device_id = d.id
        JOIN device_types dt ON d.device_type_id = dt.id
        JOIN commands c ON rs.command_id = c.id
        WHERE rs.routine_id = :routine_id
          AND rs.is_active = true
        ORDER BY rs.step_order
    """

    step_rows = db.execute(
        text(steps_query),
        {"routine_id": routine["id"]}
    ).mappings().all()

    steps = []

    for row in step_rows:
        parameters = row["parameters"]

        if isinstance(parameters, str):
            parameters = json.loads(parameters)

        steps.append(
            {
                "step_order": row["step_order"],
                "device_name": row["device_name"],
                "device_type": row["device_type"],
                "tool_name": row["tool_name"],
                "parameters": parameters,
                "delay_seconds": row["delay_seconds"] or 0,
            }
        )

    return {
        "routine_name": routine["routine_name"],
        "routine_display_name": routine["routine_display_name"],
        "description": routine["description"],
        "steps": steps,
    }