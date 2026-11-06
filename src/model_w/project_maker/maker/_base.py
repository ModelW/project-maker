import shutil
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from subprocess import PIPE, Popen

from ..errors import ProjectMakerError
from ..template import render, render_line

#: Files which can exist locally in the template (because it's developed and
#: tested in place) but must never end up in a generated project. This is
#: deliberately independent from the template's .gitignore files, which are
#: meant for the generated projects.
LOCAL_FILES = [
    # Python
    "__pycache__/",
    "*.py[cod]",
    ".venv/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    # Node
    "node_modules/",
    ".svelte-kit/",
    "/front/build/",
    ".nuxt/",
    ".eslintcache",
    # Environment (the committed ones are .env-template and .env.test)
    ".env",
    ".env.*",
    "!.env.test",
    # Test results
    "/api/bdd/report/results/",
    "/api/bdd/performance/results/",
    # Misc
    "*.log",
    ".DS_Store",
    ".idea/",
    ".vscode/",
]


#: Receives the description of each step of the generation, as it starts
Progress = Callable[[str], None]


def no_progress(step: str) -> None:
    """Default progress callback, which ignores the steps"""


class BaseComponent:
    """
    A component is away to configure the behavior of the Maker (see the related
    docstring).
    """

    #: Set by the Maker during the generation, see report()
    progress: Progress = staticmethod(no_progress)

    def report(self, step: str) -> None:
        """
        Tells whoever follows the generation that a (long) step starts.

        Parameters
        ----------
        step
            Human-readable description of the step
        """

        self.progress(step)

    def accept(self, path: Path, context: Mapping):
        raise NotImplementedError

    def context(self, path: Path, context: Mapping) -> Mapping:
        return context

    def target_sub_path(self, path: Path, context: Mapping) -> Path:
        """
        Gives a chance to the component to move an accepted file somewhere
        else in the target. This allows, for example, to install an
        alternative implementation of a file depending on the options.

        Parameters
        ----------
        path
            Path of the file relative to the template root (not rendered yet)
        context
            Context of the file
        """

        return path

    def post_process(self, root: Path, path: Path, context: Mapping) -> None:
        pass

    def finalize(self, root: Path, context: Mapping) -> None:
        """
        Called once all files have been rendered, before the Git repository
        gets initialized. This is the place for whole-project operations like
        running formatters/linters with auto-fix or generating lockfiles.

        Parameters
        ----------
        root
            Root of the generated project
        context
            Global context of the generation
        """

    def start(self) -> None:
        """Hook to start resources needed for the component"""

    def stop(self) -> None:
        """Hook to stop the resources that were stopped"""


class YesComponent(BaseComponent):
    """
    A test component that will accept all files.
    """

    def accept(self, path: Path, context: Mapping):
        return True


class Exec:
    """
    A shortcut to execute Git commands below
    """

    def __init__(self, cwd: str | Path):
        self.cwd = Path(cwd)

    def exec(self, cmd: Sequence[str], env: Mapping[str, str] | None = None):
        # Resolved explicitly: on Windows, Popen doesn't find the .cmd/.bat
        # shims (like the ones of npm or pipx) from their bare name
        path = env.get("PATH") if env else None
        cmd = [shutil.which(cmd[0], path=path) or cmd[0], *cmd[1:]]
        p = Popen(cmd, cwd=self.cwd, stdout=PIPE, stderr=PIPE, env=env)
        out, err = p.communicate()

        if p.returncode != 0:
            raise ProjectMakerError(
                f"Failed to execute {cmd}: {err.decode()}{out.decode()}"
            )


