from __future__ import print_function

import os
from os.path import abspath, realpath, join, dirname
import sys

import yaml

base_dir = abspath(join(dirname(realpath(__file__)), '..'))

config_path = None
if os.environ.get('CONFIG_FROM_ENV'):
    print("Loading config from environment variables", file=sys.stderr)
    general_yml_example_fname = join(base_dir, 'conf', 'general.yml-example')
    with open(general_yml_example_fname) as f:
        example_config = yaml.load(f)
    config = {
        k: os.environ[k]
        for k in example_config.keys()
        if k in os.environ
    }
else:
    config_path =  join(base_dir, 'conf', 'general.yml')
    print("Loading config from {0}".format(config_path), file=sys.stderr)
    with open(config_path) as f:
        config = yaml.load(f)
