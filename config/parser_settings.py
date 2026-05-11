import argparse


def set_parser():
    parser = argparse.ArgumentParser(description="ADL3 helper")

    parser.add_argument(
        "--log-name",
        type=str,
        default=None,
        help="Set log name. Might be helpful for debug sessions"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Set logging level to debug"
    )

    return parser
