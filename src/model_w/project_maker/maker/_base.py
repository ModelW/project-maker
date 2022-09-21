from pathlib import Path
from typing import Mapping, Sequence

from model_w.project_maker.template import render, render_line


class BaseComponent:
    """
    A component is away to configure the behavior of the Maker (see the related
    docstring).
    """

    def accept(self, path: Path):
        raise NotImplementedError

    def context(self, path: Path, context: Mapping) -> Mapping:
        return context


class YesComponent(BaseComponent):
    """
    A test component that will accept all files.
    """

    def accept(self, path: Path):
        return True


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

        for file in source.glob("**/*"):
            if not file.is_file():
                continue

            for component in self.components:
                sub_path = file.relative_to(source)

                if component.accept(sub_path):
                    file_context, target_path = self.prepare_target(
                        component, context, sub_path, target
                    )
                    self.render_file(file, file_context, target_path)
                    continue

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
                while buf := f.read(1024 ** 2):
                    t.write(buf)
