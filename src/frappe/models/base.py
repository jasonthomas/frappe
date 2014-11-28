#! -*- encoding: utf-8 -*-
"""
Models for the base of the recommendation system. The base of the recommendation system makes uses of the user, item
amd connection between them.
"""

from __future__ import division, absolute_import, print_function
import click
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from frappe.decorators import Cached

__author__ = "joaonrb"


class Item(models.Model):
    """
    Item to be used by recommending system
    """
    name = models.CharField(_("name"), max_length=255)
    external_id = models.CharField(_("external id"), max_length=255, unique=True)

    @staticmethod
    @Cached()
    def get_item(external_id):
        """
        Return item from external id.
        """
        return Item.objects.get(external_id=external_id)

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(self.name)

    @staticmethod
    def load_to_cache():
        items = Item.objects.all()
        for item in items:
            Item.get_item.update((item.external_id,), item)


class User(models.Model):
    """
    User to own items in recommendation system.
    """
    external_id = models.CharField(_("external id"), max_length=255, unique=True)
    items = models.ManyToManyField(Item, verbose_name=_("items"), blank=True, through="Inventory")

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.external_id

    def __unicode__(self):
        return unicode(self.external_id)

    @staticmethod
    @Cached()
    def get_user(external_id):
        """
        Get the user id from external id
        :param external_id: User external id
        :return: The User instance
        """
        return User.objects.get(external_id=external_id)

    @staticmethod
    @Cached()
    def get_user_items(user_id):
        """
        Get user items
        :param user_id: User id
        :return: A list of user items in inventory
        """
        return [entry.item_id for entry in Inventory.objects.filter(user_id=user_id)]

    @property
    def owned_items(self):
        """
        Get the owned items from cache. Key item id and value the inventory register
        """
        return {
            item_id: Item.get_item(item_id)
            for item_id in User.get_user_items(self.pk)
        }

    def has_more_than(self, n):
        """
        Check if user has more than n items owned
        """
        return len(self.owned_items) > n

    @staticmethod
    def load_to_cache():
        users = User.objects.all()
        for user in users:
            User.get_user.update((user.external_id,), user)


class Inventory(models.Model):
    """
    The connection between the user and the item. It has information about the user and the item such as acquisition
    date and eventually the date in which the item is dropped.
    """
    user = models.ForeignKey(User, verbose_name=_("user"), to_field="external_id")
    item = models.ForeignKey(Item, verbose_name=_("item"), to_field="external_id")

    class Meta:
        verbose_name = _("owned item")
        verbose_name_plural = _("owned items")

    def __str__(self):
        return _("%(item)s item for user %(user)s") % {"item": self.item_id, "user": self.user_id}

    def __unicode__(self):
        return _("%(item)s item for user %(user)s") % {"item": self.item_id, "user": self.user_id}

    @staticmethod
    def load_to_cache():
        inventory = Inventory.objects.all().order_by("user_id").values_list("user_id", "item_id")
        users = {}
        for user_id, item_id in inventory:
            if user_id in users:
                users[user_id].append(item_id)
            else:
                users[user_id] = [item_id]
        for user, items in users.items():
            User.get_user_items.update((user,), items)
