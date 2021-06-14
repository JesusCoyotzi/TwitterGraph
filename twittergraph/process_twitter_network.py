import argparse
import logging

from networkanalysis.network_analysis import TwitterNetwork
#import networkanalysis.network_analysis as nets


def parse_arguments():
  parser = argparse.ArgumentParser(description="Load and analysis twitter graphs")
  parser.add_argument('filename',help='Graph filename')
  parser.add_argument('attributes_filename',help='Nodes attributes filename')
  parser.add_argument('--top',default=10,type=int,help="Number of elements to print for statistics")
  parser.add_argument('--degree',default=10,type=int,help="Degree threshold for pruning, everythin below will be removed from graph ")
  parser.add_argument('--out-file',default='processed.csv',help='Filename for processed graph filename')
  parser.add_argument('--pagerank-filename',default='top_pagerank.csv',help ='Filename for file containing top nodes based on pagerank value ')
  parser.add_argument('--degree-filename',default='top_degree.csv',help ='Filename for file containing top nodes based on degree')
  return parser.parse_args()

def set_logging():
  """ Tiny logger for analysis """
  logger = logging.getLogger("NetworkAnalysis")
  logger.setLevel(logging.INFO)

  fmt = logging.Formatter("%(levelname)s %(funcName)s: %(message)s")

  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)
  ch.setFormatter(fmt)
  logger.addHandler(ch)

  fmt = logging.Formatter("%(asctime)s - %(levelname)s %(funcName)s: %(message)s")
  fh = logging.FileHandler("net_analysis.log")
  fh.setLevel(logging.DEBUG)
  fh.setFormatter(fmt)
  logger.addHandler(fh)

if __name__=="__main__":
  # Small driver program:
  # Initialization
  set_logging()
  args = parse_arguments()
  tw = TwitterNetwork(args.filename,args.attributes_filename)  

  # Get top n nodes by degree, connections in graph 
  _, top_deg = tw.get_net_degree(top=args.top)
  top_deg_df = tw.get_attr_slice(top_deg)

  # Most nodes in a social graph will have very few connections or edges
  # This is called degree and nodes with a very small degree are both
  # the most muereous and give very little information
  # Remove nodes with less than specified degree to make more manageable
  # In further processing
  tw.prune_nodes(args.degree)

  # Get pagerank and return list of top ids based on it
  pr, top_pgrnk_lst = tw.get_pagerank(top=args.top)
  top_pgrnk_df = tw.get_attr_slice(top_pgrnk_lst)
  top_pgrnk_df["pagerank"] = top_pgrnk_df.index.map(pr)
  
  # Save top nodes by degree and by pagerank to disk 
  top_pgrnk_df.to_csv(args.pagerank_filename)
  top_deg_df.to_csv(args.degree_filename)

  # Save processed graph to file
  if 'csv' in args.out_file:
    tw.save_adjlist(args.out_file)
  elif 'graphml' in args.out_file:
    tw.save_graphml(args.out_file)
  else:
    logger.error("Format not supported for file %s",args.out_file)


