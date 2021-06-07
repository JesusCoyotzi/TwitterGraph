import networkx as nx
import pandas as pd
import logging

logger = logging.getLogger("NetworkAnalysis")

def my_fun():
  print("Func")
  return 

class TwitterNetwork():
  """Thin frontend of Networkx for a Twitter social network"""
  def __init__(self,graph_filename,attr_filename):
    """ Load and set properties """
    self.load_graph(graph_filename)
    self.load_attributes(attr_filename)
    self.max_node, self.min_node = self.get_min_max_nodes()
    logger.info("Largest degree node: %s",self.max_node)
    logger.info("Smallest degree node: %s",self.min_node)
    return 
 
  def load_graph(self,filename):
    """ Load graph from adjacency list txt file"""
    logger.info("Reading adjacency list: %s",filename)
    self.net = nx.read_adjlist(filename,delimiter=',',nodetype=int)
    logger.info("Network has %s nodes",self.net.number_of_nodes())
    logger.info("Network has %s edges",self.net.number_of_edges())
    return
 
  def load_attributes(self,filename):   
    logger.info("Reading attributes file: %s",filename)
    self.attr = pd.read_csv(filename,index_col='id',lineterminator='\n')
    self.attr.index = self.attr.index.map(int)
    logger.info("Got %s nodes attributes" , len(self.attr))
    return

  def get_min_max_nodes(self,top=10):
    """ Get highest and lowest order node also print top 5 elemtes"""
    sorted_nodes = sorted(self.net.degree, key=lambda x: x[1], reverse=True)
    for i in range(top):
      deg = sorted_nodes[i][1]
      n = sorted_nodes[i][0]
      screen_name = self.attr.loc[n]['screen_name']
      logger.info("%s node: %s|%s has %s degree",i,n,screen_name,deg)
    return sorted_nodes[0], sorted_nodes[-1]
     
  def prune_nodes(self):
    """Remove all nodes with certain threshold"""
    pass
   
