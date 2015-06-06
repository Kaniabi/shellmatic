#!/bin/env python
"""
  ___________ __                ___         __
  \_   _____/|  |  _____     __| _/_______ |__|  ____
   |    __)_ |  |  \__  \   / __ | \_  __ \|  | /    \\
   |        \|  |__ / __ \_/ /_/ |  |  | \/|  ||   |  \\
  /_______  /|____/(____  /\____ |  |__|   |__||___|  /
          \/            \/      \/                  \/

"""
from __future__ import unicode_literals
from ben10.execute import GetUnicodeArgv
from ben10.filesystem import CreateFile
from clikit.app import App
from shellmatic import Shellmatic as _Shellmatic
import os



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
def Reset(console_, shellmatic_, config_, shared_dir=None, projects_dir=None):
    """
    Resets the environment to its default.
    """
    console_.Print(config_.reset_filename)
    shellmatic_.LoadJson(config_.reset_filename)
    batch_contents = shellmatic_.AsBatch()
    console_.Print(batch_contents, indent=1)
    #CreateFile(config_.environment_filename, batch_contents)


if __name__ == '__main__':
    argv = GetUnicodeArgv()[1:]
    app.Main(argv)
