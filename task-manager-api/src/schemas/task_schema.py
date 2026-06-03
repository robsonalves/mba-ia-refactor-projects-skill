from datetime import datetime

from marshmallow import Schema, fields, validate

from src.config.constants import (
    PRIORITY_MAX,
    PRIORITY_MIN,
    TASK_STATUSES,
    TITLE_MAX,
    TITLE_MIN,
)


class TaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=TITLE_MIN, max=TITLE_MAX))
    description = fields.Str(load_default="")
    status = fields.Str(load_default="pending", validate=validate.OneOf(TASK_STATUSES))
    priority = fields.Int(load_default=3, validate=validate.Range(min=PRIORITY_MIN, max=PRIORITY_MAX))
    user_id = fields.Int(load_default=None, allow_none=True)
    category_id = fields.Int(load_default=None, allow_none=True)
    due_date = fields.Str(load_default=None, allow_none=True)
    tags = fields.Raw(load_default=None, allow_none=True)


task_create_schema = TaskSchema()
task_update_schema = TaskSchema(partial=True)


def parse_due_date(value):
    if value is None or value == "":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def normalize_tags(value):
    if value is None:
        return None
    if isinstance(value, list):
        return ",".join(str(t) for t in value)
    return str(value)
