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
        impacted = {}
        for impacted_part in impacted_parts:
            impacted[impacted_part] = self.parts[impacted_part]
        return impacted

    def influence(self, influenced_parts):
        influenced = {}
        for part in influenced_parts:
            influenced[part] = self.parts[part]
        prev_size = 0
        while prev_size != len(influenced):
            prev_size = len(influenced)
            for part in influenced.keys()[:]:
                for influencer in self.parts[part].influencers:
                    influenced[influencer] = self.parts[influencer]
        return influenced


    @staticmethod
    def needed_tests(impacted_parts):
        tests = set([])
        for part in impacted_parts.values():
            tests |= part.tests
        return tests

    @staticmethod
    def generate_dot_string(sub_parts, dot_file):
        def normalize(name):
            translation_table = string.maketrans(' -.|()*',
                                                 '_______')
            new_name = name.split(' - ')[-1]
            return string.translate(new_name, translation_table)

        dot_string = 'strict digraph "influence map" {\n'
        for part in sub_parts:
            if "EVERYTHING" in sub_parts[part].influencers:
                # let's make it special shape, and leave it as that
                # arrows would be ugly
                dot_string += "{0} [shape = box]".format(
                                          normalize(sub_parts[part].name))
                continue  # EVERYTHING means we are done
            for influencer in sub_parts[part].influencers:
                try:
                    try:
                        sub_parts[influencer].influencing |= set([part])
                    except AttributeError:
                        sub_parts[influencer].influencing = set([part])
                except KeyError:
                    continue

        for part in sub_parts:
            part_display_name = normalize(sub_parts[part].name)
            try:
                influencing_display_names = map(lambda x: normalize(x),
                                                sub_parts[part].influencing)
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
parser.add_argument('--changes', dest='changes', action="store_true",
                    help=("Input contains list of changed parts, and "
                          "prints all parts influenced by this change set"))
parser.add_argument('--influence', dest='influence', action="store_true",
                    help=("Print out all parts that are influencing "
                          "those specified."))
parser.add_argument('inputs', nargs=argparse.REMAINDER)
options = parser.parse_args()

if __name__ == "__main__":
    project = Project()
    yaml_loader(options.project_file, project)
    if options.changes:
        impact = project.impact(options.inputs)
        print(impact)
        if options.dot_file:
            dot_string = project.generate_dot_string(impact, options.dot_file)
        to_test = project.needed_tests(impact)
        if options.nice_output:
            separator = '\n'
        else:
            separator = ', '
        print("List of impacted parts: {0}".format(separator.join(impact)))
        print("Tests to run: {0}".format(separator.join(to_test)))
    elif options.influence:
        influence = project.influence(options.inputs)
        print(influence)
        if options.dot_file:
            dot_string = project.generate_dot_string(influence, options.dot_file)
        to_test = project.needed_tests(influence)
        if options.nice_output:
            separator = '\n'
        else:
            separator = ', '
        print("List of influenced parts: {0}".format(separator.join(influence)))
        print("Tests to run: {0}".format(separator.join(to_test)))
    elif options.dot_file:
        project.generate_dot_string(project.parts, options.dot_file)
