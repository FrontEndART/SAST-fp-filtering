from dataclasses import dataclass
from pathlib import Path
from collections import deque
import pprint

import click
import tree_sitter
import tree_sitter_java as ts_java
from tree_sitter import Language, Parser


@dataclass
class Position:
    line: int
    col: int

    def __eq__(self, other):
        if not isinstance(other, Position):
            return NotImplemented
        return self.line == other.line and self.col == other.col

    def __hash__(self):
        return hash((self.line, self.col))


@dataclass
class CodeRange:
    start_pos: Position
    end_pos: Position

    def __repr__(self):
        return f"CodeRange({self.start_pos.line}:{self.start_pos.col}-{self.end_pos.line}:{self.end_pos.col})"

    def __eq__(self, other):
        if not isinstance(other, CodeRange):
            return NotImplemented
        return self.start_pos == other.start_pos and self.end_pos == other.end_pos

    def __hash__(self):
        return hash((self.start_pos, self.end_pos))

    def overlaps_with(self, other_range: "CodeRange") -> bool:
        """Checks if this CodeRange overlaps with another."""
        return not (
            self.end_pos.line < other_range.start_pos.line
            or self.start_pos.line > other_range.end_pos.line
            or (
                self.start_pos.line == other_range.end_pos.line
                and self.start_pos.col > other_range.end_pos.col
            )
            or (
                self.end_pos.line == other_range.start_pos.line
                and self.end_pos.col < other_range.start_pos.col
            )
        )


@dataclass
class CodeElement:
    range: CodeRange
    id: str
    type: str


def get_java_parser() -> Parser:
    """Returns a parser for Java language."""
    JAVA_LANGUAGE = Language(ts_java.language())
    return Parser(JAVA_LANGUAGE)


def find_identifier(node) -> None | tree_sitter.Node:
    if node.type == "identifier":
        return node
    for child in node.children:
        result = find_identifier(child)
        if result is not None:
            return result
    return None


def find_overlapping_elements(
    file_path: Path, ranges: list[CodeRange], node_type: str
) -> dict[CodeRange, list[CodeElement]]:
    """Finds code elements of the given type overlapping with the provided ranges."""
    with file_path.open("r") as file:
        source_code = file.read()

    parser = get_java_parser()
    tree = parser.parse(bytes(source_code, "utf8"))

    elements = {range_: [] for range_ in ranges}

    def traverse_tree(root_node):
        queue = deque([root_node])

        while queue:
            node = queue.popleft()

            if node.type == node_type:
                node_range = CodeRange(
                    Position(node.start_point[0] + 1, node.start_point[1] + 1),
                    Position(node.end_point[0] + 1, node.end_point[1] + 1),
                )
                for target_range in ranges:
                    if node_range.overlaps_with(target_range):
                        node_id = find_identifier(node).text.decode()
                        elements[target_range].append(
                            CodeElement(node_range, node_id, node_type)
                        )

                        break

            for child in node.children:
                queue.append(child)

    traverse_tree(tree.root_node)

    return elements


def parse_range(range_str: str) -> CodeRange:
    """Parses a range string into a CodeRange instance."""
    start_str, end_str = range_str.strip().split("-")
    start_line, start_col = map(int, start_str.split(":"))
    end_line, end_col = map(int, end_str.split(":"))
    return CodeRange(Position(start_line, start_col), Position(end_line, end_col))


@click.command()
@click.option(
    "--file",
    required=True,
    type=click.Path(exists=True),
    help="The path to the source code file.",
)
@click.option(
    "--ranges",
    required=True,
    type=str,
    help="The code ranges to find overlapping elements in. Ranges should be comma-separated and in the format "
    '"start_line:start_col-end_line:end_col".',
)
@click.option(
    "--element",
    default="method_declaration",
    type=str,
    help="The type of code element to find. Default: method_declaration.",
)
def main(file: str, ranges: str, element: str):
    file_path = Path(file)
    ranges = [parse_range(range_str) for range_str in ranges.split(",")]
    overlapping_elements = find_overlapping_elements(file_path, ranges, element)
    pprint.pprint(overlapping_elements, width=40, compact=True)


if __name__ == "__main__":
    main()
