from structs import *
import globs
import math


## Get the number of used LUTRAMS to implement this node
#  @return The number of needed luts
def getNumLuts(node):


    packingType = getPackingType(node)
    num_luts = 0

    if packingType == 'simple':
        num_luts = 1

    elif packingType == 'tightly':
        #the input width
        mux_size = len(node.inputs)

        # calc the number of used luts for this mux.
        num_luts = int(math.ceil((mux_size-globs.host_size)/(globs.host_size-1.0)) + 1)

    #complex
    else:

        #the input width
        mux_size = len(node.inputs)

        level_size = mux_size
        num_luts = 0
        while level_size > 1:
            level_size = int(math.ceil((level_size*1.0) / globs.host_size))
            num_luts += level_size

    #return the result
    return num_luts


## Analyse the packing of the mux
#  @return The packing type: 'simple',  'tightly' or 'complex'
def getPackingType(node):

    #the returned packing mode
    packing = 'complex'

    #the input width
    mux_size = len(node.inputs)

    # a node fit in a single LUTRAM.
    if mux_size <= globs.host_size:
        packing = 'simple'

    #tightly packed
    elif mux_size <= globs.host_size*globs.host_size:
        packing = 'tightly'

    #mux_size <= globs.host_size*globs.host_size or greater
    else:
        packing = 'complex'

    return packing


## A helper function for write_LUTRAM
#  returns a string '{ name1, name2 , ... }' for a given list of names
def list_to_vector(names):
    string = '{'
    for n in names:
        string = string + n + ','
    string = string[0:-1] + '}'
    return string


## write the verilog code for the LUTRAM.
# The LUTRAM can be a lutram of a routing mux, a ffmux or a eLUT
# @param name the name of the LUTRAM
# @param input_names a list of the input wires names
# @param output_name The name of the output wire
#       without the unregistered and registered appendix.
#       NOTE: there will be an unregistered an register output with that name
# @param config_offset the lut id of that stage
# @param config_stage The current stage.
# @param is_eLUT if the LUTRAM is an elUT
# @param is_ffmux if the LUTRAm is a mux on a ble
def write_LUTRAM(f, name, input_names, output_name, \
         config_offset, config_stage,  is_eLUT,  is_ffmux):

    #is it a regular mux or a mux on a ble?
    #the first input is the name of the LUTRAM wire of the lut .
    #remember that this LUTRAM have two outputs
    if is_ffmux:
        input_names.append(input_names[0] + '_unreg')
        input_names[0] = input_names[0] + '_reg'

    ## assign an 0 driver to every unconnected input
    while len(input_names) < globs.host_size:
        input_names.append("1'b0")

    #is it an eLUT or just a mux?
    if is_eLUT:
        string ='''
        elut_custom ''' + name + ''' ('''
    else:
        string ='''
        lut_custom ''' + name + ''' ('''

    string +='''
    .a(wr_addr), // input [5 : 0] a
    .d(wr_data[''' + str(config_offset) + ''']), // input [0 : 0]
    '''
    f.write(string)

    #connect the name of the input wires
    string = '.dpra(' + list_to_vector(input_names) + \
         '), // input [5 : 0] dpra'
    f.write(string)

    f.write('''
    .clk(clk), // input clk
    .we(wren[''' + str(config_stage) + ''']), // input we
    ''')
    #connect the name of the output wires.
    #if its an elut than we have two output wires instead of one
    if is_eLUT:
        f.write( '.dpo(' + output_name + \
             '_unreg), // unregistered output')

        f.write('''
        .qdpo_clk(clk2), // run clk
        .qdpo_rst(ffrst), // input flip flop reset
        ''')
        f.write( '.qdpo(' + output_name + \
             '_reg)); // registered output\n\n')
    else:
        f.write( '.dpo(' + output_name + '));\n\n')


