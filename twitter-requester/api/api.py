# -*- coding: utf-8 -*-
import requests
import json
from types import SimpleNamespace
from threading import Lock
import traceback
from . import keyring
from datetime import date
import threading
import time
import os

# General API Exception. Any API exception can be caught from it.

class ApiError(Exception):
    
    def __init__(self, message="Twitter API returned error code {}", code=000):
        if code != 000:
            self.message = message.format(code)
        else:
            self.message = message
        super().__init__(self.message)

# Rate Limit API exception code 429

class RateLimitError(ApiError):

    def __init__(self, message="Rate limit have been exhausted for the resource."):
        super().__init__(message=message)

# Forbidden API exception code 403

class ForbiddenError(ApiError):

    def __init__(self, message="Request was actively refused by API."):
        super().__init__(message=message)

# Not Found API exception code 404

class NotFoundError(ApiError):

    def __init__(self, message="Endpoint was not found."):
        super().__init__(message=message)

# Exception handler

def raiseError(code):
    if code == 429:
        raise RateLimitError()
    if code == 403:
        raise ForbiddenError()
    if code == 404:
        raise NotFoundError()
    raise ApiError(code=code)

""" Paginate a request until the number of pages is reached
or there are no more pages to be requested. """

class Paginator():

    def __init__(self, npages, url, key, parameters, call, next_field):
        self.npages = npages
        self.url = url
        self.key = key
        self.parameters = parameters
        self.call = call
        self.next_field = next_field

    def pages(self):
        page = 0
        while True:
            status = self.call(self.url, self.key, self.parameters)
            yield status
            time.sleep(0.1)
            page += 1
            if hasattr(status.meta, "next_token") and page != self.npages:           
                self.parameters[self.next_field] = status.meta.next_token
            else:
                break
            

# Manage get requests to Twitter API. It expects App authenticaton
# only.

class Api():

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(Api, cls).__new__(cls)
            return cls._instance

    # Setup default parameters that request should return.

    def __init__(self, keys):
        self.tweets = "id,text,created_at,author_id,public_metrics,referenced_tweets"
        self.users = "id,username,description,public_metrics,verified,created_at"
        self.expansions = "author_id"
        self.keys_user_timeline = keyring.Keyring(keys)
        self.keys_search_tweets = keyring.Keyring(keys)
        self.keys_full_search = keyring.Keyring(keys)
        self.keys_retweeters = keyring.Keyring(keys)
        self.keys_count = keyring.Keyring(keys)

    # Set the bearer token at the header of request. The bearer token 
    # allows more calls than the standart one.

    def auth(self, bearer_token):
        print(bearer_token)
        return {"Authorization": "Bearer {}".format(bearer_token)}

    # Perform the GET request to Twitter API, deserializing the JSON
    # response into a python object Status.

    def call(self, url, key, params):
        response = requests.request("GET", url, headers=self.auth(key), params=params) # GET request to URL endpoint
        if response.status_code != 200:
            raiseError(response.status_code)
        return json.loads(json.dumps(response.json()), object_hook=lambda d: SimpleNamespace(**d)) # Turns raw json into python object.

    # Limit handling of status pagination. It uses 'keyring.py' as an Object Pool to
    # perform calls up to the limit handling all exceptions and key reseting stuff.

    def limit_handler(self, paginator, keyring):
        paginator_pages = paginator.pages()
        while True:
            try:
                yield next(paginator_pages)
            except RateLimitError:
                now = time.time()
                print(str(threading.get_ident()) + " Key exhausted sleeping " + str(keyring.timer_key(paginator.key) - now))
                time.sleep(keyring.timer_key(paginator.key) - now)
                keyring.release(paginator.key)
                paginator.key = keyring.request()
                continue
            except ForbiddenError:
                continue
            except ApiError as e:
                #dirname = os.path.dirname('log-twitter-api.txt')
                #if not os.path.exists('logs'):
                    #os.makedirs('logs')
                #with open('logs/log-twitter-api.txt', 'w+') as log:
                    #log.write(str(date.today()) + ": Twitter API reported an error: " + str(e) + " \n")
                    #log.write(traceback.format_exc())
                raise e
            except StopIteration:
                keyring.release(paginator.key)
                break

    # Request to User Timeline endpoint. Check Twitter API documentation
    # for further details.

    def user_timeline(self, id, npages=-1, max_results=100, start_time=None, end_time=None, next_field="pagination_token"):
        parameters = dict()
        parameters['tweet.fields'] = self.tweets
        parameters['user.fields'] = self.users
        parameters['expansions'] = self.expansions
        parameters['max_results'] = max_results
        if start_time:
            parameters['start_time'] = start_time
        if end_time:
            parameters['end_time'] = end_time
        url = 'https://api.twitter.com/2/users/{}/tweets'.format(id)
        key = self.keys_user_timeline.request()
        return self.limit_handler(Paginator(npages, url, key, parameters, self.call, next_field), self.keys_user_timeline)

    # Request to search tweets endpoint on Twitter API
    
    def search_tweets(self, query, npages=1, start_time=None, end_time=None, max_results=100, next_field="next_token"):
        parameters = dict()
        parameters['query'] = query
        parameters['tweet.fields'] = self.tweets
        parameters['user.fields'] = self.users
        parameters['expansions'] = self.expansions
        parameters['max_results'] = max_results
        if start_time:
            parameters['start_time'] = start_time
        if end_time:
            parameters['end_time'] = end_time
        url = 'https://api.twitter.com/2/tweets/search/recent'
        key = self.keys_search_tweets.request()
        return self.limit_handler(Paginator(npages, url, key, parameters, self.call, next_field), self.keys_search_tweets)

    # Request to full-archive search endpoint on Twitter API
    
    def full_search(self, query, npages=1, start_time=None, end_time=None, max_results=100, next_field="next_token"):
        parameters = dict()
        parameters['query'] = query
        parameters['tweet.fields'] = self.tweets
        parameters['user.fields'] = self.users
        parameters['expansions'] = self.expansions
        parameters['max_results'] = max_results
        if start_time:
            parameters['start_time'] = start_time
        if end_time:
            parameters['end_time'] = end_time
        url = 'https://api.twitter.com/2/tweets/search/all'
        key = self.keys_full_search.request()
        return self.limit_handler(Paginator(npages, url, key, parameters, self.call, next_field), self.keys_full_search)

    # Request to retweeters endpoint on Twitter API
    
    def retweeters_of(self, id):
        parameters = dict()
        parameters['tweet.fields'] = self.tweets
        parameters['user.fields'] = self.users
        parameters['expansions'] = 'pinned_tweet_id'
        url = 'https://api.twitter.com/2/tweets/{}/retweeted_by'.format(id)
        key = self.keys_retweeters.request()
        return self.limit_handler(Paginator(1, url, key, parameters, self.call, "next_token"), self.keys_retweeters)

    # Request to count all endpoint on Twitter API
    
    def count(self, query, start_time=None, end_time=None, next_field="next_token"):
        parameters = dict()
        parameters['query'] = query
        if start_time:
            parameters['start_time'] = start_time
        if end_time:
            parameters['end_time'] = end_time
        url = 'https://api.twitter.com/2/tweets/counts/all'
        key = self.keys_count.request()
        return self.limit_handler(Paginator(-1, url, key, parameters, self.call, next_field), self.keys_count)