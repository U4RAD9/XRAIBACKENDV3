from django.db import models

class OtpMaster(models.Model):
    otp_id = models.AutoField(primary_key=True)
    otp = models.CharField(max_length=10)
    otp_datetime = models.DateTimeField(auto_now_add=True)
    mobile = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.mobile} - {self.otp}"
