#!/bin/env python
from __future__ import unicode_literals
from ben10.foundation.string import Indent
from clikit.app import App
import sys
import six


BRANCH_MASTER = 'master'


app = App('br', 'Git repository branches manager.')


class CmdError(RuntimeError):

    def __init__(self, cmd, cwd, out_lines):
        RuntimeError.__init__(self, 'Error output generated while executing: %s' % cmd)
        self.cmd = cmd
        self.cwd = cwd
        self.out_lines = out_lines


def ExecuteCmd(cmd, cwd, split=False, verbose=False, condition=True, redirect_output=True):
    '''
    Executes the given command in the given cwd.

    Returns a formatted output controller by the arguments.

    :param unicode cmd:
        The command to execute.

    :param unicode cwd:
        The directory to perform the execution.

    :param bool split:
        If true, returns a list instead of a text, spliting

    :param bool verbose:
        If true, added the executed command to the resulting lines.

    :param bool condition:
        If True, executes normally, otherwise skips the execution (and mark it as skipped in the
        resulting text).

    :return unicode|list(unicode):
        Returns the output of the command as a text.
        If split==True, returns as a list
        If verbose==True, also returns the executed command.

    TODO: BOSMAN-197: Replace or use Execute on "br" command.
    '''
    import shlex
    import subprocess

    result = ''

    if verbose:
        result += '<yellow>%s</>\n' % cmd

    if condition:
        if redirect_output:
            stdout = subprocess.PIPE
        else:
            stdout = None

        popen = subprocess.Popen(
            shlex.split(cmd),
            cwd=cwd,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            bufsize=1,
            shell=False,
        )
        if stdout == subprocess.PIPE:
            output, _ = popen.communicate()
            output = output.decode('ascii')
        else:
            output = u''
            popen.wait()

        if popen.returncode != 0:
            raise RuntimeError('retcode=%d\n%s' % (popen.returncode, output))

        if verbose:
            output = Indent(output)

        result += output
    else:
        result += '<white>skipped</>\n'

    if split:
        result = result.splitlines()

    return result


def GetCurrentBranch(repo):
    '''
    Returns the repository current branch.

    :param unicode repo:
        A local git working directory.
    '''
    result = GetLocalBranches(repo)
    if len(result) == 0:
        return None
    return result[0]


def BranchAndStatus(repo):
    '''
    Returns the repository branch and status.

    :param unicode repo:
        A local git working directory.

    :return 2-tuple:
        [0]: Current branch.
        [1]: Status lines.
    '''
    result = ExecuteCmd('git status -b -s', cwd=repo, split=True)
    return result[0], result[1:]


def GetLocalBranches(repo):
    '''
    Returns a list of local branches for the given repository.

    :param unicode repo:
        A local git working directory.
    '''
    r_current = None
    r_branches = []
    for i_branch in ExecuteCmd('git branch', cwd=repo, split=True):
        branch = i_branch.strip('* ')
        if '*' in i_branch:
            r_current = branch
        elif branch:
            r_branches.append(branch)
    return [r_current] + sorted(r_branches)


def GetRemotes(repo):
    '''
    Returns a list of remotes.

    :param unicode repo:
        A local git working directory.

    '''
    return ExecuteCmd('git remote', repo).splitlines()


def GetRemoteBranches(repo, remote='origin'):
    '''
    Returns a list of remote branches for the given repository.

    :param unicode repo:
        A local git working directory.

    :param unicode remote:
        Remote name used to list branches.

    :return list(unicode):
        List of remote branches in the given `remote`. Branches do not include remote name, i.e.:
            ['master', 'branch'] instead of ['origin/master', 'origin/branch']
    '''
    remote_branches = ExecuteCmd('git branch -r', repo).splitlines()

    # Strip spaces
    remote_branches = [b.strip() for b in remote_branches]

    # Remove HEAD -> pointer
    remote_branches = [b for b in remote_branches if '->' not in b]

    # Remove branches in other remotes
    remote_branches = [b for b in remote_branches if b.startswith(remote + '/')]

    # Remove remote name from branches
    remote_branches = [b.replace(remote + '/', '') for b in remote_branches]

    return remote_branches