## write the header of the verilog file
# @param f the file handle
def writeHeader(f):

    numinputs = 0
    numoutputs = 0
    for key in globs.IOs:

        numinputs = numinputs + len(globs.IOs[key].inputs)
        numoutputs = numoutputs + len(globs.IOs[key].outputs)

    header = """
    `include "define.v"
    //ZUMA global routing Entity
    //automatically generated by script
    module ZUMA_custom_generated
    #(
    """
    f.write(header)

    f.write('parameter N_NUMLUTS = ' + str(globs.params.N) + ',\n')
    f.write('parameter I_CLINPUTS = ' + str(globs.params.I) + ',\n')
    f.write('parameter K_LUTSIZE  = ' + str(globs.params.K) + ',\n')
    f.write('parameter CONFIG_WIDTH  = ' + str(globs.params.config_width)+ '\n')

    header2 = """
     )
    (
    clk,
    fpga_inputs,
    fpga_outputs,
    config_data,
    config_en,
    progress,
    config_addr,
    clk2,
    ffrst
    );
    """
    f.write(header2)

    string = 'input [' + str(numinputs) +'-1:0] fpga_inputs;\n'
    f.write(string)
    string = 'input [' + str(32) +'-1:0] config_data;\n'
    f.write(string)
    string = 'input [CONFIG_WIDTH-1:0] config_addr;\n'
    f.write(string)
    string = 'input config_en;\n'
    f.write(string)
    string = 'output [ ' +  str(numoutputs)+ '-1:0] fpga_outputs;\n'
    f.write(string)
    string = 'output [15:0] progress;\n'
    f.write(string)
    f.write('wire [4096:0] wren;\n')
    f.write('wire [5:0] wr_addr;\n')
    f.write('wire [CONFIG_WIDTH-1:0] wr_data;\n')
    f.write('input clk;\n')
    f.write('input clk2;\n')
    f.write('input ffrst;\n')

    f.write('assign wr_data = config_data;\n');

## write the footer of the verilog file
#  @param f the file handle
def writeFooter(f):

    # write the config controller
    f.write('parameter NUM_CONFIG_STAGES = ' + \
        str(len(globs.config_pattern)) + ';')
    string = """
    config_controller_simple
    #(
        .WIDTH(CONFIG_WIDTH),
        .STAGES(NUM_CONFIG_STAGES),
        .LUTSIZE(K_LUTSIZE)
    )
    configuration_ctrl
    (
        .clk(clk),
        .reset(1'b0),
        .wren_out(wren),
        .progress(progress),
        .wren_in(config_en),
        .addr_in(config_addr),
        .addr_out(wr_addr)
    );
    """
    f.write(string)
    f.write('endmodule')


## get the right mux_prefix for a given node.
# @param node The node instance
# @return return c_mux_ or mux_ depending on the node type
def getMuxPrefix(node):

    #nodes on a cluster get a different prefix
    if (6 < node.type and node.type < 10):
        mux_prefix = 'c_mux_'
    else:
        mux_prefix = 'mux_'

    return mux_prefix

## Add a simple mux node to the technology mapped graph.
# This node represents a mux implemented through a single lutram
def addSimpleNode(node):

    #the node name
    name = str(node.id)

    #the names of the nodes in the last level have always the same pattern
    #NOTE: the names for the input of the mapped node are different as the
    #original names in the node graph because the mapping process can translate
    #an input node to several mapped nodes.
    input_names = [(str(i)) for i in node.inputs]

    mappedNode = TechnologyMappedNode(node,name,input_names)
    #add the node to the node graph
    globs.technologyMappedNodes.add(mappedNode)

## Translate a mux node which fit in a single LUTRAM.
# write it to the file and append the node id to the current config row
def writeSimpleLut(node,config_row,f):

    mux_prefix = getMuxPrefix(node)
    node_prefix = 'node_'

    output_name = node_prefix + str(node.id)
    input_names = [(node_prefix + str(i)) for i in node.inputs]
    name = mux_prefix + str(node.id)

    config_offset = len(config_row)
    config_stage = len(globs.config_pattern)

    write_LUTRAM(f, name, \
                 input_names, \
                 output_name, \
                 config_offset, \
                 config_stage, \
                 node.eLUT, node.ffmux )

    config_row.append( node.id)


