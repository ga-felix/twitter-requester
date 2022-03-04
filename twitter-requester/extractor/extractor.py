# -*- coding: utf-8 -*-
from api import api
from datetime import datetime

class DataProcessor():

    def has_reference(self, tweet):
        return hasattr(tweet, "referenced_tweets")

    def has_meta(self, page):
        return hasattr(page, "meta")

    def has_data(self, page):
        return hasattr(page, "data")

    def process_page_data(self, page):
        authors = list(page.includes.users)
        if self.has_data(page):
            for index, tweet in enumerate(page.data):
                tweet.author = next((a for a in authors if a.id == tweet.author_id), None)
                tweet.referenced_tweet_id, tweet.referenced_tweet_author_id = 0, 0
                tweet.reference_type = ''

                if hasattr(tweet, "referenced_tweets"):
                    for ref in tweet.referenced_tweets:
                        ref_tweet = next((t for t in page.includes.tweets if t.id == ref.id), None)
                        tweet.referenced_tweet_id = ref_tweet.id
                        tweet.referenced_tweet_author_id = ref_tweet.author_id
                        tweet.reference_type = ref.type
                        self.tweets.append(tweet)
                else:
                    self.tweets.append(tweet)
        
        if self.has_meta(page):
            self.tweets[0].meta = page.meta
                
    def process_page(self, pages):
        self.tweets = list()
        for page in pages:
            self.process_page_data(page)
        return self.tweets

class QueryBuilder():

    def __init__(self):
        self.query = str()

    def write_from(self, user):
        if user != None:
            self.query += " from:{}".format(user)

    def write_retweets_of(self, user):
        self.query += " retweets_of:{}".format(user)

    def write_del_type(self, del_retweets, del_replies, del_quotes, del_verified):
        if del_retweets:
            self.query += " -is:retweet"
        if del_replies:
            self.query += " -is:reply"
        if del_quotes:
            self.query += " -is:quote"
        if del_verified:
            self.query += " -is:verified"

    def write_type_only(self, retweets_only, replies_only, quotes_only, verified):
        if retweets_only:
            self.query += " is:retweet"
        if replies_only:
            self.query += " is:reply"
        if quotes_only:
            self.query += " is:quote"
        if verified:
            self.query += " is:verified"

    def write_lang(self, lang):
        self.query += " lang:" + lang

    def write_keywords(self, keywords):
        temp_query = str()
        for keyword in keywords:
            temp_query += "(\"" + keyword + "\")" + " OR "
        self.query = temp_query[:len(temp_query) - 4]

    def build(self, keywords, lang="pt", retweets_only=False, replies_only=False, quotes_only=False, verified=False, del_retweets=False, del_replies=False, del_quotes=False, del_verified=False, retweets_of=None, from_user=None):
        self.write_keywords(keywords)
        self.write_lang(lang)
        if retweets_of != None:
            self.write_retweets_of(retweets_of)
            del_retweets, del_quotes = False, False
        self.write_from(from_user)
        self.write_type_only(retweets_only, replies_only, quotes_only, verified)
        self.write_del_type(del_retweets, del_replies, del_quotes, del_verified)
        return self.query
        
class Lookup():

    def __init__(self, keys):
        self.t_api = api.Api(keys)
        self.data = DataProcessor()
    
    def get_first_tweet(self, query, end_time=None, npages=-1, max_results=500):
        if end_time == None:
            end_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        tweets = self.data.process_page(self.t_api.full_search(query, start_time="2006-03-21T12:51:00Z", end_time=end_time, npages=npages, max_results=max_results))
        return tweets.sort(key=lambda x: x.id, reverse=True)

    def get_archive_tweets(self, query, start_time=None, end_time=None, npages=-1, max_results=500):
        return self.data.process_page(self.t_api.full_search(query, start_time=start_time, end_time=end_time, npages=npages, max_results=max_results))

    def get_recent_tweets(self, query, start_time=None, end_time=None, npages=-1, max_results=500):
        return self.data.process_page(self.t_api.search_tweets(query, start_time=start_time, end_time=end_time, npages=npages, max_results=max_results))

    def count_tweets(self, query, start_time=None, end_time=None):
        tweets = self.data.process_page(self.t_api.count(query, start_time=start_time, end_time=end_time))
        return tweets[0].meta.total_tweet_count