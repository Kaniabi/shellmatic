from __future__ import unicode_literals
from ben10.filesystem import GetFileContents, NormalizePath, StandardizePath, CreateFile
from ben10.foundation.decorators import Comparable
from ben10.foundation.odict import odict
from ben10.foundation.reraise import Reraise
from ben10.foundation.types_ import CheckType
import ntpath
import os



LOGO = r"""
  ________ _           _    _                    _    _
 /   ____/| |_   ____ | |  | | _______  _____ __/ |_ |_| ____
 \____  \ |   \ /  _ \| |  | | \      \ \__  \\_  __\| |/  __\
 /       \| |  \\  __/| |__| |__| | |  \ / __ \_| |  | |\  \__
/________/|_|  / \___/|___/|___/|_|_|\_//____  /|_|  |_| \___/
             \/                              \/
"""





class EnvVarTypeError(TypeError):
    '''
    No variable type defined.
    The type for an environment variable (EnvVar) is set as a flag containing one of the constants
    EnvVar.TYPE_XXX.
    '''


#===================================================================================================
# ConfigFile
#===================================================================================================
class Shellmatic(object):
    '''
    Environment variables and aliases handling.
    '''

    class ValueType(object):
        pass

    @Comparable
    class TextValue(ValueType):

        TYPENAME = 'text'

        def __init__(self, text):
            self.__text = text.decode('ascii')
            CheckType(self.__text, unicode)

        def _cmpkey(self):
            '''
            Implements Comparable._cmpkey
            '''
            return self.__text

        def __unicode__(self):
            return self.__text

        def __repr__(self):
            return '<TextValue %s>' % self.__unicode__()

        def ExpandVars(self):
            self.__text = os.path.expandvars(self.__text)

        def AsList(self):
            return [self.__text]

        def AsBatch(self, expandvars=False, nodep=False):
            '''
            :param bool expandvars:
                If True expand environment variables references in the returning value.
                If False platformize environment variables references.
            '''
            if expandvars:
                result = os.path.expandvars(self.__text)
            elif nodep:
                result = self.__text
            else:
                result = self._EnvVarReferencesOut(self.__text)
            return result

        def IsDir(self):
            return os.path.isdir(os.path.expandvars(self.__path))

        @classmethod
        def _EnvVarReferencesOut(cls, value):
            import re
            return re.sub('\$(\w+)', lambda x: '%' + x.group(1).upper() + '%', value)


    @Comparable
    class PathValue(ValueType):

        TYPENAME = 'path'

        def __init__(self, path):
            self.__path = StandardizePath(path, strip=True)
            assert isinstance(self.__path, unicode)

        def _cmpkey(self):
            '''
            Implements Comparable._cmpkey
            '''
            return StandardizePath(ntpath.normcase(self.__path))

        def __unicode__(self):
            return self.__path

        def __repr__(self):
            return '<PathValue %s>' % self.__unicode__()

        @property
        def path(self):
            return os.path.expandvars(self.__path)

        def ExpandVars(self):
            self.__path = os.path.expandvars(self.__path)

        def AsList(self):
            return [self.__path.lower()]

        def AsBatch(self, expandvars=False, nodep=False):
            '''
            :param bool expandvars:
                If True expand environment variables references in the returning value.
                If False platformize environment variables references.
            '''
            if expandvars:
                result = os.path.expandvars(self.__path)
            elif nodep:
                result = ntpath.normpath(self.__path)
            else:
                result = ntpath.normpath(self.__path)
                result = ntpath.normcase(result)
                result = self._PlatformizeEnvVarsReferences(result)
            return result

        def IsDir(self):
            return os.path.isdir(self.path)

        def IsFile(self):
            return os.path.isfile(self.path)

        def CreateFile(self, contents, encoding=None):
            return CreateFile(self.path, contents, encoding=encoding)

        @classmethod
        def _PlatformizeEnvVarsReferences(cls, value):
            import re
            return re.sub('\$(\w+)', lambda x: '%' + x.group(1).upper() + '%', value)


    @Comparable
    class PathListValue(ValueType):

        TYPENAME = 'pathlist'

        def __init__(self, value):
            self.__pathlist = []
            if not isinstance(value, (list, tuple)):
                value = value.split(ntpath.pathsep)
            for i in value:
                # Remove empty values and avoid duplicate values
                if not i:
                    continue
                path = Shellmatic.PathValue(i)
                if path in self.__pathlist:
                    continue
                self.__pathlist.append(path)

        def _cmpkey(self):
            '''
            Implements Comparable._cmpkey
            '''
            return [i._cmpkey() for i in self.__pathlist]

        def __unicode__(self):
            return '\n'.join(map(unicode, self.__pathlist))

        def __repr__(self):
            return '<PathListValue %s>' % self.__unicode__()

        def ExpandVars(self):
            for i in self.pathlist:
                i.ExpandVars()

        def AsList(self):
            result = []
            for i in self.__pathlist:
                result += i.AsList()
            return result

        def AsBatch(self, expandvars=False, nodep=False):
            '''
            :param bool expandvars:
                If True expand environment variables references in the returning value.
                If False platformize environment variables references.
            '''
            result = [i.AsBatch(expandvars=expandvars, nodep=nodep) for i in self.__pathlist]
            return ntpath.pathsep.join(result)

        def Remove(self, value):
            if isinstance(value, unicode):
                value = Shellmatic.PathValue(value)
            CheckType(value, Shellmatic.PathValue)

            new_pathlist = self.__pathlist[:]
            try:
                new_pathlist.remove(value)
            except ValueError as e:
                pathlist_items = '\n  - '.join(map(unicode,new_pathlist))
                Reraise(
                    e,
                    'While trying to remove value "%s" from path-list:\n  - %s' % (
                        value,
                        pathlist_items
                    )
                )
            self.__pathlist = new_pathlist



    @Comparable
    class EnvVar(object):
        '''
        Represents an environment variable, with special handling of flags for TYPES (text, path,
        pathlist) and processing details (nodep).
        '''

        FLAG_NODEP = 'nodep'

        TYPE_TEXT = 'text'
        TYPE_PATH = 'path'
        TYPE_PATHLIST = 'pathlist'
        TYPES = (TYPE_TEXT, TYPE_PATH, TYPE_PATHLIST)

        DEFAULT_FLAGS = {
            'TERM' : {TYPE_TEXT},
            'PROMPT' : {TYPE_TEXT, FLAG_NODEP},
            'HOME' : {TYPE_TEXT},
            'PATH' : {TYPE_PATHLIST},
            # Linux
            'LD_LIBRARY_PATH' : {TYPE_PATHLIST},
            # Windows
            'COMPUTERNAME' : {TYPE_TEXT},
            'NUMBER_OF_PROCESSORS' : {TYPE_TEXT},
            'PROCESSOR_ARCHITECTURE' : {TYPE_TEXT},
            'PROCESSOR_IDENTIFIER' : {TYPE_TEXT},
            'PROCESSOR_LEVEL' : {TYPE_TEXT},
            'PROCESSOR_REVISION' : {TYPE_TEXT},
            'OS' : {TYPE_TEXT},
            'USERNAME' : {TYPE_TEXT},
            'USERDOMAIN' : {TYPE_TEXT},
            'PATHEXT' : {TYPE_TEXT},  # Take Command only?
            # Eladrin
            'VIRTUALENV' : {TYPE_TEXT},
            # Python
            'PYTHONPATH' : {TYPE_PATHLIST},
        }

        def __init__(self, name, value):
            self.flags, self.name = self._SplitName(name)

            # Set a type as a flag IF any type were set.
            if not self.flags.intersection(set(self.TYPES)):
                new_flags = self._GetDefaultFlags(self.name, value)
                self.flags.update(new_flags)

            self.value = self._ValueIn(self.flags, self.name, value)


        @classmethod
        def _GetDefaultFlags(cls, name, value):
            '''
            Returns default flags for the given variable name and value.

            :param unicode name:
            :param unicode value:
            :return set(unicode):
            '''
            result = cls.DEFAULT_FLAGS.get(name)
            if result is not None:
                return result
            if ntpath.pathsep in value:
                # Wild and dangerous guess. Let's see how thi behaves.
                return {cls.TYPE_PATHLIST}
            return {cls.TYPE_PATH}


        def __repr__(self):
            flags = ':'.join(sorted(self.flags))
            name = self.name
            return '<EnvVar %(flags)s:%(name)s>' % locals()


        @property
        def fullname(self):
            parts = list(sorted(self.flags))
            parts.append(self.name)
            return ':'.join(parts)


        def AsBatch(self, append=False):
            '''
            Returns a line of BATCH script (windows) to set this in the environment.

            :param bool append:
                If True generate a script line that appends a value to the environment variable.
                If False generate a script that sets the value to the environment variable.
            :return unicode:
            '''
            name = self.name
            value = self.value.AsBatch(nodep=self.FLAG_NODEP in self.flags)
            if append:
                format = 'set %(name)s=%%%(name)s%%;%(value)s'
            else:
                format = 'set %(name)s=%(value)s'
            return format % locals()


        def _cmpkey(self):
            '''
            Implements Comparable._cmpkey
            '''
            return self.name


        def GetDependencies(self):
            '''
            :return set(unicode):
            '''
            import re

            dependencies = []

            if self.FLAG_NODEP in self.flags:
                return set()

            for i in self.value.AsList():
                dependencies += re.findall('\$(\w+)', i)
            return {i.upper() for i in dependencies}


        @classmethod
        def _ValueIn(cls, flags, name, value):
            '''
            Format INcomming value to store it properly.

            Most important format path and pathlist to a platform-independent format.
            '''
            if isinstance(value, Shellmatic.ValueType):
                return value
            if cls.TYPE_TEXT in flags:
                return Shellmatic.TextValue(value)
            elif cls.TYPE_PATH in flags:
                return Shellmatic.PathValue(value)
            elif cls.TYPE_PATHLIST in flags:
                return Shellmatic.PathListValue(value)
            raise EnvVarTypeError('Variable %(name)s have no type defined on flags (%(flags)s).' % locals())


        @classmethod
        def _SplitName(cls, name):
            '''
            Splits an name into flags and name.

            :param uncode name:
                A name containing flags. Eg.: flag:flag2:name
            '''
            if isinstance(name, str):
                name = name.decode('UTF-8')
            assert isinstance(name, unicode)
            flags = set()
            if ':' in name:
                name_parts = name.split(':')
                name = name_parts[-1]
                for i in name_parts[:-1]:
                    flags.add(i)
            return flags, name

    SECTION_ENVIRONMENT = 'environment'
    ENVIRONMENT_FILENAME = '.shellmatic.json'

    def __init__(self):
        self.environment = odict()
        self.alias = odict()
        self.calls = odict()


    def LoadEnvironment(self, environ=os.environ):
        '''
        Loads environment from the current environment.

        :param dict|None environ:
            An alternative to os.environ. Used for testing purposes.
        '''
        for i_name, i_value in environ.iteritems():
            self.EnvironmentSet('_environ:' + i_name, i_value)


    def EnvironmentSet(self, name, value):
        self.environment[name] = self.EnvVar(name, value)


    def AsBatch(self, console_, append=False):
        '''
        :param clikit.Console console_:
        :return unicode:
        '''

        def TopologicalSort(source):
            '''
            :param list(unicode, set(unicode)) source:
            :return list(object):
            '''
            defined = {i[0] for i in source}
            pending = source[:]
            emitted = []
            while pending:
                next_pending = []
                next_emitted = []
                for entry in pending:
                    name, deps = entry
                    deps.difference_update(set((name,)), emitted) # <-- pop self from dep
                    if deps & defined:  # <-- consider a cycle only between defined variables
                        next_pending.append(entry)
                    else:
                        yield name
                        emitted.append(name) # <-- not required, but preserves original order
                        next_emitted.append(name)
                if not next_emitted:
                    dep = ','.join(next_pending[0][-1])
                    raise ValueError('Cyclic dependency detected: %(dep)s (dependency of %(name)s).' % locals())
                pending = next_pending
                emitted = next_emitted

        # Groups env-vars by name
        sources = {}
        envvars = {}
        for i_envvar in self.environment.itervalues():
            sources.setdefault(i_envvar.name, set()).update(i_envvar.GetDependencies())
            envvars.setdefault(i_envvar.name, []).append(i_envvar)

        result = []
        seen = set()
        for i_name in TopologicalSort(sorted(sources.items())):
            for j_envvar in envvars[i_name]:
                do_append = append and self.EnvVar.TYPE_PATHLIST in j_envvar.flags
                do_append = do_append or j_envvar.name in seen
                result.append(j_envvar.AsBatch(append=do_append))
                seen.add(j_envvar.name)

        return '\n'.join(result)


    def LoadJson(self, filename, flags=()):
        '''
        Loads the configuration from a JSON file.

        :param unicode filename:
        '''
        import json

        data = json.loads(GetFileContents(filename, encoding='UTF-8'))
        for i_name, i_value in data.get(self.SECTION_ENVIRONMENT, {}).iteritems():
            name = ':'.join(sorted(flags) + [i_name])
            self.EnvironmentSet(name, i_value)


    def SaveJson(self, filename, flags=()):
        '''
        Saves the configuration in a JSON file.

        :param unicode filename:
        '''
        import json

        environment = {
            i : v.value.AsList()
            for (i,v) in
            self.environment.iteritems()
        }
        data = {
            'environment' : environment,
        }
        contents = json.dumps(
            data,
            sort_keys=True,
            indent=4,
            separators=(',', ': '),
            ensure_ascii=False
        ).decode('UTF-8')
        CreateFile(filename, contents, encoding='UTF-8')


    def Workon(self, console_, name):
        """
        Activate a project's virtualenv.

        The virtual environment must be placed on $PROJECTS_DIR/<name>/.venv

        :param name: The project name.
        """
        # Obtain the new project and venv directories
        new_project_dir = self.PathValue('$PROJECTS_DIR/%(name)s' % locals())
        new_venv_home = self.PathValue('%(new_project_dir)s/.venv' % locals())
        new_scripts_dir = self.PathValue('%(new_venv_home)s/scripts' % locals())

        # Check if the new virtualenv really exists
        if not new_venv_home.IsDir():
            console_.Print('%s: Unable to find virtualenv.' % new_venv_home.path)
            return

        # Unload previous virtualenv (if any)
        old_name = os.environ.get('VIRTUALENV')
        if old_name and not old_name.startswith('('):
            old_venv_home = self.PathValue('$PROJECTS_DIR/%(old_name)s/.venv' % locals())
            old_scripts_dir = self.PathValue('%(old_venv_home)s/scripts' % locals())

            path = self.PathListValue(os.environ['PATH'])
            path.Remove(old_scripts_dir)
            self.EnvironmentSet('_environ:PATH', path)

        # Load new virtualenv
        self.EnvironmentSet(name + ':venv:PATH', new_scripts_dir.path)
        self.EnvironmentSet(name + ':venv:VIRTUALENV', name)
        self.EnvironmentSet(name + ':venv:PYTHONHOME', new_venv_home.path)
        console_.Print('%s: Activating virtualenv.' % new_venv_home.path)

        # Load environment configuration
        new_config_filename = new_project_dir.path + '/' + self.ENVIRONMENT_FILENAME
        if os.path.isfile(new_config_filename):
            self.LoadJson(new_config_filename, flags=(name,))
            console_.Print('%s: Loading configuration.' % new_config_filename)

        # Change directory to the project.
        #envout_.Call('cdd %(new_project_dir)s' % locals())


    def PrintList(self, console_, logo=True):
        if logo:
            console_.Print(LOGO)

        by_flags = {}
        for i_name, i_envvar in sorted(self.environment.iteritems()):
            flags = ':'.join(sorted(i_envvar.flags))
            by_flags.setdefault(flags, []).append(i_envvar)

        for i_flags, i_envvars in sorted(by_flags.iteritems()):
            console_.Print('<green>%s</>' % i_flags)
            for j_envvar in i_envvars:
                console_.Item('<white>%s</>: %s' % (j_envvar.name, j_envvar.value), indent=1)
