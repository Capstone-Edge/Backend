from typing import Any


def validate_llm_parse_result(
    parsed: dict[str, Any],
    tools_data: dict[str, Any],
    states_data: dict[str, Any],
) -> tuple[bool, str | None]:
    """
    LLM이 생성한 commands가 DB 기반 MCP Tool/Resource 규격을 만족하는지 검증한다.
    """

    commands = parsed.get("commands", [])

    # 재질문이면 commands가 비어 있어도 정상
    if parsed.get("clarification_needed") is True:
        return True, None

    if not isinstance(commands, list):
        return False, "commands must be a list"

    tool_map = {
        tool["name"]: tool
        for tool in tools_data.get("tools", [])
    }

    device_names = {
        device["device_name"]
        for device in states_data.get("devices", [])
    }

    for command in commands:
        tool_name = command.get("tool_name")
        device_name = command.get("device_name")
        parameters = command.get("parameters", {})

        if device_name not in device_names:
            return False, f"Unknown device_name: {device_name}"

        if tool_name not in tool_map:
            return False, f"Unknown tool_name: {tool_name}"

        tool_schema = tool_map[tool_name].get("input_schema", {})
        properties = tool_schema.get("properties", {})
        required = tool_schema.get("required", [])

        for required_key in required:
            if required_key not in parameters:
                return False, f"Missing required parameter: {required_key}"

        for key, value in parameters.items():
            if key not in properties:
                return False, f"Unknown parameter '{key}' for tool '{tool_name}'"

            spec = properties[key]

            if "enum" in spec and value not in spec["enum"]:
                return False, f"Invalid enum value for {key}: {value}"

            if "minimum" in spec and isinstance(value, (int, float)):
                if value < spec["minimum"]:
                    return False, f"{key} is below minimum: {value}"

            if "maximum" in spec and isinstance(value, (int, float)):
                if value > spec["maximum"]:
                    return False, f"{key} is above maximum: {value}"

    return True, None