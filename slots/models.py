from django.db import models

class SlotMaster(models.Model):
    slot_id = models.AutoField(primary_key=True)
    slot_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
