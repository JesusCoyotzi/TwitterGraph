import argparse 
import logging

from networkcollection.twitter_graph import TwitterGraph

import sys

def parse_arguments():
  parser = argparse.ArgumentParser(description="Program to collect social networks via twitter api and associated utilities")
  parser.add_argument('--nodes', default="nodes.csv",help="File to store node information")
  parser.add_argument('--edges', default="edges.csv",help="File for adjacency list, edge information")
  parser.add_argument('--user-cache',default="user_cache.txt", help="Filename for user cache file")
  parser.add_argument('--follows-cache',default="follow_cache.txt", help="Filename for follows cache file")
  
  subparser = parser.add_subparsers(title="Subcommands",description='Valid commands',dest='cmd')

  net_parser = subparser.add_parser('make-network',help='Create a graph from a twitter social network from certain pivot')
  net_parser.add_argument('pivot',help='User to pivot/start graph from ')

  follower_parser = subparser.add_parser('get-followers',help='Get followers for some arbitrary account')
  follower_parser.add_argument('user',help='User to get followers from')
  follower_parser.add_argument('--followers-file', default='ids.txt',help="Files to store collected ids")

  hydrate_parser = subparser.add_parser('hydrate-ids', help='Hydrate lists of ids and stores them on nodes file')
  hydrate_parser.add_argument('ids_file', metavar='ids-file', help="File with list of ids to hydrate ")

  args = parser.parse_args()
  return args

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
  #sys.exit(1)
  grph = TwitterGraph(nodes_filename=args.nodes,
          edges_filename=args.edges,
          user_cache_name=args.user_cache,
          follow_cache_name=args.follows_cache)

  
  if args.cmd == 'get-followers':
    grph.load_caches()
    follows = grph.get_followers(args.user,max_count=None)
    grph.save_ids(args.followers_file,follows)
  elif args.cmd == 'hydrate-ids':
    grph.load_caches()
    ids = grph.read_ids(args.ids_file)
    usrs = grph.get_users_from_ids(ids) 
#    grph.persist_users(usrs)
  elif args.cmd == 'make-network':
    grph.make_network(args.pivot)

  
