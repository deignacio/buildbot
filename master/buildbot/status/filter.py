# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

import re, types

from buildbot.util import ComparableMixin, NotABranch

class StatusFilter(ComparableMixin):
    
    compare_attrs = ('filter_fn', 'result_checks', 'checks')
    
    def __init__(self,
                 filter_fn=None,
                 builderName=None, builderName_re=None, builderName_fn=None,
                 project=None, project_re=None, project_fn=None,
                 branch=None, branch_re=None, branch_fn=None):
        """
        Similar to a ChangeFilter for changes.

        @type  filter_fn: function
        @param filter_fn: takes a builderStatus, returns a boolean

        @type  builderName: string or list
        @param builderName: builderName(s) to filter on
        
        @type  builderName_re: regular expression
        @param builderName_re: matches builderName

        @type  builderName_fn: function
        @param builderName_fn: takes the builderName, returns a boolean

        @type  project: string or list
        @param project: project(s) to filter on
        
        @type  project_re: regular expression
        @param project_re: matches project

        @type  project_fn: function
        @param project_fn: takes the project, returns a boolean

        @type  branch: string or list
        @param branch: branch(es) to filter on
        
        @type  branch_re: regular expression
        @param branch_re: matches branch

        @type  branch_fn: function
        @param branch_fn: takes the branch, returns a boolean
        """
        def mklist(x):
            if x is not None and type(x) is not types.ListType:
                return [ x ]
            return x
        def mklist_br(x): # branch needs to be handled specially
            if x is NotABranch:
                return None
            if type(x) is not types.ListType:
                return [ x ]
            return x
        def mkre(r):
            if r is not None and not hasattr(r, 'match'):
                r = re.compile(r)
            return r

        self.filter_fn = filter_fn
        self.checks = [
            (mklist(builderName), mkre(builderName_re), builderName_fn, "name"),
            (mklist(project), mkre(project_re), project_fn, "project"),
            (mklist(branch), mkre(branch_re), branch_fn, "branch"),
        ]

    def _filter_value(self, value, filt_list, filt_re, filt_fn):
        if filt_list is not None and value not in filt_list:
            return False
        if filt_re is not None and (value is None or not filt_re.match(value)):
            return False
        if filt_fn is not None and not filt_fn(value):
            return False
        return True

    def filter_status(self, builderStatus):
        if self.filter_fn is not None and not self.filter_fn(builderStatus):
            return False
        for filt_list, filt_re, filt_fn, attr in self.checks:
            value = getattr(builderStatus, attr)
            if not self._filter_value(value, filt_list, filt_re, filt_fn):
                return False
        return True
    
    def __repr__(self):
        checks = []
        check_tuples = self.checks + [self.result_checks + tuple(["result"])]
        for (filt_list, filt_re, filt_fn, chg_attr) in check_tuples:
            if filt_list is not None and len(filt_list) == 1:
                checks.append('%s == %s' % (chg_attr, filt_list[0]))
            elif filt_list is not None:
                checks.append('%s in %r' % (chg_attr, filt_list))
            if filt_re is not None :
                checks.append('%s ~/%s/' % (chg_attr, filt_re))
            if filt_fn is not None :
                checks.append('%s(%s)' % (filt_fn.__name__, chg_attr))

        return "<%s on %s>" % (self.__class__.__name__, ' and '.join(checks))
    
            