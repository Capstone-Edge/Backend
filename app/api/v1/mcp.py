import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db

router = APIRouter(prefix="/api/v1/mcp", tags=["MCP"])


@router.get("/resources/device-states")
def get_mcp_device_states(
    device_name: str | None = Query(default=None),
    device_type: str | None = Query(default=None),
    location: str | None = Query(default=None),
    is_active: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    query = """
        SELECT
            d.name AS device_name,
            dt.name AS device_type,
            d.display_name AS display_name,
            d.location AS location,
            ds.state_data AS state,
            ds.updated_at AS updated_at
        FROM device_states ds
        JOIN devices d ON ds.device_id = d.id
        JOIN device_types dt ON d.device_type_id = dt.id
        WHERE d.is_active = :is_active
    """

    params = {"is_active": is_active}

    if device_name:
        query += " AND d.name = :device_name"
        params["device_name"] = device_name

    if device_type:
        query += " AND dt.name = :device_type"
        params["device_type"] = device_type

    if location:
        query += " AND d.location = :location"
        params["location"] = location

    query += " ORDER BY d.name"

    rows = db.execute(text(query), params).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="No device states found")

    devices = []

    for row in rows:
        state = row["state"]

        # PyMySQL이 JSON을 문자열로 반환하는 경우 처리
        if isinstance(state, str):
            state = json.loads(state)

        devices.append(
            {
                "device_name": row["device_name"],
                "device_type": row["device_type"],
                "display_name": row["display_name"],
                "location": row["location"],
                "state": state,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
        )

    return {"devices": devices}


@router.get("/tools")
def get_mcp_tools(
    device_type: str | None = Query(default=None),
    is_active: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    query = """
        SELECT
            c.id AS command_id,
            c.tool_name AS tool_name,
            c.action_name AS action_name,
            c.description AS command_description,
            dt.name AS device_type,
            cp.param_name AS param_name,
            cp.param_type AS param_type,
            cp.is_required AS is_required,
            cp.allowed_values AS allowed_values,
            cp.min_value AS min_value,
            cp.max_value AS max_value,
            cp.description AS param_description
        FROM commands c
        JOIN device_types dt ON c.device_type_id = dt.id
        LEFT JOIN command_parameters cp ON cp.command_id = c.id
        WHERE c.is_active = :is_active
          AND dt.is_active = :is_active
    """

    params = {"is_active": is_active}

    if device_type:
        query += " AND dt.name = :device_type"
        params["device_type"] = device_type

    query += " ORDER BY dt.name, c.tool_name, cp.id"

    rows = db.execute(text(query), params).mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="No MCP tools found")

    tools_dict = {}

    for row in rows:
        tool_name = row["tool_name"]

        if tool_name not in tools_dict:
            tools_dict[tool_name] = {
                "name": tool_name,
                "device_type": row["device_type"],
                "action_name": row["action_name"],
                "description": row["command_description"],
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            }

        param_name = row["param_name"]

        # 파라미터가 없는 명령도 고려
        if param_name is None:
            continue

        param_schema = {
            "type": row["param_type"],
        }

        # allowed_values가 있으면 JSON 파싱 후 enum으로 변환
        if row["allowed_values"] is not None:
            allowed_values = row["allowed_values"]

            if isinstance(allowed_values, str):
                allowed_values = json.loads(allowed_values)

            param_schema["enum"] = allowed_values

        # min/max가 있으면 minimum/maximum으로 변환
        if row["min_value"] is not None:
            if row["param_type"] == "integer":
                param_schema["minimum"] = int(row["min_value"])
            else:
                param_schema["minimum"] = row["min_value"]

        if row["max_value"] is not None:
            if row["param_type"] == "integer":
                param_schema["maximum"] = int(row["max_value"])
            else:
                param_schema["maximum"] = row["max_value"]

        if row["param_description"] is not None:
            param_schema["description"] = row["param_description"]

        tools_dict[tool_name]["input_schema"]["properties"][param_name] = param_schema

        if row["is_required"]:
            tools_dict[tool_name]["input_schema"]["required"].append(param_name)

    return {
        "tools": list(tools_dict.values())
    }