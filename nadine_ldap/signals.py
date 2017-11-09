from __future__ import unicode_literals

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save

@receiver(pre_save, sender=User)
def user_pre_save(**kwargs):
    import pdb;pdb.set_trace()
    pass

@receiver(post_save, sender=User)
def user_post_save(**kwargs):
    import pdb;pdb.set_trace()
    pass