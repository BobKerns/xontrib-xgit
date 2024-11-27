'''
Tests for `GitContext`.
'''

from typing import Any, cast
from unittest.mock import NonCallableMock
from pathlib import Path

to_json: Any
from_json: Any


def test_context_loads(modules, sysdisplayhook):
    with modules('xontrib.xgit.context') as ((m_ctx), vars):
        assert m_ctx is not None

def test_context_simple(with_xgit, worktree, sysdisplayhook):
    import xontrib.xgit.context as ctx
    ctx = ctx._GitContext(worktree.repository.context.session, worktree=worktree)
    assert ctx is not NonCallableMock

def test_context_json(with_xgit,
                      worktree,
                      git_context,
                      git,
                      sysdisplayhook,
                      test_branch):
    import xontrib.xgit.context as ctx
    from xontrib.xgit.to_json import to_json
    head = worktree.rev_parse('HEAD')
    branch = worktree.symbolic_ref('HEAD')
    ctx = git_context
    ctx.worktree=worktree
    ctx.branch = branch
    ctx.commit = head
    j = to_json(ctx, repository=worktree.repository)
    loc = worktree.location
    expected = {
        'branch': branch,
        'path': '.',
        'commit': head,
        'worktree': {
            "repository": str(loc / '.git'),
            'path': str(worktree.path),
            'repository_path': str(loc / '.git'),
            'branch': branch,
            'commit': head,
            'locked': '',
            'prunable': '',
        },
    }
    assert isinstance(j, dict)
    j = cast(dict, j)
    assert j['worktree'] == expected['worktree']
    assert j == expected