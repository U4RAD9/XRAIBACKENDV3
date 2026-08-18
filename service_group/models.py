from django.db import models

class ServiceGroup(models.Model):
    service_group_id = models.AutoField(primary_key=True)
    service_group_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    added_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
