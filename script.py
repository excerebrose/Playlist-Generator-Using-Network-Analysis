import os
import sys
import sqlite3
import community
import networkx as nx
import scipy

def pairwise(l):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    return list(zip(l[::2], l[1::2]))

global_db_data = dict()
global_tracklist = dict()
global_graph = nx.Graph()
global_communities = dict()
global_partition = dict()
node_mappings = dict()
mtx = None
sinking = None

def preprocess():
  ''' Generate dictionary from existing similars database '''
  global node_mappings
  unique_nodes = set()
  db = sqlite3.connect("lastfm_similars.db")
  with db:
    cursor = db.cursor()
    cursor.execute("SELECT * from similars_src")
    rows = cursor.fetchall()
    for row in rows:
      song_id = row[0]
      similar_songs = pairwise(row[1].split(","))
      global_db_data[song_id] = similar_songs
      # Add all the nodes to the unique nodes
      unique_nodes.add(song_id)
      for song in similar_songs:
        unique_nodes.add(song[0])
  db.close()
  # Create Node Mappings for indexing
  node_mappings = dict(zip(unique_nodes,range(len(unique_nodes))))


def generate_similarity_file(threshold=0.6):
  # Create Similarity Text File
  with open('similarity_graph.txt', 'w') as outfile:
    for k,v in global_db_data.items():
      for track in v:
        if float(track[1]) >= threshold:
          line = '{},{},{}\n'.format(node_mappings[k], node_mappings[track[0]], track[1])
          outfile.write(line)


def generate_track_meta():
  ''' Generate dictionary of tracknames that exist in the db nodes '''
  with open("unique_tracks.txt", 'r') as tracklist:
    for line in tracklist:
      track = line.strip().split('<SEP>')
      global_tracklist[track[0]] = track[2] + ' - ' + track[3]


def generate_graph(filename='similarity_graph.txt'):
  with open(filename) as infile:
    for line in infile:
      line = line.strip().split(',')
      global_graph.add_edge(int(line[0]), int(line[1]), weight=float(line[2]))


def generate_community(G=global_graph, threshold=0.60):
  # Compute the best partition
  global global_partition
  
  global_partition = community.best_partition(G)
  with open('partition.txt','w') as outfile:
    for k,v in global_partition.items():
        line = '{}, {}\n'.format(k,v)
        outfile.write(line)
        if v not in global_communities:
          global_communities[v] = []
        global_communities[v].append(k)        
  print('Theshold: {}'.format(threshold))
  print('Number of Communities: {}'.format(len(set(global_partition.values()))))
  print('Modularity: {}'.format(community.modularity(global_partition, G)))


def setupPP():
  global mtx
  global sinking
  N = len(node_mappings)
  mtx = nx.to_scipy_sparse_matrix(global_graph, nodelist=node_mappings.values(), format="coo")
  mtx = mtx.asformat('csr')
  # Matrix Normalisaton 
  rowSum = scipy.array(mtx.sum(axis=1)).flatten()
  rowSum[rowSum != 0] = 1./rowSum[rowSum != 0]
  invDiag = scipy.sparse.spdiags(rowSum.T, 0, N, N, format='coo')
  mtx = invDiag * mtx
  sinking = scipy.where(rowSum == 0)[0]


def PPR(v=None,alpha=0.85,max_iter=100, tol=1e-6):
  N = len(node_mappings) 
  x = scipy.repeat(1./N, N)
  if v is None:
    v = scipy.repeat(1./N, N)
  v /= v.sum()
  #power iteration:
  for _ in range(max_iter):
    xlast = x
    x = alpha*(x*mtx + sum(x[sinking])*v) + (1-alpha)*v
    if scipy.absolute(x-xlast).sum() < tol:
      scores = {}
      for k,v in node_mappings.items():
        scores[k] = x[v]
      return scores
  raise RuntimeError('Power iteration failed to converge in {} iterations.'.format(max_iter))


def gen_playlist():
  N = len(node_mappings)
  seed = input("Song seeds (seperated by ;) :")
  seed_raw = seed.strip().split(";")
  seed = []
  for tid,song in global_tracklist.items():
      for track in seed_raw:
          track = track.strip()
          if song == track:
              seed.append(node_mappings[tid])
  if len(seed) != len(seed_raw):
      print("Some songs were missing in the list of tracks")
  if len(seed) == 0:
      return
  discover_rate = float(input("Pick Variety rate from 0 to 1: "))
  listLength = int(input("Playlist length: "))
 
  v = scipy.repeat(discover_rate*0.01/float(N),N)
  for track in seed:
    for song in global_communities[global_partition[track]]:
      v[song] = 1./N
    for track in seed:
      v[track] = len(global_communities[global_partition[track]])/float(N)
            
  rank = PPR(v)
  playlist = sorted(rank, key=rank.get, reverse=True)
  scores = [rank[i] for i in playlist]
  unique_list = []
  i,j = 0,0
  while i < listLength:
      song = global_tracklist[playlist[j]]
      j += 1
      if song not in unique_list:
          i += 1
          unique_list.append(song)
          print(song)


if __name__ == '__main__':
  print("Serialising Database")
  preprocess()
  generate_similarity_file()
  print("Generating Graph & Running Community Partition")
  generate_graph()
  generate_community()
  print("Setup PageRank")
  setupPP()
  print("Generating Track Meta")
  generate_track_meta()
  while True:
    gen_playlist()

