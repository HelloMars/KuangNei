from kuangnei import consts
from kuangnei.utils import logger
from kuangnei.global_permission import GlobalPermission

from django.db.models.signals import post_syncdb
from django.contrib.auth import models as auth_models


def add_permissions(sender, **kwargs):
    GlobalPermission.objects.get_or_create(codename=consts.FORBIDDEN_AUTH, name=consts.FORBIDDEN_AUTH)

post_syncdb.connect(add_permissions, sender=auth_models)

logger.debug("Load main/__init__.py")
