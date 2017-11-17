#!/usr/bin/env python
# -*- coding: utf-8 -*-
# The line above is to signify that the script contains utf-8 encoded characters.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Adapted from https://github.com/VertNet/bigquery

__author__ = "Javier Otegui"
__contributors__ = "Javier Otegui, John Wieczorek"
__copyright__ = "Copyright 2017 vertnet.org"
__version__ = "repochecker.py 2017-11-16T21:11-03:00"

import os
import json
import urllib
import logging

from google.appengine.api import urlfetch, mail, modules
import webapp2

URLFETCH_DEADLINE = 60
MODULE_NAME = "tools-repochecker"
MODULE_URL = modules.get_hostname(module=MODULE_NAME)

IS_DEV = os.environ.get('SERVER_SOFTWARE', '').startswith('Development')

SENDER = "Resource Name Checker <repochecker@vertnet-portal.appspotmail.com>"

if IS_DEV:
    ADMINS = ["tuco@berkeley.edu"]
else:
    ADMINS = [
        "dbloom@vertnet.org",
        "tuco@berkeley.edu"
    ]

ghb_url = "https://api.github.com"
cdb_url = "https://vertnet.cartodb.com/api/v2/sql"

def apikey(serv):
    """Return credentials file as a JSON object."""
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        '{0}.key'.format(serv))
    key = open(path, "r").read().rstrip()
    return key

def get_all_repos():
    """Extract list of github_orgnames and github_reponames from Carto."""
    query = "select github_orgname, github_reponame from resource_staging"
    query += " where ipt is true and networks like '%VertNet%';"
    vals = {
        'api_key': apikey('cdb'),
        'q': query
    }
    data = urllib.urlencode(vals)
    urlfetch.set_default_fetch_deadline(URLFETCH_DEADLINE)
    result = urlfetch.fetch(url=cdb_url, payload=data, method=urlfetch.POST)

    all_repos = json.loads(result.content)['rows']
    logging.info("Got {0} repos currently in Carto".format(len(all_repos)))

    result = []
    for repo in all_repos:
        result.append((repo['github_orgname'], repo['github_reponame']))

    return result

def check_failed_repos():
    """Check repository name consistency between Carto and GitHub."""
    failed_repos = []
    all_repos = get_all_repos()
    repos = {}
    headers = {
        'User-Agent': 'VertNet',  # Authenticate as VertNet
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token {0}'.format(apikey('gh'))
    }

    for repo in all_repos:
        orgname = repo[0]
        reponame = repo[1]

        if orgname is None or reponame is None:
            failed_repos.append(repo)
            continue

        rpc = urlfetch.create_rpc()
        url = '/'.join([ghb_url, 'repos', orgname, reponame])
#        print 'url: %s' % url
        urlfetch.set_default_fetch_deadline(URLFETCH_DEADLINE)
        urlfetch.make_fetch_call(rpc, url, headers=headers)
        repos[repo] = rpc
        result = rpc.get_result()
        content = json.loads(result.content)
        try:
            name = content['name']
        except KeyError, e:
            logging.info('GitHub repository %s not found' % url)
#            print 'KeyError: %s' % e 
            failed_repos.append((orgname,reponame))

#     orgname='pbdb-feedback'
#     reponame='test'
#     rpc = urlfetch.create_rpc()
#     url = '/'.join([ghb_url, 'repos', orgname, reponame])
#     print 'url: %s' % url
#     urlfetch.set_default_fetch_deadline(URLFETCH_DEADLINE)
#     urlfetch.make_fetch_call(rpc, url, headers=headers)
#     repos[repo] = rpc
#     result = rpc.get_result()
#     content = json.loads(result.content)
#     try:
#         name = content['name']
#     except KeyError, e:
#         print 'KeyError: %s' % e 
#         print 'content: %s' % content
#         failed_repos.append((orgname,reponame))
# 
#     orgname='test-feedback'
#     reponame='test'
#     rpc = urlfetch.create_rpc()
#     url = '/'.join([ghb_url, 'repos', orgname, reponame])
#     print 'url: %s' % url
#     urlfetch.set_default_fetch_deadline(URLFETCH_DEADLINE)
#     urlfetch.make_fetch_call(rpc, url, headers=headers)
#     repos[repo] = rpc
#     result = rpc.get_result()
#     content = json.loads(result.content)
#     try:
#         name = content['name']
#     except KeyError, e:
#         print 'KeyError: %s' % e 
#         print 'content: %s' % content
#         failed_repos.append((orgname,reponame))

    return failed_repos

class RepoChecker(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        logging.info("Checking consistency of repository names.")
        failed_repos = check_failed_repos()

        res = {
            'result': None
        }

        if len(failed_repos) > 0:
            res['failed_repos'] = failed_repos
            res['result'] = "error"
            logging.error("There were issues in the repository name matching.")

            error_message = "\n".join([", ".join(x) for x in failed_repos])
            mail.send_mail(
                sender=SENDER,
                to=ADMINS,
                subject="Resource name checker failed",
                body="""
Hey there,

This is an automatic message sent by the Resource name checker to inform
you that the script found {0} name inconsistencies in some repositories between
the Carto resource_staging table and the name of organization and/or repository
on GitHub. These are the specific repositories that failed (names as in
Carto):

{1}

Please, fix them and then go to {2} to restart the process.

Thank you!
""".format(len(failed_repos), error_message, "http://%s/" % MODULE_URL))

        else:
            res['result'] = "success"
            logging.info("The consistency check could not find any issue.")

        self.response.write(json.dumps(res))

app = webapp2.WSGIApplication([
    ('/', RepoChecker),
    ('/repochecker', RepoChecker)
], debug=True)
