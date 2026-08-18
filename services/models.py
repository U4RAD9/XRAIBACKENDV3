from django.db import models
from service_group.models import ServiceGroup

class Service(models.Model):
    service_id = models.AutoField(primary_key=True)
    service_group = models.ForeignKey(ServiceGroup, on_delete=models.CASCADE, db_column='service_group_id')
    service_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    added_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
