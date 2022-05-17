import pandas as pd
from Bio.KEGG import REST

def create3Dnetwork(networkDataDir, networkLayers, stylexml):
    layerTable = pd.read_table(networkLayers, sep="\t")

def createTransomicEdges(suid, transomicEdges):
    pass


def createTransomicEdge(row, nt, edgetbl, suid):
    pass

def importLayer(row):
    pass

def getKgml(pathwayID):
    f = open("pathwayID" + ".xml", "a")
    f.write(REST.kegg_get("eco01100", "kgml").read())
    f.close()
    
