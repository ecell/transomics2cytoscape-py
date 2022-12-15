import pandas as pd
import py4cytoscape as p4c
import time
import requests

def create3Dnetwork(networkLayers):
    layerTable = pd.read_table(networkLayers, header=None, sep="\t")
    networkSUID = layerTable.apply(importLayer, axis=1)
    layerTable = pd.concat([layerTable, networkSUID], axis=1)
    nodetables = layerTable.apply(getNodeTableWithLayerinfo, axis=1)
    layeredNodes = getLayeredNodes(nodetables)
    edgetables = layerTable.apply(getEdgeTableWithLayerinfo, axis=1)
    layeredEdges = pd.concat(edgetables.tolist())
    layeredNodes.to_csv("layeredNodes.csv")
    layeredEdges.to_csv("layeredEdges.csv")
    p4c.commands_post('cy3d set renderer')
    suID = p4c.create_network_from_data_frames(layeredNodes.astype(str), layeredEdges.astype(str))
    return suID

def importLayer(row: pd.Series) -> int:
    r = requests.get("https://rest.kegg.jp/get/" + row.array[1] + "/kgml")
    kgml = row.array[1] + ".xml"
    f = open(kgml, "w")
    f.write(r.text)
    f.close()
    print("Importing " + kgml)
    res = p4c.import_network_from_file(kgml)
    #time.sleep(3)
    xy = p4c.get_table_columns(table='node', columns=['KEGG_NODE_X', 'KEGG_NODE_Y'])
    xy.rename(columns={"KEGG_NODE_X": "x_location", "KEGG_NODE_Y": "y_location"}, inplace=True)
    p4c.load_table_data(xy, table_key_column="SUID")
    p4c.update_style_mapping(p4c.get_current_style(), p4c.map_visual_property("NODE_X_LOCATION", "x_location", "p"))
    p4c.update_style_mapping(p4c.get_current_style(), p4c.map_visual_property("NODE_Y_LOCATION", "y_location", "p"))
    p4c.fit_content()
    if row.array[3]:
        print("Creating a node at each midpoint of the edge...")
        createMidnodes(res['networks'][0])
    return res['networks'][0]

def getNodeTableWithLayerinfo(row: pd.Series) -> pd.DataFrame:
    nt = p4c.get_table_columns(table="node", network=row.array[4])
    nt['z_location'] = row.array[2]
    nt['LAYER_INDEX'] = row.array[0]
    return nt

def getLayeredNodes(nodetables: pd.DataFrame) -> pd.DataFrame:
    nodetable3d = pd.concat(nodetables.array)
    return nodetable3d.rename(columns={"SUID": "id"})

def getEdgeTableWithLayerinfo(row: pd.Series) -> pd.DataFrame:
    et = p4c.get_table_columns(table="edge", network=row.array[4])
    #return et
    print("Getting edge info. This function is kinda slow...")
    ei = p4c.get_edge_info(et["SUID"].tolist(), network=row.array[4])
    print("Finished getting edge info.")
    et['source'] = list(map(lambda x: x['source'], ei))
    et['target'] = list(map(lambda x: x['target'], ei))
    et['LAYER_INDEX'] = row.array[0]
    return et

