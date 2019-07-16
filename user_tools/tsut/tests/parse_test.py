from argparse import ArgumentParser
import sys

print (sys.argv)

def print_line():
    print ("----------------------------------------------------------------------")


# print("base_parser")
# base_parser = ArgumentParser(add_help=False)
# args = "('--base1', help='first base parser arg')"
# base_parser.add_argument(args)
# base_parser.print_usage()
# print_line()
#
# print("base_parser_2")
# base_parser_2 = ArgumentParser(parents=[base_parser])
# base_parser_2.add_argument("--base3", help="another added in base_parser_2")
# base_parser_2.print_usage()
# print_line()
#
# print("parser_1")
# parser_1 = ArgumentParser(parents=[base_parser])
# parser_1.print_usage()
# print_line()
#
# print("parser_2")
# parser_2 = ArgumentParser(parents=[base_parser_2], conflict_handler="resolve")
# parser_2.print_usage()
# print_line()
#
# print("parser_1_and_2")
#
# parser_1_and_2 = ArgumentParser(parents=[parser_1, parser_2], conflict_handler="resolve")
# parser_1_and_2.print_usage()
# print_line()

def add_args_a(parser):
    parser.add_argument("--arg_a1")
    parser.add_argument("--arg_a2")
    parser.add_argument("--common")

def add_args_b(parser):
    parser.add_argument("--arg_b1")
    parser.add_argument("--arg_b2")
    parser.add_argument("--common")

parser = ArgumentParser(conflict_handler="resolve")
add_args_a(parser)
add_args_b(parser)

parser.print_usage()
