import types
import zipfile
import StringIO
import tempfile
from contextlib import closing
import os
import os.path
import requests

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
        if username:
            self._set_username(username)
        else:
            if load_data is not False:
                if isinstance(load_data, dict):
                    self._user_data = load_data
                elif isinstance(load_data, types.StringTypes) and os.path.exists(load_data):
                    self.load_user_data(load_data)
                else:
                    raise DAPIError('Unable to determine how to load the provided load_data')
            else:
                if os.path.exists(os.path.expanduser('~/.dapi.cfg')):
                    self.load_user_data(os.path.expanduser('~/.dapi.cfg'))
                elif api_key:
                    self.save_user_data(os.path.expanduser('~/.dapi.cfg'))

        self._headers = {'X-API-Key': api_key}


    def _validate_membership_id(self, membership_id, use_own=True):
        if membership_id is None:
            if not use_own:
                raise DAPIError('No membership_id was provided')

            if not self._user_data or ('membershipId' not in self._user_data):
                raise DAPIError('Own username was not specified or internal user data is missing')

            return self._user_data['membershipId']

        return membership_id

    def save_user_data(self, data_file, force_write=False):
        if os.path.exists(data_file):
            if not force_write:
                raise DAPIError('Existing user_data configuration in place at "%s"' % data_file)
            os.remove(data_file)

        with open(data_file, 'wb') as f:
            pickle.dump(self._user_data, f)

        return True

    def load_user_data(self, data_file, force_read=False):
        if not os.path.exists(data_file):
            if not force_read:
                return self._user_data

            raise DAPIError('Unable to read user_data from file "%s"' % data_file)

        with open(data_file, 'rb') as f:
            self._user_data = pickle.load(f)

        return self._user_data

    def _set_username(self, username, silent=True):
        if not username:
            return False
        try:
            usr = self.search(username=username)
            if not usr:
                if not silent:
                    raise DAPIError('Invalid or empty result when searching for "%s"' % username)
                return False
            usr['account'] = self.get_account(membership_id=usr['membershipId'])
            self._user_data = usr
            return True
        except Exception,ex:
            if not silent:
                raise ex
            return False

    def get_inventory(self, character_id, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return self._call('1/Account/%s/Character/%s/Inventory/Summary/' % (membership_id, character_id))

    def get_full_inventory(self, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)

        res = {}
        cids = map(lambda c: c['characterBase']['characterId'], self._user_data['account']['characters'])
        return dict.fromkeys(cids, [self.get_inventory(membership_id=membership_id, character_id=c) for c in cids])

    def get_inventory_item(self, item_id):
        membership_id = self._validate_membership_id(membership_id)
        res = self._call('Manifest/InventoryItem/%s' % item_id)

        if not res:
            return None
        return InventoryItem(res['requestedId'], res['inventoryItem'])

    def get_account(self, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return self._call('1/Account/%s/Summary/' % membership_id)

    def get_characters(self, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        acct = self.get_account(membership_id=membership_id)
        return acct['characters']

    def get_character(self, character_id, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return self._call('1/Account/%s/Character/%s' % (membership_id, character_id))

    def get_vault(self, membership_id=None):
        membership_id = self._validate_membership_id(membership_id)
        return False

    def search(self, username):
        return self._call('SearchDestinyPlayer/1/%s/' % username)

    def fetch_world_manifest(self, lang='en'):
        lang = lang.lower()
        manifests = self._call('Manifest')

        if 'mobileWorldContentPaths' not in manifests:
            raise DAPIError('Unable to find manifest world content')

        if lang not in manifests['mobileWorldContentPaths']:
            raise DAPIError('Unable to find world manifest for language "%s"' % lang)

        manifest_path = manifests['mobileWorldContentPaths'][lang]

        try:
            manifest_url = 'https://www.bungie.net%s' % manifests['mobileWorldContentPaths'][lang]
            tmp_path = tempfile.gettempdir()
            f_name = os.path.basename(manifest_path)
            dst_path = os.path.join(tmp_path, f_name)

            with closing(requests.get(manifest_url)) as req:
                manifest_zip = zipfile.ZipFile(StringIO.StringIO(req.content))
                manifest_zip.extractall(path=tmp_path)

            if not os.path.exists(dst_path):
                raise DAPIError('Unable to unzip manifest into %s (filename: "%s")' % (
                    tmp_path, f_name))

            return dst_path
        except zipfile.BadZipfile, ex:
            raise DAPIError('Manifest appears to be an invalid zip file: %s' % str(ex))
        except requests.RequestException, ex:
            raise DAPIError('Error fetching manifest from server: %s' % str(ex))

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

                if (len(res) == 1):
                    if isinstance(res, dict) and ('data' in res):
                        res = res['data']
                    elif isinstance(res, list):
                        res = res[0]

                return res
        except requests.exceptions.RequestsWarning,ex:
            raise DAPIError('Error in API request for "%s": "%s"' % (request_path, str(ex)), base_ex=ex)
