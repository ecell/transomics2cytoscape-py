import pandas as pd
import py4cytoscape as p4c
from Bio.KEGG import REST

def create3Dnetwork(networkDataDir, networkLayers, stylexml):
    layerTable = pd.read_table(networkLayers, sep="\t")

def createTransomicEdges(suid, transomicEdges):
    pass

def createTransomicEdge(row, nt, edgetbl, suid):
    pass

def importLayer(row):
    getKgml(row.array[2])
    kgml = row.array[2] + ".xml"
    print("Importing " + kgml)
    res = p4c.import_network_from_file(kgml)

def getKgml(pathwayID):
    f = open("pathwayID" + ".xml", "a")
    f.write(REST.kegg_get("eco01100", "kgml").read())
    f.close()
    