def GetMergedBranches(repo, remote='origin', branch='master'):
    '''
    :param unicode repo:
        A local git working directory.

    :param unicode remote:
        Name of the remote we are comparing against, looking for merged branches.

    :param unicode branch:
        Name of the remote branch we are comparing against, looking for merged branches.

    :return list(unicode):
        A list of all local branches that are already fully merged to `remote`/`branch` (branches
        that do not have any commit that doesn't already exist there)
    '''
    # Find all branches that are already merged with remote master
    merged_branches = ExecuteCmd('git branch --merged ' + remote + '/master', repo).splitlines()

    # Never delete the current branch
    merged_branches = [b.strip() for b in merged_branches if '*' not in b]

    # Never delete branches that still exist in the remote
    remote_branches = GetRemoteBranches(repo, remote)
    merged_branches = [b for b in merged_branches if b not in remote_branches]

    return merged_branches


def FindBranch(repos, branch, remote=False, ignore=None):
    '''
    Finds a matching branch looking for branch names in all repositories.

    Find either a exact match (preferable) or a similar match (using 'in' operator).

    :param list(unicode) repos:
        List of repositories

    :param unicode branch:
        The branch name or part of the name.

    :param bool remote:
        If True, also searches remote branches.

    :param unicode ignore:
        Ignore branches that contain this string when looking for switch matches.

    :return 2-tuple(unicode, list(unicode)):
        Returns the branch name and a list of repositories that have that branch.
    '''
    # Maps all found branches to their respective repositories.
    branch_to_repo = {}
    for i_repo in repos:
        branches = set(GetLocalBranches(i_repo))

        if remote:
            branches = branches.union(GetRemoteBranches(i_repo))

        for j_branch in branches:
            if j_branch is None:
                continue
            if ignore and ignore in j_branch:
                continue
            branch_to_repo.setdefault(j_branch, []).append(i_repo)

    if branch not in branch_to_repo:
        # If we can't find a exact branch name match, we must perform a "similar" search.
        # Only one branch name on all repositories must match.
        match_branches = {i for i in branch_to_repo.keys() if branch in i}
        if len(match_branches) == 0:
            raise RuntimeError("Can't find a branch matching '%s'." % branch)
        if len(match_branches) > 1:
            raise RuntimeError(
                "Found multiple matches for '%s':\n\t%s" % \
                (branch, '\n\t'.join(sorted(match_branches)))
            )
        branch = match_branches.pop()

    return branch, branch_to_repo[branch]


def CommitDiff(repo, branch1, branch2):
    '''
    Obtain the commit diff between branch1 and branch2 (and the other way arround).

    :param unicode repo:
        A local git working directory.

    :param unicode branch1:
        A valid branch name on repo.

    :param unicode branch2:
        A valid branch name on repo.

    :return unicode:
        Returns a string with the list of different commits between branch1 and branch2.
    '''
    result = ''
    result += ExecuteCmd('git log --oneline ' + branch1 + '..' + branch2 + ' "--pretty=format:import <darkred>%h</> %s%n               %aE"', cwd=repo)
    result += ExecuteCmd('git log --oneline ' + branch2 + '..' + branch1 + ' "--pretty=format:export <darkgreen>%h</> %s%n               %aE"', cwd=repo)
    return result


def CommitCount(repo, branch1, branch2):
    '''
    Returns the number of commits between the two given branches.

    :param unicode repo:
        A local git working directory.

    :param unicode branch1:
        A valid branch name on repo.

    :param unicode branch1:
        A valid branch name on repo.

    :return tuple(int, int):
        [0]: Number of commits the branch1 adds compared with branch2
        [1]: Number of commits the branch2 adds compared with branch1
    '''
    try:
        result = ExecuteCmd('git rev-list --count --left-right %(branch1)s...%(branch2)s' % locals(), cwd=repo, split=True)
        return tuple(int(i) for i in result[0].strip().split('\t'))
    except RuntimeError:
        return (-1, -1)


