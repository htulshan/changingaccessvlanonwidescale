#!/usr/bin/env python3

"to generate config files for devices using jinja module"

from jinja2 import Environment, FileSystemLoader
import csv

class ConfGen():

    def generateconfigfiles(self, device, data):

        env = Environment(loader=FileSystemLoader(''))
        template = env.get_template('vlanassignment.txt')
        with open(f'configfiles/{device}_config.txt', 'w') as f:
            f.write(template.render(data))

        print(device)


    def main(self):

        input("Data to generate config will be collected from 'confgendata.csv'")
        data = []
        configsrcdata = []

        #filtering data to extract interesting interfaces
        with open('confgendata.csv') as f:
            data = list(csv.DictReader(f))

        for interface in data:
            newinterface = {}
            if interface['vlan'] != interface['newvlan']:
                newinterface['ip'] = interface['ip']
                newinterface['port'] = interface['interface']
                newinterface['vlan'] = interface['newvlan']
                configsrcdata.append(newinterface)

        #generating unique device list
        devices = list(set([interface['ip'] for interface in configsrcdata]))
        devices.sort()

        #creting dictonary of devices and interface to be configured
        devicedata = {}
        for i in devices:
            devicedata[i] = []
            for j in configsrcdata:
                if j['ip'] == i:
                    devicedata[i].append({'port' : j['port'], 'vlan': j['vlan']})

        print("Generated config for:")

        for device, configdata in devicedata.items():
            self.generateconfigfiles(device, {'variables':configdata})

        print("Configuration files saved to 'configfiles/'.")
        input("Script complete, press RETURN to exit")

if __name__ == "__main__":
    test = ConfGen()
    test.main()
