# Generated by Django 5.1.2 on 2024-11-15 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Aplicacion1', '0004_reserva_confirmada'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='archivo_reserva',
            field=models.FileField(blank=True, null=True, upload_to='reservas/documentos'),
        ),
        migrations.AddField(
            model_name='reserva',
            name='comentario',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='reserva',
            name='foto_instalacion',
            field=models.ImageField(blank=True, null=True, upload_to='reservas/fotos_instalacion'),
        ),
    ]
