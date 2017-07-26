#!/usr/bin/env python2

#   Copyright (c) 2017 Red Hat, Inc. All rights reserved.
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import copy
import string
import sys
import yaml


class Part(object):
    def __init__(self,
                 name,
                 project,
                 description=None,
                 tests=None,
                 influencers=None):
        self.name = name
        self._project = project
        self.description = description
        self._tests = None
        self._influencers = None
        self.tests = tests
        self.influencers = influencers

    @property
    def tests(self):
        return copy.copy(self._tests)

    @tests.setter
    def tests(self, value):
        try:
            self._tests = set(value)
        except TypeError:
            self._tests = set([])

    @property
    def influencers(self):
        return copy.copy(self._influencers)

    @influencers.setter
    def influencers(self, value):
        try:
            self._influencers = set(value)
        except TypeError:
            self._influencers = set([])


class Project(object):
    def __init__(self):
        self.parts = {}

    def create_part(self,
                    name,
                    description=None,
                    tests=None,
                    influencers=None):
        new_part = Part(name, self, description, tests, influencers)
        self.parts[name] = new_part

    def impact(self, changed_parts):
        impacted_parts = set(changed_parts)
        prev_size = 0
        while prev_size != len(impacted_parts):
            for part in self.parts:
                if impacted_parts & self.parts[part].influencers or \
                   'EVERYTHING' in self.parts[part].influencers:
                    impacted_parts.add(part)
            prev_size = len(impacted_parts)
        return impacted_parts

    def needed_tests(self, impacted_parts):
        tests = set([])
        for part in impacted_parts:
            tests |= self.parts[part].tests
        return tests

    def generate_dot_string(self, dot_file):
        def normalize(name):
            translation_table = string.maketrans(' -.|()*',
                                                 '_______')
            new_name = name.split(' - ')[-1]
            return string.translate(new_name, translation_table)

        dot_string = 'strict digraph "influence map" {\n'
        for part in self.parts:
            if "EVERYTHING" in self.parts[part].influencers:
                # let's make it special shape, and leave it as that
                # arrows would be ugly
                dot_string += "{0} [shape = box]".format(
                                          normalize(self.parts[part].name))
                continue  # EVERYTHING means we are done
            for influencer in self.parts[part].influencers:
                try:
                    self.parts[influencer].influencing |= set([part])
                except AttributeError:
                    self.parts[influencer].influencing = set([part])

        for part in self.parts:
            part_display_name = normalize(self.parts[part].name)
            try:
                influencing_display_names = map(lambda x: normalize(x),
                                                self.parts[part].influencing)
                if len(influencing_display_names) == 1:
                    dot_string += "{0} -> {1};\n".format(part_display_name,
                                           " ".join(influencing_display_names))
                else:
                    dot_string += "{0} -> {{{1}}};\n".format(part_display_name,
                                           " ".join(influencing_display_names))
            except AttributeError:
                # this node is not influencing anything
                dot_string += "{0};\n".format(part_display_name)
        dot_string += "}"
        with open(dot_file, 'w') as output_file:
            output_file.write(dot_string)


def yaml_loader(filepath, project):
    with open(filepath, 'r') as yaml_file:
        yaml_docs = yaml.safe_load_all(yaml_file)
        for yaml_doc in yaml_docs:

            project.create_part(**yaml_doc)


parser = argparse.ArgumentParser()
parser.description = ('Evaluates influence tree provided within project yaml '
                      'file, and prints out impacted parts and tests to cover '
                      'them, based on list of changed parts from command line')
parser.add_argument('-p', '--project-file', dest='project_file', required=True)
parser.add_argument('--nice', dest='nice_output', action="store_true",
                    help="Formats output to be readable by human")
parser.add_argument('--dot', dest='dot_file',
                    help=("Generates dot file to be "
                          "used by graphwiz generator"))
parser.add_argument('changes', nargs=argparse.REMAINDER)
options = parser.parse_args()

if __name__ == "__main__":
    project = Project()
    yaml_loader(options.project_file, project)
    if options.dot_file:
        dot_string = project.generate_dot_string(options.dot_file)
        sys.exit()
    impact = project.impact(options.changes)
    to_test = project.needed_tests(impact)
    if options.nice_output:
        separator = '\n'
    else:
        separator = ', '
    print("List of impacted parts: {0}".format(separator.join(impact)))
    print("Tests to run: {0}".format(separator.join(to_test)))
