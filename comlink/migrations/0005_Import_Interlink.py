from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def forward(apps, schema_editor):
    # This migration relied on the old Interlink system but that does not work
    # anymore because it has been removed.  If you need this code to port your
    # Interlink models to Comlink simply uncomment this method. --JLS
    #
    # User = apps.get_model(settings.AUTH_USER_MODEL)
    # InterlinkMailingList = apps.get_model("interlink", "MailingList")
    # ComlinkMailingList = apps.get_model("comlink", "MailingList")
    # EmailMessage = apps.get_model("comlink", "EmailMessage")
    #
    # print("  Moving Interlink Data...")
    # for old_list in InterlinkMailingList.objects.all():
    #     print("    Importing Interlink MailingList '%s'" % old_list.name)
    #     new_list = ComlinkMailingList.objects.filter(name=old_list.name).first()
    #     if not new_list:
    #         print("    Creating List '%s'" % old_list.name)
    #         new_list = ComlinkMailingList.objects.create (
    #             name = old_list.name,
    #             subject_prefix = old_list.subject_prefix,
    #             address = old_list.email_address,
    #             is_members_only = True,
    #             is_opt_out = old_list.is_opt_out,
    #             enabled = old_list.enabled,
    #         )
    #
    #         print("    Adding Subcribers and Unsubscribed...")
    #         for u in old_list.subscribers.all():
    #             new_list.subscribers.add(u)
    #         # for u in old_list.unsubscribed.all():
    #         #     new_list.unsubscribed.add(u)
    #         for u in old_list.moderators.all():
    #             new_list.moderators.add(u)
    #
    #         print("    Moving Emails...")
    #         for old_msg in old_list.incoming_mails.all():
    #             if not old_msg.body and not old_msg.html_body:
    #                 print("! Found Empty Email: %s" % old_msg.subject)
    #                 continue
    #             text_body = old_msg.body
    #             if not text_body:
    #                 text_body = ""
    #             html_body = old_msg.html_body
    #             if not html_body:
    #                 html_body = old_msg.body
    #             new_msg = EmailMessage.objects.create(
    #                 mailing_list = new_list,
    #                 user = old_msg.owner,
    #                 received = old_msg.sent_time,
    #                 sender = old_msg.origin_address,
    #                 from_str = old_msg.origin_address,
    #                 recipient = old_list.email_address,
    #                 subject = old_msg.subject[:255],
    #                 body_plain = text_body,
    #                 body_html = html_body,
    #             )
    #     print("  Done")
    return True


class Migration(migrations.Migration):

    dependencies = [
        ('comlink', '0004_EmailMessage'),
    ]

    operations = [
        # Fire off the big Important
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
