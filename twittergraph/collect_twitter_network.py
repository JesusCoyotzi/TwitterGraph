import argparse 
import logging

from networkcollection.twitter_graph import TwitterGraph

def parse_arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument('user')
  parser.add_argument('--nodes', default="nodes.csv",help="Filename for nodes file")
  parser.add_argument('--edges', default="edges.csv",help="Filename for edges file")
  parser.add_argument('--user-cache',default="user_cache.txt", help="Filename for user cache file")
  parser.add_argument('--follows-cache',default="follow_cache.txt", help="Filename for follows cache file")
  return parser.parse_args()

def set_logging():
  """ Set logger for rest of operations"""
  logger = logging.getLogger("TwitterGraph")
  logger.setLevel(logging.DEBUG)

  fmt = logging.Formatter("%(asctime)s - %(levelname)s %(funcName)s: %(message)s")

  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)
  ch.setFormatter(fmt)
  logger.addHandler(ch)

  fh = logging.FileHandler("twitter_net.log")
  fh.setLevel(logging.DEBUG)
  fh.setFormatter(fmt)
  logger.addHandler(fh)

  return

if __name__ == "__main__":
  # Set up logging
  set_logging()
  args = parse_arguments()
  grph = TwitterGraph(nodes_filename=args.nodes,
          edges_filename=args.edges,
          user_cache_name=args.user_cache,
          follow_cache_name=args.follows_cache)
  #grph.get_friends(args.user)
  
  #f = grph.get_followers(args.user)
  #u = grph.get_users_from_ids(f)
  
  grph.make_network(args.user)
  
