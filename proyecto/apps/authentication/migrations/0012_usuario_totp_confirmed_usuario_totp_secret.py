# Generated by Django 5.0.6 on 2025-06-11 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0011_remove_asesor_usuario_remove_paciente_usuario_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='totp_confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='totp_secret',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
