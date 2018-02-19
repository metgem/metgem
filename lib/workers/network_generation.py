import itertools

import numpy as np
import multiprocessing as mp

from pyteomics import mgf

from .base_worker import BaseWorker  
    
    
class NetworkVisualizationOptions:
    """Class containing Network visualization options.

    Attributes:
        top_k (int): Maximum numbers of edges for each nodes in the network. Default value = 10
        pairs_min_cosine (float): Minimum cosine score for network generation. Default value = 0.65
        max_connected_nodes (int): Maximum size of a Network cluster. Default value = 1000

    """
    def __init__(self):
        self.top_k = 10 # Maximum numbers of edges for each nodes in the network
        self.pairs_min_cosine = 0.65 # Minimum cosine score for network generation
        self.max_connected_nodes = 1000


    def setValues(self, options):
        """Set the values passed in arguments

        Args :
            options (tulpe): list of options values in the following order
                option[0] = top_k
                option[1] = pairs_min_cosine
                option[2] = max_connected_nodes

        """
        self.top_k = options[0]
        self.pairs_min_cosine = options[1]
        self.max_connected_nodes = options[2]
        
    
def generate_network(scores_matrix, spectra, options, use_self_loops=True):
    interactions = []
    
    num_spectra = len(spectra)
    
    np.fill_diagonal(scores_matrix, 0)
    triu = np.triu(scores_matrix)
    triu[triu<=options.pairs_min_cosine] = 0
    for i in range(num_spectra):
        # indexes = np.argpartition(triu[i,], -options.top_k)[-options.top_k:] # Should be faster and give the same results
        indexes = np.argsort(triu[i,])[-options.top_k:]
        indexes = indexes[triu[i, indexes] > 0]
            
        for index in indexes:
            interactions.append((i, index,
                spectra[i].mz_parent-spectra[index].mz_parent, triu[i, index]))
    
    interactions = np.array(interactions, dtype=[('Source', int), ('Target', int), ('Delta MZ', np.float32), ('Cosine', np.float32)])
    interactions = interactions[np.argsort(interactions, order='Cosine')[::-1]]

    # Top K algorithm, keep only edges between two nodes if and only if each of the node appeared in each other’s respective top k most similar nodes
    mask = np.zeros(interactions.shape[0], dtype=bool)
    for i, (x, y, _, _) in enumerate(interactions):
        x_ind = np.where(np.logical_or(interactions['Source']==x, interactions['Target']==x))[0][:options.top_k]
        y_ind = np.where(np.logical_or(interactions['Source']==y, interactions['Target']==y))[0][:options.top_k]
        if (x in interactions[y_ind]['Source'] or x in interactions[y_ind]['Target']) \
          and (y in interactions[x_ind]['Source'] or y in interactions[x_ind]['Target']):
            mask[i] = True
    interactions = interactions[mask]
    
    # Add selfloops for individual nodes without neighbors
    if use_self_loops:
        unique = set(itertools.chain.from_iterable((x['Source'], x['Target']) for x in interactions))
        selfloops = set(range(0, triu.shape[0])) - unique
        size = interactions.shape[0]
        interactions.resize((size + len(selfloops)))
        interactions[size:] = [(i, i, 0., 1.) for i in selfloops]

    return interactions