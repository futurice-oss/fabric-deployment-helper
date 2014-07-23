#!/usr/bin/env python
import os, sys, argparse

from fabric.api import execute

from soppa.file import import_string

def use_fabric_env(path):
    path = path or env.sync_filename
    local_env = json.loads(open(path, 'r').read().strip() or '{}')
    env.update(**local_env)

def main(args):
    use_fabric_env(args.filename)
    execute(import_string(args.cmd))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run stuff.')
    parser.add_argument('--cmd', type=str)
    parser.add_argument('--filename', type=str)
    args = parser.parse_args()
    main(args)