## Add a tighly packed mux node to the technology mapped graph.
# This node represents a mux which is implemented through several mapped nodes
# divided into two levels
def addTightlyNodes(node):

    # calc the number of used luts for this mux.
    num_luts = getNumLuts(node)

    count = 0

    #node names of the first lvl
    firstLvlNodes = []

    #write first level
    for n in range(num_luts - 1):

        name = str(node.id) + '_' + str(count)

        #append the node name for input of the second level
        firstLvlNodes.append(name)

        inputNodesIDs = node.inputs[count:count+globs.host_size]
        input_names = [(str(i)) for i in inputNodesIDs]

        mappedNode = TechnologyMappedNode(node,name,input_names)

        #add it to the node graph
        globs.technologyMappedNodes.add(mappedNode)

        count = count + globs.host_size

    #now write the second level

    #the second lvl is a single mux with input from the first lvl
    #and the rest of of the input nodes which not fit in the lvl.

    name = str(node.id)

    #set the input. the nodes of the first lvl
    input_names = firstLvlNodes

    #no add the rest names. not fit in the first lvl.
    inputNodesIDs = node.inputs[count:]
    input_names2 = [(str(i)) for i in inputNodesIDs]

    mappedNode = TechnologyMappedNode(node,name,input_names + input_names2)

    #add it to the node graph
    globs.technologyMappedNodes.add(mappedNode)



## Tranlate a mux node which fits into two levels of LUTRAMs.
# For the first level divide the inputs
# equally over maximal #hostsize LUTRAMS.
# The second level then gets the outputs
# of these first level LUTRAMs.
# Write the LUTRAMS to the output file and append
# the node ids to the current config row.
# note: the second lvl is one single LUTRAM
def writeTightlyLut(node,config_row,f):

    mux_prefix = getMuxPrefix(node)
    node_prefix = 'node_'

    count = 0
    mux_nodes = []

    # calc the number of used luts for this mux.
    num_luts = getNumLuts(node)

    #write first level
    for n in range(num_luts - 1):

        output_name = node_prefix + str(node.id) + '_' + str(count)
        input_names = [(node_prefix + str(i)) for i in node.inputs[count:count+globs.host_size]]
        name = mux_prefix + str(node.id) + '_' + str(count)
        config_offset = len(config_row)
        config_stage = len(globs.config_pattern)

        f.write( '\t\t\twire ' + output_name + ';\n')
        #append the output name for input of the second level
        mux_nodes.append(output_name)

        write_LUTRAM(f, name, \
                    input_names, \
                    output_name, \
                    config_offset, \
                    config_stage, \
                    node.eLUT, node.ffmux )

        count = count + globs.host_size
        config_row.append( node.id)

    #now write the second level

    output_name = node_prefix + str(node.id)
    input_names = mux_nodes + \
                  [(node_prefix + str(i)) for i in node.inputs[count:]]

    name = mux_prefix + str(node.id)

    config_offset = len(config_row)
    config_stage = len(globs.config_pattern)

    write_LUTRAM(f, name, \
                 input_names, \
                 output_name, \
                 config_offset, \
                 config_stage, \
                 node.eLUT, node.ffmux )

    config_row.append( node.id)

## Add a complex packed mux node to the technology mapped graph.
# This node represents a mux which is implemented through many mapped nodes
# in several levels.
def addComplexNode(node):

    #the input width
    mux_size = len(node.inputs)

    count = 0
    level_size = int(math.ceil((mux_size*1.0)/globs.host_size))

    #node names of the current lvl
    mux_nodes = []

    # Level 0 (input nodes)
    for n in range(level_size - 1):

        name = str(node.id) + '_' + str(count)
        mux_nodes.append(name)

        input_names = [(str(i)) for i in node.inputs[count:count+globs.host_size]]

        mappedNode = TechnologyMappedNode(node,name,input_names)
        #add it to the node graph
        globs.technologyMappedNodes.add(mappedNode)

        count = count + globs.host_size

    #last node in the lvl 0
    name = str(node.id) + '_' + str(count)
    mux_nodes.append(name)

    input_names = [(str(i)) for i in node.inputs[count:]]

    mappedNode = TechnologyMappedNode(node,name,input_names)
    #add it to the node graph
    globs.technologyMappedNodes.add(mappedNode)

    # Further levels
    level_size = int(math.ceil((level_size*1.0)/globs.host_size))
    level = 0
    next_level_mux_nodes = []

    while level_size > 1:
        count  = 0
        level += 1

        for n in range(level_size - 1):

            name = str(node.id) + '_' + str(count) + '_' + str(level)
            next_level_mux_nodes.append(name)

            input_names = [str(i) for i in mux_nodes[count:count+globs.host_size]]

            mappedNode = TechnologyMappedNode(node,name,input_names)
            #add it to the node graph
            globs.technologyMappedNodes.add(mappedNode)

            count = count + globs.host_size

        #last node of this lvl

        name = str(node.id) + '_' + str(count) + '_' + str(level)
        next_level_mux_nodes.append(name)

        input_names = [str(i) for i in mux_nodes[count:]]

        mappedNode = TechnologyMappedNode(node,name,input_names)
        #add it to the node graph
        globs.technologyMappedNodes.add(mappedNode)

        level_size = int(math.ceil((level_size*1.0)/globs.host_size))
        mux_nodes = next_level_mux_nodes
        next_level_mux_nodes = []

    # Write last level (single LUT)

    name = str(node.id)
    input_names = mux_nodes

    mappedNode = TechnologyMappedNode(node,name,input_names)
    #add it to the node graph
    globs.technologyMappedNodes.add(mappedNode)


