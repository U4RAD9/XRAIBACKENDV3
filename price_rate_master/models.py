from django.db import models
from services.models import Service
from locations.models import Location

class PriceRateMaster(models.Model):
    id = models.AutoField(primary_key=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='price_rates')
    visit_type = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service.service_name} - {self.visit_type} ({self.price})"

class PriceRateMasterLocation(models.Model):
    id = models.AutoField(primary_key=True)
    price_rate_master = models.ForeignKey(PriceRateMaster, on_delete=models.CASCADE, related_name='location_prices')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='custom_prices')
    custom_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.location.location_name} - {self.custom_price}"
