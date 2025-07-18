from tortoise import fields
from tortoise.models import Model


class ParsingLog(Model):
    id = fields.UUIDField(pk=True)
    partner_id = fields.UUIDField()
    order_id = fields.UUIDField(null=True)
    order_number = fields.CharField(max_length=64)
    parser_name = fields.CharField(max_length=64)
    success = fields.BooleanField()
    status = fields.CharField(max_length=128, null=True)
    error_message = fields.TextField(null=True)
    raw_data = fields.JSONField(null=True)
    parsed_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "parsing_log"
        ordering = ["-parsed_at"]
