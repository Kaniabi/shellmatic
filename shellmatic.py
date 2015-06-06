from __future__ import unicode_literals
from ben10.filesystem import GetFileContents, NormalizePath, StandardizePath
from ben10.foundation.decorators import Comparable
from ben10.foundation.odict import odict
import os



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

    '''

    @Comparable
    class EnvVar(object):

        TEXT_NAMES = (
            'TERM',
            'PROMPT',
            'HOME',
            # Windows
            'COMPUTERNAME',
            'NUMBER_OF_PROCESSORS',
            'PROCESSOR_ARCHITECTURE',
            'PROCESSOR_IDENTIFIER',
            'PROCESSOR_LEVEL',
            'PROCESSOR_REVISION',
            'OS',
            'USERNAME',
            'USERDOMAIN',
            'PATHEXT',  # TCC?
            # Eladrin
            'VIRTUALENV',
        )

        PATHLIST_NAMES = (
            'PATH',
            'PYTHONPATH',
            'LD_LIBRARY_PATH'
        )

        DEFAULT_FLAGS = {
            'TERM' : {'text'},
            'PROMPT' : {'text'},
            'HOME' : {'text'},
            'PATH' : {'pathlist'},
            'PROMPT' : {'nodep'},
            # Linux
            'LD_LIBRARY_PATH' : {'pathlist'},
            # Windows
            'COMPUTERNAME' : {'text'},
            'NUMBER_OF_PROCESSORS' : {'text'},
            'PROCESSOR_ARCHITECTURE' : {'text'},
            'PROCESSOR_IDENTIFIER' : {'text'},
            'PROCESSOR_LEVEL' : {'text'},
            'PROCESSOR_REVISION' : {'text'},
            'OS' : {'text'},
            'USERNAME' : {'text'},
            'USERDOMAIN' : {'text'},
            'PATHEXT' : {'text'},  # Take Command only?
            # Eladrin
            'VIRTUALENV' : {'text'},
            # Python
            'PYTHONPATH' : {'pathlist'},
        }

        TYPE_TEXT = 'text'
        TYPE_PATH = 'path'
        TYPE_PATHLIST = 'pathlist'
        TYPES = (TYPE_TEXT, TYPE_PATH, TYPE_PATHLIST)

        def __init__(self, name, value):
            self.flags, self.name = self._SplitName(name)

            # Set a type as a flag IF any type were set.
            if not self.flags.intersection(set(self.TYPES)):
                self.flags.update(self._GetDefaultFlags(self.name, value))

            self.value = self._ValueIn(self.flags, value)


        def __repr__(self):
            flags = ':'.join(self.flags)
            name = self.name
            return '<EnvVar %(flags)s:%(name)s>' % locals()


        def AsBatch(self, append=False):
            '''
            Returns a line of BATCH script (windows) to set this in the environment.

            :param bool append:
                If True generate a script line that appends a value to the environment variable.
                If False generate a script that sets the value to the environment variable.
            :return unicode:
            '''
            name = self.name
            value = self._ValueOut(self.flags, self.value)
            if append:
                format = 'set %(name)s=%%%(name)s%%;%(value)s'
            else:
                format = 'set %(name)s=%(value)s'
            return format % locals()


        def _cmpkey(self):
            return self.name


        def GetDependencies(self):
            '''
            :return set(unicode):
            '''
            import re

            def MakeList(value):
                if isinstance(value, unicode):
                    return [value]
                return value

            dependencies = []

            if 'nodep' in self.flags:
                return dependencies

            for i in MakeList(self.value):
                dependencies += re.findall('\$(\w+)', i)
            return {i.upper() for i in dependencies}


        @classmethod
        def _ValueIn(cls, flags, value):
            '''
            Format INcomming value to store it properly.

            Most important format path and pathlist to a platform-independent format.
            '''
            if cls.TYPE_TEXT in flags:
                return value
            elif cls.TYPE_PATH in flags:
                return cls._PathIn(value)
            elif cls.TYPE_PATHLIST in flags:
                return cls._PathListIn(value)
            raise EnvVarTypeError(flags)


        @classmethod
        def _PathIn(cls, value):
            '''
            Format INcomming path value to a platform-indepdent format.

            :param unicode value:
                A path.

            :return unicode:
                A platform-independent path.
            '''
            return StandardizePath(os.path.normcase(value), strip=True)


        @classmethod
        def _PathListIn(cls, value):
            '''
            Format INcomming path-list value to a platform-indepdent format.

            :param unicode|list(unicode)|tuple(unicode) value:
                A path-list in a string or in a sequence.

            :return list(unicode):
                A list of platform-independent paths.
            '''
            result = []
            if not isinstance(value, (list,tuple)):
                value = value.split(os.pathsep)
            for i in map(cls._PathIn, value):
                # Remove empty values and avoid duplicate values
                if i and i not in result:
                    result.append(i)
            return result


        @classmethod
        def _ValueOut(cls, flags, value):
            '''
            Format OUTgoing value to export it properly.
            '''
            if cls.TYPE_TEXT in flags:
                return cls._TextOut(value)
            elif cls.TYPE_PATH in flags:
                return cls._PathOut(value)
            elif cls.TYPE_PATHLIST in flags:
                return cls._PathListOut(value)
            raise EnvVarTypeError(flags)


        @classmethod
        def _TextOut(cls, value):
            assert isinstance(value, unicode)
            return cls._ExpandEnvVars(value)


        @classmethod
        def _PathOut(cls, value):
            assert isinstance(value, unicode)
            result = os.path.normcase(value)
            result = cls._ExpandEnvVars(result)
            result = NormalizePath(result)
            return result


        @classmethod
        def _PathListOut(cls, value):
            assert isinstance(value, list)
            return os.pathsep.join(map(cls._PathOut, value))


        @classmethod
        def _ExpandEnvVars(cls, value):
            import re
            return re.sub('\$(\w+)', lambda x: '%' + x.group(1).upper() + '%', value)


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
            if os.pathsep in value:
                # Wild and dangerous guess.
                return {cls.TYPE_PATHLIST}
            return {cls.TYPE_PATH}


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


    def __init__(self):
        self.environment = odict()
        self.alias = odict()
        self.calls = odict()


    def LoadEnvironment(self, environ=None):
        '''
        Loads environment from the current environment.

        :param dict|None environ:
            An alternative to os.environ. Used for testing purposes.
        '''
        if environ is None:
            environ = os.environ
        for i_name, i_value in environ.iteritems():
            self.EnvironmentSet(i_name, i_value)


    def EnvironmentSet(self, name, value):
        self.environment[name] = self.EnvVar(name, value)


    def AsBatch(self):
        '''
        :return unicode:
        '''

        def TopologicalSort(source):
            '''

            Perform topo sort on elements.

            :param list(unicode, object, set(unicode)) source:
            :return list(object):
            '''
            pending = source[:]
            emitted = []
            while pending:
                next_pending = []
                next_emitted = []
                for entry in pending:
                    name, value, deps = entry
                    deps.difference_update(set((name,)), emitted) # <-- pop self from dep
                    if deps:
                        next_pending.append(entry)
                    else:
                        yield value
                        emitted.append(name) # <-- not required, but preserves original order
                        next_emitted.append(name)
                if not next_emitted:
                    raise ValueError("Cyclic dependency detected: %s %r" % (name, (next_pending,)))
                pending = next_pending
                emitted = next_emitted

        # Groups env-vars by name
        envvars_by_name = odict()
        for i_envvar in self.environment.itervalues():
            envvars_by_name.setdefault(i_envvar.name, []).append(i_envvar)

        source = []
        for i_name, i_envvars in sorted(envvars_by_name.iteritems()):
            dependencies = set()
            for j_envvar in i_envvars:
                for k_dependency in j_envvar.GetDependencies():
                    dependencies.add(k_dependency)
            source.append((i_name, i_envvars, dependencies))

        result = []
        seen = set()
        for i_envvars in TopologicalSort(source):
            for j_envvar in i_envvars:
                result.append(j_envvar.AsBatch(append=j_envvar.name in seen))
                seen.add(j_envvar.name)

        return '\n'.join(result)


    def LoadJson(self, filename):
        '''
        Loads the configuration from a JSON file.

        :param unicode filename:
        '''
        import json
        data = json.loads(GetFileContents(filename))

        for i_name, i_value in data.get('vars', {}).iteritems():
            self.EnvironmentSet(i_name, i_value)
