import unittest
import os
import sqlite3
from collect import init_db
from report import cursor, generate_top_committers_report
from datetime import datetime
import csv


class TestReport(unittest.TestCase):

  def setUp(self):
    init_db()

  def testTopCommitters(self):
    rows= cursor.execute('select * from git_users;');
    self.assertTrue(len(rows.fetchall()) is 0)
    rows= cursor.execute('select * from git_commits;');
    self.assertTrue(len(rows.fetchall()) is 0)
    rows= cursor.execute('select * from git_repos;');
    self.assertTrue(len(rows.fetchall()) is 0)

    for i in xrange(1,10):
      cursor.execute("insert into git_users(id,login) values(?,?)", (i, hex(i)))
      cursor.execute("insert into git_repos(id,name) values(?,?)", (i*100, hex(i*100)))
      k=(i*100)/(i+1)
      for j in xrange(1,k):
        cursor.execute("insert into git_commits(sha,committer_id,repo_id,datetime) values(?,?,?,?)", (hex(j+i*k),i,i*100,datetime.now()))
    generate_top_committers_report()

    with open(os.path.join(os.environ.get('reports_path'), 'top_committers.csv')) as csvreport:
      csvreader = csv.reader(csvreport)
      csvreader.next()
      for row in csvreader:
        original_value = int(row[1],16)
        computed_value = (original_value*100/(original_value+1)) - 1
        self.assertTrue(computed_value == int(row[2]))

  def tearDown(self):
    cursor.execute('drop table git_users;')
    cursor.execute('drop table git_repos;')
    cursor.execute('drop table git_commits;')

if __name__ == '__main__':
  unittest.main()