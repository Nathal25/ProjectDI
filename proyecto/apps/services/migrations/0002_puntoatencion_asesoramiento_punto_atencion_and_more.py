# Generated by Django 5.0.6 on 2025-04-10 17:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_remove_paciente_condespecial'),
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PuntoAtencion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('servicio_ofrecido', models.CharField(max_length=100)),
                ('admin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='puntos_admin', to='authentication.admin')),
                ('asesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='puntos_asesor', to='authentication.asesor')),
            ],
        ),
        migrations.AddField(
            model_name='asesoramiento',
            name='punto_atencion',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_relacionados', to='services.puntoatencion'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='consultamedica',
            name='punto_atencion',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_relacionados', to='services.puntoatencion'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reclamarmedicamentos',
            name='punto_atencion',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_relacionados', to='services.puntoatencion'),
            preserve_default=False,
        ),
    ]
