#!/bin/env python
"""
Shellmatic

"""

from __future__ import unicode_literals
from ben10.execute import GetUnicodeArgv
from ben10.filesystem import CreateFile
from clikit.app import App
from shellmatic import Shellmatic as _Shellmatic
import os



LOGO = r"""
  ________ _           _    _                    _    _
 /   ____/| |_   ____ | |  | | _______  _____ __/ |_ |_| ____
 \____  \ |   \ /  _ \| |  | | \      \ \__  \\_  __\| |/  __\
 /       \| |  \\  __/| |__| |__| | |  \ / __ \_| |  | |\  \__
/________/|_|  / \___/|___/|___/|_|_|\_//____  /|_|  |_| \___/
             \/                              \/
"""


app = App('shellmatic', 'Automatic Shell.')


@app.Fixture
def Config():

    class _Config(object):

        @property
        def reset_filename(self):
            return os.path.join(os.path.dirname(__file__), 'reset.json')

        @property
        def environment_filename(self):
            return os.environ.get(
                'SHELLMATIC_BATCH',
                _Shellmatic.EnvVar._PathOut('$TEMP/.shellmatic.bat')
            )

    return _Config()


@app.Fixture
def Shellmatic():
    return _Shellmatic()


@app
def Reset(console_, shellmatic_, config_, shared_dir=None, projects_dir=None, test=False):
    """
    Resets the environment to its default (reset.json).
    """
    console_.Print(LOGO)
    console_.Print(config_.reset_filename)
    shellmatic_.LoadJson(config_.reset_filename)

    batch_contents = shellmatic_.AsBatch(console_)
    if test:
        console_.Print(batch_contents, indent=1)
    else:
        CreateFile(config_.environment_filename, batch_contents)


@app
def Load(console_, shellmatic_, config_, filename, test=False):
    """
    Loads a environment file in JSON format.
    """
    console_.Print(LOGO)
    shellmatic_.LoadJson(filename)

    batch_contents = shellmatic_.AsBatch(console_)
    if test:
        console_.Print(batch_contents, indent=1)
    else:
        CreateFile(config_.environment_filename, batch_contents)


if __name__ == '__main__':
    argv = GetUnicodeArgv()[1:]
    app.Main(argv)
