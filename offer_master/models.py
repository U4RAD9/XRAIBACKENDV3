from django.db import models
from service_group.models import ServiceGroup
from locations.models import Location
from user_type.models import UserType

class OfferMaster(models.Model):
    id = models.AutoField(primary_key=True)
    offer_name = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    discount_type = models.CharField(max_length=50) # "Item Level" or "Invoice Level"
    service_group = models.ManyToManyField(ServiceGroup, blank=True, related_name='offers')
    location = models.ManyToManyField(Location, blank=True, related_name='offers')
    user_type = models.ManyToManyField(UserType, blank=True, related_name='offers')
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.offer_name} ({self.discount}%)"
