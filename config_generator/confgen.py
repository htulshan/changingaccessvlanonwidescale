#!/usr/bin/env python3
"to generate config files for devices using jinja module"

from jinja2 import Environment, FileSystemLoader
import csv
import yaml

class ConfGen():

    def main(self):

        print("=="*20)
        input("Ensure that all the input data is present in input/templates, input/result.csv, press RETURN to continue")


        #setting the environment parameters for jinja
        print("=="*20)
        print("Reading Template from 'input/templates'.")
        env = Environment(loader=FileSystemLoader('input/templates'))
        template = env.get_template('intdescriptiontemp.txt')

        #input data of result.csv
        print("=="*20)
        print("Reading 'input/result.csv'.")
        devicelist = []
        with open('input/result.csv') as f:
            devicelist = list(csv.DictReader(f))

        writeresultlist = []
        #to create config file per device
        print("=="*20)
        print("Reading input variable files from 'input/inputfiles/', and writing config to 'output/outputfiles/'.")
        for device in devicelist:
            devicedict = {}
            devicedict = device.copy()

            #to get variable list of device
            devicedata = []
            with open(f'input/inputfiles/{device["filename"]}') as f:
                devicedata = yaml.safe_load(f)

            #to write config file of the device and writting it to file 'output/outputfiles/{device["ip"]}_config.txt'
            with open(f'output/outputfiles/{device["ip"]}_config.txt', 'w') as f:
                f.write(template.render(devicedata))
            devicedict['filename'] = f'{device["ip"]}_config.txt'
            devicedict['filecreated'] = True

            writeresultlist.append(devicedict)

        #writing result to result.csv file
        with open('output/result.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames = list(writeresultlist[0].keys()), quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            writer.writeheader()
            for d in writeresultlist:
            	writer.writerow(d)

        print("=="*20)
        input("Data has been written in 'output/outputfiles/{device[ip]}_config.txt', output/result.csv. Press RETURN to exit script")
        print("=="*20)

if __name__ == "__main__":
    test = ConfGen()
    test.main()
