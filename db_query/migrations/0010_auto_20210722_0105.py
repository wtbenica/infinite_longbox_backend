# Generated by Django 3.2.5 on 2021-07-22 01:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db_query', '0009_auto_20210722_0029'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gcdcharacter',
            name='membership',
        ),
        migrations.AddField(
            model_name='gcdcharacterappearance',
            name='membership',
            field=models.TextField(null=True),
        ),
    ]
