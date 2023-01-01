from pathlib import Path
from subprocess import PIPE, Popen
from typing import Mapping, Sequence

from ..errors import ProjectMakerError
from ..template import render, render_line


class BaseComponent:
    """
    A component is away to configure the behavior of the Maker (see the related
    docstring).
    """

    def accept(self, path: Path, context: Mapping):
        raise NotImplementedError

    def context(self, path: Path, context: Mapping) -> Mapping:
        return context

    def post_process(self, root: Path, path: Path, context: Mapping) -> None:
        pass

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

    def exec(self, cmd: Sequence[str]):
        p = Popen(cmd, cwd=self.cwd, stdout=PIPE, stderr=PIPE)

        if p.wait() != 0:
            raise ProjectMakerError(
                f"Failed to execute {cmd}: {p.stderr.read().decode()}"
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

    def make(self, source: Path, target: Path, context: Mapping):
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
        """

        if target.exists() and (not target.is_dir() or [*target.iterdir()]):
            raise ProjectMakerError(f"Target {target} is not empty or is not a dir")

        try:
            for component in self.components:
                component.start()

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

        finally:
            for component in self.components:
                component.stop()

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

            with open(target_path, encoding="utf-8", mode="w") as t:
                t.write(target_content)
        except UnicodeDecodeError:
            with open(file, mode="rb") as f, open(target_path, "wb") as t:
                while buf := f.read(1024**2):
                    t.write(buf)
