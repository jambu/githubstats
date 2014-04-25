githubstats
===========

Simple python scripts to pull out stats using the github API

Dependencies
============

https://pypi.python.org/pypi/requests

Quickstart
==========
sudo pip install requests

cp config.sh.sample config.sh (Change the values there to input the correct credentials and filepaths)

source config.sh

python collect.py 

(currently, the code only pulls repos which shows up in this page https://github.com/search?q=created%3A%3E2014-01-01+stars%3A%3E2000&type=Repositories&ref=searchresults) This is to prevent high runtime of collect.py

after this script is done run the reports.

python report.py -h

python report.py

The csv files will be created in the project root (this can be changed by changing the report_path env variable)

Facts
=====

The numbers for top committers do not match with the graphs displayed in the github UI. However, it matches with the github contributors api call.

In the commits per hour report, I do not show the average but the number of commits to a repo in a particular hour of any day.
(Average means I have to divide by seven I guess (or I misunderstood the statement)

I have not used the statistics API of github even though some reports could have been generated with it.
It pulls only the last year's data.

TODO LIST
=========

Logging
Change the db queries from %s format to prevent sql injection
tests