def createMidnodes(networkSUID):
    et = p4c.get_table_columns(table='edge', network=networkSUID)
    print("getting node positions...")
    xyloc = p4c.get_table_columns(table='node', network=networkSUID, columns=['SUID', 'x_location', 'y_location'])
    print("getting edge information...")
    einfo = p4c.get_edge_info(et['SUID'].tolist(), network=networkSUID)
    einfodf = pd.DataFrame.from_dict(einfo)
    midxydf = pd.DataFrame.from_dict([getMidLoc(x, xyloc) for x in einfo])
    midNodeInfo = einfodf.join(midxydf)    
    midNodeInfo.rename(columns={"SUID": "orig_edge_SUID"}, inplace=True)
    print("creating midpoint nodes...")
    midNodes = p4c.add_cy_nodes(et['SUID'].apply(str).to_list())
    midNodeInfo['orig_edge_SUID'] = midNodeInfo['orig_edge_SUID'].apply(str)
    p4c.load_table_data(midNodeInfo, data_key_column="orig_edge_SUID", table="node", table_key_column="name")
    p4c.update_style_mapping(p4c.get_current_style(), p4c.map_visual_property("NODE_X_LOCATION", "x_location", "p"))
    p4c.update_style_mapping(p4c.get_current_style(), p4c.map_visual_property("NODE_Y_LOCATION", "y_location", "p"))
    print("deleting edges...")
    p4c.invert_edge_selection()
    p4c.delete_selected_edges()
    print("start collecting node IDs to connect...")
    midNodesName2suid =  pd.DataFrame.from_dict(midNodes)
    midNodeInfo = pd.merge(midNodeInfo, midNodesName2suid, left_on='orig_edge_SUID', right_on='name')
    src2mid = midNodeInfo[['source', 'SUID']]
    src2mid.rename(columns={"SUID": "target"}, inplace=True)
    mid2tgt = midNodeInfo[['SUID', 'target']]
    mid2tgt.rename(columns={"SUID": "source"}, inplace=True)
    res = p4c.cyrest_post("networks/" + str(networkSUID) + "/edges", body=src2mid.to_dict('records'))
    res = p4c.cyrest_post("networks/" + str(networkSUID) + "/edges", body=mid2tgt.to_dict('records'))

def getMidLoc(elem, xyloc):
    sourcexy = xyloc[xyloc['SUID'] == elem['source']]
    targetxy = xyloc[xyloc['SUID'] == elem['target']]
    midx_location = (int(sourcexy['x_location'].values[0]) + int(targetxy['x_location'].values[0])) / 2
    midy_location = (int(sourcexy['y_location'].values[0]) + int(targetxy['y_location'].values[0])) / 2
    return {'x_location': midx_location, 'y_location': midy_location}

def installCyApps():
    apps = p4c.get_installed_apps()
    # checking Apps
    is_cy3d_installed = False
    is_keggscape_installed = False
    for app in apps:
        if app['appName'] == 'Cy3D':
            is_cy3d_installed = True
        if app['appName'] == 'KEGGScape':
            is_keggscape_installed = True
    if is_cy3d_installed:
        print("Cy3D is NOT installed. transomics2cytoscape installs Cy3D.")
        p4c.install_app("Cy3D")
    if is_keggscape_installed:
        print("KEGGScape is NOT installed. transomics2cytoscape installs KEGGScape.")
        p4c.install_app("KEGGScape")

# getEdgeTableWithLayerinfo <- function(row){
#     et = RCy3::getTableColumns(table = "edge", network = as.numeric(row[5]))
#     message("Getting edge info. This function is kinda slow...")
#     ei = RCy3::getEdgeInfo(et$SUID, as.numeric(row[5]))
#     message("Finished getting edge info.")
#     et["source"] = unlist(lapply(ei, function(x) x$source))
#     et["target"] = unlist(lapply(ei, function(x) x$target))
#     LAYER_INDEX = rep(row[1], nrow(et))
#     return(cbind(et, LAYER_INDEX))
# }

# getLayeredNodes <- function(nodetables){
#     nodetable3d = dplyr::bind_rows(nodetables)
#     layeredNodes <- nodetable3d %>% rename(id = "SUID")
#     layeredNodes["id"] = as.character(layeredNodes$id)
#     return(layeredNodes)
# }

def createTransomicEdges(suid, transomicEdges):
    pass

def createTransomicEdge(row, nt, edgetbl, suid):
    pass

# create3Dnetwork <- function(networkDataDir, networkLayers,
#                             stylexml) {
#     owd <- setwd(networkDataDir)
#     on.exit(setwd(owd))
#     tryCatch({
#         RCy3::cytoscapePing()
#     }, error = function(e) {
#         stop("can't connect to Cytoscape. \n
#             Please check that Cytoscape is up and running.")
#     })
#     installCyApps()
#     layerTable = utils::read.table(networkLayers, sep="\t")
#     networkSUID = apply(layerTable, 1, importLayer)
#     layerTable = cbind(layerTable, networkSUID)
#     nodetables <- apply(layerTable, 1, getNodeTableWithLayerinfo)
#     layeredNodes <- getLayeredNodes(nodetables)
#     edgetables <- apply(layerTable, 1, getEdgeTableWithLayerinfo)
#     layeredEdges <- getLayeredEdges(edgetables)
#     RCy3::commandsPOST('cy3d set renderer')
#     suID <- RCy3::createNetworkFromDataFrames(layeredNodes, layeredEdges)
#     setTransomicStyle(stylexml, suID)
#     return(suID)
# }