def CommitCounts(repo, branch):
    '''
    Obtain the commits counts for the given branch.

    :return tuple(2-tuple, 2-tuple):
        Returns "CommitCount" information between the branch and its origin [0] and the branch
        between the master.
        CommitCount is a tuple(int, int) containing:
            [0]: Number of commits the branch1 adds compared with branch2
            [1]: Number of commits the branch2 adds compared with branch1
    '''
    origin_counts = CommitCount(repo, branch, 'origin/%s' % branch)
    master_counts = CommitCount(repo, branch, BRANCH_MASTER)
    return origin_counts, master_counts


def IsDirty(repo):
    '''
    Check if the git repository has changes in it.

    :param unicode repo:
        A local git working directory.
    '''
    result = ExecuteCmd('git status -s -uno', cwd=repo)
    result = [i for i in result if i.strip()]
    return len(result) > 0


def ExecuteCommands(console_, repo, commands, repl_dict={}, redirect_output=True):
    '''
    Shortcut to execute a bunch of commands.

    :param clikit.Console console_:
        Where to print the output.

    :param unicode repo:
        A local git working directory.

    :param list(unicode) commands:
        List of commands to execute.
        You may use dictionary replacement syntax for symbols defined in repl_dict.

    :param dict(unicode:unicode) repl_dict:
        A dictionary with symbols to expand on each command in commands.
    '''
    for i_command in commands:
        command = i_command % repl_dict
        try:
            output = ExecuteCmd(command, cwd=repo, verbose=True, redirect_output=redirect_output)
        except Exception as e:
            output = unicode(e)
            red_line = '<red>' + '*' * 80 + '</>'
            output = red_line + '\n' + output + '\n' + red_line
            output = ('<yellow>%s</>\n' % command) + output
            console_.Print(output, indent=1)
            return False

        console_.Print(output)
    return True


@app.Fixture
def Repos():
    '''
    Returns list of repositories to process.

    For now only considers the git working directories found in the current directory.
    '''
    import os
    import six

    if os.path.exists('.git'):
        return [os.getcwd()]

    r_repos = []
    for i_dir in os.listdir('.'):
        if os.path.exists('%s/.git' % i_dir):
            r_repos.append(i_dir)
    return sorted(r_repos)


@app
def ls(console_, repos_, branch=''):
    '''
    Lists and print status for all repositories and their local branches in the current directory.

    :param branch: Only lists branches maching this mask.
    '''

    def GetFlags(counts):
        result = []
        if counts[0] > 0:  # Local changes not on remote
            result.append('needs push')
        if counts[1] > 0:  # Remote changes that are not on local branch yet
            result.append('needs pull')
        if counts[3] > 1:  # Master have some commits that need to
            result.append('needs rom (rebase on master)')
        return result

    branches = {}

    if branch:
        branch, repos = FindBranch(repos_, branch)
    else:
        repos = repos_

    for i_repo in repos:
        status_output = ExecuteCmd('git status -s --untracked-files=no', cwd=i_repo, split=True)
        working_count = len(status_output)
        working_color = 'white' if working_count == 0 else 'red'

        repo_line = '<teal>%s</>:' % i_repo
        if working_count:
            repo_line += ' <%s>(%s local changes)</>' % (working_color, working_count)
        console_.Print(repo_line)
        if branch:
            local_branches = [branch]
        else:
            local_branches = GetLocalBranches(i_repo)
        branch_color = 'green'
        for j_branch in local_branches:
            if j_branch is None:
                continue

            origin_counts, master_counts = CommitCounts(i_repo, j_branch)
            counts = list(origin_counts) + list(master_counts)

            origin_color = 'white'
            if origin_counts[0] > 0 and origin_counts[1] > 0:
                origin_color = 'red'
            elif origin_counts[0] > 0 or origin_counts[1] > 0:
                origin_color = 'yellow'
            origin_counts = 'o:%d/%d' % tuple(origin_counts)

            master_color = 'white'
            if master_counts[1] > 0:
                master_color = 'yellow'
            elif master_counts[0] > 0:
                master_color = 'green'
            master_counts = 'm:%d/%d' % tuple(master_counts)

            indent = 1
            flags_str = '<%s>%-7s</>  <%s>%-7s</>' % (origin_color, origin_counts, master_color, master_counts)
            console_.Item('%(flags_str)s  <%(branch_color)s>%(j_branch)s</>' % locals(), indent=indent)

            branch_color = 'darkgreen'

            flags = GetFlags(counts)
            for i_flag in  flags:
                console_.Item(i_flag, indent=indent + 5)

            branches.setdefault(j_branch, []).append(i_repo)


