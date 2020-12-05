#!/usr/bin/env python3
"""
Creates new dependency tree with graphdeps for each report run
Updates past dependency tree with graphdeps after each change using last report run
"""

import os
from pathlib import Path
import subprocess
import argparse
import platform
import graphdeps

CONFIG_DIR = os.path.join(Path.home(), '.cache', 'taskwarrior-showdeps')
FILTERS_PATH = os.path.join(CONFIG_DIR, 'last_graphdeps_query.cfg')


def make_config_dir():
    """Create CONFIG_DIR directory"""
    if not os.path.isdir(CONFIG_DIR):
        Path(CONFIG_DIR).mkdir(parents=True)


def check_report_type(user_args):
    """Return location of first command or 0 if no command found"""

    # List of commands found at https://taskwarrior.org/docs/commands/
    commands_full = ['add', 'annotate', 'append', 'calc', 'config', 'context',
                     'count', 'delete', 'denotate', 'done', 'duplicate',
                     'edit', 'execute', 'export', 'help', 'import', 'log',
                     'logo', 'modify', 'prepend', 'purge', 'start',
                     'stop', 'synchronize', 'undo', 'version']
    commands_dict = {}

    # Create dictionary of all commands where key is length of commands
    max_command_length = len(max(commands_full, key=len))
    for i in range(2, max_command_length):
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
        if 2 <= arg_length <= max_command_length:
            if commands_dict[arg_length].count(arg) == 1:
                # Command found and unique
                return command_location
    return 0


def main(user_args, output, task, show, all_projects, verbose, show_deleted):
    """
    Shows dependency tree for reports and updates tree for each subsequent
    command run
    """

    # Check if input is valid
    if user_args == None and all_projects == False:
        print('Argument required (unless running all-projects)')
        exit()

    # Set IMAGE_PATH
    if output:
        # Use user-defined path if specified
        IMAGE_PATH = output_path
    elif show:
        # If showing image, store in CONFIG_DIR
        IMAGE_PATH = os.path.join(CONFIG_DIR, 'last_deps_image.png')
    else:
        # IF not showing image, make it easily found by saving in current directory
        IMAGE_PATH = os.path.join('deps.png')

    # Check for CONFIG_DIR
    make_config_dir()

    # Get graphdeps_query for graphdeps
    command_location = check_report_type(user_args)
    if command_location == 0:
        # user_args is report, so generate new graphdeps_query
        if verbose:
            print('Running new filter to create dependency tree')

        # Update saved graphdeps_query if user_args are report
        graphdeps_query = user_args  # list with each filter as a separate element
        with open(FILTERS_PATH, 'w') as f:
            f.write(' '.join(graphdeps_query))

        # Run Taskwarrior using user_args (same as graphdeps_query)
        if task:
            subprocess.run(['task', ' '.join(user_args)], check=False)

    else:
        # user_args is command, so use last graphdeps_query
        if verbose:
            print('Rerunning last filter to create dependency tree')

        # Load graphdeps_query last used if user_args are a command
        with open(FILTERS_PATH, 'r') as f:
            graphdeps_query = [f.read().replace('\n', '')]  # list containing 1 element
            # Split list so each filter is a separate element
            graphdeps_query = graphdeps_query[0].split(' ')

        # Run Taswarrior using user_args
        if task:
            tw_command = ['task']
            for i in range(0, command_location):
                # Append commands individually
                tw_command.append(user_args[i])
            # Append filters as one string
            tw_command.append(' '.join(user_args[command_location:]))
            subprocess.run(tw_command, check=False)

    # Update dependency tree using graphdeps_query
    if not show_deleted:
        graphdeps_query.append('-DELETED')
    if all_projects:
        # TODO
        # for project in projects:
        #    project_graphdeps_query = graphdeps_query
        #    project_graphdeps_query.append('pro:' + project)
        #    graphdeps.main(proect_graphdeps_query, IMAGE_PATH + project, verbose)
    # else:
        graphdeps.main(graphdeps_query, IMAGE_PATH, verbose)

    # Show dependency tree or where it was saved
    if show:

        if platform.system() == 'Linux':
            # Check if feh is running (returns 0 if it is, 1 if it is not)
            feh = subprocess.run(['pidof', 'feh'], capture_output=True, check=False)

            # Open feh if not running
            if feh.returncode == 1:
                subprocess.Popen(['feh', '--auto-zoom', IMAGE_PATH])

        elif platform.system() == 'Windows':
            subprocess.Popen(['start', IMAGE_PATH], shell=True)

        else:
            print('Your system platform could not be determined to open image')
    else:
        print('Imaged saved to ' + IMAGE_PATH)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Show dependency tree if '
                                     'report or update tree if command')
    parser.add_argument('user_args', nargs='*', help='Commands or filters')
    parser.add_argument('-o', '--output', help='Output path without extension')
    parser.add_argument('--task', action='store_true', help='Runs the command in Taskwarrior before generating dependency tree')
    parser.add_argument('--show', action='store_true', help='Shows the dependency tree in an image viewer instead of saving to current directory')
    parser.add_argument('--all-projects', action='store_true', help='Save dependency tree for each project, appending project name to output path')
    parser.add_argument('--show-deleted', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()
    main(args.user_args, args.output, args.task, args.show, args.all_projects, args.verbose, args.show_deleted)
