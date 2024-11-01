# xontrib-xgit

An [xonsh](https://xon.sh) command-line environment for exploring git repositories and histories.

This provides a set of commands that return objects for both display and pythonic manipulation.

If you like the idea click ⭐ on the repo and <a href="https://twitter.com/intent/tweet?text=Nice%20xontrib%20for%20the%20xonsh%20shell!&url=https://github.com/BobKerns/xontrib-xgit" target="_blank">tweet</a>.

## Installation

To install use xpip:

```xsh
xpip install xontrib-xgit
# or: xpip install -U git+https://github.com/BobKerns/xontrib-xgit
```

## Usage

```xsh
xontrib load xgit
```

## Commands

### git-cd (Command)

`git-cd [`_path_`]`

Update the git working directory (and the process working directory if the directory exists in the worktree).

If _path_ is in a different worktree or repository, it will switch automatically to that worktree and repository.

With no arguments, returns to the root of the current repository.

### git-pwd (Command)

`git-pwd`

Print information about the current git context, including:

- `repository`; Repository path per worktree
- `common`: Repository common path
- `worktree`: Worktree root path
- `git_path`: Path within the repository
- `branch`: Current Branch
- `commit`: Current commit
- `cwd`: Working directory (what `pwd` would print)

This just returns (and displays) the [`XGIT`](#xgit-variable) variable if it is not `None`. In scripts you can just reference this variable directly.

### XGIT (Variable)

The current `GitContext`. This is the same as the value returned from the [`git-pwd`](#git-pwd-command) command.

It will be `None` when not inside a git worktree or repository.

### XGIT_CONTEXTS (variable)

A dictionary of `GitContext` objects, one for every worktree or repository we have visited.

This allows one to switch between repositories without losing context.

### git-ls (Command)

This returns the directory as an object which can be accessed from the python REPL:

```bash
>>> git-ls
_3: GitTree(c000f7a0a713b405fe0de6531fdbdfff3ff65d38)[7]
    - 569f95766c26158241a665763c76b93b103538b9     3207 .gitignore
    D 46b57ab337456176669e75513dbe0f5eeca38a22        1 .vscode
    - a3990ed1209000756420fae0ee6386e051204a60     1066 LICENSE
    - 505d8917cd9697185e30bb79238be4d84d02693e       50 README.md
    D 6f0c75cd8b53eeb83198dd5c6caea5361a240e20        2 bstring
    - 16494e4075e5cc44c5a928c7a325b8bc7bf552d5       23 requirements.txt
    D 05433255eddde7d3261f07a45b857374e6087278       10 xontrib-xgit
>>> _['README.md']
GitFile(- 505d8917cd9697185e30bb79238be4d84d02693e       50)
>>> _.hash
'505d8917cd9697185e30bb79238be4d84d02693e'
```

### git_ls (Function)

The functional version of the `git-ls` command.

```python
git_ls('xontrib-xgit')
```

## Credits

This package was created with [xontrib template](https://github.com/xonsh/xontrib-template).

--------------------

## Xontrib Promotion (DO and REMOVE THIS SECTION)

- ✅ Check that your repository name starts from `xontrib-` prefix. It helps Github search find it.

- ✅ Add `xonsh`, `xontrib` and other thematic topics to the repository "About" setting.

- ✅ Add preview image in "Settings" - "Options" - "Social preview". It allows to show preview image in Github Topics and social networks e.g. Twitter.

- ✅ Enable "Sponsorship" in "Settings" - "Features" - Check "Sponsorships".

- Add xontrib to the [awesome-xontribs](https://github.com/xonsh/awesome-xontribs).

- Publish your xontrib to PyPi via Github Actions and users can install your xontrib via `xpip install xontrib-myxontrib`. Easiest way to achieve it is to use Github Actions. Register to [https://pypi.org/](https://pypi.org) and [create API token](https://pypi.org/help/#apitoken). Go to repository "Settings" - "Secrets" and your PyPI API token as `PYPI_API_TOKEN` as a "Repository Secret". Now when you create new Release the Github Actions will publish the xontrib to PyPi automatically. Release status will be in Actions section. See also `.github/workflows/release.yml`.

- Write a message to: [xonsh Gitter chat](https://gitter.im/xonsh/xonsh?utm_source=xontrib-template&utm_medium=xontrib-template-promo&utm_campaign=xontrib-template-promo&utm_content=xontrib-template-promo), [Twitter](https://twitter.com/intent/tweet?text=xonsh%20is%20a%20Python-powered,%20cross-platform,%20Unix-gazing%20shell%20language%20and%20command%20prompt.&url=https://github.com/BobKerns/xontrib-xgit), [Reddit](https://www.reddit.com/r/xonsh), [Mastodon](https://mastodon.online/).