@app
def st(console_, repos_):
    '''
    Statuses
    '''
    on_master = []
    on_branches = {}
    for i_repo in repos_:
        branch = GetCurrentBranch(i_repo)
        if branch is None:
            on_branches.setdefault('## (no branch)', []).append(i_repo)
            continue

        if branch == BRANCH_MASTER:
            on_master.append(i_repo)
            continue

        branch_status, file_status = BranchAndStatus(i_repo)
        commit_diff = CommitDiff(i_repo, branch, BRANCH_MASTER)

        if not (file_status or commit_diff.strip()):
            on_branches.setdefault(branch_status, []).append(i_repo)
            continue

        console_.Print('<teal>%s</>: %s' % (i_repo, branch_status))
        if file_status:
            console_.Print(file_status, indent=1, newlines=2)
        if commit_diff.strip():
            console_.Print(commit_diff, indent=1, newlines=2)

    if on_master:
        console_.Print('<green>## %s</>:' % BRANCH_MASTER)
        console_.Print(', '.join(on_master), newlines=2)

    for i_branch, i_repos in sorted(six.iteritems(on_branches)):
        console_.Print('<green>%s</>:' % i_branch)
        console_.Print(', '.join(sorted(i_repos)), newlines=2)


@app
def lg(console_, repos_, remote='origin'):
    '''
    Git log with one commit per line, using graph, considering all current branches.

    :param remote: Which remote to fetch the changes?
    '''
    for i_repo in repos_:
        console_.Print('<teal>%(i_repo)s</>:' % locals())

        branches = GetLocalBranches(i_repo)
        current_branch = branches[0]
        branches_str = ' '.join(branches)

        commands = [
            "git --no-pager log --graph --oneline --decorate -n20 --pretty=format:'%%C(yellow)%%h%%Creset -%%C(bold green)%%d%%Creset %%s %%C(green)(%%cr) %%C(cyan)<%%ae>%%Creset' --abbrev-commit --date=relative %(branches_str)s",
        ]
        ExecuteCommands(console_, i_repo, commands, locals(), redirect_output=False)


@app
def Import(console_, repos_, *branches):
    import getpass

    def ImportToRepo(repo, branches):
        is_dirty = IsDirty(repo)

        result = ''
        result += ExecuteCmd('git stash', repo, verbose=True, condition=is_dirty)
        result += ExecuteCmd('git rebase master', repo, verbose=True)
        result += ExecuteCmd('git stash pop', repo, verbose=True, condition=is_dirty)
        return result

    if not branches:
        branches = [getpass.getuser()]

    for i_repo in repos_:
        console_.Print('<teal>%(i_repo)s</>:' % locals())

        # Processes only the required branches.
        branch = GetCurrentBranch(i_repo)
        if branch not in branches:
            continue

        console_.Print(ImportToRepo(i_repo, branches), indent=1)


