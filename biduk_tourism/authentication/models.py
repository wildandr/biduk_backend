from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model yang memperluas AbstractUser dengan field tambahan
    untuk kebutuhan Sistem Informasi Pariwisata Kecamatan Biduk-Biduk
    """
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username
