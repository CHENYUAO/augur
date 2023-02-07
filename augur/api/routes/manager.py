#SPDX-License-Identifier: MIT
"""
Creates routes for the manager
"""


# TODO: Need to come back and fix this later

import logging
import time
import requests
import sqlalchemy as s
from sqlalchemy import exc
from flask import request, Response
import json
# from augur.config import AugurConfig
import os 
import traceback

from celery import group, chain

from augur.tasks.github import *
from augur.application.db.session import DatabaseSession
from augur.application.db.util import execute_session_query
from augur.application.db.models.augur_data import Repo, RepoGroup
from augur.application.config import AugurConfig 
from augur.tasks.db.refresh_materialized_views import *
from augur.tasks.git.facade_tasks import *
from augur.tasks.github.detect_move.tasks import detect_github_repo_move
from augur.tasks.init.celery_app import engine
from augur.tasks.github.releases.tasks import collect_releases
from augur.tasks.github.repo_info.tasks import collect_repo_info
from augur.tasks.init.celery_app import celery_app as celery
from augur.tasks.github.pull_requests.files_model.tasks import process_pull_request_files
from augur.tasks.github.pull_requests.commits_model.tasks import process_pull_request_commits

CELERY_GROUP_TYPE = type(group())
CELERY_CHAIN_TYPE = type(chain())

AUGUR_API_VERSION = 'api/unstable'

logger = logging.getLogger(__name__)

