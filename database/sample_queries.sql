USE smart_home_aiot;

SHOW TABLES;

SELECT 'device_types' AS table_name, COUNT(*) AS count FROM device_types
UNION ALL
SELECT 'devices', COUNT(*) FROM devices
UNION ALL
SELECT 'commands', COUNT(*) FROM commands
UNION ALL
SELECT 'command_parameters', COUNT(*) FROM command_parameters
UNION ALL
SELECT 'device_states', COUNT(*) FROM device_states
UNION ALL
SELECT 'routines', COUNT(*) FROM routines
UNION ALL
SELECT 'routine_steps', COUNT(*) FROM routine_steps;

SELECT
    dt.name AS device_type,
    c.action_name,
    c.tool_name,
    c.display_name
FROM commands c
JOIN device_types dt ON c.device_type_id = dt.id
ORDER BY dt.name, c.id;

SELECT
    dt.name AS device_type,
    c.tool_name,
    cp.param_name,
    cp.param_type,
    cp.is_required,
    cp.default_value,
    cp.allowed_values,
    cp.min_value,
    cp.max_value
FROM command_parameters cp
JOIN commands c ON cp.command_id = c.id
JOIN device_types dt ON c.device_type_id = dt.id
ORDER BY dt.name, c.id, cp.id;

SELECT
    r.name AS routine_name,
    r.display_name AS routine_display_name,
    rs.step_order,
    d.name AS device_name,
    c.tool_name,
    JSON_PRETTY(rs.input_params) AS input_params,
    rs.delay_seconds
FROM routine_steps rs
JOIN routines r ON rs.routine_id = r.id
JOIN devices d ON rs.device_id = d.id
JOIN commands c ON rs.command_id = c.id
ORDER BY r.name, rs.step_order;