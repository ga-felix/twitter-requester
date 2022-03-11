# -*- coding: utf-8 -*-
import abc
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms.community import girvan_newman
import random

class Clustering(abc.ABC):


    @abc.abstractclassmethod
    def do(cls, df, targets, from_field='author_id', to_field='referenced_tweet_author_id'):
        pass

class LouvainClustering(Clustering):


    @classmethod
    def create_graph(cls, df, nodes, from_field, to_field):
        intersect, graph = dict(), nx.Graph()
        for rowSn in df:
            row, found = vars(rowSn), False
            for node in nodes:
                if row['text'].startswith(node):
                    found = True
            if not found:
                continue
            if row[to_field] not in intersect.keys():
                if row[to_field] != 0:
                    intersect[row[to_field]] = list()
            if row[from_field] not in intersect[row[to_field]]:
                if row[from_field] != 0:
                    intersect[row[to_field]].append(row[from_field])
        for a_key in intersect.keys():
            for b_key in intersect.keys():
                if not graph.has_edge(a_key, b_key) and a_key != b_key:
                    weight = len(set.intersection(set(intersect[a_key]), set(intersect[b_key])))
                    graph.add_edge(a_key, b_key, weight=weight)
        return (graph, intersect)

    @classmethod
    def do(cls, df, targets, from_field='author_id', to_field='referenced_tweet_author_id'):
        r = cls.create_graph(df, targets, from_field, to_field)
        graph, intersect = r[0], r[1]
        communities_gen = girvan_newman(graph)
        top_level_communities = next(communities_gen)
        communities_color = list()
        colors = ['red','blue','yellow','black']
        for index, community in enumerate(top_level_communities):
            if index < len(colors):
                communities_color.append([community, colors[index]])
            else:
                communities_color.append([community, colors[len(colors) - 1]])
        print(communities_color)
        color_map = list()
        for node in graph:
            for community in communities_color:
                if node in community[0]:
                    color_map.append(community[1])
                    break
        print(color_map)
        nx.draw(graph, node_color=color_map, node_size=[len(intersect[n])/len(graph.nodes)for n in intersect.keys()])
        plt.show()
        return df