## Tranlate a mux node which fits into several levels of LUTRAMs.
# Used if the node even doesn't fit into the k^2 size(tightly packed)
# TODO:are there cases were this solution breaks?.
# Quick approach: Not as tightly packed as above case
# In this approach every LUT only serves one level (depth)

def writeComplexLut(node,config_row,f):

    mux_prefix = getMuxPrefix(node)
    node_prefix = 'node_'

    #the input width
    mux_size = len(node.inputs)

    count = 0
    level_size = int(math.ceil((mux_size*1.0)/globs.host_size))
    mux_nodes = []
    # Level 0 (input nodes)
    for n in range(level_size - 1):
        node_name = node_prefix + str(node.id) + \
                        '_' + str(count)
        f.write( '\t\t\twire ' + node_name + ';\n')
        mux_nodes.append(node_name)


        name = mux_prefix + str(node.id) + '_' + str(count)
        input_names = [(node_prefix + str(i)) for i in node.inputs[count:count+globs.host_size]]
        output_name = node_name

        config_offset = len(config_row)
        config_stage = len(globs.config_pattern)

        write_LUTRAM(f, name, \
                 input_names, \
                 output_name, \
                 config_offset, \
                 config_stage, \
                 node.eLUT, node.ffmux )

        count = count + globs.host_size
        config_row.append( node.id )

    node_name = node_prefix + str(node.id) + '_' + str(count)

    f.write( '\t\t\twire ' + node_name + ';\n')
    mux_nodes.append(node_name)


    name = mux_prefix + str(node.id) + '_' + str(count)
    input_names = [(node_prefix + str(i)) for i in node.inputs[count:]]
    output_name = node_name

    config_offset = len(config_row)
    config_stage = len(globs.config_pattern)

    write_LUTRAM(f, name, \
                 input_names, \
                 output_name, \
                 config_offset, \
                 config_stage, \
                 node.eLUT, node.ffmux )

    config_row.append( node.id )

    # Further levels
    level_size = int(math.ceil((level_size*1.0)/globs.host_size))
    level = 0
    next_level_mux_nodes = []

    while level_size > 1:
        count  = 0
        level += 1
        for n in range(level_size - 1):

            node_name = node_prefix + \
                        str(node.id) + '_' + \
                        str(count) + '_' + \
                        str(level)
            f.write( '\t\t\twire ' + node_name + ';\n')

            next_level_mux_nodes.append(node_name)

            name = mux_prefix + str(node.id) + '_' + str(count) + '_' + str(level)
            input_names = [str(i) for i in mux_nodes[count:count+globs.host_size]]
            output_name = node_name

            config_offset = len(config_row)
            config_stage = len(globs.config_pattern)

            write_LUTRAM(f, name, \
                         input_names, \
                         output_name, \
                         config_offset, \
                         config_stage, \
                         node.eLUT, node.ffmux )

            count = count + globs.host_size
            config_row.append( node.id )

        node_name = node_prefix + str(node.id) + \
                        '_' + str(count) + '_' + str(level)
        f.write( '\t\t\twire ' + node_name + ';\n')

        next_level_mux_nodes.append(node_name)

        name = mux_prefix + str(node.id) + '_' + str(count) + '_' + str(level)
        input_names = [str(i) for i in mux_nodes[count:]]
        output_name = node_name

        config_offset = len(config_row)
        config_stage = len(globs.config_pattern)

        write_LUTRAM(f, name, \
                    input_names, \
                    output_name, \
                    config_offset, \
                    config_stage, \
                    node.eLUT, node.ffmux )

        config_row.append( node.id )
        level_size = int(math.ceil((level_size*1.0)/globs.host_size))
        mux_nodes = next_level_mux_nodes
        next_level_mux_nodes = []

    # Write last level (single LUT)

    name =  mux_prefix + str(node.id)
    input_names = mux_nodes
    output_name = node_prefix + str(node.id)

    config_offset = len(config_row)
    config_stage = len(globs.config_pattern)

    write_LUTRAM(f, name, \
                input_names, \
                output_name, \
                config_offset, \
                config_stage, \
                node.eLUT, node.ffmux )

    config_row.append( node.id )

