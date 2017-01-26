'''
destinyapi - Destiny API Wrapper for PYthon

This file provides Python objects which represent the API-returned item objects
'''

from .exc import DAPIError

class InventoryItem(object):
    _item_id = None
    _api_object = {}
    _attrs = {'name': 'itemName', 'is_equippable': 'equippable', 'class_type': 'classType',
              'description': 'itemDescription', 'item_type': 'itemTypeName', 'tier_type': 'tierTypeName'}

    def __init__(self, item_id, api_object={}):
        self.__item_id = item_id
        if api_object:
            self._api_object = api_object

    def get(self, name, default=None):
        if name not in self._attrs:
            return default
        attr_name = self._attrs[name]
        return self._api_object.get(attr_name, default)

    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        return '<InventoryItem(id=%s, name=%s)>' % (self.item_id, self.get('name', 'None'))

    def __str__(self):
        res = '%s (%s)' % (self.get('name', 'None'), self.get('description', 'N/A'))
        return res.encode('ascii', errors='ignore')

    item_id = property(fget=lambda self: self._item_id, doc='Item ID')
    api_object = property(fget=lambda self: self._api_object, doc='API Object')

__all__ = ['InventoryItem']
