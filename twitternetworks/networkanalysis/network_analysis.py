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
    return 

  @staticmethod
  def read_node_list(filename):
    with open(filename,'r') as node_file:
      node_list = node_file.read().split()
    logger.info("Loaded %s nodes from %s",len(node_list),filename)
    # Go froms string to integer
    node_list = list(map(int,node_list))
    return node_list
 
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

  def set_node_names(self):
    """ Set twitter handle as name attribute for each node """
    name_df = self.attr['screen_name']
    attr_dic = name_df.to_dict()
    nx.set_node_attributes(self.net,attr_dic,name='username')
    return 
  
  def get_statistics(self,n=10):
    """ Compute basic statistics for graph, prints n top elements """
    self.get_net_degree(top=n)
    self.get_pagerank(top=n)
    return 

  def get_net_degree(self,top=10):
    """ Return sorted list of nodes based on degree also print top elements
    Also returns tops n ids based on degree"""
    sorted_nodes = sorted(self.net.degree, key=lambda x: x[1], reverse=True)
    top_list = []
    for i in range(top):
      deg = sorted_nodes[i][1]
      n = sorted_nodes[i][0]
      top_list.append(n)
      try:
        screen_name = self.attr.loc[n]['screen_name']
        logger.debug("%s node: %s|%s has %s degree",i,n,screen_name,deg)
      except KeyError as e:
        logger.warning("%s node not found in file",i)
        logger.warning("%s node not found in file",e)
        
    self.max_node = sorted_nodes[0]
    self.min_node = sorted_nodes[-1]
    logger.info("Largest degree node: %s",self.max_node)
    logger.info("Smallest degree node: %s",self.min_node)
    return self.net.degree , top_list 
     
  def get_pagerank(self,top=10):
    """Compute pagerank for network, return pagerank dict
        and also returns top nodes based on pageranks score"""
    logger.info("Getting pagerank")
    page_rank = nx.pagerank(self.net)
    sorted_page = sorted(page_rank.items(), key=lambda x: x[1], reverse=True)
    top_list = []
    for i in range(top):
      page = sorted_page[i][1]
      n = sorted_page[i][0]
      top_list.append(n)
      try:
        screen_name = self.attr.loc[n]['screen_name']
        logger.debug("%s node: %s|%s has pagerank %s",i,n,screen_name,page)
      except KeyError as e:
        logger.info("%s node has no id file (?)")
        logger.warning("%s node not found in file",e)
    return page_rank, top_list

  def get_attr_slice(self,part):
    """ Return a slice of the attributes dataframe based on node list"""
    output_slice  = self.attr.loc[part]
    return output_slice
    
  def slice_attr(self,update_df=False):
    """ Return attributers dataframe only for nodes actually on graph"""
    # May have more nodes on the attribute files than nodes in the graph
    node_lst = list(self.net.nodes)
    output_slice = self.attr.loc[node_lst]
    if update_df:
      # This effectively removes every node not in graph from attributes dataframe
      self.attr = output_slice 

    return output_slice

  def prune_nodes(self,prune_thr=5):
    """Remove all nodes with certain order threshold"""
    pruned_nodes = [ n for n,d in self.net.degree if d < prune_thr]
    logger.info("Removing %s nodes with degree < %s",len(pruned_nodes),prune_thr)
    self.net.remove_nodes_from(pruned_nodes)
    logger.info("Network has %s edges remaining",self.net.number_of_edges())
    return

  def remove_nodes(self,nodes):
    """ Remove nodes from network"""
    logger.info("Removing %s nodes from list",len(nodes))
    self.net.remove_nodes_from(nodes)
    logger.info("Network has %s edges remaining",self.net.number_of_edges())
    return
      
   
  def save_graphml(self,filename):
    """ Save graph as GraphML """ 
    nx.write_graphml_lxml(self.net,filename)
    return 
  
  def save_adjlist(self,filename):
    """ Save graph as adjlist """ 
    nx.write_adjlist(self.net,filename,delimiter=',')
    return

