from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group, Permission, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class UserRoles(models.TextChoices):
        SUPERADMIN = 'a', "admin"

    full_name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=UserRoles.choices, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name='custom_user_set', blank=True, verbose_name='groups',
                                    help_text='The groups this user belongs to')
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_permissions_set', blank=True,
                                              verbose_name='user permissions',
                                              help_text='Specific permissions for this user.', )

    USERNAME_FIELD = 'phone_number'

    objects = UserManager()

    def __str__(self):
        return f'{self.full_name or ""} {self.phone_number}'

    class Meta:
        db_table = 'user'