def create_routes(server):

    @server.app.route('/{}/add-repos'.format(AUGUR_API_VERSION), methods=['POST'])
    def add_repos():
        """ returns list of successfully inserted repos and repos that caused an error
            adds repos belonging to any user or group to an existing augur repo group
            'repos' are in the form org/repo, user/repo, or maybe even a full url 
        """
        # if authenticate_request(server.augur_app, request):
        group = request.json['group']
        repo_manager = Repo_insertion_manager(group, engine)
        group_id = repo_manager.get_org_id()
        if group_id == -1:
            return Response(status_code = 401, response = json.dumps({'error': "not existing repo_group"}))
        errors = {}
        errors['invalid_inputs'] = []
        errors['failed_records'] = []
        success = []
        repos = request.json['repos']
        for repo in repos:
            url = Git_string(repo)
            url.clean_full_string()
            try:
                url.is_repo()
                repo_name = url.get_repo_name()
                repo_parent = url.get_repo_organization()
            except ValueError:
                errors['invalid_inputs'].append(repo)
            else:   
                try:
                    repo_id = repo_manager.insert_repo(group_id, repo_parent, repo_name)
                except exc.SQLAlchemyError:
                    errors['failed_records'].append(repo_name)
                else: 
                    success.append(get_inserted_repo(group_id, repo_id, repo_name, group, repo_manager.github_urlify(repo_parent, repo_name)))
        status_code = 200
        summary = {'repos_inserted': success, 'repos_not_inserted': errors}
        summary = json.dumps(summary)
        # else:
        #     status_code = 401
        #     summary = json.dumps({'error': "Augur API key is either missing or invalid"})

        return Response(response=summary,
                        status=status_code,
                        mimetype="application/json")

    @server.app.route('/{}/create-repo-group'.format(AUGUR_API_VERSION), methods=['POST'])
    def create_repo_group():
        if authenticate_request(server.augur_app, request):
            group = request.json['group']
            repo_manager = Repo_insertion_manager(group, engine)
            summary = {}
            summary['errors'] = []
            summary['repo_groups_created'] = []

            if group == '':
                summary['errors'].append("invalid group name")
                return Response(response=summary, status=200, mimetype="application/json")
                
            try:
                group_id = repo_manager.get_org_id()
            except TypeError:
                try:
                    group_id = repo_manager.insert_repo_group()
                except TypeError:
                    summary['errors'].append("couldn't create group")
                else: 
                    summary['repo_groups_created'].append({"repo_group_id": group_id, "rg_name": group})
            else:
                summary['errors'].append("group already exists")

            summary = json.dumps(summary)
            status_code = 200
        else:
            status_code = 401
            summary = json.dumps({'error': "Augur API key is either missing or invalid"})

        return Response(response=summary, 
                        status=status_code, 
                        mimetype="application/json")

    @server.app.route('/{}/import-org'.format(AUGUR_API_VERSION), methods=['POST'])
    def add_repo_group():
        """ creates a new augur repo group and adds to it the given organization or user's repos
            takes an organization or user name 
        """
        if authenticate_request(server.augur_app, request):
            group = request.json['org']
            repo_manager = Repo_insertion_manager(group, engine)
            summary = {}
            summary['group_errors'] = []
            summary['failed_repo_records'] = []
            summary['repo_records_created'] = []
            group_exists = False
            try:
                #look for group in augur db
                group_id = repo_manager.get_org_id()
            except TypeError:
                #look for group on github
                if repo_manager.group_exists_gh():
                    try:
                        group_id = repo_manager.insert_repo_group()
                    except TypeError:
                        summary['group_errors'].append("failed to create group")
                    else:
                        group_exists = True
                else:
                    summary['group_errors'].append("could not locate group in database or on github")
            else:
                group_exists = True

            if group_exists:
                summary['group_id'] = str(group_id)
                summary['rg_name'] = group
                try:
                    repos_gh = repo_manager.fetch_repos()
                    repos_in_augur = repo_manager.get_existing_repos(group_id)
                    repos_db_set = set()
                    for name in repos_in_augur:
                        #repo_git is more reliable than repo name, so we'll just grab everything after the last slash 
                        name = (name['repo_git'].rsplit('/', 1)[1])
                        repos_db_set.add(name)
                    repos_to_insert = set(repos_gh) - repos_db_set

                    for repo in repos_to_insert:
                        try:
                            repo_id = repo_manager.insert_repo(group_id, group, repo)
                        except exc.SQLAlchemyError:
                            summary['failed_repo_records'].append(repo)
                        else:
                            summary['repo_records_created'].append(get_inserted_repo(group_id, repo_id, repo, group, repo_manager.github_urlify(group, repo)))
                except requests.ConnectionError:
                    summary['group_errors'] = "failed to find the group's child repos"
                    logger.debug(f'Error is: {e}.')
                except Exception as e: 
                    logger.debug(f'Error is: {e}.')

            status_code = 200
            summary = json.dumps(summary)
        else:
            status_code = 401
            summary = json.dumps({'error': "Augur API key is either missing or invalid"})

        return Response(response=summary,
                        status=status_code,
                        mimetype="application/json")
        
    @server.app.route('/{}/start_tasks'.format(AUGUR_API_VERSION), methods=['POST'])
    def start_repo_collection():
        repo_id = request.json['repo_id']
        with DatabaseSession(logger) as session:
            repo = session.query(Repo).filter(Repo.repo_id==repo_id).one()
            if not repo:
                summary = json.dumps({'error': "repo not exist!"})
                return Response(response=summary, status=100, mimetype="application/json")
            create_collection_task(repo=repo)
        return Response(status=200, mimetype="application/json")
 
    
    def get_inserted_repo(groupid, repoid, reponame, groupname, url):
        inserted_repo={}
        inserted_repo['repo_group_id'] = str(groupid)
        inserted_repo['repo_id'] = str(repoid)
        inserted_repo['repo_name'] = reponame
        inserted_repo['rg_name'] = groupname
        inserted_repo['url'] = url
        return inserted_repo

class Repo_insertion_manager():
    ROOT_AUGUR_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    def __init__(self, organization_name, database_connection):
        #self.initialize_logging()
        self.org = organization_name
        self.db = database_connection
        ## added for keys
        self._root_augur_dir = Repo_insertion_manager.ROOT_AUGUR_DIR
        self.augur_config = AugurConfig(logger, engine)
        ##########

    def get_existing_repos(self, group_id):
        """returns repos belonging to repogroup in augur db"""
        select_repos_query = s.sql.text("""
            SELECT repo_git from augur_data.repo
            WHERE repo_group_id = :repo_group_id
        """)
        select_repos_query = select_repos_query.bindparams(repo_group_id = group_id)
        result = self.db.execute(select_repos_query)
        return result.fetchall()

