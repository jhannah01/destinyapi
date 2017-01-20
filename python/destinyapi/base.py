import requests
import os
import os.path
import types
from contextlib import closing

try:
    import cPickle as pickle
except NameError:
    import pickle
    pass

from .exc import DAPIError

class DAPI(object):
    _base_url = 'https://www.bungie.net/platform/destiny/'
    _headers = {}
    _user_data = {}

    def __init__(self, api_key, username=None, load_data=False):
        self._headers = {'X-API-Key': api_key}

        if username:
            self.set_username(username)
        else:
            if load_data is not False:
                if isinstance(load_data, dict):
                    self._user_data = load_data
                elif isinstance(load_data, types.StringTypes) and os.path.exists(load_data):
                    self.load_user_data(load_data)
                else:
                    raise DAPIError('Unable to determine how to load the provided load_data')
            elif os.path.exists(os.path.expanduser('~/.dapi.cfg')):
                self.load_user_data(os.path.expanduser('~/.dapi.cfg'))

    def _validate_membership_id(self, membership_id):
        if membership_id is None:
            if not self._user_data.has_key('membershipId'):
                raise DAPIError('Own username was not specified')

            return self._user_data['membershipId']

        return membership_id

    def dump_user_data(self):
        if not self._user_data:
            return None

        res = self._user_data
        res['account'] = self.get_account(self._user_data['membershipId'])

        return res

    def save_user_data(self, data_file, force_write=False):
        if os.path.exists(data_file):
            if not force_write:
                raise DAPIError('Existing user_data configuration in place at "%s"' % data_file)
            os.remove(data_file)

        with open(data_file, 'wb') as f:
            pickle.dump(self._user_data, f)

        return True

    def load_user_data(self, data_file):
        if not os.path.exists(data_file):
            raise DAPIError('Unable to read user_data from file "%s"' % data_file)

        with open(data_file, 'rb') as f:
            self._user_data = pickle.load(f)

        return self._user_data

    def set_username(self, username):
        res = self.search(username)

        if len(res) != 1:
            return False

        res = res[0]

        res['account'] = self.get_account(res['membershipId'])
        self._user_data = res

    def get_inventory(self, character_id, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return self._call('1/Account/%s/Character/%s/Inventory/Summary/' % (membership_id, character_id))

    def get_full_inventory(self, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)

        res = {}
        cids = map(lambda c: c['characterBase']['characterId'], self._user_data['account']['characters'])
        return dict.fromkeys(cids, [self.get_inventory(membership_id=membership_id, character_id=c) for c in cids])

    def get_account(self, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return self._call('1/Account/%s/Summary/' % membership_id)

    def get_vault(self, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return False

    def search(self, username):
        return self._call('SearchDestinyPlayer/1/%s/' % username)

    def get_manifest(self, type_id, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return self._call('Manifest/%s/%s' % (type_id, membership_id))

    def get_all_items_summary(self, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return self._call('1/Account/%s/Items/' % membership_id)

    def _call(self, request_path, *args, **kwargs):
        if request_path.startswith('/'):
            request_path = request_path[1:]

        if not request_path.endswith('/'):
            request_path = '%s/' % request_path

        u = '%s/%s' % (self._base_url, request_path)

        try:
            with closing(requests.get(u, headers=self._headers)) as req:
                data = req.json()

                error_stat = data.get('ErrorStatus', 'UnknownError')
                if error_stat != 'Success':
                    raise DAPIError('Error calling "%s": "%s"' % (request_path, error_stat), results=req)

                res = data.get('Response', {})
                if not res:
                    return None

                if (len(res) == 1) and ('data' in res):
                    res = res['data']

                return res
        except requests.exceptions.RequestsWarning,ex:
            raise DAPIError('Error in API request for "%s": "%s"' % (request_path, str(ex)), base_ex=ex)
