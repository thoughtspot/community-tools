"""
Contains all of the classes for working with a ThoughtSpot data model.

Copyright 2017 ThoughtSpot

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse


def main():
    """
    Strips comments from files, including /* */, //, and # types of comments.  If these are valid in your code, it may
    break them.  Q&D tool.
    """
    args = parse_args()

    with open(args.filename, "r") as f:
        for row in f.readline():
            pass


def parse_args():
    """Parses the arguments from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="name of file to strip comments from")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
