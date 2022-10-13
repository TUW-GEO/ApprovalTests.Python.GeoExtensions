import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="convert `git describe` output to PEP440 conform version")
    parser.add_argument('git_version', type=str, help='output of `git describe`')
    args = parser.parse_args()
    git_version = args.git_version
    parts = git_version.split('-')
    if len(parts) == 1:
        sys.stdout.write(git_version)
    else:
        sys.stdout.write(f"{parts[0]}.dev{parts[1]}")
