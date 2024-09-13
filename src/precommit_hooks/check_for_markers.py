#!/usr/bin/env python3
"""
This script checks for the presence of debug markers in the code.
"""
import re
import sys
from argparse import ArgumentParser, Namespace
from difflib import unified_diff
from io import BytesIO
from typing import Iterable, cast

from git import Diff, GitCommandError, Repo
from git.objects.base import Object


def parse_args() -> Namespace:
    """
    Parse the command-line arguments.
    """
    parser = ArgumentParser(description="Check for debug markers in the code")
    parser.add_argument(
        "--pattern",
        "-p",
        action="append",
        help="A regex pattern to search for in the code (can be specified multiple times)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="The files to check. If not specified, all files in the index will be checked",
    )
    return parser.parse_args()


def read_blob(blob: Object | None) -> str:
    """
    Read the contents of a blob from GitPython and return it as a string.

    :param blob: The blob to read
    :return: The contents of the blob as a string
    """
    if not blob:
        return ""
    buffer = BytesIO()
    blob.stream_data(buffer)  # type: ignore
    try:
        return buffer.getvalue().decode("utf8")
    except UnicodeDecodeError:
        # Not a text-file most likely and we'll ignore it
        return ""


def parse_line_number(line: str) -> int:
    """
    Given a unified-diff header in the format of "@@ -14,0 +15 @@", extract the
    line-number as it appears in the target file.

    :param line: A single line from a unified-diff
    :return: The line number

    Example:

    >>> parse_line_number('@@ -14,0 +20,3 @@')
    20
    """
    if not line.startswith("@@"):
        raise ValueError("Not a unified-diff header")
    parts = line.split(" ")
    if len(parts) != 4:
        raise ValueError("Not a unified-diff header")
    return int(parts[2].split(",")[0])


def collect_errors(
    filename: str, new_data: str, old_data: str, error_patterns: list[str]
) -> list[str]:
    """
    Given two versions of a file, collect all lines that contain a debug marker.

    :param filename: The name of the file
    :param data_a: The original version of the file
    :param data_b: The new version of the file
    :param error_patterns: A list of error patterns to search for
    :return: A list of errors that should be reported
    """
    errors: list[str] = []
    diff_result = unified_diff(
        old_data.splitlines(), new_data.splitlines(), lineterm="", n=0
    )
    line_number = 1
    for line in diff_result:
        if line.startswith("@@"):
            line_number = parse_line_number(line)
        if not line.startswith("+") or line.strip() == "+++":
            # Only lines with a "+" are incoming changes. We should not complain
            # if a debug-marker is *removed* so we skip those.
            continue
        for pattern in error_patterns:
            if re.search(pattern, line):
                errors.append(
                    f"Error pattern {pattern!r} detected at {filename}:{line_number}"
                )
        if line.startswith("+"):
            line_number += 1
    return errors


def main():
    """
    Main entry-point for the pre-commit hook.
    """
    args = parse_args()
    repo = Repo(".")
    try:
        against = repo.git.rev_parse("HEAD", verify=True)
    except GitCommandError:
        against = ""
    if not against:
        # Initial commit: diff against an empty tree object
        against = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    errors: list[str] = []
    diff_result = cast(Iterable[Diff], repo.index.diff(against, paths=args.files or None))  # type: ignore
    for diff in diff_result:
        if diff.a_blob == diff.b_blob or diff.b_blob is None:
            continue
        new_data = read_blob(diff.a_blob)
        old_data = read_blob(diff.b_blob)
        errors.extend(
            collect_errors(diff.b_path or "", new_data, old_data, args.pattern)
        )
    if errors:
        for error in errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
