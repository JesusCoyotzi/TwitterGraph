import twitter
import argparse 
import json
import csv 

import os
import getpass

import threading
import queue

import logging


def parse_arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument('user')
  parser.add_argument('--nodes', default="nodes.csv",help="Filename for nodes file")
  parser.add_argument('--edges', default="edges.csv",help="Filename for edges file")
  parser.add_argument('--user-cache',default="user_cache.txt", help="Filename for user cache file")
  parser.add_argument('--follows-cache',default="follow_cache.txt", help="Filename for follows cache file")
  return parser.parse_args()

class twitter_graph():  

  def __init__(self,auto_sleep=False,
               nodes_filename = "nodes.csv",
               edges_filename="edges.csv",
               user_cache_name="user_cache.txt",
               follow_cache_name="follow_cache.txt"):
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
    
    self.user_cache_name = user_cache_name
    self.follow_cache_name = follow_cache_name
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


  def save_cache(self,fname,ids):
    """ Save to cache files """
    fmt = "{}\n"
    with open(fname, 'a') as cache:
      if isinstance(ids,list):
        logger.debug("Saving %s ids to %s",len(ids),fname)
        for i in ids:
          cache.write(fmt.format(i))
      else:   
        logger.debug("Saving %s id to %s",ids,fname)
        cache.write(fmt.format(ids))
  
    return

  def load_cache(self,fname):
    if not os.path.isfile(fname):
      return []

    with open(fname, 'r') as cache:
        cache = cache.read()
        cache = cache.split() 
    return cache

  def _make_nodes_headers(self):
    """Start users file for this run """
    if os.path.isfile(self._nodes_filename):
      logger.info("Nodes files already exists won't overwrite")
      return

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
      logger.error("When getting followers for id {}".format(username))
      logger.error("Failed. Error: {}".format(e))
   
    return followers

  def get_followers_id(self,user_id):
    followers_ids = []
    try:
      followers_ids = self.api.GetFollowerIDs(user_id)
      logger.info("Found {} followers from {}".format(len(followers_ids),user_id))
    except twitter.error.TwitterError as e: 
      logger.error("When getting followers for id {}".format(user_id))
      logger.error("Failed. Error: {}".format(e))

    return followers_ids

  def persist_followers(self,usr,followers):
    adj_lst = [usr] + followers
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
      friends_ids = self.api.GetFriendIDs(user_id)
      print("Found {} friends from {}".format(len(friends_ids),user_id))
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
    # Can't add pivot/root to cache else won't start on secon runs
    edges=self.get_followers(root)
    logger.info("Loading caches")
    self.user_cache = self.load_cache(self.user_cache_name)
    self.follow_cache = self.load_cache(self.follow_cache_name)
    
    # Instances 2 thread, one consults followers other hydrate users
    followers_th = threading.Thread(target=self.get_network, args=(edges,),daemon=False)
    users_th = threading.Thread(target=self.hydrate_ids, daemon=False)
    
    logger.info("Starting thread")
    followers_th.start()
    users_th.start()
    
    followers_th.join()
    users_th.join()

    return
    
  def get_network(self,edges):
    """ From pivots follows ids get all ids"""
    for e in edges:
      if str(e) in self.follow_cache:
        logger.info("ID %s already on followers cache",e)
        continue
      # Get followers from each edge
      followers_list=self.get_followers_id(e)
      # Add to hydration queue 
      self.queue.put(followers_list)
      # Save to cache and persists
      self.save_cache(self.follow_cache_name,e) 
      self.persist_followers(e,followers_list)

    # Stop when everythin is done
    logger.info("All finished stop threads")
    self.stop.set()
    
  def hydrate_ids(self):
    """Hydrate ids in parallel"""
    logger.info("Starting user scraping")
    while not self.stop.is_set() or not self.queue.empty():
      # Queue stores list of ids not individual ids
      try:
        ids = self.queue.get(timeout=10)
      except queue.Empty as e:
        # In case queue is empty before stop is set
        logger.debug("Queue is empty for more than 10 secs")
        continue
      new_ids = set(ids) - set(self.user_cache)
      new_ids_lst = list(new_ids)
      logger.info("Found %s ids not in cache",len(new_ids))
      users = self.get_users_from_ids(new_ids_lst)
      # Persist users and cache 
      self.save_cache(self.user_cache_name,new_ids_lst)
      self.persist_users(users)

    logger.info("User scraping finished") 
    return     


if __name__ == "__main__":
  # Set up logging
  logger = logging.getLogger("Networks")
  logger.setLevel(logging.DEBUG)

  fmt = logging.Formatter("%(asctime)s: %(message)s")

  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)
  ch.setFormatter(fmt)
  logger.addHandler(ch)

  fh = logging.FileHandler("twitter_net.log")
  fh.setLevel(logging.DEBUG)
  fh.setFormatter(fmt)
  logger.addHandler(fh)

  args = parse_arguments()
  grph = twitter_graph(nodes_filename=args.nodes,
          edges_filename=args.edges,
          user_cache_name=args.user_cache,
          follow_cache_name=args.follows_cache)
  #grph.get_friends(args.user)
  
  logger.info("Scraping network, pivot from %s",args.user)
  #f = grph.get_followers(args.user)
  #u = grph.get_users_from_ids(f)
  
  grph.make_network(args.user)
  
