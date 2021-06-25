# !/bin/bash

# From raw data
python3 twittergraph/process_twitter_network.py edges-final.csv nodes-pruned.csv  --top 100 --pagerank-filename processed_pagerank.csv --degree-filename processed_degree.csv --out-file processed_elbueno.csv --degree 100

# For further refinement

python3 twittergraph/process_twitter_network.py nets/processed_elbueno.csv nodes-pruned.csv  --top 100 --pagerank-filename popcapped_pagerank.csv --degree-filename popcapped_degree.csv --out-file popcapped.csv --degree -2

python3 twittergraph/process_twitter_network.py nets/processed_elbueno.csv nodes-pruned.csv  --top 100 --pagerank-filename popcapped_pagerank.csv --degree-filename popcapped_degree.csv --out-file popcapped.csv --degree -2 --remove-filename nets/remove.txt 

