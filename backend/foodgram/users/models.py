from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.constants import MAX_LENGTH_ROLE, MAX_LENGTH_NAME
from foodgram.enums import Role


class Person(AbstractUser):
    role = models.CharField(
        'Роль пользователя',
        max_length=MAX_LENGTH_ROLE,
        choices=Role.choices(),
        default=Role.USER.value)
    first_name = models.CharField('Имя', max_length=MAX_LENGTH_NAME)
    last_name = models.CharField('Фамилия', max_length=MAX_LENGTH_NAME)
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH_NAME,
        blank=False,
        unique=True
    )
    email = models.EmailField(
        'Адрес эл. почты',
        blank=False,
        unique=True
    )
    password = models.CharField(max_length=MAX_LENGTH_NAME,
                                verbose_name='Пароль',
                                blank=False)
    avatar = models.ImageField(blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    @property
    def is_user(self):
        return self.role == Role.USER.value

    @property
    def is_admin(self):
        return self.role == Role.ADMIN.value

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
