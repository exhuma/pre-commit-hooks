#!/usr/bin/env python3
from subprocess import check_output, CalledProcessError
import sys

def main():
    try:
        check_output(["git", "rev-parse", "--verify", "HEAD"])
        against = "HEAD"
    except CalledProcessError:
        # Initial commit: diff against an empty tree object
        against = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


    lines = check_output(["git", "diff", "--cached", against]).splitlines()
    matching = [line for line in lines if b"# xxx" in line.lower()]

    if matching:
        print("This commit would introduce an XXX marker!", file=sys.stderr)
        print(b"\n".join(matching))
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