## This doesn't permit importing of an individual's repo, as they don't show up under "orgs"
#    def group_exists_gh(self):
#        url = url = "https://api.github.com/orgs/{}".format(self.org)
#        res = requests.get(url).json()
#        try:
#            if res['message'] == "Not Found":
#                return False
#        except KeyError:
#            return True

## Revised Version of Method
    def group_exists_gh(self):
        url = url = "https://api.github.com/orgs/{}".format(self.org)
        ## attempting to add key due to rate limiting
        gh_api_key = self.augur_config.get_value('Database', 'key')
        self.headers = {'Authorization': 'token %s' % gh_api_key}
        #r = requests.get(url=cntrb_url, headers=self.headers)
####### Original request code
#        res = requests.get(url).json()
########
        res = requests.get(url=url, headers=self.headers).json()
        try:
            if res['message'] == "Not Found":
                url = url = "https://api.github.com/users/{}".format(self.org) 
                res = requests.get(url=url, headers=self.headers).json()
                if res['message'] == "Not Found":
                    return False
        except KeyError:
            return True

    def insert_repo(self, orgid, given_org, reponame):
        with DatabaseSession(logger) as session:
            repogit = self.github_urlify(given_org, reponame)
            repo_data = {
                "repo_group_id": int(orgid),
                "repo_git": repogit,
                "repo_status": "New",
                "tool_source": 'API',
                "tool_version": "1.0",
                "data_source": "Git"
            }
            repo_unique = ["repo_git"]
            return_columns = ["repo_id"]
            result = session.insert_data(repo_data, Repo, repo_unique, return_columns, on_conflict_update=False)
            if not result:
                return None
            return result[0]["repo_id"]

    def insert_repo_with_cli(group_id, repos):
        with GithubTaskSession(logger) as session:
            controller = RepoLoadController(session)
            for repo in repos:
                repo_data = {}
                repo_data["url"] = repo
                repo_data["repo_group_id"] = group_id
                print(
                    f"Inserting repo with Git URL `{repo_data['url']}` into repo group {repo_data['repo_group_id']}")
                controller.add_cli_repo(repo_data)

    def github_urlify(self, org, repo):
        return "https://github.com/" + org + "/" + repo

    def get_org_id(self):
        with DatabaseSession(logger) as session:
            try:
                repo_group = session.query(RepoGroup).filter(RepoGroup.rg_name==self.org).one()
                return repo_group.repo_group_id
            except Exception as e:
                return -1
        
    def insert_repo_group(self):
        """creates a new repo_group record and returns its id"""
        insert_group_query = s.sql.text("""
            INSERT INTO augur_data.repo_groups(rg_name, rg_description, rg_website, rg_recache, rg_last_modified, rg_type, 
                tool_source, tool_version, data_source, data_collection_date)
            VALUES (:group_name, '', '', 1, CURRENT_TIMESTAMP, 'Unknown', 'Loaded by user', 1.0, 'Git', CURRENT_TIMESTAMP)
            RETURNING repo_group_id
        """)
        insert_group_query = insert_group_query.bindparams(group_name = self.org)
        result = self.db.execute(insert_group_query)
        row = result.fetchone()
        return row['repo_group_id']

    def fetch_repos(self):
        """uses the github api to return repos belonging to the given organization"""
        gh_api_key = self.augur_config.get_value('Database', 'key')
        self.headers = {'Authorization': 'token %s' % gh_api_key} 
        repos = []
        page = 1
        url = self.paginate(page)
        res = requests.get(url, headers=self.headers).json()
        while res:
            for repo in res:
                repos.append(repo['name'])
            page += 1
            res = requests.get(self.paginate(page)).json()
        return repos

## Modified pagination to account for github orgs that look like orgs but are actually users. 
    def paginate(self, page):
### Modified here to incorporate the use of a GitHub API Key
        gh_api_key = self.augur_config.get_value('Database', 'key')
        self.headers = {'Authorization': 'token %s' % gh_api_key}    
        url = "https://api.github.com/orgs/{}/repos?per_page=100&page={}"
        res = requests.get(url, headers=self.headers).json()
        if res['message'] == "Not Found":
            url = "https://api.github.com/users/{}/repos?per_page=100&page={}" 
            res = requests.get(url=url, headers=self.headers).json()
        return url.format(self.org, str(page))


        #r = requests.get(url=cntrb_url, headers=self.headers)
