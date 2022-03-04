# -*- coding: utf-8 -*-
import abc
import networkx as nx
import itertools
import matplotlib.pyplot as plt

class Clustering(abc.ABC):


    @abc.abstractclassmethod
    def do(cls, df, from_field='author_id', to_field='referenced_tweet_author_id'):
        pass

class LouvainClustering(Clustering):


    @classmethod
    def create_graph(cls, df, from_field, to_field):
        intersect, graph = dict(), nx.Graph()
        for rowSn in df:
            row = vars(rowSn)
            if row[to_field] not in intersect.keys():
                intersect[row[to_field]] = list()
                intersect[row[to_field]].append(row[from_field])
            else:
                if row[from_field] not in intersect[row[to_field]]:
                    intersect[row[to_field]].append(row[from_field])
        for a_key in intersect.keys():
            for b_key in intersect.keys():
                if a_key != b_key:
                    weight = len(set.intersection(set(intersect[a_key]), set(intersect[b_key])))
                    graph.add_edge(a_key, b_key, weight=weight)
        return graph

    @classmethod
    def do(cls, df, from_field='author_id', to_field='referenced_tweet_author_id'):
        graph = cls.create_graph(df, from_field, to_field)
        nx.draw(graph)
        plt.show()
        return df
