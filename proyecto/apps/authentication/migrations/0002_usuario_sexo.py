# Generated by Django 5.0.6 on 2025-04-02 02:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='sexo',
            field=models.CharField(choices=[('m', 'M'), ('f', 'F')], default='m', max_length=10),
        ),
    ]