## print debug information for every node into the given file.
# Print node type and location
# @param n the node
# @param f the filehandle
def printNodeInformation(n,f):

        if n.type is 3: #OPIN
            if n.location[0] in [0, globs.clusterx] or n.location[1] in [0, globs.clustery]:
                #edge, thee are IOS
                f.write('//FPGA input at ' + str(n.location) + '\n')
            else:
                #cluster
                f.write('//cluster output at ' + str(n.location) + '\n')
        elif n.type is 4: #IPIN
            if n.location[0] in [0, globs.clusterx] or n.location[1] in [0, globs.clustery]:
                #edge, thee are IOS
                f.write('//FPGA output at ' + str(n.location) + '\n')
            else:
                #cluster
                f.write('//cluster input at ' + str(n.location) + '\n')
        elif n.type is 5 or n.type is 6: #CHANX
            if n.type is 5:
                f.write('//sbox driver x at  ' + str(n.location) + '\n')
            else:
                f.write('//sbox driver y at ' + str(n.location) + '\n')
        elif n.type is 10: #global IO
            if len(n.edges) == 0:
                f.write('//global output ordering node for output #' + str(globs.orderedOutputs.index(n.id)) + '\n')
            else:
                f.write('//global input ordering node for input #' + str(globs.orderedInputs.index(n.id)) + '\n')
        elif n.eLUT: #ELUT
            f.write('//internal cluster node (eLUT) at  ' + str(n.location) + '\n')
            #print "LUT! " + str(n.location) + " " + str(n.id)
        elif n.ffmux: #FFMUX
            f.write('//internal cluster node (ffmux) at  ' + str(n.location) + '\n')
            #print "FFMUX! " + str(n.location) + " " + str(n.id)
        else: #7 cluster input crossbar
            f.write('//internal cluster node at  ' + str(n.location) + '\n')

        f.write('//size: ' + str(len(n.inputs)) + '\n//inputs: ' + str(n.inputs) + '\n')

## fix the edge attribute of every node of the mapped graph.
# TODO: This is just a workaround. Normally there shouldn't be nodes
# that need this fix
# TODO: it seems that the normal node graph has the same problem, that there
# exist nodes with missing nodes in the edge list.
def fixEdges():

    #fix the input egde connections.
    for node in globs.technologyMappedNodes.getNodes():
        for inputNodeName in node.inputs:
            inputNode = globs.technologyMappedNodes.getNodeByName(inputNodeName)
            if node.name not in inputNode.edges:
                inputNode.edges.append(node.name)


## Set the source attribute for mapped opins and ffmuxes nodes.
# These mapped nodes need this fix because they have a single fix input.
def updateMappedFFMuxSource():

    #set the source of the ble muxes
    for node in globs.technologyMappedNodes.getNodes():

        if node.parentNode.ffmux :
            node.source = node.inputs[0]

    #set the source of the mapped opins
    for key in globs.clusters:
        cl = globs.clusters[key]
        for n in range(globs.params.N):
            opin_id = cl.outputs[n].id
            opin = globs.nodes[opin_id]
            #this opin has just on input
            mappedNodeName = opin.mappedNodes[0]
            mappedNode = globs.technologyMappedNodes.getNodeByName(mappedNodeName)

            mappedNode.source = mappedNode.inputs[0]

## Mark several mapped nodes a passthrough node.
# A passthrough node is a node which can be optimized away
# and will be implemented as a fix wiring.
# This is done by using the assign statement
# in the verilog ouput file for two nodes.
def markPassTroughNodes():

    for node in globs.technologyMappedNodes.getNodes():

        #source sinks ipins iomuxes eLUT ffmuxes are leaved untouched.
        #the rest can be optimized

        #TODO: ipins with only one input should now be marked as passTrough
        #as well because they could be optimized by a wire assigment.
        #WORKAROUND: would break the sdf analysis for now. So we keep it.
        if len(node.inputs) == 1:

            if (node.type == 4):
                print "BuildVerilog: Found an ipins with onyly one input, node id" + str(node.id)
                node.passTrough = False

            elif (node.type < 3 or node.type > 7):
                node.passTrough = False
            else:
                node.passTrough = True
                #set the source attribute for them
                #easier for the timimng analysis
                node.source = node.inputs[0]
        else:
            node.passTrough = False