@app
def Export(console_, repos_, remote='origin'):
    '''
    Exports commits from the current branch to master.

    :param remote: Which remote to fetch the changes?
    '''

    for i_repo in repos_:
        console_.Print('<teal>%(i_repo)s</>:' % locals())

        commands = [
            'git merge -q --no-commit %(current_branch)s',
            'git push origin master'
        ]

        current_branch = GetCurrentBranch(i_repo)
        if current_branch != 'master':
            commands = ['git checkout -q master'] + commands + ['git checkout -q %(current_branch)s']

        is_dirty = IsDirty(i_repo)
        if is_dirty:
            commands = ['git stash'] + commands + ['git stash pop']

        ExecuteCommands(console_, i_repo, commands, locals())


@app
def Fetch(console_, repos_, remote='origin'):
    '''
    Fetches remote changes for all local branches, updating all origin/XXX refs.

    :param remote: Which remote to fetch the changes?
    '''
    for i_repo in repos_:
        console_.Print('<teal>%(i_repo)s</>:' % locals())

        # Prune deleted remote branches
        ExecuteCommands(console_, i_repo, ['git fetch --prune'])

        # Fetch changes from all existing remote branches and tags (must be done after we prune, or
        # the command might fail for trying to fetch a deleted branch).
        branches = GetRemoteBranches(i_repo, remote)
        branches_str = ' '.join(branches)
        ExecuteCommands(console_, i_repo, ['git fetch --tags %(remote)s %(branches_str)s'], locals())


@app
def Pull(console_, repos_, remote='origin'):
    '''
    Pulls remote changes for all local branches, synchronizing all local branches with their
    respective origins. Updates both refs origin/XXX and XXX.

    :param remote: Which remote to fetch the changes?
    '''
    for i_repo in repos_:
        console_.Print('<teal>%(i_repo)s</>:' % locals())

        if len(GetRemotes(i_repo)) == 0:
            console_.Print('No remotes!', indent=1)
            continue

        # Execute fetch before the rest of the commands to have an updated CommitCounts for further
        # processing.
        r = ExecuteCommands(console_, i_repo, ['git fetch --prune'])
        if not r:
            continue

        # Fetch changes from all existing remote branches and tags (must be done after we prune, or
        # the command might fail for trying to fetch a deleted branch).
        remote_branches = GetRemoteBranches(i_repo, remote)
        local_branches = GetLocalBranches(i_repo)

        branches = set(local_branches).intersection(remote_branches)

        branches_str = ' '.join(branches)
        r = ExecuteCommands(console_, i_repo, ['git fetch --tags %(remote)s %(branches_str)s'], locals())
        if not r:
            continue

        # Store current branch before we start switching around
        current_branch = GetCurrentBranch(i_repo)

        # Perform the pull
        commands = []
        for j_branch in branches:
            (o1, o2), (m1, m2) = CommitCounts(i_repo, j_branch)
            if o1 == 0 and o2 > 0:
                commands += [
                    'git checkout %(j_branch)s' % locals(),
                    'git pull --rebase --no-commit %(remote)s %(j_branch)s' % locals(),
                ]
        commands += [
            'git checkout %(current_branch)s',
        ]

        # Stash local changes if needed
        is_dirty = IsDirty(i_repo)
        if is_dirty:
            commands = ['git stash'] + commands + ['git stash pop']

        r = ExecuteCommands(console_, i_repo, commands, locals())
        if not r:
            continue

        # After everything is up to date, prune local branches that are fully merged to
        # origin/master, and do not exist in the remote
        merged_branches = GetMergedBranches(i_repo, remote=remote, branch='master')
        if merged_branches:
            r = ExecuteCommands(console_, i_repo, ['git branch -D ' + ' '.join(merged_branches)])
            if not r:
                continue


