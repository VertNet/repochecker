import os
import json
import urllib
import logging

from google.appengine.api import urlfetch, mail, modules
import webapp2

__author__ = '@jotegui'

URLFETCH_DEADLINE = 60
MODULE_NAME = "tools-repochecker"
MODULE_URL = modules.get_hostname(module=MODULE_NAME)

IS_DEV = os.environ.get('SERVER_SOFTWARE', '').startswith('Development')

SENDER = "Resource Name Checker <repochecker@vertnet-portal.appspotmail.com>"

if IS_DEV:
    ADMINS = ["javier.otegui@gmail.com"]
else:
    ADMINS = [
        "javier.otegui@gmail.com",
        "dbloom@vertnet.org",
        "larussell@vertnet.org",
        "tuco@berkeley.edu"
    ]

ghb_url = "https://api.github.com"
cdb_url = "https://vertnet.cartodb.com/api/v2/sql"


def apikey(serv):
    """Return credentials file as a JSON object."""
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        '{0}.key'.format(serv))
    key = open(path, "r").read().rstrip()
    # logging.info("KEY %s" % key)
    return key


def get_all_repos():
    """Extract list of github_orgnames and github_reponames from CartoDB."""
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
    logging.info("Got {0} repos currently in CartoDB".format(len(all_repos)))

    result = []
    for repo in all_repos:
        result.append((repo['github_orgname'], repo['github_reponame']))

    return result


def check_failed_repos():
    """Check repository name consistency between CartoDB and GitHub."""
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
        url = '/'.join([ghb_url, 'orgs', orgname, 'repos'])
        urlfetch.set_default_fetch_deadline(URLFETCH_DEADLINE)
        urlfetch.make_fetch_call(rpc, url, headers=headers)

        repos[repo] = rpc

    for repo in sorted(repos):
        rpc = repos[repo]
        result = rpc.get_result()
        content = json.loads(result.content)
        logging.info("Got {0} repos for {1}".format(len(content), repo[0]))
        # When org is missing, API returns dict, not list
        try:
            repo_list = [x['name'] for x in content]
        except TypeError:
            failed_repos.append(repo)
        # When org exists but repo doesn't
        if repo_list is None or repo[1] not in repo_list:
            failed_repos.append(repo)

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

This is an automatic message sent by the Resource name checker tool to inform
you that the script found {0} name inconsistencies in some repositories between
CartoDB's resource_staging table and the name of organization and/or repository
on GitHub. These are the specific repositories that failed (names as in
CartoDB):

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
