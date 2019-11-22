#!/usr/bin/env python3
""" To generate variable list for config generation using jinja lib """

import csv
import re
import yaml
class GeneratingVaribalefiles():

    #to read the result csv for extracting data
    def input(self):

        devicelist = []

        print("=="*20)
        input("Confirm that all the required data is store in input/result, input/inputfiles/files, press RETURN to continue")

        print("=="*20)
        print("Reading data from input/result.csv") #reads the result csv
        with open('input/result.csv') as f:
            devicelist = list(csv.DictReader(f))

        return devicelist


    #to take data from data file and using a reg extracting interesting data
    def extract_variale(self, data):

        cdpreg = 'Device ID: (?P<deviceid>\S+).+?Interface: (?P<localinterface>\S+[^,\s]).+?Port ID \(outgoing port\): (?P<remoteport>\S+)'

        match = re.findall(cdpreg, data, re.DOTALL)
        writedata = []
        writedict = {}
        if match:
            for i in match:
                datadict = {
                    'deviceid' : i[0],
                    'localint' : i[1],
                    'remoteint' : i[2]
                    }
                writedata.append(datadict)
        writedict['variables'] = writedata
        return(writedict)


    #to write data to file
    def write_data(self, writedata, ip):

        if writedata:

            with open(f'output/outputfiles/{ip}_variable.yaml', 'w') as f:
                yaml.dump(writedata, f)
            return f'{ip}_variable.yaml', True

        return NA, False

    def main(self):

        #to get the csv file
        devicelist = self.input()
        writeresult = []
        #to read data for each device
        for device in devicelist:
            data = ''
            with open(f'input/inputfiles/{device["filename"]}') as f:
                data = f.read()

            #extracing interesting data
            devicevariables = self.extract_variale(data)

            #writing data to file
            filename, filecreated = self.write_data(devicevariables, device['ip'])

            #writing result to csv
            devicedata = device.copy()
            devicedata['filename'] = filename
            devicedata['filecreated'] = filecreated

            writeresult.append(devicedata)

        with open('output/result.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames = list(writeresult[0].keys()), quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            writer.writeheader()
            for d in writeresult:
            	writer.writerow(d)

        print("=="*20)
        input("Data written to output/outputfiles/, output/result.csv. Press RETURN to exit the script. ")
        print("=="*20)


if __name__ == '__main__':
    test = GeneratingVaribalefiles()
    test.main()
