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
import re


def dump_yaml_snippet(name):
    with open('template.yaml', 'r') as template_file:
        template = template_file.read()
        print(template.format(**{'name':name}))

parser = argparse.ArgumentParser()
parser.description = ('Creates yaml skeleton based on file structured by '
                      'indentation. For example of how to format input file '
                      'see example.skel file.')
parser.add_argument('-t', '--template',
                    dest='template', default='template.yaml')
parser.add_argument('structure_file')
options = parser.parse_args()

namespace = []
namespace_indent = [1]
with open(options.structure_file, 'r') as source:
    line = source.readline()
    mo = re.match('^( *)\* *(.*)', line)
    previous_indent = len(mo.group(1))
    previous = mo.group(2)
    for line in source.readlines():
        mo = re.match('^( *)\* *(.*)', line)
        indent = len(mo.group(1))
        text = mo.group(2)
        if indent > previous_indent:
            # it was a group, no printing
            namespace += [previous]
            namespace_indent += [previous_indent]
        elif indent == previous_indent:
            dump_yaml_snippet(' - '.join(namespace + [previous]))
        else:
            # got out of group
            dump_yaml_snippet(' - '.join(namespace + [previous]))
            if indent == namespace_indent[-1]:
                # returning back to known group
                namespace.pop()
                previous_indent = namespace_indent.pop()
            else:
                # just a different subgroup
                previous_indent = indent
            previous = text
            # no common code for this else branch
            continue
        previous_indent = indent
        previous = text
# last line
dump_yaml_snippet(' - '.join(namespace + [previous]))
