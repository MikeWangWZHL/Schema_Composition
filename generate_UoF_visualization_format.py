from __future__ import annotations

import json
import numpy as np
import os
from os import listdir
from os.path import isfile, join
from copy import deepcopy

from itertools import combinations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Sized, Tuple, Any, Union, Set

from data import *
import networkx as nx 

# CONSTANTS
DEFAULT_SCORE = [
    [
        "scorer_li", 
        0.0
    ], 
    [
        "scorer_nd", 
        0.0
    ], 
    [
        "scorer_ei", 
        0.0
    ], 
    [
        "scorer_nc", 
        0.0
    ], 
    [
        "scorer_er", 
        0.0
    ], 
    [
        "scorer_ps", 
        0.0
    ], 
    [
        "scorer_eec", 
        0.0
    ], 
    [
        "scorer_qer", 
        0.0
    ], 
    [
        "scorer_hs", 
        0.0
    ], 
    [
        "scorer_qenr", 
        0.0
    ], 
    [
        "scorer_epm", 
        0.0
    ], 
    [
        "scorer_ccd", 
        0.0
    ], 
    [
        "scorer_aec", 
        0.0
    ], 
    [
        "scorer_aetl", 
        0.0
    ], 
    [
        "scorer_ser", 
        0.0
    ], 
    [
        "scorer_x", 
        0.0
    ]
]
DEFAULT_EDGE_PROVENANCE_SENT = ["place holder"]
DEFAULT_TIME_RANGE = ", "
DEFAULT_GRAPH = {}
DEFAULT_NODE_PROVENANCE_STRING = ""

# Hyperparam
IF_USE_ABBR_TYPE_NAME = True

@dataclass
class Link:
    target: int 
    source: int
    edge_relation:str 
    edge_provenance: str = None
    edge_provenance_sentence: List[str] = None
    key: int = 0
    edge_provenance_offset: List[Tuple[str,str]] = None
    
    @staticmethod
    def from_nx_edge(nx_edge_data, id_mapping):
        source_id = id_mapping[nx_edge_data[0]]
        target_id = id_mapping[nx_edge_data[1]]
        edge_type = nx_edge_data[2]['type']
        return Link(
            target = target_id,
            source = source_id,
            edge_relation = edge_type,
            edge_provenance = "",
            edge_provenance_sentence = DEFAULT_EDGE_PROVENANCE_SENT,
            edge_provenance_offset = []
        )

    def to_dict(self):
        link_dict = {
            'target':self.target,
            'source':self.source,
            'edge_relation':self.edge_relation,
            'edge_provenance':self.edge_provenance,
            'edge_provenance_sentence':self.edge_provenance_sentence,
            'key':self.key,
            'edge_provenance_offset':self.edge_provenance_offset
        }
        return link_dict

@dataclass
class Node:
    node_text: str
    node_text_en: str
    node_cluster_id: str
    node_id: str
    id: int
    is_mention_id: bool = False
    node_provenance: str = None
    node_cluster_name: str = None
    node_start_time_range: str = None
    node_end_time_range: str = None
    node_provenance_string: List[str] = None
    node_provenance_offset: List[Tuple[str,str]] = None

    @staticmethod
    def from_nx_node(nx_node_data, id_mapping, using_group = True):
        node_id_str = nx_node_data[0]
        node_id_int = id_mapping[node_id_str]
        node_type = nx_node_data[1]['type']
        # use shorter label name
        if IF_USE_ABBR_TYPE_NAME:
            node_type = node_type.split('.')[1]

        node_group_id = nx_node_data[1]['group']
        node_group_str = f'Group_{node_group_id}'
        if using_group:
            return Node(
                node_text = node_type,
                node_text_en = node_type,
                node_cluster_id = node_group_str,
                node_id = node_id_str,
                id = node_id_int,
                node_provenance = "",
                node_cluster_name = node_group_str,
                node_start_time_range = DEFAULT_TIME_RANGE,
                node_end_time_range = DEFAULT_TIME_RANGE,
                node_provenance_string = [],
                node_provenance_offset = []
            )
        else:
            return Node(
                node_text = node_type,
                node_text_en = node_type,
                node_cluster_id = node_id_str,
                node_id = node_id_str,
                id = node_id_int,
                node_provenance = "",
                node_cluster_name = node_id_str,
                node_start_time_range = DEFAULT_TIME_RANGE,
                node_end_time_range = DEFAULT_TIME_RANGE,
                node_provenance_string = [],
                node_provenance_offset = []
            )

    def to_dict(self):
        node_dict = {
            "node_text": self.node_text,
            "node_text_en": self.node_text_en,
            "node_cluster_id": self.node_cluster_id,
            "node_id": self.node_id,
            "id": self.id,
            "is_mention_id": self.is_mention_id,
            "node_provenance": self.node_provenance,
            "node_cluster_name": self.node_cluster_name,
            "node_start_time_range": self.node_start_time_range,
            "node_end_time_range": self.node_end_time_range,
            "node_provenance_string": self.node_provenance_string,
            "node_provenance_offset": self.node_provenance_offset
        }
        return node_dict
        

