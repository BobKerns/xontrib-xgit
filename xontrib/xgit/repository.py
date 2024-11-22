'''
Implementation of the `GitRepository` class.
'''

from contextlib import suppress
from dataclasses import field
from pathlib import Path, PurePosixPath
import re
from typing import Literal, Optional, Sequence, cast, overload

from xonsh.lib.pretty import RepresentationPrinter

from xontrib.xgit.types import InitFn, GitObjectType
import xontrib.xgit.ref_types as rt
import xontrib.xgit.object_types as ot
import xontrib.xgit.context_types as ct
import xontrib.xgit.worktree as wtree
import xontrib.xgit.objects as obj
import xontrib.xgit.context as ctx
from xontrib.xgit.ref import _GitRef
from xontrib.xgit.git_cmd import _GitCmd
from xontrib.xgit.to_json import JsonDescriber


DEFAULT_BRANCH=(
    'refs/heads/main',
    'refs/heads/master',
    "HEAD",
    'refs/remotes/origin/HEAD',
)
'''
The intent is to identify a default branch by examining the repository and/or worktree.
'''

RE_HEX = re.compile(r'^[0-9a-f]{6,}$')

class _GitRepository(_GitCmd, ct.GitRepository):
    """
    A git repository.
    """

    __path: Path
    @property
    def path(self) -> Path:
        """
        The path to the repository. If this is for a worktree,
        it is the path to the worktree-specific part.
        For the main worktree, this is the same as `common`.
        """
        return self.__path

    __worktrees: ct.WorktreeMap|InitFn['_GitRepository',ct.WorktreeMap] = field(default_factory=dict)
    @property
    def worktrees(self) -> dict[Path, 'ct.GitWorktree']:
        if callable(self.__worktrees):
            self.__worktrees = self.__worktrees(self)
        return self.__worktrees

    __preferred_worktree: 'ct.GitWorktree|None' = None
    @property
    def worktree(self) -> 'ct.GitWorktree':
        """
        Get the preferred worktree.
        """
        if self.__preferred_worktree is not None:
            return self.__preferred_worktree
        if callable(self.__worktrees):
            self.__worktrees = self.__worktrees(self)
        if self.path.name == ".git":
            worktree = self.get_worktree(self.path.parent)
            if worktree is not None:
                self.__preferred_worktree = worktree
                return worktree
            commit = self.git('rev-parse', '--verify', '--quiet', 'HEAD', check=False)
            branch_name = self.git('symbolic-ref', '--quiet', 'HEAD', check=False)
            branch = None
            if branch_name:
                branch = _GitRef(branch_name, repository=self)
            worktree = wtree._GitWorktree(
                            path=self.path.parent,
                            repository=self,
                            repository_path=self.path,
                            branch=branch,
                            commit=obj._git_object(commit, self, 'commit'),
                            locked='',
                            prunable='',
                        )
            self.__preferred_worktree = worktree
            self.__worktrees[self.path.parent] = worktree
            return cast('ct.GitWorktree', worktree)

        with suppress(StopIteration):
            worktree = next(iter(self.worktrees.values()))
            if worktree is not None:
                self.__preferred_worktree = worktree
                return worktree
        raise ValueError("No worktrees found for repository")

    def get_worktree(self, key: Path|str) -> 'ct.GitWorktree|None':
        if callable(self.__worktrees):
            self.__worktrees = self.__worktrees(self)
        return self.__worktrees.get(Path(key).resolve())

    __objects: dict['ot.GitHash', 'ot.GitObject'] = field(default_factory=dict)
    """
    The path to the common part of the repository. This is the same for all worktrees.
    """

    def get_reference(self, ref: 'rt.RefSpec|None' = None) -> 'rt.GitRef|None':
        if ref is None:
            ref = DEFAULT_BRANCH
        def check_ref(ref: 'rt.RefSpec') -> 'rt.GitRef|None':
            with suppress(Exception):
                match ref:
                    case PurePosixPath():
                        return check_ref(str(ref))
                    case rt.GitRef():
                        pass
                    case str():
                        ref = ref.strip()
                        if ref:
                            return _GitRef(ref, repository=self.worktree.repository)
                    case Sequence():
                        return next(
                            rr
                            for rr in (self.get_reference(r) for r in ref)
                            if rr is not None
                        )
        return check_ref(ref)

    @overload
    def get_object(self, hash: 'ot.Commitish', type: Literal['commit']) -> 'ot.GitCommit':
        ...
    @overload
    def get_object(self, hash: 'ot.Treeish', type: Literal['tree']) -> 'ot.GitTree':
        ...
    @overload
    def get_object(self, hash: 'ot.Blobish', type: Literal['blob'],
                   size: int=-1) -> 'ot.GitBlob':
        ...
    @overload
    def get_object(self, hash: 'ot.Tagish', type: Literal['tag']) -> 'ot.GitTagObject':
        ...
    @overload
    def get_object(self, hash: 'ot.Objectish',
                   type: Optional[GitObjectType]=None,
                   size: int=-1
                   ) -> 'ot.GitObject':
        ...
    def get_object(self, hash: 'ot.Objectish',
                   type: Optional[GitObjectType]=None,
                   size: int=-1
                   ) -> 'ot.GitObject':
        match hash:
            case ot.GitObject():
                return hash
            case rt.GitRef():
                hash = self.git('rev-parse', '--verify', '--quiet', hash.name)
            case str():
                hash = hash.strip()
                if not hash:
                    raise ValueError(f"Invalid hash: {hash!r}")
                if RE_HEX.match(hash):
                    try:
                        hash = self.git('rev-parse', '--verify', '--quiet', hash)
                    except ValueError:
                        hash = self.git('rev-parse', '--verify', '--quiet', f'refs/heads/{hash}')
                else:
                    if not hash.startswith('refs/'):
                        hash = f'refs/heads/{hash}'
                    hash = self.git('rev-parse', '--verify', '--quiet', hash)
            case _:
                raise ValueError(f"Invalid hash: {hash!r}")
        return obj._git_object(hash, self, type, size)

    def __init__(self, *args,
                 path: Path = Path(".git"),
                 **kwargs):
        super().__init__(path.parent)
        self.__path = path
        def init_worktrees(self: '_GitRepository') -> 'ct.WorktreeMap':
            bare: bool = False
            result: dict[Path, 'ct.GitWorktree'] = {}
            worktree: Path = path.parent.resolve()
            branch: 'rt.GitRef|None' = None
            commit: 'ot.GitCommit|None' = None
            locked: str = ''
            prunable: str = ''
            for l in self.git_lines('worktree', 'list', '--porcelain'):
                match l.strip().split(' ', maxsplit=1):
                    case ['worktree', wt]:
                        worktree = Path(wt).resolve()
                    case ['HEAD', c]:
                        commit = self.get_object(c, 'commit')
                        self.__objects[commit.hash] = commit
                    case ['branch', b]:
                        b = b.strip()
                        if b:
                            branch = _GitRef(b, repository=self)
                        else:
                            branch = None
                    case ['locked', l]:
                        locked = l.strip('"')
                        locked = locked.replace('\\n', '\n')
                        locked = locked.replace('\\"', '"')
                        locked =locked.replace('\\\\', '\\')
                    case ['locked']:
                        locked = '-'''
                    case ['prunable', p]:
                        prunable = p.strip('"')
                        prunable = prunable.replace('\\n', '\n')
                        prunable = prunable.replace('\\"', '"')
                        prunable =prunable.replace('\\\\', '\\')
                    case ['prunable']:
                        prunable = '-'''
                    case ['detached']:
                        branch = None
                    case ['bare']:
                        bare = True
                    case _ if l.strip() == '':
                        repository_path = Path(self.git('rev-parse', '--absolute-git-dir'))
                        repository_path = repository_path.resolve()
                        assert commit is not None, "Commit has not been set."
                        result[worktree] = wtree._GitWorktree(
                            path=worktree,
                            repository=self,
                            repository_path=repository_path,
                            branch=branch,
                            commit=commit,
                            locked=locked,
                            prunable=prunable,
                        )
                        worktree = path.parent
                        branch = None
                        commit = None
                        locked = ''
                        prunable = ''
            return result
        self.__worktrees = init_worktrees
        self.__objects = {}



    def to_json(self, describer: JsonDescriber):
        return str(self.path)

    @staticmethod
    def from_json(data: str, describer: JsonDescriber):
        return _GitRepository(data)

    def _repr_pretty_(self, p: RepresentationPrinter, cycle: bool):
        if cycle:
            p.text(f"GitRepository({self.path}")
        else:
            with p.group(4, "Repository:"):
                p.break_()
                p.text(f"path: {ctx._relative_to_home(self.path)}")
                p.break_()
                with p.group(4, "worktrees:", "\n"):
                    wts = self.worktrees.values()
                    f1 = max(len(str(ctx._relative_to_home(wt.path)))
                             for wt in wts)
                    def shorten_branch(branch: str):
                        branch = branch.replace('refs/heads/', '')
                        branch = branch.replace('refs/remotes/', '')
                        branch = branch.replace('refs/tags/', 'tag:')
                        return branch
                    f2 = max(len(shorten_branch(wt.branch.name if wt.branch else '-')) for wt in wts)
                    f4 = max(len(wt.commit.author.person.name) for wt in wts)
                    for wt in self.worktrees.values():
                        p.breakable()
                        branch = shorten_branch(wt.branch.name if wt.branch else '-')
                        p.text(f"{str(ctx._relative_to_home(wt.path)):{f1}s}: {branch:{f2}s} {wt.commit.hash} {wt.commit.author.person.name:{f4}s} {wt.commit.author.date}")
                p.breakable()
                p.text(f"preferred_worktree: {ctx._relative_to_home(self.worktree.path)}")
                p.break_()
                p.text(f"objects: {len(self.__objects)}")
