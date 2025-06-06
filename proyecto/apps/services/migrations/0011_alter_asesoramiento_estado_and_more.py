# Generated by Django 5.0.6 on 2025-06-02 23:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0010_asesoramiento_estado_consultamedica_estado_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asesoramiento',
            name='estado',
            field=models.CharField(choices=[('Pendiente', 'pendiente'), ('Atendido', 'atendido')], default='Pendiente', max_length=10),
        ),
        migrations.AlterField(
            model_name='consultamedica',
            name='estado',
            field=models.CharField(choices=[('Pendiente', 'pendiente'), ('Atendido', 'atendido')], default='Pendiente', max_length=10),
        ),
        migrations.AlterField(
            model_name='reclamarmedicamentos',
            name='estado',
            field=models.CharField(choices=[('Pendiente', 'pendiente'), ('Atendido', 'atendido')], default='Pendiente', max_length=10),
        ),
    ]
