from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Book, UserBookRelation

# первый вариант
admin.site.register(Book)

# второй вариант
@admin.register(UserBookRelation)
class UserBookRelationAdmin(ModelAdmin):
    pass