#write a wire in the verilog file for every node output
def writeWires(file):

    #write connections. one wire for every node output.
    #Also sink and sources.
    #TODO: are there unconnected sources through the cluster reassignment
    #of opins?
    for node in globs.nodes:

        # an eLut have two outputs.
        # one registered and one unregistered output
        if node.eLUT:
            string = 'wire node_' + str(node.id) + '_reg;\n'
            string += 'wire node_' + str(node.id) + '_unreg;\n'
        # the rest have only one output
        else:
            string = 'wire node_' + str(node.id) + ';\n'
        file.write(string)


## This function creates a verilog file,
## which represent the unconfigured structure of the fpga
# @param filename The filename of the verilog file.
def build_global_routing_verilog(filename):


# Because a mux can be implemented with sereval LUTRAMS,
# because of its input width, we have to track the the placment
# of a node of the node graph to its actual count and place of LUTRAMS.
# Therefore we use the config_patter array.
# The config_patter array describe this technolgy mapping,
# in form of array of nodeIds.
# every column in a row has a nodeId, and therefore a reference to a node
# in the node graph.
# More then one column can has the same reference, because there were
# sereval LUTRAMS used for that node.
# Every row in the config_patter is called a stage
# where the addressable LUTRAMS of a stage are configured
# by the controller bit by bit.
# the maximal number of LUTRAMS in a config row is the
# adressable size, i.e the config width of the controller.
# This config_patter array will also be written to the file configpattern.txt

