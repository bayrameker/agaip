# agaip/models/task.py
from tortoise import fields, models

class Task(models.Model):
    id = fields.IntField(pk=True)
    agent_id = fields.CharField(max_length=50)
    payload = fields.JSONField()
    result = fields.JSONField(null=True)
    status = fields.CharField(max_length=20, default="pending")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
