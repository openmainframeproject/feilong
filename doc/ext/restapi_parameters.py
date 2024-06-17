# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from collections import OrderedDict
import os
import re

from docutils import nodes
from docutils.parsers.rst.directives.tables import Table
from docutils.statemachine import ViewList
from sphinx.util import logging
from sphinx.util.osutil import copyfile
import yaml


YAML_CACHE = {}
LOG = logging.getLogger(__name__)


def ordered_load(
        stream, Loader=yaml.SafeLoader, object_pairs_hook=OrderedDict):
    """Load yaml as an ordered dict

    This allows us to inspect the order of the file on disk to make
    sure it was correct by our rules.
    """
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    OrderedLoader.add_constructor(
        u'tag:yaml.org,2002:float',
        yaml.constructor.SafeConstructor.construct_yaml_str)

    return yaml.load(stream, OrderedLoader)


class RestAPIParametersDirective(Table):

    headers = ["Name", "In", "Type", "Description"]

    def _load_param_file(self, fpath):
        global YAML_CACHE
        if fpath in YAML_CACHE:
            return YAML_CACHE[fpath]

        lookup = {}
        LOG.info("Fpath: %s" % fpath)
        try:
            with open(fpath, 'r') as stream:
                lookup = ordered_load(stream)
        except IOError:
            LOG.warning(
                "Parameters file %s not found" % fpath,
                (self.env.docname, None))
            return
        except yaml.YAMLError as exc:
            LOG.warning(exc)
            raise

        # FIXME: check sorting

        return lookup

    def yaml_from_file(self, fpath):
        """Collect Parameter stanzas from inline + file.

        This allows use to reference an external file for the actual
        parameter definitions.
        """

        lookup = self._load_param_file(fpath)
        if not lookup:
            return

        content = "\n".join(self.content)
        parsed = yaml.safe_load(content)
        LOG.info("Params loaded is %s" % parsed)
        LOG.info("Lookup table looks like %s" % lookup)
        new_content = list()
        for paramlist in parsed:
            if not isinstance(paramlist, dict):
                LOG.warning(
                    ("Invalid parameter definition ``%s``. Expected "
                     "format: ``name: reference``. "
                     " Skipping." % paramlist),
                    (self.state_machine.node.source,
                     self.state_machine.node.line))
                continue
            for name, ref in paramlist.items():
                if ref in lookup:
                    new_content.append((name, lookup[ref]))
                else:
                    LOG.warning(
                        ("No field definition for ``%s`` found in ``%s``. "
                         " Skipping." % (ref, fpath)),
                        (self.state_machine.node.source,
                         self.state_machine.node.line))

        LOG.info("New content %s" % new_content)
        self.yaml = new_content

    def run(self):
        self.env = self.state.document.settings.env
        self.app = self.env.app

        # Make sure we have some content, which should be yaml that
        # defines some parameters.
        if not self.content:
            error = self.state_machine.reporter.error(
                'No parameters defined',
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno)
            return [error]

        if not self.content:
            error = self.state_machine.reporter.error(
                'No parameters defined',
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno)
            return [error]

        if not len(self.arguments) >= 1:
            error = self.state_machine.reporter.error(
                'No reference file defined',
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno)
            return [error]

        rel_fpath, fpath = self.env.relfn2path(self.arguments.pop())
        self.yaml_file = fpath
        self.yaml_from_file(self.yaml_file)

        self.max_cols = len(self.headers)
        self.options['widths'] = [20, 10, 10, 60]
        self.col_widths = self.get_column_widths(self.max_cols)
        if isinstance(self.col_widths, tuple):
            # In docutils 0.13.1, get_column_widths returns a (widths,
            # colwidths) tuple, where widths is a string (i.e. 'auto').
            # See https://sourceforge.net/p/docutils/patches/120/.
            self.col_widths = self.col_widths[1]
        # Actually convert the yaml
        title, messages = self.make_title()
        LOG.info("Title %s, messages %s" % (title, messages))
        table_node = self.build_table()
        self.add_name(table_node)
        if title:
            table_node.insert(0, title)
        return [table_node] + messages

    def get_rows(self, table_data):
        rows = []
        groups = []
        trow = nodes.row()
        entry = nodes.entry()
        para = nodes.paragraph(text=unicode(table_data))
        entry += para
        trow += entry
        rows.append(trow)
        return rows, groups

        # Add a column for a field. In order to have the RST inside
    # these fields get rendered, we need to use the
    # ViewList. Note, ViewList expects a list of lines, so chunk
    # up our content as a list to make it happy.
    def add_col(self, value):
        entry = nodes.entry()
        result = ViewList(value.split('\n'))
        self.state.nested_parse(result, 0, entry)
        return entry

    def show_no_yaml_error(self):
        trow = nodes.row(classes=["no_yaml"])
        trow += self.add_col("No yaml found %s" % self.yaml_file)
        trow += self.add_col("")
        trow += self.add_col("")
        trow += self.add_col("")
        return trow

    def collect_rows(self):
        rows = []
        groups = []
        try:
            LOG.info("Parsed content is: %s" % self.yaml)
            for key, values in self.yaml:
                min_version = values.get('min_version', '')
                max_version = values.get('max_version', '')
                desc = values.get('description', '')
                classes = []
                if min_version:
                    desc += ("\n\n**New in version %s**\n" % min_version)
                    min_ver_css_name = ("rp_min_ver_" +
                                        str(min_version).replace('.', '_'))
                    classes.append(min_ver_css_name)
                if max_version:
                    desc += ("\n\n**Deprecated in version %s**\n" %
                             max_version)
                    max_ver_css_name = ("rp_max_ver_" +
                                        str(max_version).replace('.', '_'))
                    classes.append(max_ver_css_name)
                trow = nodes.row(classes=classes)
                name = key
                if values.get('required', False) is False:
                    name += " (Optional)"
                trow += self.add_col(name)
                trow += self.add_col(values.get('in'))
                trow += self.add_col(values.get('type'))
                trow += self.add_col(desc)
                rows.append(trow)
        except AttributeError as exc:
            if 'key' in locals():
                LOG.warning("Failure on key: %s, values: %s. %s" %
                              (key, values, exc))
            else:
                rows.append(self.show_no_yaml_error())
        return rows, groups

    def build_table(self):
        table = nodes.table()
        tgroup = nodes.tgroup(cols=len(self.headers))
        table += tgroup

        tgroup.extend(
            nodes.colspec(colwidth=col_width, colname='c' + str(idx))
            for idx, col_width in enumerate(self.col_widths)
        )

        thead = nodes.thead()
        tgroup += thead

        row_node = nodes.row()
        thead += row_node
        row_node.extend(nodes.entry(h, nodes.paragraph(text=h))
                        for h in self.headers)

        tbody = nodes.tbody()
        tgroup += tbody

        rows, groups = self.collect_rows()
        tbody.extend(rows)
        table.extend(groups)

        return table


def setup(app):
    app.add_directive('restapi_parameters', RestAPIParametersDirective)

