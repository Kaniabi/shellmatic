from __future__ import unicode_literals
from ben10.foundation.string import Dedent
from ben10.foundation.types_ import Null
from shellmatic import Shellmatic
import os
import pytest



def testEnvVarSplitName():
    assert Shellmatic.EnvVar._SplitName('PATH') == (set(), 'PATH')
    assert Shellmatic.EnvVar._SplitName('alpha:bravo:charlie:PATH') == ({'alpha','bravo','charlie'}, 'PATH')
    assert Shellmatic.EnvVar._SplitName('path:PATH') == ({'path'}, 'PATH')


def testEnvVarRepr():
    assert repr(Shellmatic.EnvVar('PATH', '/usr/bin')) == '<EnvVar pathlist:PATH>'
    assert repr(Shellmatic.EnvVar('windows:pathlist:PATH', 'c:/windows/system32')) == '<EnvVar pathlist:windows:PATH>'


def testEnvVarCompare():
    a = Shellmatic.EnvVar('ALPHA', '')
    b = Shellmatic.EnvVar('BRAVO', '')
    assert a < b

    c = Shellmatic.EnvVar('ALPHA', '')
    assert a == c

    d = Shellmatic.EnvVar('path:windows:ALPHA', '')
    assert a == d


def testEnvVarGetDependencies():
    a = Shellmatic.EnvVar('ALPHA', '$ALPHA/bravo/$CHARLIE')
    assert a.GetDependencies() == {'ALPHA', 'CHARLIE'}

    a = Shellmatic.EnvVar('nodep:ALPHA', '$ALPHA/bravo/$CHARLIE')
    assert a.GetDependencies() == set()


def testEnvVarAsBatch():
    # Default type "path" will handle both slashes and environment variables expansions.
    a = Shellmatic.EnvVar('ALPHA', '$ALPHA/bravo/$CHARLIE')
    assert a.AsBatch() == 'set ALPHA=%ALPHA%\\bravo\\%CHARLIE%'

    # Type "text" won't handle slashes ('/' -> '\')
    a = Shellmatic.EnvVar('text:ALPHA', '$ALPHA/bravo/$CHARLIE')
    assert a.AsBatch() == 'set ALPHA=%ALPHA%/bravo/%CHARLIE%'

    # Flag "nodep" won't handle environment variables expansion ('$X' -> '%X%')
    a = Shellmatic.EnvVar('text:nodep:ALPHA', '$ALPHA/bravo/$CHARLIE')
    assert a.AsBatch() == 'set ALPHA=$ALPHA/bravo/$CHARLIE'


def testLoadEnvironment(monkeypatch):
    s = Shellmatic()

    environ = {
        'PATH' : r'X:\BEN10\source\python;;x:\eladrin\Bin;x:\tiefling10/source/python',
        'PATHLIST' : 'x:/ALPHA;c:\Windows',
        b'BYTES' : b'alpha',
    }

    s.LoadEnvironment(environ)

    obtained = sorted([(i.name, i.flags, i.value) for i in s.environment.itervalues()])
    expected = [
        (
            'BYTES',
            {'path'},
            'alpha'
        ),
        (
            'PATH',
            {'pathlist'},
            [
                'x:/ben10/source/python',
                'x:/eladrin/bin',
                'x:/tiefling10/source/python',
            ]
        ),
        (
            'PATHLIST',
            {'pathlist'},
            [
                'x:/alpha',
                'c:/windows',
            ]
        ),
    ]
    assert obtained == expected


def testEnvironmentSet():
    s = Shellmatic()

    s.EnvironmentSet('text:ALPHA', 'Alpha')
    obtained = sorted([(i.name, i.flags, i.value) for i in s.environment.itervalues()])
    expected = [
        (
            'ALPHA',
            {'text'},
            'Alpha'
        ),
    ]
    assert obtained == expected

    s.EnvironmentSet('path:BRAVO', r'x:/Bravo\directory/FOLDER')
    obtained = sorted([(i.name, i.flags, i.value) for i in s.environment.itervalues()])
    expected += [
        (
            'BRAVO',
            {'path'},
            'x:/bravo/directory/folder'
        ),
    ]
    assert obtained == expected

    s.EnvironmentSet('pathlist:CHARLIE', r'x:/Charlie;c:\Windows;a:\Install')
    obtained = sorted([(i.name, i.flags, i.value) for i in s.environment.itervalues()])
    expected += [
        (
            'CHARLIE',
            {'pathlist'},
            [
                'x:/charlie',
                'c:/windows',
                'a:/install'
            ]
        ),
    ]
    assert obtained == expected

    assert s.AsBatch(Null()) == Dedent(
        '''
        set ALPHA=Alpha
        set BRAVO=x:\\bravo\\directory\\folder
        set CHARLIE=x:\\charlie;c:\\windows;a:\\install
        '''
    )


def testAsBatch():
    s = Shellmatic()
    s.EnvironmentSet('ALPHA', '$ZULU')
    assert s.AsBatch(Null()) == 'set ALPHA=%ZULU%'

    s.EnvironmentSet('ZULU', '$ALPHA')
    with pytest.raises(ValueError):
        s.AsBatch(Null())


def testReset():
    s = Shellmatic()
    filename = os.path.join(os.path.dirname(__file__), 'test.json')
    s.LoadJson(filename)
    obtained = s.AsBatch(Null())
    expected = Dedent(
        '''
        set PROJECTS_DIR=x:
        set SHARED_DIR=d:\\shared
        set PYTHONHOME=%SHARED_DIR%\\python27
        set PATH=%PYTHONHOME%;%PYTHONHOME%\\scripts
        set PATH=%PATH%;%SHARED_DIR%\\jdk\\bin
        '''
    )
    assert obtained == expected


def testPathOut():
    assert Shellmatic.EnvVar._PathOut('x:/Alpha\\Bravo/CHARLIE') == 'x:\\alpha\\bravo\\charlie'
    assert Shellmatic.EnvVar._PathOut('$shared_dir/alpha') == '%SHARED_DIR%\\alpha'
    assert Shellmatic.EnvVar._PathOut('$python_home;$python_home/scripts') == '%PYTHON_HOME%;%PYTHON_HOME%\\scripts'
