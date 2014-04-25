import unittest
import os
import sqlite3
from collect import cursor, init_db, load_repos_data, update_user_location_data



class TestCollect(unittest.TestCase):

  def setUp(self):
    init_db()

  def testInitDB(self):
    tables = cursor.execute('select name from sqlite_master where type="table";')
    tables = tables.fetchall()
    tables = map(lambda x: x[0], tables)
    self.assertIn('git_users', tables)
    self.assertIn('git_repos', tables)
    self.assertIn('git_commits', tables)

  def testLoadReposData(self):

    repos = [{'id':1, 
              'name':'testRepo',
              'owner':{'id':1,'login':'testOwner'}
              }]
    load_repos_data(repos)
    test_repo = cursor.execute('select * from git_repos where id=1;').fetchall()
    self.assertTrue(len(test_repo) is 1)
    self.assertTrue(test_repo[0]['name']=='testRepo')
    load_repos_data(repos)
    test_repo = cursor.execute('select * from git_repos where id=1;').fetchall()
    self.assertTrue(len(test_repo) is 1)

  def testUpdateUserLocationData(self):
    cursor.execute("insert into git_users(id,login) values('1','testUser');")
    user_with_location = {'id':1, 'location':'Chennai, India'}
    users = cursor.execute("select * from git_users;")
    users= users.fetchall()
    self.assertTrue(users[0]['location'] is None)
    update_user_location_data(user_with_location)
    users = cursor.execute("select * from git_users;")
    users= users.fetchall()
    self.assertTrue(users[0]['location'] == 'Chennai, India')

  def tearDown(self):
    cursor.execute('drop table git_users;')
    cursor.execute('drop table git_repos;')
    cursor.execute('drop table git_commits;')


if __name__ == '__main__':
  unittest.main()