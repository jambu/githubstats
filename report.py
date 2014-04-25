import os, csv
import argparse
import sqlite3
from datetime import datetime

db_conn = sqlite3.connect(os.environ.get('db_path', ":memory:"))
db_conn.row_factory= sqlite3.Row
cursor = db_conn.cursor()

def get_csv_writer(csvfile):
  return csv.writer(csvfile,quoting=csv.QUOTE_MINIMAL)

def generate_top_committers_report():
  filepath = os.environ.get('report_path', '') + 'top_committers.csv'
  with open(filepath, 'w') as csvfile:
    
    writer = get_csv_writer(csvfile)
  
    top_committers = cursor.execute('''select r.name as repo,u.login as user, count.commit_count as top_commit_count from git_repos as r,
     git_users as u,(select repo_id, committer_id, count(*) as commit_count from git_commits group by repo_id,
     committer_id order by datetime asc) as count where r.id = count.repo_id and u.id=count.committer_id group by 
     count.repo_id having max(count.commit_count);''')
    
    writer.writerow(['Repository_name','Top committer','Number of commits'])
    for tc in top_committers.fetchall():
      writer.writerow([tc['repo'], tc['user'], tc['top_commit_count']])

def generate_project_commits_report(start_date, end_date):

  filepath = os.environ.get('report_path', '') + 'project_commits.csv'
  with open(filepath, 'w') as csvfile:
    
    writer = get_csv_writer(csvfile)
    
    project_commits = cursor.execute('''select r.name as repo, count(*) as commit_count from git_repos as r, 
      git_commits as c where r.id=c.repo_id and c.datetime >=? and c.datetime<? group by r.name''', (start_date, end_date))
    
    writer.writerow(['Repository_name','Start Date','End Date', 'Number of commits'])
    for pc in project_commits.fetchall():
      writer.writerow([pc['repo'], start_date, end_date, pc['commit_count']])

def generate_commits_per_hour_report():

  filepath = os.environ.get('report_path', '') + 'commits_per_hour.csv'
  with open(filepath, 'w') as csvfile:
    
    writer = get_csv_writer(csvfile)
    
    commits_per_hour = cursor.execute('''select r.name as repo, hour_data.hour as hour, hour_data.count as hour_count from git_repos as r,
   (select repo_id, strftime("%H", datetime) + 1 as hour, count(*) as count from git_commits group by repo_id, hour)
    as hour_data where r.id = hour_data.repo_id;''')
    
    writer.writerow(['Repository name', 'Hour of the day', 'Number of commits in the hour'])
    
    #TODO: Hours where there are no commits are not present in the sql output, should be added to the csv.
    for row in commits_per_hour.fetchall():
      writer.writerow([row['repo'], row['hour'], row['hour_count']])

def generate_commits_per_location_report(start_date, end_date, location):

  filepath = os.environ.get('report_path', '') + 'commits_per_location.csv'
  with open(filepath, 'w') as csvfile:
    writer = get_csv_writer(csvfile)
    
    commits_per_location = cursor.execute('''select u.location, count(*) as commit_count from 
      git_commits as c, git_users as u where u.id = c.committer_id and 
      u.location=? and c.datetime >=? and c.datetime<? group by u.location''', (location, start_date, end_date))
    
    writer.writerow(['Start Date','End Date', 'Location', 'Number of commits'])
    
    for cpl in commits_per_location.fetchall():
      writer.writerow([start_date, end_date, location, cpl['commit_count']])

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
        description="Report generator parser"
        )
  parser.add_argument('-r', '--reports', nargs='*', help='''Give the report names to be generated,
    This includes top-committers, project-commits, commits-per-hour, commits-per-location''')
  parser.add_argument('-s', '--start-date', help="YYYY-MM-DD")
  parser.add_argument('-e', '--end-date', help="YYYY-MM-DD")
  parser.add_argument('-l', '--location', help="Specify a location location for the commits per location report Ex. 'San Francisco' \
    (This is the default location)")
  parser.set_defaults(reports=['top-committers'])
  parser.set_defaults(location='San Francisco')
  parser.set_defaults(start_date='1970-01-01')
  parser.set_defaults(end_date=datetime.now().strftime("%Y-%m-%d"))


  args=parser.parse_args()

  if 'top-committers' in args.reports:
    generate_top_committers_report()
  if 'project-commits' in args.reports:
    generate_project_commits_report(args.start_date, args.end_date)
  if 'commits-per-hour' in args.reports:
    generate_commits_per_hour_report()
  if 'commits-per-location' in args.reports:
    generate_commits_per_location_report(args.start_date, args.end_date, args.location)

