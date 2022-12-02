"""Utility functions that are useful for several Github tasks"""
from typing import Any, List, Tuple
from augur.tasks.github.util.github_paginator import GithubPaginator, hit_api, process_dict_response
from httpx import Response
import logging
import json
import httpx


# This function adds a key value pair to a list of dicts and returns the modified list of dicts back
def add_key_value_pair_to_dicts(data: List[dict], key: str, value: Any) -> List[dict]:
    """Adds a key value pair to a list of dicts

    Args:
        data: list of dicts that is being modified
        key: key that is being added to dicts
        value: value that is being added to dicts

    Returns:
        list of dicts with the key value pair added
    """

    for item in data:

        item[key] = value

    return data

def get_owner_repo(git_url: str) -> Tuple[str, str]:
    """Gets the owner and repository names of a repository from a git url

    Args:
        git_url: the git url of a repository

    Returns:
        the owner and repository names in that order
    """
    split = git_url.split('/')

    owner = split[-2]
    repo = split[-1]

    if '.git' == repo[-4:]:
        repo = repo[:-4]

    return owner, repo


def parse_json_response(logger: logging.Logger, response: httpx.Response) -> dict:
    # try to get json from response
    if not response.text.replace(" ", ""):
        #Empty string response
        raise EOFError("Empty response could not be parsed!")

    try:
        return response.json()
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Error invalid return from GitHub. Response was: {response.text}. Error: {e}")
        return json.loads(json.dumps(response.text))


# Hit the endpoint specified by the url and return the json that it returns if it returns a dict.
# Returns None on failure.
def request_dict_from_endpoint(session, url, timeout_wait=10):
    #session.logger.info(f"Hitting endpoint: {url}")

    attempts = 0
    response_data = None
    success = False

    while attempts < 10:
        try:
            response = hit_api(session.oauths, url, session.logger)
        except TimeoutError:
            session.logger.info(
                f"User data request for enriching contributor data failed with {attempts} attempts! Trying again...")
            time.sleep(timeout_wait)
            continue

        if not response:
            attempts += 1
            continue
        
        try:
            response_data = response.json()
        except:
            response_data = json.loads(json.dumps(response.text))

        if type(response_data) == dict:
            err = process_dict_response(session.logger,response,response_data)

            
            #If we get an error message that's not None
            if err and err != GithubApiResult.SUCCESS:
                attempts += 1
                session.logger.info(f"err: {err}")
                continue

            #session.logger.info(f"Returned dict: {response_data}")
            success = True
            break
        elif type(response_data) == list:
            session.logger.warning("Wrong type returned, trying again...")
            session.logger.info(f"Returned list: {response_data}")
        elif type(response_data) == str:
            session.logger.info(
                f"Warning! page_data was string: {response_data}")
            if "<!DOCTYPE html>" in response_data:
                session.logger.info("HTML was returned, trying again...\n")
            elif len(response_data) == 0:
                session.logger.warning("Empty string, trying again...\n")
            else:
                try:
                    # Sometimes raw text can be converted to a dict
                    response_data = json.loads(response_data)

                    err = process_dict_response(session.logger,response,response_data)

                    #If we get an error message that's not None
                    if err and err != GithubApiResult.SUCCESS:
                        continue
                    
                    success = True
                    break
                except:
                    pass
        attempts += 1
    if not success:
        return None

    return response_data