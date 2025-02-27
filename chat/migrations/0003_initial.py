# Generated by Django 5.1.5 on 2025-02-10 23:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('chat', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='projectmessage',
            name='read_by',
            field=models.ManyToManyField(related_name='read_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='projectmessage',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_project_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='messageattachment',
            name='message',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='chat.projectmessage'),
        ),
        migrations.AddIndex(
            model_name='projectconversation',
            index=models.Index(fields=['-updated_at'], name='chat_projec_updated_bbccac_idx'),
        ),
        migrations.AddIndex(
            model_name='projectconversation',
            index=models.Index(fields=['project', '-updated_at'], name='chat_projec_project_d51689_idx'),
        ),
        migrations.AddIndex(
            model_name='projectmessage',
            index=models.Index(fields=['conversation', 'created_at'], name='chat_projec_convers_f7af16_idx'),
        ),
        migrations.AddIndex(
            model_name='projectmessage',
            index=models.Index(fields=['sender', 'created_at'], name='chat_projec_sender__13e4d5_idx'),
        ),
        migrations.AddIndex(
            model_name='messageattachment',
            index=models.Index(fields=['message', 'uploaded_at'], name='chat_messag_message_f34817_idx'),
        ),
    ]
