import json
import logging

from app.core.logger import _JsonFormatter


def test_structured_log_keeps_flow_fields_but_omits_unapproved_content():
    record = logging.makeLogRecord({
        "name": "bridgeai",
        "levelno": logging.INFO,
        "levelname": "INFO",
        "msg": "agent.tool.started",
        "event": "agent.tool.started",
        "tool_name": "list_recent_emails",
        "message_body": "private email text",
    })

    result = json.loads(_JsonFormatter().format(record))

    assert result["event"] == "agent.tool.started"
    assert result["tool_name"] == "list_recent_emails"
    assert "request_id" not in result
    assert "message_body" not in result