####### Original request code
#        res = requests.get(url).json()
########
        res = requests.get(url=url, headers=self.headers).json()



#        url = "https://api.github.com/orgs/{}/repos?per_page=100&page={}"
#        res = requests.get(url).json()
#        if res['message'] == "Not Found":
#            url = "https://api.github.com/users/{}/repos?per_page=100&page={}" 
#            res = requests.get(url).json()
#        return url.format(self.org, str(page))

def create_collection_task(repo):
    tasks_with_repo_domain = [detect_github_repo_move.si(repo.repo_git)]
    preliminary_tasks = group(*tasks_with_repo_domain)
    
    repo_info_tasks = []
    first_tasks_repo = group(collect_issues.si(repo.repo_git),collect_pull_requests.si(repo.repo_git))
    second_tasks_repo = group(collect_events.si(repo.repo_git),
        collect_github_messages.si(repo.repo_git),process_pull_request_files.si(repo.repo_git), process_pull_request_commits.si(repo.repo_git))
    repo_chain = chain(first_tasks_repo,second_tasks_repo)
    issue_dependent_tasks = [repo_chain]
    repo_task_group = group(
        *repo_info_tasks,
        chain(group(*issue_dependent_tasks),process_contributors.si()),
        generate_facade_chain(logger),
        collect_releases.si()
    )
    repo_collect_task = chain(repo_task_group, refresh_materialized_views.si())
    
    for tasks in [preliminary_tasks, repo_collect_task]:
        logger.info(f"Starting phase {tasks.__name__}")
        try:
            phaseResult = tasks.apply_async() 

            # if the job is a group of tasks then join the group
            if isinstance(tasks, CELERY_GROUP_TYPE): 
                with allow_join_result():
                    phaseResult.join()

        except Exception as e:
            #Log full traceback if a phase fails.
            logger.error(
            ''.join(traceback.format_exception(None, e, e.__traceback__)))
            logger.error(
                f"Phase {tasks.__name__} has failed during augur collection. Error: {e}")
            raise e


class Git_string():
    """ represents possible repo, org or username arguments """
    def __init__(self, string_to_process):
        self.name = string_to_process

    def clean_full_string(self):
        """remove trailing slash, protocol, and source if present"""
        org = self.name
        if org.endswith('/'):
            org = org[:-1]
        if org.startswith('https://'):
            org = org[8:]
            slash_index = org.find('/')
            org = org[slash_index+1:]
        if org.startswith('git://'):
            org = org[6:]
            slash_index = org.find('/') 
            org = org[slash_index+1:]
        self.name = org

    def is_repo(self):
        """test for org/repo or user/repo form"""
        slash_count = 0
        for char in self.name:
            if char == '/':
                slash_count += 1
        if slash_count == 1:
            return
        else:
            raise ValueError
        
    def get_repo_organization(self):
        org = self.name
        return org[:org.find('/')]

    def get_repo_name(self):
        repo = self.name
        return repo[repo.find('/')+1:]

def authenticate_request(augur_app, request):

    # do I like doing it like this? not at all
    # do I have the time to implement a better solution right now? not at all
    user = augur_app.config.get_value('Database', 'user')
    password = augur_app.config.get_value('Database', 'password')
    host = augur_app.config.get_value('Database', 'host')
    port = augur_app.config.get_value('Database', 'port')
    dbname = augur_app.config.get_value('Database', 'name')

    DB_STR = 'postgresql://{}:{}@{}:{}/{}'.format(
            user, password, host, port, dbname
    )

    operations_db = s.create_engine(DB_STR, poolclass=s.pool.NullPool)

    update_api_key_sql = s.sql.text("""
        SELECT value FROM augur_operations.augur_settings WHERE setting='augur_api_key';
    """)

    retrieved_api_key = operations_db.execute(update_api_key_sql).fetchone()[0]

    try:
        given_api_key = request.json['augur_api_key']
    except KeyError:
        return False

    if given_api_key == retrieved_api_key and given_api_key != "invalid_key":
        return True
    else:
        return False
