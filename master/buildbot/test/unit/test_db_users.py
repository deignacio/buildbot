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

import sqlalchemy as sa
from twisted.trial import unittest
from buildbot.db import users
from buildbot.test.util import connector_component
from buildbot.test.fake import fakedb

class TestUsersConnectorComponent(connector_component.ConnectorComponentMixin,
                                 unittest.TestCase):

    def setUp(self):
        d = self.setUpConnectorComponent(
                table_names=['users', 'users_info', 'changes', 'change_users'])
        def finish_setup(_):
            self.db.users = users.UsersConnectorComponent(self.db)
        d.addCallback(finish_setup)
        return d

    def tearDown(self):
        return self.tearDownConnectorComponent()

    # sample user data

    user1_rows = [
        fakedb.User(uid=1, identifier='soap'),
        fakedb.UserInfo(uid=1, attr_type='IPv9', attr_data='0578cc6.8db024'),
    ]

    user2_rows = [
        fakedb.User(uid=2),
        fakedb.UserInfo(uid=2, attr_type='git',
                        attr_data='Tyler Durden <tyler@mayhem.net>'),
        fakedb.UserInfo(uid=2, attr_type='irc', attr_data='durden')
    ]

    user1_dict = {
        'uid': 1,
        'identifier': u'soap',
        'IPv9': u'0578cc6.8db024',
    }

    user2_dict = {
        'uid': 2,
        'identifier': u'soap',
        'irc': u'durden',
        'git': u'Tyler Durden <tyler@mayhem.net>'
    }

    # tests

    def test_addUser_new(self):
        d = self.db.users.addUser(identifier='soap',
                                  attr_type='subspace_net_handle',
                                  attr_data='Durden0924')
        def check_user(uid):
            def thd(conn):
                users_tbl = self.db.model.users
                users_info_tbl = self.db.model.users_info
                users = conn.execute(users_tbl.select()).fetchall()
                infos = conn.execute(users_info_tbl.select()).fetchall()
                self.assertEqual(len(users), 1)
                self.assertEqual(users[0].uid, uid)
                self.assertEqual(users[0].identifier, 'soap')
                self.assertEqual(len(infos), 1)
                self.assertEqual(infos[0].uid, uid)
                self.assertEqual(infos[0].attr_type, 'subspace_net_handle')
                self.assertEqual(infos[0].attr_data, 'Durden0924')
            return self.db.pool.do(thd)
        d.addCallback(check_user)
        return d

    def test_addUser_existing(self):
        d = self.insertTestData(self.user1_rows)
        d.addCallback(lambda _ : self.db.users.addUser(
                                  identifier='soapy',
                                  attr_type='IPv9',
                                  attr_data='0578cc6.8db024'))
        def check_user(uid):
            self.assertEqual(uid, 1)
            def thd(conn):
                users_tbl = self.db.model.users
                users_info_tbl = self.db.model.users_info
                users = conn.execute(users_tbl.select()).fetchall()
                infos = conn.execute(users_info_tbl.select()).fetchall()
                self.assertEqual(len(users), 1)
                self.assertEqual(users[0].uid, uid)
                self.assertEqual(users[0].identifier, 'soap') # not changed!
                self.assertEqual(len(infos), 1)
                self.assertEqual(infos[0].uid, uid)
                self.assertEqual(infos[0].attr_type, 'IPv9')
                self.assertEqual(infos[0].attr_data, '0578cc6.8db024')
            return self.db.pool.do(thd)
        d.addCallback(check_user)
        return d

    def test_addUser_race(self):
        def race_thd(conn):
            # note that this assumes that both inserts can happen "at once".
            # This is the case for DB engines that support transactions, but
            # not for MySQL.  so this test does not detect the potential MySQL
            # failure, which will generally result in a spurious failure.
            conn.execute(self.db.model.users.insert(),
                    uid=99, identifier='soap')
            conn.execute(self.db.model.users_info.insert(),
                    uid=99, attr_type='subspace_net_handle',
                    attr_data='Durden0924')
        d = self.db.users.addUser(identifier='soap',
                                  attr_type='subspace_net_handle',
                                  attr_data='Durden0924',
                                  _race_hook=race_thd)
        def check_user(uid):
            self.assertEqual(uid, 99)
            def thd(conn):
                users_tbl = self.db.model.users
                users_info_tbl = self.db.model.users_info
                users = conn.execute(users_tbl.select()).fetchall()
                infos = conn.execute(users_info_tbl.select()).fetchall()
                self.assertEqual(len(users), 1)
                self.assertEqual(users[0].uid, uid)
                self.assertEqual(users[0].identifier, 'soap')
                self.assertEqual(len(infos), 1)
                self.assertEqual(infos[0].uid, uid)
                self.assertEqual(infos[0].attr_type, 'subspace_net_handle')
                self.assertEqual(infos[0].attr_data, 'Durden0924')
            return self.db.pool.do(thd)
        d.addCallback(check_user)
        return d

    def test_addUser_existing_identifier(self):
        d = self.insertTestData(self.user1_rows)
        d.addCallback(lambda _ : self.db.users.addUser(
                                  identifier='soap',
                                  attr_type='telepathIO(tm)',
                                  attr_data='hmm,lye'))
        def cb(_):
            self.fail("shouldn't get here")
        def eb(f):
            f.trap(sa.exc.IntegrityError, sa.exc.ProgrammingError)
            pass # expected
        d.addCallbacks(cb, eb)
        return d

    def test_getUser(self):
        d = self.insertTestData(self.user1_rows)
        def get1(_):
            return self.db.users.getUser(1)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict, self.user1_dict)
        d.addCallback(check1)
        return d

    def test_getUser_multi_attr(self):
        d = self.insertTestData(self.user2_rows)
        def get1(_):
            return self.db.users.getUser(2)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict, self.user2_dict)
        d.addCallback(check1)
        return d

    def test_getUser_no_match(self):
        d = self.insertTestData(self.user1_rows)
        def get3(_):
            return self.db.users.getUser(3)
        d.addCallback(get3)
        def check3(none):
            self.assertEqual(none, None)
        d.addCallback(check3)
        return d

    def test_updateUser_existing_type(self):
        d = self.insertTestData(self.user1_rows)
        def update1(_):
            return self.db.users.updateUser(
                uid=1, attr_type='IPv9', attr_data='abcd.1234')
        d.addCallback(update1)
        def get1(_):
            return self.db.users.getUser(1)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict['IPv9'], 'abcd.1234')
            self.assertEqual(usdict['identifier'], 'soap') # no change
        d.addCallback(check1)
        return d

    def test_updateUser_new_type(self):
        d = self.insertTestData(self.user1_rows)
        def update1(_):
            return self.db.users.updateUser(
                uid=1, attr_type='IPv4', attr_data='123.134.156.167')
        d.addCallback(update1)
        def get1(_):
            return self.db.users.getUser(1)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict['IPv4'], '123.134.156.167')
            self.assertEqual(usdict['IPv9'], '0578cc6.8db024') # no change
            self.assertEqual(usdict['identifier'], 'soap') # no change
        d.addCallback(check1)
        return d

    def test_updateUser_identifier(self):
        d = self.insertTestData(self.user1_rows)
        def update1(_):
            return self.db.users.updateUser(
                uid=1, identifier='lye')
        d.addCallback(update1)
        def get1(_):
            return self.db.users.getUser(1)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict['identifier'], 'lye')
            self.assertEqual(usdict['IPv9'], '0578cc6.8db024') # no change
        d.addCallback(check1)
        return d

    def test_updateUser_both(self):
        d = self.insertTestData(self.user1_rows)
        def update1(_):
            return self.db.users.updateUser(
                uid=1, identifier='lye',
                attr_type='IPv4', attr_data='123.134.156.167')
        d.addCallback(update1)
        def get1(_):
            return self.db.users.getUser(1)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict['identifier'], 'lye')
            self.assertEqual(usdict['IPv4'], '123.134.156.167')
            self.assertEqual(usdict['IPv9'], '0578cc6.8db024') # no change
        d.addCallback(check1)
        return d

    def test_updateUser_race(self):
        def race_thd(conn):
            conn.execute(self.db.model.users_info.insert(),
                    uid=1, attr_type='IPv4',
                    attr_data='8.8.8.8')
        d = self.insertTestData(self.user1_rows)
        def update1(_):
            return self.db.users.updateUser(
                uid=1, attr_type='IPv4', attr_data='123.134.156.167',
                _race_hook=race_thd)
        d.addCallback(update1)
        def get1(_):
            return self.db.users.getUser(1)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict['identifier'], 'soap')
            self.assertEqual(usdict['IPv4'], '8.8.8.8')
            self.assertEqual(usdict['IPv9'], '0578cc6.8db024') # no change
        d.addCallback(check1)
        return d

    def test_update_NoMatch_identifier(self):
        d = self.insertTestData(self.user1_rows)
        def update3(_):
            return self.db.users.updateUser(
                uid=3, identifier='abcd')
        d.addCallback(update3)
        def get1(_):
            return self.db.users.getUser(1)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict['identifier'], 'soap') # no change
        d.addCallback(check1)
        return d

    def test_update_NoMatch_attribute(self):
        d = self.insertTestData(self.user1_rows)
        def update3(_):
            return self.db.users.updateUser(
                uid=3, attr_type='abcd', attr_data='efgh')
        d.addCallback(update3)
        def get1(_):
            return self.db.users.getUser(1)
        d.addCallback(get1)
        def check1(usdict):
            self.assertEqual(usdict['IPv9'], '0578cc6.8db024') # no change
        d.addCallback(check1)
        return d

    def test_removeUser_uid(self):
        d = self.insertTestData(self.user1_rows)
        def remove1(_):
            return self.db.users.removeUser(1)
        d.addCallback(remove1)
        def check1(_):
            def thd(conn):
                r = conn.execute(self.db.model.users.select())
                r = r.fetchall()
                self.assertEqual(len(r), 0)
            return self.db.pool.do(thd)
        d.addCallback(check1)
        return d

    def test_removeNoMatch(self):
        d = self.insertTestData(self.user1_rows)
        def check(_):
            return self.db.users.removeUser(uid=3)
        d.addCallback(check)
        return d
