#!/usr/bin/env python2
import argparse
import copy
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
                if impacted_parts & self.parts[part].influencers:
                    impacted_parts.add(part)
            prev_size = len(impacted_parts)
        return impacted_parts

    def needed_tests(self, impacted_parts):
        tests = set([])
        for part in impacted_parts:
            tests |= self.parts[part].tests
        return tests


def yaml_loader(filepath, project):
    with open(filepath, 'r') as yaml_file:
        yaml_docs = yaml.safe_load_all(yaml_file)
        for yaml_doc in yaml_docs:

            project.create_part(**yaml_doc)


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--project-file', dest='project_file', required=True)
parser.add_argument('changes', nargs=argparse.REMAINDER)
options = parser.parse_args()

if __name__ == "__main__":
    project = Project()
    yaml_loader(options.project_file, project)
    changes = options.changes
    impact = project.impact(changes)
    to_test = project.needed_tests(impact)
    print("List of impacted parts: {0}".format(", ".join(impact)))
    print("Tests to run: {0}".format(", ".join(to_test)))