class Maker:
    """
    The goal of the maker is to provide a way to copy a source directory into
    a target directory while applying the code template language on both the
    inside of the files and their names.

    In order to allow a maximum configurability, it will lean on a list of
    components which for each file can decide to accept and and to enrich the
    context for those files.

    As a result a component "front" can accept the files for the front-end
    while a component "back" can accept the files for the backend and so forth.
    """

    def __init__(self, components: Sequence[BaseComponent]):
        self.components: Sequence[BaseComponent] = components

    def make(
        self,
        source: Path,
        target: Path,
        context: Mapping,
        progress: Progress = no_progress,
    ):
        """
        Copies the whole tree from source into the target, while rendering
        what needs to be.

        Parameters
        ----------
        source
            Source directory to render
        target
            Target to populate
        context
            Context to be used in template
        progress
            Called with the description of each step as it starts
        """

        if target.exists() and (not target.is_dir() or [*target.iterdir()]):
            raise ProjectMakerError(f"Target {target} is not empty or is not a dir")

        try:
            for component in self.components:
                component.progress = progress
                component.start()

            progress("Rendering the template")

            for file in source.rglob("*"):
                if not file.is_file():
                    continue

                for component in self.components:
                    sub_path = file.relative_to(source)

                    if component.accept(sub_path, context):
                        file_context, target_path = self.prepare_target(
                            component, context, sub_path, target
                        )
                        self.render_file(file, file_context, target_path)
                        component.post_process(
                            target,
                            target_path.relative_to(target),
                            file_context,
                        )
                        continue

            for component in self.components:
                component.finalize(target, context)
        finally:
            for component in self.components:
                component.stop()
                component.progress = no_progress

        progress("Creating the Git repository")
        self.init_git(target)

    def init_git(self, target):
        """
        Runs the equivalent of "git init" and "git flow init -d" in the target
        folder. Since we want to keep on with the standard branch names that
        other projects are using, we unfold manually what git-flow-init would
        do, with hardcoded values.
        """

        e = Exec(target)
        e.exec(["git", "init", "-b", "master"])
        e.exec(["git", "config", "gitflow.branch.master", "master"])
        e.exec(["git", "config", "gitflow.branch.develop", "develop"])
        e.exec(["git", "symbolic-ref", "HEAD", "refs/heads/master"])
        e.exec(["git", "commit", "--allow-empty", "--quiet", "-m", "Initial commit"])
        e.exec(["git", "branch", "--no-track", "develop", "master"])
        e.exec(["git", "checkout", "-q", "develop"])
        e.exec(["git", "config", "gitflow.prefix.feature", "feature/"])
        e.exec(["git", "config", "gitflow.prefix.bugfix", "bugfix/"])
        e.exec(["git", "config", "gitflow.prefix.release", "release/"])
        e.exec(["git", "config", "gitflow.prefix.hotfix", "hotfix/"])
        e.exec(["git", "config", "gitflow.prefix.support", "support/"])
        e.exec(["git", "config", "gitflow.prefix.versiontag", ""])
        e.exec(["git", "config", "gitflow.path.hooks", ".git/hooks"])
        e.exec(["git", "add", "-A"])

    def prepare_target(self, component, context, sub_path, target):
        """
        For a given component and file, computes the target path and context
        for the render.
        """

        file_context = component.context(sub_path, context)
        sub_path = component.target_sub_path(sub_path, file_context)
        target_sub_path = Path(render_line(f"{sub_path}", file_context))
        target_path = target / target_sub_path

        target_path.parent.mkdir(parents=True, exist_ok=True)

        return file_context, target_path

    def render_file(self, file: Path, file_context: Mapping, target_path: Path):
        """
        Renders (if text) or copies (if binary) the source file into the
        target path.

        Notes
        -----
        We consider that the file is binary if it is not containing proper
        UTF-8 text. If you wish to encode files in another charset than UTF-8
        well you should be ashamed and so should be your family, your
        descendents and your cats.

        Parameters
        ----------
        file
            Source file to be rendered/copied
        file_context
            Context to be used in rendering
        target_path
            Target path to write
        """

        try:
            with open(file, encoding="utf-8") as f:
                target_content = render(f, file_context)

            # LF everywhere, including on Windows (no newline translation)
            with open(target_path, encoding="utf-8", mode="w", newline="\n") as t:
                t.write(target_content)
        except UnicodeDecodeError:
            with open(file, mode="rb") as f, open(target_path, "wb") as t:
                while buf := f.read(1024**2):
                    t.write(buf)
