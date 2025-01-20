# Generated by Django 5.1.5 on 2025-01-20 12:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contacts", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="projectmessage",
            name="read_by",
            field=models.ManyToManyField(
                related_name="read_messages", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="projectmessage",
            name="sender",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sent_project_messages",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="messageattachment",
            name="message",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attachments",
                to="contacts.projectmessage",
            ),
        ),
        migrations.AddIndex(
            model_name="projectconversation",
            index=models.Index(
                fields=["-updated_at"], name="contacts_pr_updated_18d967_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="projectconversation",
            index=models.Index(
                fields=["project", "-updated_at"], name="contacts_pr_project_c76487_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="projectmessage",
            index=models.Index(
                fields=["conversation", "created_at"],
                name="contacts_pr_convers_18f809_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="projectmessage",
            index=models.Index(
                fields=["sender", "created_at"], name="contacts_pr_sender__aea048_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="messageattachment",
            index=models.Index(
                fields=["message", "uploaded_at"], name="contacts_me_message_adbdfc_idx"
            ),
        ),
    ]
