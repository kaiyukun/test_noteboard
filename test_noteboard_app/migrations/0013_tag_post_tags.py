# Generated by Django 4.2.14 on 2024-11-24 04:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_noteboard_app', '0012_notification'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(blank=True, to='test_noteboard_app.tag'),
        ),
    ]