@dataclass
class MataData:
    narratives: Dict[str, Any] = None
    scores: List[Tuple[str,float]] = None
    node_to_atomic_hypothesis_index: Dict[str, List[int]] = None
    
    @staticmethod
    def from_nodes(nx_graph, nodes):
        # from list of Node()
        default_node_to_atomic_hypothesis_index = {}
        for node in nodes:
            default_node_to_atomic_hypothesis_index[node.node_id] = [0]
        graph_name = nx_graph.graph['name']
        default_narratives = {graph_name:[]}
        return MataData(
            narratives = default_narratives,
            scores = DEFAULT_SCORE,
            node_to_atomic_hypothesis_index = default_node_to_atomic_hypothesis_index
        )

    def to_dict(self):
        return {
            'narratives':self.narratives,
            'scores':self.scores,
            'node_to_atomic_hypothesis_index':self.node_to_atomic_hypothesis_index
        }

@dataclass
class UoFGraph:
    directed: bool = True
    graph: dict = None
    links: List[Link] = None
    nodes : List[Node] = None
    multigraph: bool = True
    
    @staticmethod
    def from_nx_graph(nx_graph,id_mapping,using_group = True):
        nodes_data = nx_graph.nodes().data()
        edges_data = nx_graph.edges().data()
        nodes = [Node.from_nx_node(n,id_mapping,using_group = using_group) for n in nodes_data]
        links = [Link.from_nx_edge(e,id_mapping) for e in edges_data]
        return UoFGraph(
            graph = DEFAULT_GRAPH,
            links = links,
            nodes = nodes
        )

    def to_dict(self):
        return {
            'directed':self.directed,
            'graph':self.graph,
            'links':[link.to_dict() for link in self.links],
            'nodes':[node.to_dict() for node in self.nodes],
            'multigraph':self.multigraph
        }

@dataclass
class InputData:
    directed: bool = True
    neighbor_graph: UoFGraph = None
    links: List[Link] = None
    nodes : List[Node] = None
    multigraph: bool = True
    graph: dict = None
    meta_data: MataData = None

    @staticmethod
    def from_nx_graph(nx_graph,id_mapping, using_group = True):
        nb_graph = UoFGraph.from_nx_graph(nx_graph,id_mapping, using_group = using_group)
        links = nb_graph.links
        nodes = nb_graph.nodes
        return InputData(
            neighbor_graph = nb_graph,
            links = links,
            nodes = nodes,
            graph = DEFAULT_GRAPH,
            meta_data = MataData.from_nodes(nx_graph, nodes)
        )
    
    def to_dict(self):
        return {
            'directed': self.directed,
            'neighbor_graph': self.neighbor_graph.to_dict(),
            'links': [link.to_dict() for link in self.links],
            'nodes': [node.to_dict() for node in self.nodes],
            'multigraph':self.multigraph,
            'graph':self.graph,
            'meta_data':self.meta_data.to_dict()
        }

def get_id_mapping(nx_graph):
    id_mapping = {}
    for node in nx_graph.nodes():
        id_mapping[node] = len(id_mapping)
    return id_mapping

'''main usage'''

def convert_to_UoF_format(nx_graph, using_group = False, output_json_path = None):
    '''
    input a nx_graph, output a json file that can be put into the 'var input_data' in their html files.
    using_group: if True, 'group' attribute for each node will be used as their cluster name in the output json
    '''
    id_mapping = get_id_mapping(nx_graph)

    input_data = InputData.from_nx_graph(nx_graph,id_mapping, using_group = using_group)
    with open(output_json_path,'w') as out:
        json.dump(input_data.to_dict(), out, indent = 4)
        
    # print(id_mapping)


    

