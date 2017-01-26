'''
destinyapi - Destiny API Wrapper for Python

This file provides Python objects which represent the API-returned character object

'''

from datetime import datetime
from pandas import DataFrame

from .exc import DAPIError

class Character(object):
    '''Represents the Destiny API character object and provides associated functionality'''

    UNKNOWN_CLASS = None
    TITAN_CLASS = 0
    HUNTER_CLASS = 1
    WARLOCK_CLASS = 2

    _class_types = {UNKNOWN_CLASS: 'Unknown', TITAN_CLASS: 'titan', HUNTER_CLASS: 'hunter', WARLOCK_CLASS: 'warlock'}

    _obj_values = {}

    _membership_id = None
    _character_id = None
    _level = None
    _light_level = None
    _progress = None
    _pct_next = None
    _emblem_path = None
    _bg_path = None
    _is_prestige = None

    ##_obj_values = {'classType': 0, 'customization': {}, 'genderType': 0,
    ##               'dateLastPlayed': None, 'powerLevel': 0, 'customization': {}}

    _customization_labels = {'decalColor': 'Decal Color', 'decalIndex': 'Decal Index',
                    'eyeColor': 'Eye Color', 'wearHelmet': 'Wear Helmet'}

    _extra_labels = {'grimoireScore': 'Grimoire Score', 'lastCompletedStoryHash': 'Last Completed Story (Hash)',
                   'minutesPlayedThisSession': 'Minutes Played (This Session)', 'minutesPlayedTotal':
                   'Minutes Played (Total)', 'dateLastPlayed': 'Date Last Played'}

    def __init__(self, membership_id, character_id, level=None, light_level=None, progress=None, pct_next=None,
                 emblem_path=None, bg_path=None, is_prestige=None, **kwargs):
        self._membership_id = membership_id
        self._character_id = character_id
        self._level = level
        self._light_level = light_level
        self._progress = progress
        self._pct_next = pct_next
        self._emblem_path = emblem_path
        self._bg_path = bg_path
        self._is_prestige = is_prestige
        if 'characterBase' in kwargs:
            ext_args = kwargs.pop('characterBase')
            self._obj_values = kwargs.update(ext_args)
        else:
            self._obj_values = kwargs

    @classmethod
    def fetch(cls, dapi, membership_id, character_id=None, character_class=None):
        '''Fetches and builds a Character object based on provided membership ID and requested character class.

        Args:
            dapi (`DAPI` object): The Destiny API object
            membership_id (str): The membership ID for the requested Destiny user
            character_class (None or str): Optional argument specifying the character class to return. Must be
            either: 'titan', 'warlock' or 'hunter'

        Returns:
            `Character`: The representation of the requested character from the Destiny API
        '''
        try:
            if character_id:
                return Character.from_api(dapi.get_character(character_id=character_id, membership_id=membership_id))

            chars = {}
            for tmp_c in dapi.get_characters(membership_id=membership_id):
                c_type = tmp_c['characterBase']['classType']
                chars[c_type] = Character.from_api(tmp_c)

            if not character_class:
                return dict([(cls._class_types.get(k, 'unknown'), v) for k,v in chars.items()])

            class_name = [k for k,v in cls._class_types.items() if v == character_class.lower()]

            if not class_name:
                raise DAPIError('Invalid class type requested: %r' % character_class)
            else:
                return chars[class_name[0]]
        except DAPIError,ex:
            raise ex
        except Exception,ex:
            raise DAPIError('Unable to fetch character: "%s"' % str(ex))

    @classmethod
    def from_api(cls, api_obj):
        kwargs = {}
        if 'characterBase' in api_obj:
            kwargs = {'level': api_obj.get('characterLevel', None),
                      'progress': api_obj.get('levelProgression', None),
                      'pct_next': api_obj.get('percentToNextLevel', None),
                      'emblem_hash': api_obj.get('emblemHash', None),
                      'emblem_path': api_obj.get('emblemPath', None),
                      'bg_path': api_obj.get('backgroundPath', None),
                      'is_prestige': api_obj.get('isPrestigeLevel',None)}
            kwargs['light_level'] = api_obj['characterBase']['powerLevel']
            api_obj = api_obj['characterBase']

        if 'membershipId' not in api_obj:
            raise DAPIError('No "membershipId" field present in API object')

        if 'characterId' not in api_obj:
            raise DAPIError('No "characterId" field present in API object')

        m_id = api_obj.pop('membershipId')
        c_id = api_obj.pop('characterId')

        char = Character(membership_id=m_id, character_id=c_id, **kwargs)

        if 'customization' in api_obj:
            cust = api_obj.pop('customization')
            char._obj_values['customization'] = dict([(k, cust[k]) for k in char._customization_labels if k in cust])

        if 'stats' in api_obj:
            stats = api_obj.pop('stats')
            char._obj_values['stats'] = dict([(k.lower().split('_')[-1],stats[k]['value']) for k in stats])

        for k in api_obj:
            if k in char._extra_labels:
                char._obj_values[k] = api_obj[k]

        return char

    def get_last_played(self, as_string=False):
        last_date = self._obj_values.get('dateLastPlayed', None)
        if not last_date:
            return None

        try:
            dt = datetime.strptime(last_date, '%Y-%m-%dT%I:%M:%SZ')
            if not dt:
                return None

            if as_string:
                return dt.ctime()

            return dt
        except Exception,ex:
            return None

    def get_progress(self, as_string=False):
        if not self._progress:
            return None

        if as_string:
            res = ''

            lvl = self._progress.get('level', 0)
            if lvl < 40:
                res = 'Level %d of 40 (%.01f%% till next) -- ' % (lvl, self._progress.get('pct_next_level', 0))

            res = '%sCurrent Progress: %d [Daily: %.01f%% -- Weekly: %.01f%%]' % (res,
                self._progress.get('currentProgress', 0), self._progress.get('dailyProgress', 0),
                self._progress.get('weeklyProgress', 0))

            return res

        return self._progress

    def get_stats(self, as_string=False):
        if 'stats' not in self._obj_values:
            return None

        if not as_string:
            return self._obj_values['stats']

        tbl = []
        layout = [
            ['intellect', 'discipline', 'strength'],
            ['armor', 'recovery', 'agility'],
            ['optics', 'defense']
        ]

        for idx in xrange(0, 3):
            tbl.append(['%s -> %03d' % (name.title().ljust(3), self._obj_values['stats'][name])
                        for name in layout[idx]])
        if idx == 2:
            lrow = tbl.pop()
            tbl.append([lrow[0], '- '*8, lrow[1]])

        return DataFrame(tbl).to_string(index=False, header=False)

    level = property(fget=lambda self: self._level, doc='Base Character Level')
    light_level = property(fget=lambda self: self._light_level, doc='Light Level')
    pct_next_level = property(fget=lambda self: self._pct_next, doc='Percent to the next level')
    emblem_path = property(fget=lambda self: self._emblem_path, doc='Emblem Path')
    bg_path = property(fget=lambda self: self._bg_path, doc='Background Path')
    progress = property(fget=lambda self: self.get_progress(as_string=True), doc='Progress Stats')

    grimoire_score = property(fget=lambda self: self._obj_values.get('grimoireScore', None),
                              doc='Grimoire Score')
    min_played_session = property(fget=lambda self: self._obj_values.get('minutesPlayedThisSession', None),
                                  doc='Minutes Played (Session)')
    min_played_total = property(fget=lambda self: self._obj_values.get('minutesPlayedTotal', None),
                                doc='Minutes Played (Total)')
    last_played = property(fget=lambda self: self.get_last_played(as_string=True),
                           doc='Last Date and Time Played')
    class_type = property(fget=lambda self: self._class_types.get(self._obj_values.get('classType', None)).title(),
                          doc='Character Class')

    membership_id = property(fget=lambda self: self._membership_id, doc='Membership ID')
    character_id = property(fget=lambda self: self._character_id, doc='Character ID')

    def __str__(self):
        return '%s (Level %s) [ID: %s]' % (self.class_type, self.level, self.character_id)

__all__ = ['Character']
