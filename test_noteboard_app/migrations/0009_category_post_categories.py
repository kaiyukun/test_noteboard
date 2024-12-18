# Generated by Django 4.2.5 on 2024-08-24 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_noteboard_app', '0008_member_followers_member_only_followers_flg'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='posts', to='test_noteboard_app.category'),
        ),
    ]
