#!/bin/env python
"""
"I'm in" environment control utility.
"""
from __future__ import unicode_literals
from ben10.execute import GetUnicodeArgv
from ben10.filesystem import CreateFile
from ben10.foundation.string import Dedent
from clikit.app import App
from shellmatic import LOGO, Shellmatic as _Shellmatic
import os


app = App('shellmatic', 'Automatic Shell.')


@app.Fixture
def Config():

    class _Config(object):

        @property
        def reset_filename(self):
            return os.path.join(os.path.dirname(__file__), 'reset.json')

        @property
        def batch_filename(self):
            return os.environ.get('SHELLMATIC_BATCH', '$TEMP/.shellmatic.bat')

        @property
        def user_filename(self):
            return '$APPDATA/.shellmatic.json'

        @property
        def project_filename(self):
            return '.eladrin.json'

    return _Config()


@app.Fixture
def Shellmatic():
    shellmatic = _Shellmatic()
    return shellmatic


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
        CreateFile(config_.batch_filename, batch_contents)


@app
def List(console_, shellmatic_, config_):
    """
    List current shellmatic configuration.
    """
    filename = shellmatic_.PathValue(config_.user_filename)

    if filename.IsFile():
        shellmatic_.LoadJson(filename.path)
    else:
        shellmatic_.LoadEnvironment()
        shellmatic_.SaveJson(filename.path)

    shellmatic_.PrintList(console_)


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
        CreateFile(config_.batch_filename, batch_contents)


@app
def Set(console_, shellmatic_, config_, name, value, test=False):
    """
    Sets an environment variable.

    :param name:
    :param value:
    """
    shellmatic_.EnvironmentSet(name, value)
    shellmatic_.PrintList(console_)

    batch_contents = shellmatic_.AsBatch(console_)
    if test:
        console_.Print(batch_contents, indent=1)
    else:
        CreateFile(config_.batch_filename, batch_contents)


@app(alias=('activate', 'wo'))
def Workon(console_, shellmatic_, config_, name, test=False):
    """
    Activate a project's virtualenv.

    The virtual environment must be placed on $PROJECTS_DIR/<name>/.venv

    :param name: The project name.
    """
    # Obtain the new project and venv directories
    new_project_dir = shellmatic_.PathValue('$PROJECTS_DIR/%(name)s' % locals())
    new_venv_home = shellmatic_.PathValue('%(new_project_dir)s/.venv' % locals())
    new_scripts_dir = shellmatic_.PathValue('%(new_venv_home)s/scripts' % locals())

    # Check if the new virtualenv really exists
    if not new_venv_home.IsDir():
        console_.Print('%s: Unable to find virtualenv.' % new_venv_home)
        return

    # Unload previous virtualenv (if any)
    old_name = os.environ.get('VIRTUALENV')
    if old_name and not old_name.startswith('('):
        old_venv_home = shellmatic_.PathValue('$PROJECTS_DIR/%(old_name)s/.venv' % locals())
        old_scripts_dir = shellmatic_.PathValue('%(old_venv_home)s/scripts' % locals())

        path = shellmatic_.PathListValue(os.environ['PATH'])
        path.Remove(old_scripts_dir)
        shellmatic_.EnvironmentSet('_environ:PATH', path)

    # Load new virtualenv
    shellmatic_.EnvironmentSet(name + ':PATH', new_scripts_dir.path)
    shellmatic_.EnvironmentSet(name + ':VIRTUALENV', name)
    shellmatic_.EnvironmentSet(name + ':PYTHONHOME', new_venv_home.path)
    console_.Print('%s: Activating virtualenv.' % new_venv_home)

    # Load environment configuration
    new_config_filename = new_project_dir.path + '/' + config_.project_filename
    if os.path.isfile(new_config_filename):
        shellmatic_.LoadJson(new_config_filename)
        console_.Print('%s: Loading configuration.' % new_config_filename)

    # Change directory to the project.
    #envout_.Call('cdd %(new_project_dir)s' % locals())

    # Generate the batch script
    batch_contents = shellmatic_.AsBatch(console_)
    if test:
        console_.Print(batch_contents, indent=1)
    else:
        CreateFile(config_.batch_filename, batch_contents)


if __name__ == '__main__':
    argv = GetUnicodeArgv()[1:]
    app.Main(argv)