# createTransomicEdges <- function(suid, transomicEdges) {
#     transomicTable <- utils::read.table(transomicEdges, sep="\t")
#     nt = RCy3::getTableColumns(table = "node", network = suid)
#     #et = RCy3::getTableColumns(table = "edge", network = suid)
#     #addedEdges = list()
#     edgetbl = tibble(source=numeric(), target=numeric(),
#                     interaction=character())
#     for (i in seq_len(nrow(transomicTable))) {
#         row = transomicTable[i,]
#         #edgetbl = createTransomicEdge(row, nt, et, edgetbl, suid)
#         edgetbl = createTransomicEdge(row, nt, edgetbl, suid)
#     }
#     #return(edgetbl)
#     body = purrr::transpose(dplyr::distinct(edgetbl))
#     RCy3::cyrestPOST(
#         paste("networks", suid, "edges", sep = "/"),
#         body = body
#     )
#     return(suid)
# }

# createTransomicEdge <- function(row, nt, edgetbl, suid) {
#     sourceLayerIndex = as.character(row[1])
#     #sourceTableType = as.character(row[2])
#     sourceTableColumnName = as.character(row[2])
#     sourceTableValue = as.character(row[3])
#     targetLayerIndex = as.character(row[4])
#     #targetTableType = as.character(row[6])
#     targetTableColumnName = as.character(row[5])
#     targetTableValue = as.character(row[6])
#     transomicEdgeType= as.character(row[7])
#     # if (sourceTableType == "node" && targetTableType == "edge"){
#     #     addedEdges = createNode2Edge(nt, sourceLayerIndex, sourceTableValue,
#     #                     sourceTableColumnName, et, targetLayerIndex,
#     #                     targetTableValue, targetTableColumnName,
#     #                     transomicEdgeType, addedEdges, suid)
#     #} else if (sourceTableType == "node" && targetTableType == "node"){
#     edgetbl = createNode2Node(nt, sourceLayerIndex, sourceTableValue,
#                         sourceTableColumnName, targetLayerIndex,
#                         targetTableValue, targetTableColumnName,
#                         transomicEdgeType, edgetbl)
#     # } else if (sourceTableType == "edge" && targetTableType == "edge"){
#     #     addedEdges = createEdge2Edge(et, sourceLayerIndex, sourceTableValue,
#     #                     sourceTableColumnName, targetLayerIndex,
#     #                     targetTableValue, targetTableColumnName,
#     #                     transomicEdgeType, addedEdges, suid)
#     # }
#     return(edgetbl)
# }

# createNode2Node <- function(nt, sourceLayerIndex, sourceTableValue,
#                             sourceTableColumnName, targetLayerIndex,
#                             targetTableValue, targetTableColumnName,
#                             transomicEdgeType, edgetbl) {
#     sourceLayerNt = dplyr::filter(nt, LAYER_INDEX == sourceLayerIndex)
#     sourceNodeRows = dplyr::filter(sourceLayerNt, grepl(sourceTableValue,
#                                     !!as.name(sourceTableColumnName),
#                                     fixed = TRUE))
#     targetLayerNt = dplyr::filter(nt, LAYER_INDEX == targetLayerIndex)
#     targetNodeRows = dplyr::filter(targetLayerNt, grepl(targetTableValue,
#                                     !!as.name(targetTableColumnName),
#                                     fixed = TRUE))
#     if (nrow(targetNodeRows) > 0) {
#         for (i in seq_len(nrow(sourceNodeRows))) {
#             sourceSUID = sourceNodeRows[i, 1]
#             for (j in seq_len(nrow(targetNodeRows))){
#                 targetSUID = targetNodeRows[j, 1]
#                 #if (!(list(c(sourceSUID, targetSUID)) %in% edgetbl)) {
#                 edgetbl = edgetbl %>% tibble::add_row(source=sourceSUID,
#                             target=targetSUID,
#                             interaction=as.character(transomicEdgeType))
#                     # addedEdges = append(addedEdges,
#                     #                     list(c(sourceSUID, targetSUID)))
#                     # RCy3::addCyEdges(c(sourceSUID, targetSUID),
#                     #                 edgeType=as.character(transomicEdgeType))
#                 #}
#             }
#         }
#     }
#     return(edgetbl)
# }

