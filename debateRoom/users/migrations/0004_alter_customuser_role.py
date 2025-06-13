# Generated by Django 5.2.1 on 2025-06-09 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_customuser_is_approved_alter_customuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('moderator', 'Moderator'), ('debator', 'Debator'), ('audience', 'Audience')], default='audience', max_length=64),
        ),
    ]
