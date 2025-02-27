# Generated by Django 5.1.5 on 2025-02-10 23:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Chatbot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_message', models.TextField()),
                ('bot_response', models.TextField(blank=True, null=True)),
                ('user_message_hash', models.CharField(max_length=64)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('SUCCESS', 'Success'), ('ERROR', 'Error')], max_length=50)),
                ('chatbot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chatbot.chatbot')),
            ],
            options={
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
                'ordering': ['-timestamp'],
            },
        ),
    ]
