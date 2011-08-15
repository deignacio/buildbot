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

import re

from twisted.trial import unittest

from buildbot.status import filter
from buildbot.status.results import FAILURE, SKIPPED, SUCCESS
from buildbot.test.fake.state import State

class BuildStatus(State):
    name = ''
    branch = ''
    project = ''
    result = ''

class TestStatusFilter(unittest.TestCase):


    def setUp(self):
        self.results = []
        self.filt = None

    def tearDown(self):
        if self.results:
            raise RuntimeError("test forgot to call check()")

    def setfilter(self, **kwargs):
        self.filt = filter.StatusFilter(**kwargs)

    def yes(self, builderStatus, result, msg):
        self.results.append((self.filt.filter_status(builderStatus, result),
                             True, msg))

    def no(self, builderStatus, result, msg):
        self.results.append((self.filt.filter_status(builderStatus, result),
                             False, msg))

    def check(self):
        errs = []
        for r in self.results:
            if (r[0] or r[1]) and not (r[0] and r[1]):
                errs.append(r[2])
        self.results = []
        if errs:
            self.fail("; ".join(errs))

    def test_filter_status_filter_fn(self):
        self.setfilter(filter_fn = lambda bs : bs.x > 3)
        self.no(BuildStatus(x=2), SUCCESS, "filter_fn returns False")
        self.yes(BuildStatus(x=4), SUCCESS, "filter_fn returns True")
        self.check()
        
    def test_filter_status_filt_str(self):
        self.setfilter(project = "myproj")
        self.no(BuildStatus(project="yourproj"), SUCCESS, "non-matching PROJECT returns False")
        self.yes(BuildStatus(project="myproj"), SUCCESS, "matching PROJECT returns True")
        self.check()

    def test_filter_status_filt_list(self):
        self.setfilter(result = [SKIPPED, FAILURE])
        self.yes(BuildStatus(), SKIPPED, "matching RESULT SKIPPED returns True")
        self.yes(BuildStatus(), FAILURE, "matching RESULT FAILURE returns True")
        self.no(BuildStatus(), SUCCESS, "non-matching RESULT returns False")
        self.check()

    def test_filter_status_filt_list_None(self):
        self.setfilter(branch = ["mybr", None])
        self.yes(BuildStatus(branch="mybr"), SUCCESS, "matching BRANCH mybr returns True")
        self.yes(BuildStatus(branch=None), SUCCESS, "matching BRANCH None returns True")
        self.no(BuildStatus(branch="misc"), SUCCESS, "non-matching BRANCH returns False")
        self.check()

    def test_filter_status_filt_re(self):
        self.setfilter(builderName_re = "^hi.*")
        self.yes(BuildStatus(name="himom"), SUCCESS, "matching BUILDERNAME returns True")
        self.no(BuildStatus(name="helloworld"), SUCCESS, "non-matching BUILDERNAME returns False")
        self.check()

    def test_filter_status_filt_re_compiled(self):
        self.setfilter(project_re = re.compile("^b.*", re.I))
        self.no(BuildStatus(project="albert"), SUCCESS, "non-matching PROJECT returns False")
        self.yes(BuildStatus(project="boris"), SUCCESS, "matching PROJECT returns True")
        self.yes(BuildStatus(project="Bruce"), SUCCESS, "matching PROJECT returns True, using re.I")
        self.check()

    def test_filter_status_combination(self):
        self.setfilter(project='p', builderName='n', branch='b', result=FAILURE)
        self.no(BuildStatus(project='x', name='x', branch='x'),
                SUCCESS, "none match -> False")
        self.no(BuildStatus(project='p', name='n', branch='nope'),
                FAILURE, "three match -> False")
        self.yes(BuildStatus(project='p', name='n', branch='b'),
                FAILURE, "all match -> True")
        self.check()

    def test_filter_status_combination_filter_fn(self):
        self.setfilter(project='p', builderName='n', branch='b', result=SKIPPED,
                       filter_fn = lambda c : c.ff)
        self.no(BuildStatus(project='x', name='x', branch='x', ff=False),
                SUCCESS, "none match and fn returns False -> False")
        self.no(BuildStatus(project='p', name='n', branch='b', ff=False),
                SKIPPED, "all match and fn returns False -> False")
        self.no(BuildStatus(project='x', name='x', branch='x', ff=True),
                SUCCESS, "none match and fn returns True -> False")
        self.yes(BuildStatus(project='p', name='n', branch='b', ff=True),
                SKIPPED, "all match and fn returns True -> True")
        self.check()