# ec2reaction <- function(tsvFilePath, columnIndex, outputFilename) {
#     source2target(tsvFilePath, columnIndex, outputFilename, "reaction")
# }

# ecRow2reaRows <- function(row, columnIndex, ec2rea) {
#     ec = row[columnIndex]
#     rea = ec2rea[names(ec2rea) == ec]
#     rows = do.call("rbind", replicate(length(rea), row, simplify = FALSE))
#     return(as.data.frame(cbind(rows, as.vector(rea))))
# }

# source2target <- function(tsvFilePath, columnIndex, outputFilename, target) {
#     transomicTable = utils::read.table(tsvFilePath, sep="\t")
#     sourceVec = transomicTable[ , columnIndex]
#     sourceVec = unique(sourceVec)
#     lastIndex = length(sourceVec)
#     if (lastIndex> 100) {
#         s2t = c()
#         for (i in 1:round(lastIndex/100)) {
#             tmp = KEGGREST::keggLink(target, sourceVec[1:100*i])
#             s2t = c(s2t, tmp)
#         }
#         tmp = KEGGREST::keggLink(target,
#                             sourceVec[100*round(lastIndex/100)+1:lastIndex])
#         s2t = c(s2t, tmp)
#     } else {
#         s2t = KEGGREST::keggLink(target, sourceVec)
#     }
#     dflist = apply(transomicTable, 1, srcRow2tgtRows, columnIndex, s2t)
#     df = dplyr::bind_rows(dflist)
#     df = dplyr::select(df, -one_of("rows"))
#     lastColumn = df[ , ncol(df)]
#     originalColumn = df[ , columnIndex]
#     df[ , columnIndex] = lastColumn
#     df[ , ncol(df)] = originalColumn
#     utils::write.table(unique(df), file = outputFilename, quote = FALSE,
#                 sep = '\t', col.names = FALSE, row.names = FALSE)
# }

# srcRow2tgtRows <- function(row, columnIndex, s2t) {
#     srcId = row[columnIndex]
#     tgtId = s2t[names(s2t) == srcId]
#     rows = do.call("rbind", replicate(length(tgtId), row, simplify = FALSE))
#     return(as.data.frame(cbind(rows, as.vector(tgtId))))
# }

# gene2ec <- function(tsvFilePath, columnIndex, outputFilename) {
#     source2target(tsvFilePath, columnIndex, outputFilename, "ec")
# }

# connectMidnodeEdges = function(elem, midNodeInfo){
#     midnodeSuid = elem$SUID
#     midNodeRow = midNodeInfo[midNodeInfo['orig_edge_SUID']==elem$SUID, ]
#     sourceSuid = midNodeRow['source']
#     targetSuid = midNodeRow['target']
#     return(c(sourceSuid, midnodeSuid))
#     # return(
#     #     c(setNames(c(sourceSuid, midnodeSuid), c("source", "target")),
#     #       directed = FALSE, interaction = 'interacts with'))
#     #return(list(c(sourceSuid,midnodeSuid),c(midnodeSuid,targetSuid)))
#     #RCy3::addCyEdges(list(c(sourceSuid,midnodeSuid),c(midnodeSuid,targetSuid)))
# }

# getLayeredEdges <- function(edgetables){
#     edgetable3d = dplyr::bind_rows(edgetables)
#     edgetable3d["source"] = as.character(edgetable3d$source)
#     edgetable3d["target"] = as.character(edgetable3d$target)
#     return(edgetable3d)
# }

# setTransomicStyle <- function(xml, suid){
#     stylename = RCy3::importVisualStyles(filename = xml)
#     RCy3::setVisualStyle(stylename, network = suid)
#     message(paste("Set visual style to", stylename))
# }
