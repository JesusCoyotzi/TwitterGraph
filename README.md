# Twitter Network 

This repository is a small collections of python scripts and libraries meant to collect and analyze twitter social networks. 

Twitter is a well known social network designed around micro messages. As it name implies the service itself organizes its followers into 
a network where every user is a node connected to other users they follow. 
Twitter also provides a rather feature rich API for developers and enthusiasts allowing you to do stuff like automatics posts, bots and 
social media analysis. 

Yet despite this, to the authors knowledge there are not many tools available for doing network analysis of this platform. 
Most people interested in analyzing their twitter followers on twitter end up rolling up their own solution. 
There is [Eleurent excellent twitter-graph](https://github.com/eleurent/twitter-graph) repository, much of the work here is based on his 
ideas, and this excellent [Article on how to do this on Java](https://towardsdatascience.com/building-a-network-graph-from-twitter-data-a5e7b8672e3)
Unfortunately the former is made with mostly the with authors Twitter in mind and visualization is done in JavaScript  and the second 
is written in Java. 

The purpose of this repo is to provide a small python library and collection of scripts to collect and analyze the social network from an user
on twitter, that generalize well to most use cases and provides some cli pipeline to do some simple operations on these graphs and it is written
on only on python since the author is the most knowledgeable on this language and there is a large amount of open source data science libraries
that can be leveraged for this purpose. 

## Dependencies
This is meant to work with python 3.5 and above and the following libraries:

+ python-twitter
+ networkx

## Modules
This repo is structure as follows. Under twitternetwork you can find networkcollection, this package is in charge of collecting and creating
the twittergraph from information gathered via the API, and networkanalysis which is meant to provide a simple pipeline for some basic analyzes 
of the resulting network, this section will briefly explain both packages.

### Networkcollection
A Twitter social network is based on "follows" an user can follow you, becoming a follower and likewise you can follow people, funnily 
twitter calls this "Friends" on their API but there is no such distinction on the UI you are either following or a follower.
The API has endpoints that can provide each user followers unique identifier or ID, these ids can be then "hydrated" to return 
the full user object including username, description or bio etcetera. 
For this repo the v1 version of the API is used, since there are several python wrappers built for it, but a v2 version already exits.

Unfortunately these endpoints are rate limited meaning that they only allow for a certain amount of request in a certain time frame, 
if exceeded a rate limited exception will be returned. The underlying python-twitter library used in this repo already has logic in place to 
handle this issues and automatically sleeps for the required time if the rate is exceeded. 

For this repo 2 endpoints are used: 
+ The users/lookup with 900 requests per 15 minutes and 100 users per request. 
+ The followers/ids with 15 requests per 15 minutes and up to 5000 ids per request.

Despite, as mentioned, rate limiting logic already in place from python-twitter library. This project limits to one request to the followers 
endpoint per minute, meaning 5000 ids per minute, and one requests of 100 ids to the the users endpoint every 3 seconds. This not only spreads
the load more evenly around the time window but also allow us to paralelize the process.

Since both operation, user hydration/lookup and followers collection are orthogonal we can set up a producer consumer system. We have one thread
the producer, querying the followers endpoint and returning the graph nodes and edges, these ids are then transferred to a queue and picked up by 
the consumer thread which is in charge of hydrating the ids. Program stops when all ids have been hydrated.

Another problem with the rate limiting is that makes the process very slow, so we would not want to try to query the endpoints more than we
 absolutely need to. But given the cyclical nature of these graphs there may be instances were we find the same user more than once. For this 
a very simple cache is implemented as a list on memory, if any id is found on a cache, it is not queried and every seen/processed ids is stored on said
cache. this is also stored on disk as a file so the process can be stopped and resumed without having to start from scratch. Given we query 
two endpoints, two caches are used one for the user data and one for the followers.

This is all put together on twitter network/collect_network.py cli utility, you specify any valid twitter user and the tool will collect every follower of that account and then repeat the process on every follower. The process, stops at degree 2 because the amount of users needed to lookup grows
exponentially with the separation degree. All ids collected are also hydrated simultaneously using the producer-consumer system described before.

Results are stored in a nodes.csv file which consists the information on users collected and an edges.csv file which is 
an adjacency list of the network: On every line you have the following format

```
account1_id,follower1_id,follower2_id,...
account2_id,follower4_id,follower7_id,...
...
```
As utilities this script also provides the ability to gather all followers of a single user and store them on a file an id list.
It can  also hydrate a list of ids stored on a plain text file and store as a csv file same usage as with making the full network.
These id lists is plain text has the following format, one id per line:

```
id_1
id_2
id_3
...
```

## Network Analysis
Network analysis, and graph theory for that matter, are complete and wide fields of mathematics intersection with computer science. As such
this little repo is not meant to provide a full set of tools for formal network analysis, moreover there are several other tools out there
such as networkx, a python package, and gephi, a full network analysis suite that do that better. 

Even so it is convenient to have a couple methods to post process the resulting networks using networkx, to prune redundant nodes and decrease
its size, this will simplify further analysis with other tools. This is the twitternetwork/networkanalysis module. A small pipeline is also proposed on twitternetwork/analyze_network.py 

This scripts takes the files produced by the other package and does the following:
First it removes all nodes with degree smaller than a threshold specified, in most social networks most nodes contribute
with very little information  as the have very few followers. So removing them may ease posterior analysis. 
Secondly it may be beneficial to remove some nodes, maybe some nodes do not provide relevant information to the graph, skew analysis too much
or simply should not be a part of the graph. If a list of nodes is supplied all of them will be remove from the network.
Now it computes page rank and creates a new CSV file where it list the top nodes both by degree, most edges, and by pagerank. 
Finally it saves the graph to disk again, for now this tool supports graphml and adjacency list format. And process can then be run iteratively to
clean the graph and get some insight into it before moving to your favorite network analysis tool.