@app
def PullBranch(console_, repos_, branch, remote='origin'):
    '''
    Updates a local branch with remote value.
    '''
    def UpdateBranch(repo, branch):

        def GitCmd(cmd, cwd):
            result = '<yellow>%s</>\n' % cmd
            result += Indent(ExecuteCmd(cmd, cwd=cwd))
            return result

        current_branch = GetCurrentBranch(repo)
        result = ''
        result += ExecuteCmd('git checkout %s' % branch, cwd=repo, verbose=True)
        result += ExecuteCmd('git pull --rebase --no-commit origin', cwd=repo, verbose=True)
        result += ExecuteCmd('git checkout %s' % current_branch, cwd=repo, verbose=True)
        return result

    for i_repo in repos_:
        console_.Print('<teal>%(i_repo)s</>:' % locals())
        console_.Print(UpdateBranch(i_repo, BRANCH_MASTER), indent=1)


@app
def UpdateLocalRef(console_, repos_, branch, force=False):
    '''
    Update local reference to match the remote reference.

    :param branch: The branch to update
    :param force: If true, skips all security checks.
    '''
    def UpdateLocalRef(repo, branch):
        return ExecuteCmd(
            'git update-ref refs/heads/%(branch)s refs/remotes/origin/%(branch)s' % locals(),
            cwd=repo,
            verbose=True
        )

    for i_repo in repos_:
        console_.Print('<teal>%(i_repo)s</>:' % locals())
        console_.Print(UpdateLocalRef(i_repo, branch))


@app
def UpdateRemoteRef(console_, repos_, branch, force=False):
    '''
    Update remote reference to match the local reference.

    :param branch: The branch to update
    :param force: If true, skips all security checks.
    '''
    def UpdateLocalRef(repo, branch):
        return ExecuteCmd(
            'git update-ref refs/remotes/origin/%(branch)s refs/heads/%(branch)s' % locals(),
            cwd=repo,
            verbose=True
        )

    for i_repo in repos_:
        console_.Print('<teal>%(i_repo)s</>:' % locals())
        console_.Print(UpdateLocalRef(i_repo, branch))


@app(alias='rom')
def RebaseOnMaster(console_, repos_, force=False, *branches):
    '''
    Rebases a branch on master.

    :param force: If true, skips all security checks.
    :param branches: List of branches to update
    '''
    for i_branch in branches:
        branch, repos = FindBranch(repos_, i_branch)

        for i_repo in repos:
            console_.Print('<teal>%(i_repo)s</>:' % locals())

            commands = [
                'git rebase master',
                'git push origin --force %(branch)s',
            ]

            current_branch = GetCurrentBranch(i_repo)
            if current_branch != branch:
                commands = ['git checkout %(branch)s'] + commands + ['git checkout %(current_branch)s']

            is_dirty = IsDirty(i_repo)
            if is_dirty:
                commands = ['git stash'] + commands + ['git stash pop']

            ExecuteCommands(console_, i_repo, commands, locals())


@app(alias='sw')
def Switch(console_, repos_, branch, all=False, ignore=None):
    '''
    Switches to the given branch all repositories that have the branch.

    :param branch: The branch to switch to.
    :param all: Includes all branches when looking for switch matches (local and remote).
    :param ignore: Ignore branches that contain this string when looking for switch matches.
    '''
    branch, repos = FindBranch(repos_, branch, remote=all, ignore=ignore)

    console_.Print('\n<green>%(branch)s</>:' % locals())
    for i_repo in repos:
        if branch == GetCurrentBranch(i_repo):
            console_.Print('<teal>%(i_repo)s</>: already on requested branch.' % locals(), indent=1)
            continue

        console_.Print('<teal>%(i_repo)s</>:' % locals(), indent=1)
        console_.Print(
            Indent(
                ExecuteCmd('git checkout %(branch)s' % locals(), cwd=i_repo, verbose=True)
            )
        )


if __name__ == '__main__':
    sys.exit(app.Main())
