# Generated by Django 3.1.1 on 2020-09-18 07:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0005_userbookrelation'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='reader',
            field=models.ManyToManyField(related_name='books', through='store.UserBookRelation', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='book',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='my_books', to=settings.AUTH_USER_MODEL),
        ),
    ]