#We also use a technology mapped node graph, where the nodes represent a lutram
#on the fpga. At the moment this node graph is only used for the timing analysis.
#TODO: change the building of the verilog and blif file by using
#the information of this graph and simplify the
#writeComplexLut,writeTightlyLut,writeSimpleLut function.

    #start with the header
    f = open(filename, 'w')

    writeHeader(f)

    #we use this config row to track the used LUTRAMS in this row.
    #every row is a stage.
    config_row = []

    build_all = True #build the clusters

    registers = []

    writeWires(f)

    #the opins have just one input, so use a assign optimization
    #cluster's outputs are only connected to mux outputs.
    for key in globs.clusters:
        cl = globs.clusters[key]
        for n in range(globs.params.N):
            lut_id = cl.LUT_FFMUX_nodes[n]
            opin_id = cl.outputs[n].id
            f.write('//ffmux to cluster output at ' + str(key) + '\n')
            f.write('assign node_' + str(opin_id) + ' = node_' + str(lut_id) + ';\n')

    total_luts = 0
    #generate code for every nodes. except source and sinks
    for node in globs.nodes:

        # sources and sinks nodes will not be generated.
        if node.type < 3:
            #for now its easier to have them in the technology graph
            #because of edges consistency in the graph
            #TODO: maybe remove them?

            name = str(node.id)

            input_names = []
            for inputId in node.inputs:
                input_names.append(str(inputId))

            mappedNode = TechnologyMappedNode(node,name,input_names)
            globs.technologyMappedNodes.add(mappedNode)

            continue


        # this node is not driven. skip it.
        if len(node.inputs) < 1:

            #add the iomuxes and ipins to the technology mapped node graph
            #TODO DEPRECATED: ipins with no driver should been killed now by
            #InitFPGA.removeUndrivenNodes()
            if node.type == 10 or node.type == 4:

                if (node.type == 4):
                    print "Error a ipin with no driver shouldn't exist"
                    sys.exit(1)

                #build a passthrough node for the technology mapped node graph
                name = str(node.id)
                input_names = []

                mappedNode = TechnologyMappedNode(node,name,input_names)
                globs.technologyMappedNodes.add(mappedNode)
            else:
                #there should be no node with no inputs except iomuxes,
                #sink and sources

                print 'ERROR: Node ' + str(node.id) + ' has no input.'
                print 'node type: ' + str(node.type)
                sys.exit(1)

            continue

        # if the node have only one input we can just make a assignment
        # of the input with the output.
        node_prefix = 'node_'

        #create muxes
        n = node

        #if we use the reverse build(a build of the blif from the bitstream),
        #this node is not in the bitstream, and the build out of the bitstream
        #would fail when we don't apply this connection also in
        #the reverse build, see fix_reduced_channels.

        if len(node.inputs) == 1 and not node.ffmux:

            #build a passthrough node for the technology mapped node graph
            name = str(node.id)
            input_names = [str(node.inputs[0])]

            mappedNode = TechnologyMappedNode(node,name,input_names)
            globs.technologyMappedNodes.add(mappedNode)

            #now use the assign statement to optimize this connection
            #Note that opins on a cluster were handled before

            #seems that io ipins and opins are excluded here
            #TODO: why? make no sense to give them a lutram
            #the io muxes are former sink and source nodes.

            if node.type >= 5 and node.type <= 7:
                #other cases (IOs) are already dealt with
                if n.type is 5:
                    f.write('//sbox driver x at  ' + str(n.location) + '\n')
                elif n.type is 6:
                    f.write('//sbox driver y at ' + str(n.location) + '\n')
                elif n.type is 7:
                    f.write('//internal cluster crossbar connection at ' + str(n.location) + '\n')

                f.write('assign ' + node_prefix + str(node.id) + ' = ' + node_prefix + str(node.inputs[0]) + ';\n');

            #TODO: why we skip other nodes with input length one?
            continue

        # print debug information for every node: node type and location
        printNodeInformation(node,f)

        # now we have to write the LUTRAM construct to the verilog file.
        # first we have to check if we must split the node into several lutrams
        # because it has too much input edges.

        # calc the number of used lutrams for this mux.
        num_luts = getNumLuts(node)

        #increase the lut counter
        total_luts = num_luts + total_luts

        #determine the package type
        packingType = getPackingType(node)

        #if a node with its LUTRAMS can't fit in a row
        #we finished that row and use the next.
        #TODO: is this acceptable?

        if num_luts + len(config_row) >= globs.params.config_width:
            globs.config_pattern.append(config_row)
            config_row = []

        # a node fit in a single LUTRAM. write it to the file and append
        # the node id to the current config row.
        if packingType == 'simple':
            writeSimpleLut(node,config_row,f)
            addSimpleNode(node)


        # write two levels of LUTRAMs.
        elif packingType == 'tightly':
            writeTightlyLut(node,config_row,f)
            addTightlyNodes(node)

        # if it even doesn't fit into the k^2 size.
        # quick approach: Not as tightly packed as above case
        # In this approach every LUT only serves one level (depth)
        else:
            writeComplexLut(node,config_row,f)
            addComplexNode(node)

    #now all nodes are created.

    #mark the passtroughs
    markPassTroughNodes()

    #set the sources of the mapped ff muxes to the lut
    #and of the corresponding opins.
    updateMappedFFMuxSource()


    #fix the edge attribute of the mapped nodes
    fixEdges()


    #now add the last config row
    globs.config_pattern.append(config_row)

    # save the config pattern array to the file
    configfile = open('configpattern.txt', 'w')
    for row in globs.config_pattern:
        for item in row:
            configfile.write(str(item)+ ' ')

        configfile.write('\n')

    configfile.close()

    # now build the rest
    print 'total luts: ', total_luts

    count = 0
    if globs.params.orderedIO:
        #connect the order outputs node wires with the fpga outputs
        for output in globs.orderedOutputs:
            f.write('assign fpga_outputs[' + str(count) + \
                '] = node_' + str(output) + ';\n')
            count += 1
    else:
        for key in globs.IOs:
            IO = globs.IOs[key]
            for i in IO.outputs:
                f.write('assign fpga_outputs[' + str(count) + '] = node_' + str(i.id) + ';\n')
                count = count+1

    count = 0
    if globs.params.orderedIO:
        #connect the order inputs node wires with the fpga inputs
        for input in globs.orderedInputs:
            f.write('assign node_' + str(input) + \
                ' = fpga_inputs[' + str(count) + '];\n')
            count += 1
    else:
        for key in globs.IOs:
            IO = globs.IOs[key]
            for i in IO.inputs:
                f.write('assign node_' + str(i.id) + ' = fpga_inputs[' + str(count) + '];\n')
                count = count+1


    writeFooter(f)
