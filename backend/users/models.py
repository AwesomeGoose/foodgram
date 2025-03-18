from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import CharField
from django.utils.translation import gettext_lazy as _

from backend.constants import MAX_LEN_EMAIL, MAX_LEN_NAME


class User(AbstractUser):
    REQUIRED_FIELDS = ("username", "last_name", "first_name")
    USERNAME_FIELD = "email"

    username = models.CharField(
        _("Имя пользователя"),
        max_length=MAX_LEN_NAME,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(_("Имя"), max_length=MAX_LEN_NAME)
    last_name = models.CharField(_("Фамилия"), max_length=MAX_LEN_NAME)
    email = models.EmailField(_("Email"), max_length=MAX_LEN_EMAIL, unique=True)
    avatar = models.ImageField(
        _("Аватар"),
        upload_to="users/",
        blank=True,
    )
    bio = models.TextField(_("О себе"), blank=True, null=True)
    birth_date = models.DateField(_("Дата рождения"), blank=True, null=True)

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self) -> CharField:
        return self.first_name

    def __str__(self) -> CharField:
        return self.username

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")
        ordering = ("username",)


class Subscriptions(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriber",
        verbose_name=_("Подписчик"),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name=_("Автор"),
    )
    created_at = models.DateTimeField(_("Дата подписки"), auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username} подписан на {self.author.username}"

    class Meta:
        verbose_name = _("Подписка")
        verbose_name_plural = _("Подписки")
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="cannot_subscribe_to_self",
            ),
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_subscription",
            ),
        ]
