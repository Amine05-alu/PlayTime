# Generated by Django 5.1.2 on 2024-11-12 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Aplicacion1', '0003_rename_user_perfil_usuario_remove_perfil_bio_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='confirmada',
            field=models.BooleanField(default=False),
        ),
    ]
