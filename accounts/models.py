from django.db import models

class UserType(models.Model):
    user_type_id = models.AutoField(primary_key=True)
    user_type_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.user_type_name

class User(models.Model):
    id = models.AutoField(primary_key=True)
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE, db_column='user_type_id')
    user_name = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    full_name = models.CharField(max_length=200, null=True, blank=True)
    mpin = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.user_name

class Permission(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    controller = models.CharField(max_length=100, null=True, blank=True)
    action = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.controller}/{self.action}"

class UsersLocation(models.Model):
    location_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    longitude = models.FloatField()
    latitude = models.FloatField()
    time_stamp = models.DateTimeField(auto_now_add=True)
    slot_booking_id = models.IntegerField(null=True, blank=True)

class OtpMaster(models.Model):
    otp_id = models.AutoField(primary_key=True)
    otp = models.CharField(max_length=10)
    otp_datetime = models.DateTimeField(auto_now_add=True)
    mobile = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.mobile} - {self.otp}"
