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
from buildbot.test.fake.state import State

class BuildStatus(State):
    name = ''
    branch = ''
    project = ''

class TestStatusFilter(unittest.TestCase):


    def setUp(self):
        self.results = []
        self.filt = None

    def tearDown(self):
        if self.results:
            raise RuntimeError("test forgot to call check()")

    def setfilter(self, **kwargs):
        self.filt = filter.StatusFilter(**kwargs)

    def yes(self, builderStatus, msg):
        self.results.append((self.filt.filter_status(builderStatus),
                             True, msg))

    def no(self, builderStatus, msg):
        self.results.append((self.filt.filter_status(builderStatus),
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
        self.no(BuildStatus(x=2), "filter_fn returns False")
        self.yes(BuildStatus(x=4), "filter_fn returns True")
        self.check()
        
    def test_filter_status_filt_str(self):
        self.setfilter(project = "myproj")
        self.no(BuildStatus(project="yourproj"), "non-matching PROJECT returns False")
        self.yes(BuildStatus(project="myproj"), "matching PROJECT returns True")
        self.check()

    def test_filter_status_filt_list(self):
        self.setfilter(project = ["myproj", "yourproj"])
        self.yes(BuildStatus(project="myproj"), "matching PROJECT myproj returns True")
        self.yes(BuildStatus(project="yourproj"), "matching PROJECT yourproj returns True")
        self.no(BuildStatus(project="theirproj"), "non-matching PROJECT theirproj returns False")
        self.check()

    def test_filter_status_filt_list_None(self):
        self.setfilter(branch = ["mybr", None])
        self.yes(BuildStatus(branch="mybr"), "matching BRANCH mybr returns True")
        self.yes(BuildStatus(branch=None), "matching BRANCH None returns True")
        self.no(BuildStatus(branch="misc"), "non-matching BRANCH returns False")
        self.check()

    def test_filter_status_filt_re(self):
        self.setfilter(builderName_re = "^hi.*")
        self.yes(BuildStatus(name="himom"), "matching BUILDERNAME returns True")
        self.no(BuildStatus(name="helloworld"), "non-matching BUILDERNAME returns False")
        self.check()

    def test_filter_status_filt_re_compiled(self):
        self.setfilter(project_re = re.compile("^b.*", re.I))
        self.no(BuildStatus(project="albert"), "non-matching PROJECT returns False")
        self.yes(BuildStatus(project="boris"), "matching PROJECT returns True")
        self.yes(BuildStatus(project="Bruce"), "matching PROJECT returns True, using re.I")
        self.check()

    def test_filter_status_combination(self):
        self.setfilter(project='p', builderName='n', branch='b')
        self.no(BuildStatus(project='x', name='x', branch='x'),
                "none match -> False")
        self.no(BuildStatus(project='p', name='n', branch='nope'),
                "three match -> False")
        self.yes(BuildStatus(project='p', name='n', branch='b'),
                "all match -> True")
        self.check()

    def test_filter_status_combination_filter_fn(self):
        self.setfilter(project='p', builderName='n', branch='b',
                       filter_fn = lambda c : c.ff)
        self.no(BuildStatus(project='x', name='x', branch='x', ff=False),
                "none match and fn returns False -> False")
        self.no(BuildStatus(project='p', name='n', branch='b', ff=False),
                "all match and fn returns False -> False")
        self.no(BuildStatus(project='x', name='x', branch='x', ff=True),
                "none match and fn returns True -> False")
        self.yes(BuildStatus(project='p', name='n', branch='b', ff=True),
                "all match and fn returns True -> True")
        self.check()