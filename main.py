import argparse


def init_arg_parse():
    parser = argparse.ArgumentParser(description="MUL project")
    return parser


def main():
    parser = init_arg_parse()
    args = parser.parse_args()


if __name__ == "__main__":
    main()
