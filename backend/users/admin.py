from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from .models import User


class EmptyValueMixin:
    default_empty_display = "Нет данных"


@admin.register(User)
class UserAdmin(DjangoUserAdmin, EmptyValueMixin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name")
    readonly_fields = ("date_joined", "last_login")
    list_editable = ("is_active", "is_staff")
    list_display_links = ("email",)
    ordering = ("-date_joined",)
    fieldsets = [
        (None, {"fields": ["username", "password"]}),
        ("Личная информация", {
            "fields": ["first_name", "last_name", "email"]}),
        ("Права доступа", {
            "fields": ["is_active", "is_staff", "is_superuser"]}),
        ("Активность", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                ],
            },
        )
    ]


admin.site.unregister(Group)
