from __future__ import unicode_literals
from ben10.foundation.string import Dedent
from shellmatic import Shellmatic
import os



def testSplitName():
    assert Shellmatic.EnvVar._SplitName('PATH') == (set(), 'PATH')
    assert Shellmatic.EnvVar._SplitName('alpha:bravo:charlie:PATH') == ({'alpha','bravo','charlie'}, 'PATH')
    assert Shellmatic.EnvVar._SplitName('path:PATH') == ({'path'}, 'PATH')


def testLoadEnvironment():
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

    assert s.AsBatch() == Dedent(
        '''
        set ALPHA=Alpha
        set BRAVO=x:\\bravo\\directory\\folder
        set CHARLIE=x:\\charlie;c:\\windows;a:\\install
        '''
    )


def testReset():
    s = Shellmatic()
    filename = os.path.join(os.path.dirname(__file__), 'test.json')
    s.LoadJson(filename)
    assert s.AsBatch() == Dedent(
        '''
        set PROJECTS_DIR=x:
        set SHARED_DIR=d:\\shared
        set PYTHONHOME=%SHARED_DIR%\\python27
        set PATH=%PYTHONHOME%;%PYTHONHOME%\\scripts
        set PATH=%PATH%;%SHARED_DIR%\\jdk\\bin
        '''
    )


def testPathOut():
    assert Shellmatic.EnvVar._PathOut('x:/Alpha\\Bravo/CHARLIE') == 'x:\\alpha\\bravo\\charlie'
    assert Shellmatic.EnvVar._PathOut('$shared_dir/alpha') == '%SHARED_DIR%\\alpha'
    assert Shellmatic.EnvVar._PathOut('$python_home;$python_home/scripts') == '%PYTHON_HOME%;%PYTHON_HOME%\\scripts'
