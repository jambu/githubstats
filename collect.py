import os, time

import requests
from requests.auth import HTTPBasicAuth
import sqlite3

from parse_link_header import parse_link_value

db_conn = sqlite3.connect(os.environ.get('db_path', ":memory:"))
db_conn.row_factory= sqlite3.Row
cursor = db_conn.cursor()

def init_db():
  cursor.execute('''create table if not exists git_repos(id integer PRIMARY KEY,
                                                         name text, 
                                                         owner_id integer,
                                                         owner_login text,
                                                         FOREIGN KEY(owner_id) REFERENCES git_users(id));''')

  cursor.execute('''CREATE INDEX IF NOT EXISTS owner_id_index ON git_repos(owner_id);''')

  cursor.execute('''create table if not exists git_users(id integer PRIMARY KEY,
                                                         login text,
                                                         location text);''')

  cursor.execute('''create table if not exists git_commits(sha text PRIMARY KEY,
                                                           datetime text,
                                                           committer_id integer,
                                                           repo_id integer,
                                                           FOREIGN KEY(committer_id) REFERENCES git_users(id),
                                                           FOREIGN KEY(repo_id) REFERENCES git_repos(id)); ''')
  cursor.execute('''CREATE INDEX IF NOT EXISTS committer_id_index ON git_commits(committer_id);''')
  cursor.execute('''CREATE INDEX IF NOT EXISTS repo_id_index ON git_commits(repo_id);''')
  #cursor.execute('''insert into git_repos values (2332, "ddd", 323, "sdsdf");''');
  #a= cursor.execute('''select * from git_repos;''')
  db_conn.commit()
  
def load_repos_data(api_result):

  for repo in api_result:
      try:
        cursor.execute("INSERT INTO git_repos VALUES(%s,'%s',%s,'%s');" % (repo['id'],
                                                                      repo['name'],
                                                                      repo['owner']['id'],
                                                                      repo['owner']['login']))
      except sqlite3.IntegrityError:
        #Already the record exists from previous runs
        pass
  db_conn.commit()

def load_commit_data(api_result, repo_id):

  for commit in api_result:

      try:
        #strangely this field is null for certain commits.
        if commit['committer']:
          cursor.execute("INSERT INTO git_commits VALUES('%s','%s',%s,%s);" % (commit['sha'],
                                                                      commit['commit']['committer']['date'],
                                                                      commit['committer']['id'],
                                                                      repo_id))
      except sqlite3.IntegrityError:
        #Already the record exists from previous runs
        pass
  db_conn.commit()

def load_users_data(api_result):

  for user in api_result:
      try:
        cursor.execute("INSERT INTO git_users(id, login) VALUES(%s,'%s');" % (user['id'],
                                                                            user['login']))
      except sqlite3.IntegrityError:
        #Already the record exists from previous runs
        pass
  db_conn.commit()

def update_user_location_data(user):

  #Not every user updates his location
  if user.get('location'):
    cursor.execute("UPDATE git_users set location ='%s' WHERE id=%s;" % (user['location'],
                                                                                user['id']))
    db_conn.commit()

def get_auth():
  guser = os.environ.get('github_username', '')
  gpass = os.environ.get('github_password', '')
  if not guser or not gpass:
    return
  return HTTPBasicAuth(guser,gpass)

def get_req(path):
  result = requests.get(path, auth=get_auth())
  if result.status_code == requests.codes.ok:
    return result
  
  if result.status_code == 403 and int(result.headers['X-RateLimit-Remaining']) == 0:
    sleep_untill_rate_limit(result)
    #retry the same path after sleeping
    return get_req(path)
  else:
    result.raise_for_status()


def get_next_page_link(link_header):
  if not link_header:
    return

  header_dict = parse_link_value(link_header)
  for url, params in header_dict.iteritems():
    if params['rel'] == 'next':
      return url
  return

def sleep_untill_rate_limit(result):
  current_time = int(time.time())
  time_to_wake = int(result.headers['X-RateLimit-Reset'])
  time.sleep(time_to_wake - current_time)

def fetch_data_from_api(starting_page, callback_func):
  next_page = starting_page

  while next_page:
    print next_page
    result = get_req(next_page)
    callback_func(result.json())
    
    next_page = get_next_page_link(result.headers.get('link', None))


def fetch_and_load_data():
  base_url = 'https://api.github.com/'

  #Runtime for all repos will take long and will exceed rate limit since,
  #Location field is needed which is found only in the User api call.
  #Other option is to load all the users(through the list users api call) instead of making an api call for each user. 
  #This will exceed rate limits too since I am expecting number of users to be large.

  #repos_url = base_url + 'repositories?sort=created&direction=asc'
  #fetch_data_from_api(repos_url, load_repos_data)

  popular_repos_url = base_url + 'search/repositories?q=created:>2014-01-01+stars:>2000'
  fetch_data_from_api(popular_repos_url, lambda x: load_repos_data(x['items']))

  git_repos = cursor.execute('SELECT id, name, owner_login from git_repos;')
  for r in git_repos.fetchall():
    repo_contributors_url = base_url + 'repos/%s/%s/contributors' % (r['owner_login'], r['name'])
    fetch_data_from_api(repo_contributors_url, load_users_data)
    
    repo_commit_url = base_url + 'repos/%s/%s/commits' % (r['owner_login'], r['name'])
    fetch_data_from_api(repo_commit_url, lambda x: load_commit_data(x, r['id']))

  git_users = cursor.execute('SELECT id from git_users;')
  for u in git_users.fetchall():
    users_url = base_url + 'user/%s' % (u['id'])
    fetch_data_from_api(users_url, update_user_location_data)




if __name__ == '__main__':
  init_db()
  fetch_and_load_data()
 