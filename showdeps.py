#!/usr/bin/env python3
"""
Shows dependency tree for reports and updates tree for each subsequent
command run
"""

import sys
import os
from pathlib import Path
import subprocess
import argparse
import graphdeps

CONFIG_DIR = os.path.join(Path.home(), '.cache', 'taskwarrior-showdeps')

IMAGE_PATH = os.path.join(CONFIG_DIR, 'last_deps_image.svg')
FILTERS_PATH = os.path.join(CONFIG_DIR, 'last_report_query.cfg')


def make_config_dir():
    """Create CONFIG_DIR directory"""
    if not os.path.isdir(CONFIG_DIR):
        Path(CONFIG_DIR).mkdir(parents=True)


def check_report_type(user_args):
    """
    If command given, return location of first command
    If no user_args, return 0
    If no command found (assuming report filter), return -1
    """

    # Re-run last report if no user_args given
    if user_args == []:
        print('No arguments given, using last query to update dependency tree...')
        return 0

    # List of commands found at https://taskwarrior.org/docs/commands/
    commands_full = ['add', 'annotate', 'append', 'calc', 'config', 'context',
                     'count', 'delete', 'denotate', 'done', 'duplicate',
                     'edit', 'execute', 'export', 'help', 'import', 'log',
                     'logo', 'modify', 'prepend', 'purge', 'start',
                     'stop', 'synchronize', 'undo', 'version']
    commands_dict = {}

    # Create dictionary of all commands where key is length of commands
    max_command_length = len(max(commands_full, key=len))
    for i in range(2, max_command_length + 1):
        commands_dict[i] = []
        for command in commands_full:
            commands_dict[i].append(command[0:i])

    # Check each arg against commands of same length
    # arg matches a command if it matches only one command after truncating all
    # commands to same length as arg
    command_location = 0
    for arg in user_args:
        command_location += 1
        arg_length = len(arg)
        if 2 <= arg_length < max_command_length:
            if commands_dict[arg_length].count(arg) == 1:
                # Command found and unique
                print('Command provided, running command and then using last query to update dependency tree...')
                return command_location

    print('Report filter provided, storing new query to update dependency tree...')
    return -1


def main(user_args, show, png):
    """
    Shows dependency tree for reports and updates tree for each subsequent
    command run
    """

    # Check for CONFIG_DIR
    make_config_dir()

    # Get query for graphdeps
    command_location = check_report_type(user_args)
    if command_location == -1:
        # user_args is report, so generate new query

        # Update query if user_args are report
        query = user_args  # list with each filter as a separate element
        with open(FILTERS_PATH, 'w') as f:
            f.write(' '.join(query))

        # Run Taskwarrior
        subprocess.run(['task', ' '.join(user_args)], check=False)

    else:
        # user_args is command, so use last query

        # Load query last used if user_args are a command
        with open(FILTERS_PATH, 'r') as f:
            query = [f.read().replace('\n', '')]  # list containing 1 element
            # Split list so each filter is a separate element
            query = query[0].split(' ')

        # Run Taswarrior
        if command_location >= 1:
            tw_command = ['task']
            for user_arg in user_args:
                # Append args individually
                tw_command.append(user_arg)
            subprocess.run(tw_command, check=False)

    # Update dependency tree
    query.append('-DELETED')
    graphdeps.main(query, IMAGE_PATH, True)

    if sys.platform.startswith('linux'):
        if png:
            # Check if feh is running (returns 0 if it is, 1 if it is not)
            feh = subprocess.run(['pidof', 'feh'], capture_output=True, check=False)
            # Open feh if not running
            if feh.returncode == 1:
                subprocess.Popen(['feh', '--auto-zoom', IMAGE_PATH])
        else:
            subprocess.Popen(['xdg-open', IMAGE_PATH])
    elif sys.platform.startswith('win'):
        if show:
            subprocess.Popen(['start', IMAGE_PATH], shell=True)
    else:
        print('OS is not supported for showing image')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Taskwarrior commands'
                                                 'and update dependency tree')
    parser.add_argument('user_args', nargs='*',
                        help='Taskwarrior filters or commands')
    parser.add_argument('-s', '--show', action='store_true',
                        help='Show resulting image')
    parser.add_argument('--png', action='store_true',
                        help='Save as a png insteand of svg')

    args = parser.parse_args()
    main(args.user_args, args.show, args,png)
