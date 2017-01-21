#!/usr/bin/env python2.7

import types
import argparse
import requests
import sys, os, os.path
from contextlib import closing

from destinyapi import DAPI, DAPIError, Character
from destinyapi.helpers import print_character_stats, get_characters_from_username

from apicfg import API_KEY

try:
    import cPickle as pickle
except NameError:
    import pickel

from IPython.terminal.prompts import Prompts, Token
from IPython.terminal.ipapp import load_default_config
from traitlets.config.loader import Config

_banner = '''Welcome to the "destinyapi" IPython shell

Start with using the "dapi" object...
'''

class DAPIPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Prompt, '[dapi] <'),
            (Token.PromptNum, str(self.shell.execution_count)),
            (Token.Prompt, '>: '),
        ]

    def out_prompt_tokens(self):
        return [
            (Token.OutPrompt, '[dapi] Out<'),
            (Token.OutPromptNum, str(self.shell.execution_count)),
            (Token.OutPrompt, '>: '),
        ]

def main():
    try:
        get_ipython
    except NameError:
        nested = 0
        cfg = load_default_config()
        cfg.TerminalInteractiveShell.prompts_class=DAPIPrompt
    else:
        print 'Running nested copies of IPython. Augmenting configuration...'
        cfg = load_default_config()
        nested = 1

    from IPython.terminal.embed import InteractiveShellEmbed

    cfg.TerminalInteractiveShell.confirm_exit = False
    cfg.TerminalInteractiveShell.debug = True

    ipshell = InteractiveShellEmbed(config=cfg, banner1=_banner)

    # Setup environment
    dapi = DAPI(API_KEY)

    if os.path.exists(os.path.expanduser('~/.dapi.cfg')):
        dapi.load_user_data(os.path.expanduser('~/.dapi.cfg'))

    ipshell()

    # Cleanup environment
if __name__ == '__main__':
    main()
