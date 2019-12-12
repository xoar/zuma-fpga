import re

class BlifIO:
    def __init__(self,name,index):
        ##blif name of the input
        self.blifName = name
        ##io index: a clock get index -1.
        ##It is assumend that when the reset signal top^reset is used it
        #gets index 0 and the rest of inputs get an index increased by 1.
        #otherwise the rest of input names start by index 0.
        self.ioIndex = index

class BlifLatch:
    def __init__(self,inputNet,ouputNet):
        ##the blif name of the input net
        self.inputNet = inputNet
        ##the blif name of the ouput net
        self.outputNet = outputNet

class BlifNames:
    def __init__(self,inputNets,ouputNet,content):
        ##list of blif input net names
        self.inputNets = inputNets
        ##the blif name of the ouput net
        self.ouputNet = ouputNet
        #ABC format of the content of a logic gate:
        #1) if the content consist of only a 1 or 0, then we have
        #   a constant 1 or 0 as the output
        #2) else we have at least one a PLA description line
        #   like 0101-1 1 or 01- 0

        #internal representation:
        # For 1) we store a tuple ('-', constant output value)
        # and for 2) we store the two given values:
        # (k-input,output value)
        self.content = content

#an object to collect all information gathered in the blif file.
class BlifFile:
    def __init__(self):

        ##the input blif names: a list of BLifIO objetcs (blifname,ioIndex)
        self.inputs = []
        ##the ouput blif names: a list of BLifIO objetcs (blifname,ioIndex)
        self.outputs = []

        ##a list of BlifLatch objects
        self.latches = []
        ##a list of BlifNames objects
        self.names = []


##parser the blif file
#@return a Blif File object
def parseBlif(filename):

    #an object to collect all information gathered in the file.
    blifFile = BlifFile()

    fh = open(filename,"r")
    line = fh.readline()

    # Parse the source blif file
    # create and add the blif objetcs to the blifFile object
    while len(line) > 0:

        if line.find(".model") > -1:

            #read the next line
            line = fh.readline()

        #get the blif names of the inputs
        elif line.find(".inputs") > -1:

            inputoffset = 0

            #read items until no more backslashes appear
            items = line.strip().split(' ')[1:]
            while items[-1] == '\\':
                items = items[:-1]
                nextline = fh.readline()
                items = items + nextline.strip().split(' ')

            for item in items:
                # append the blif name to the global input list

                name = item.strip()
                index = -1

                if name == 'top^clock':
                    #add the input to the blif file
                    index = -1

                if name == 'top^reset':
                    # set reset to the first input pin
                    index = 0
                    inputoffset += 1

                elif name == 'top^in':
                    # just one input
                    index = 0

                else:
                    #extract the index from the name
                    nums = re.findall(r'\d+', item)
                    nums = [int(i) for i in nums ]

                    index = nums[-1] + inputoffset

                #add the io to the blifFile object
                blifIO = BlifIO(name,index)
                blifFile.inputs.append(blifIO)

            #read the next line
            line = fh.readline()

        #get the blif names of the outputs
        elif line.find(".outputs") > -1:

            #read items until no more backslashes appear
            items = line.strip().split(' ')[1:]
            while items[-1] == '\\':
                items = items[:-1]
                nextline = fh.readline()
                items = items + nextline.strip().split(' ')

            for item in items:
                # append the blif name to the global output list
                name = item.strip()

                if name == 'top^out':
                    # just one output
                    index = 0

                else:
                    #extract the index from the name
                    nums = re.findall(r'\d+', item)
                    nums = [int(i) for i in nums ]

                    index = nums[-1]

                #add the io to the blifFile object
                blifIO = BlifIO(name,index)
                blifFile.outputs.append(blifIO)

            #read the next line
            line = fh.readline()

        #got a latch
        elif line.find(".latch") > -1:

            #read items until no more backslashes
            items = line.strip().split(' ',1)[1].strip().split(' ')
            while items[-1] == '\\':
                items = items[:-1]
                nextline = fh.readline()
                items = items + nextline.strip().split(' ')

            #get the net names
            inputNet = items[0]
            outputNet = items[1]

            #add the latch to the blifFile object
            blifLatch = BlifLatch(inputNet,outputNet)
            blifFile.latches.append(blifLatch)

            #read the next line
            line = fh.readline()

        #got a lut.
        elif line.find(".names") > -1:

            #first read the input nets and output net names, then parse the content

            #read items until no more backslashes appear
            items = line.strip().split(' ')[1:]
            while items[-1] == '\\':
                items = items[:-1]
                nextline = fh.readline()
                items = items + nextline.strip().split(' ')

            #parse input nets and output nets
            inputNets = items[:-1]
            outputNet = items[-1]

            #now read the content
            line = fh.readline()
            items = line.split()
            content = []

            #ABC format of the content of a logic gate:
            #1) if the content consist of only a 1 or 0, then we have
            #   a constant 1 or 0 as the output
            #2) else we have at least one a PLA description line
            #   like 0101-1 1 or 01- 0

            #internal representation:
            # For 1) we store a tuple ('-', constant output value)
            # and for 2) we store the two given values:
            # (k-input,output value)

            while items[-1] == '1' or items[-1] == '0' :
                #option 1)
                #just a single output value
                if (len(items) < 2):
                    content.append(('-',items[0]))
                #option 2)
                else:
                    content.append((items[0],items[1]))

                line = fh.readline()
                items = line.split()

            #assign the content and other infos to a blifFile object
            blifNames = BlifNames(inputNets,outputNet,content)
            blifFile.names.append(blifNames)

        else:
            #read the next line
            line = fh.readline()

    #return the gathered infos
    return blifFile


def simpleTest():

    blif = parseBlif('abc_out.blif')

    print "\ninputs \n"
    for input in blif.inputs:
        print str(input.blifName) +" "+ str(input.ioIndex) + "\n"

    print "\noutputs \n"
    for output in blif.outputs:
        print str(output.blifName) +" "+ str(output.ioIndex) + "\n"

    print "\n latchces \n"
    for latch in blif.latches:
        print str(latch.inputNet) +" "+ str(latch.ouputNet) + "\n"

    print "\n names \n"
    for name in blif.names:
        print str(name.inputNets) +" "+ str(name.ouputNet) + "\n"
        print str(name.content)

def main():
    simpleTest()

if __name__ == '__main__':
    main()
