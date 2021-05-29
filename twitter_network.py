import twitter
import argparse 
import json
import csv 

import os
import getpass

import threading
import queue

import logging

logger = logging.getLogger(__name__)

def parse_arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument('user')
  parser.add_argument('--nodes',help="Filename for nodes file")
  parser.add_argument('--edges', help="Filename for edges file")
  parser.add_argument('--case', help="Filename for cache file")
  return parser.parse_args()

class twitter_graph():  

  def __init__(self,auto_sleep=False
               ,nodes_filename = "nodes.csv"
               ,edges_filename="edges.csv" 
               ,cache_filename="cache.txt"):
    # Getting credentials
    apk,aps,at,atk=self._get_credentials()
    # Initializing api 
    self.api = twitter.Api(consumer_key=apk,
                      consumer_secret=aps,
                      access_token_key=at,
                      access_token_secret=atk,
                      sleep_on_rate_limit=auto_sleep  )
    self._nodes_filename = nodes_filename
    self._edges_filename = edges_filename
                      
    self.attr_lst = ["id","name","screen_name","description",
              "followers_count","friends_count"]
      
    self.queue = queue.Queue(50) 
    self.stop = threading.Event()
    
    self.cache_filename = cache_filename
    self._make_nodes_headers()
    return

  def _get_credentials(self):
    api_key=os.environ.get("API_KEY",None)
    api_secret=os.environ.get("API_SECRET",None)
    access_token=os.environ.get("ACCESS_KEY",None)
    access_secret=os.environ.get("ACCESS_SECRET",None)
    
    if not api_key:
      api_key = getpass.getpass("API key")
    if not api_secret:
      api_secret = getpass.getpass()
    if not access_token:
      access_token = getpass.getpass()
    if not access_secret:
      access_secret = getpass.getpass()
    
    return api_key,api_secret,access_token,access_secret


  def save_cache(self,ids):
    with open(self.cache_filename, 'w') as cache:
      for i in ids:
        cache.write(i+'\n')
  
    return

  def load_cache(self):
    self.cache=""
    if not os.path.isfile(self.cache_filename):
      return

    with open(self.cache_filename, 'r') as cache:
        self.cache = cache.read()
    
    return

  def _make_nodes_headers(self):
    """Start users file for this run """
    with open(self._nodes_filename, 'w') as nodes_file:
      writer = csv.DictWriter(nodes_file, fieldnames=self.attr_lst)
      writer.writeheader()

    return

  def get_friends(self,username):
    friends = []
    try:
      friends = self.api.GetFriendIDs(screen_name=username,total_count=5000)
      logger.info("Found {} friends from {}".format(len(friends),username))
    except twitter.error.TwitterError as e: 
      logger.erorr("Failed. Error: {}".format(e))

    return friends

  def get_followers(self,username):
    followers = []
    try:
      user = self.api.UsersLookup(screen_name=username)[0]
      followers = self.api.GetFollowerIDs(user.id,total_count=5000)
      logger.info("Found {} followers from {}".format(len(followers),user.screen_name)) 
    except twitter.error.TwitterError as e: 
      logger.error("Failed. Error: {}".format(e))
   
    self.persist_followers(user,followers)

    return followers

  def get_followers_id(self,id):
    followers_ids = []
    try:
      followers_ids = self.api.GetFollowerIDs(id)
      logger.info("Found {} followers from {}".format(len(followers_ids),id))
      self.save_cache(id)
    except twitter.error.TwitterError as e: 
      logger.error("Failed. Error: {}".format(e))

    return followers_ids

  def persist_followers(self,usr,followers):
    adj_lst = [usr.id] + followers
    with open(self._edges_filename, 'a') as edges_file:
      writer = csv.writer(edges_file)
      writer.writerow(adj_lst)

    return

  def _chunks(self,lst,n=100):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
      yield lst[i:i+n]
     
  def get_users_from_ids(self,ids):
    """ Hydrate list of user ids"""
    # 300 request per 15 minuts, 100 user per request
    # So 3000 request per 15 minutes?
    ids_slices = self._chunks(ids)
    users = []
    for slc in ids_slices:
      logger.info("Looking up {} ids".format(len(slc)))
      try:
        slc_users = self.api.UsersLookup(slc,return_json=True)
        users.extend(slc_users)
      except twitter.error.TwitterError as e:
        logger.error("Failed. Error: {}".format(e))
  
      self.persist_users(users)
    return users
  
  def persist_users(self,users):
    clean_users = []
    for user in users:
      clean_users.append({k:user[k] for k in self.attr_lst})

    with open(self._nodes_filename, 'a') as nodes_file:
      writer = csv.DictWriter(nodes_file, fieldnames=self.attr_lst)
      writer.writerows(clean_users)
    #  json.dump(clean_users,nodes_file)

    return   

  def get_friends_id(self,id):
    try:
      friends_ids = self.api.GetFriendIDs(id)
      print("Found {} friends from {}".format(len(friends_ids),id))
    except twitter.error.TwitterError as e: 
      print("Failed. Error: {}".format(e))
      friends_ids = []
    return friends_ids
    
  def get_tweets(self,username):
    tweets = self.api.GetUserTimeline(screen_name=username,count=10)
    for t in tweets:
      print(t.text)    

  def make_network(self,root):
    """root is username to pivot"""
    edges=self.get_followers(root)

    # Instances 2 thread, one consults followers other hydrate users
    followers_th = threading.Thread(target=get_network, args=(edges,),daemon=True)
    users_th = threading.Thread(target=hydrate_ids, daemon=True)
    
    followers_th.start()
    users_th.start()

    return
    
  def get_network(self,ids):
    """ From pivots follows ids get all ids"""
    edges = ids 
    for e in edges:
      followers_list=self.get_followers_id(e.id)
      self.queue.put(followers_list)
      
    self.stop.set()
    
  def hydrate_ids(self):
    """Hydrate ids in parallel"""
    while self.stop.is_set() and not self.queue.empty():
      ids = self.queue.get()
      self.get_users_from_ids(ids)
    
    return     


if __name__ == "__main__":
  # Set up logging
  logger.setLevel(logging.INFO)
  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)
  fmt = logging.Formatter("%(asctime)s: %(message)s")
  ch.setFormatter = fmt
  logger.addHandler(ch)

  args = parse_arguments()
  grph = twitter_graph()
  #grph.get_friends(args.user)
  
  logger.info("Scraping network, pivot from %s",args.user)
  f = grph.get_followers(args.user)
  #u = grph.get_users_from_ids(f)
  
  #grph.make_network(args.user)
  
