# Generated by Django 5.0.6 on 2025-04-03 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_usuario_sexo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='celular',
            field=models.IntegerField(unique=True),
        ),
    ]
