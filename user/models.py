from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class Meta:
    db_table = 'user'

class UserManager(BaseUserManager):
    def create_user(self, email, password, name, phone, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수입니다.')
        if not name:
            raise ValueError('이름은 필수입니다.')
        if not password:
            raise ValueError('비밀번호는 필수입니다.')
        if not phone:
            raise ValueError('휴대폰번호는 필수입니다.')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            phone=phone,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, name, phone, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, name, phone, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=20, null=False, blank=False)         # NOT NULL
    email = models.EmailField(unique=True, max_length=50, null=False, blank=False)   # NOT NULL
    password = models.CharField(max_length=128, null=False, blank=False)    # NOT NULL, set_password로 암호화!
    phone = models.CharField(max_length=20, null=False, blank=False)        # NOT NULL
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True, null=False, blank=False)
    is_deleted = models.BooleanField(default=False, null=False, blank=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone']

    def __str__(self):
        return self.email
