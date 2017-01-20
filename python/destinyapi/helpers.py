'''
destinyapi - Destiny API Wrapper for Python

This file provides helper functions for working with the API and it's
objects

'''

from pandas import DataFrame

def print_character_stats(character, silent=False):
    '''Prints a table describing the provided `Character` object (or dict)
    and returns a dict describing the stats as well as a textual representation
    of the same

    Args:
        character (`Character` object or `dict`): The character object to use
        silent (boolean): Determines if output should be printed. (default is
        False)

    Returns:
        dict: Describes all of the extracted stats and includes a textual
        representation as well.
    '''
    bchar = character['characterBase']
    stats = bchar['stats']
    out_stats = {}
    tbl = []
    layout = [
        ['intellect', 'discipline', 'strength'],
        ['armor', 'recovery', 'agility'],
        ['optics', 'defense']
    ]

    for k in stats:
        name = k.lower().split('_')[-1]
        out_stats[name] = stats[k]['value']

    out_stats['text'] = 'Character %d [Light: %d] Stats:' % (bchar['classType'],
                                                             out_stats['light'])

    for idx in xrange(0, 3):
        tbl.append(['%s -> %03d' % (name.title().ljust(3), out_stats[name])
                    for name in layout[idx]])

        if idx == 2:
            lrow = tbl.pop()
            tbl.append([lrow[0], '- '*8, lrow[1]])

        out_stats['text'] = '%s\n%s' % (
            out_stats['text'],
            DataFrame(tbl).to_string(index=False, header=False)
        )

    if not silent:
        print out_stats['text']
        print '---------------'

    return out_stats

__all__ = ['print_character_stats']
