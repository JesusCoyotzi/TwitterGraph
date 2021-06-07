import argparse
import logging

from networkanalysis.network_analysis import TwitterNetwork
#import networkanalysis.network_analysis as nets


def parse_arguments():
  parser = argparse.ArgumentParser(description="Load and analysis twitter graphs")
  parser.add_argument('filename',help='Graph filename')
  parser.add_argument('attributes_filename',help='Nodes attributes filename')
  
  return parser.parse_args()

def set_logging():
  """ Tiny logger for analysis """
  logger = logging.getLogger("NetworkAnalysis")
  logger.setLevel(logging.DEBUG)

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
  set_logging()
  args = parse_arguments()
  tw = TwitterNetwork(args.filename,args.attributes_filename)  

