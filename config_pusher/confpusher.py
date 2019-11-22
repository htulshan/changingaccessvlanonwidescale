#!/usr/bin/env python3
""" to push configs to multiple devices """

from itertools import repeat
from concurrent.futures import ThreadPoolExecutor
import netmiko
import csv
import logging
from datetime import datetime
import time
import yaml

class ConfPusher():

    logging.basicConfig(format = '%(threadName)s %(name)s %(levelname)s: %(message)s',level=logging.INFO)

    def pre_config(self, device, commandset, ip):

        showrun = ''
        output = ''
        start_msg = '===> {} {}: {}'
        received_msg = '<=== {} {}: {}'

        try:
            logging.info(start_msg.format(datetime.now(), 'Collecting preconfig outputs from', ip))

            showrun = device.send_command("show running-config", strip_command=False)

            if commandset:
                for command in commandset:
                    output += device.send_command(command, strip_command=False) +"\n"

        except  ValueError:
            logging.info(received_msg.format(datetime.now(), 'Unable to collect preconfig outputs from', ip))
            return showrun, output, False
        else:
            logging.info(received_msg.format(datetime.now(), 'Collected preconfig outputs from', ip))
            return showrun, output, True

    def config_device(self, device, configcommands, ip):

        output = ''
        start_msg = '===> {} {}: {}'
        received_msg = '<=== {} {}: {}'

        try:
            logging.info(start_msg.format(datetime.now(), 'Pushing config to', ip))
            output += device.send_config_set(configcommands) + "\n"
        except:
            logging.info(received_msg.format(datetime.now(), 'Failed to push config on', ip))
            return output, False
        else:
            logging.info(received_msg.format(datetime.now(),'Successfully pushed configuration on', ip))
            return output, True

    def post_config(self, device, commandset, ip):

        showrun = ''
        output = ''
        start_msg = '===> {} {}: {}'
        received_msg = '<=== {} {}: {}'

        try:
            logging.info(start_msg.format(datetime.now(), 'Collecting postconfig outputs from', ip))
            showrun = device.send_command("show running-config", strip_command=False)

            if commandset:
                for command in commandset:
                    output += device.send_command(command, strip_command=False) +"\n"

        except:
            logging.info(received_msg.format(datetime.now(), 'Unable to collect postconfig outputs from', ip))
            return showrun, output, False
        else:
            logging.info(received_msg.format(datetime.now(), 'Collected postconfig outputs from', ip))
            return showrun, output, True

    def per_device_operations(self, devicedict, commandset):

        start_msg = '===> {} {}: {}'
        received_msg = '<=== {} {}: {}'

        devicedata = devicedict.copy()
        filenname = devicedata.pop('filename', None)
        configcommands = devicedata.pop('configcommands', None)

        devicedata.pop('filecreated', None)
        devicedata['banner_timeout'] = 10

        try:
            logging.info(start_msg.format(datetime.now(), 'Connection requested to', devicedata['ip']))
            device = netmiko.ConnectHandler(**devicedata)
            device.enable()
        except:
            logging.info(received_msg.format(datetime.now(), 'Connection failed to', devicedata['ip']))
            devicedata['preconfigshrun'] = 'NA'
            devicedata['preconfigoutput'] = 'NA'
            devicedata['preconfigoutputcollected'] = False
            devicedata['postconfigshrun'] = 'NA'
            devicedata['postconfigoutput'] = 'NA'
            devicedata['postconfigoutputcollected'] = False
            devicedata['configoutput'] = 'NA'
            devicedata['configured'] = False

        else:
            logging.info(received_msg.format(datetime.now(), 'Connection established with', devicedata['ip']))

            devicedata['preconfigshrun'], devicedata['preconfigoutput'], devicedata['preconfigoutputcollected'] = self.pre_config(device, commandset, devicedata['ip'])
            if devicedata['preconfigoutputcollected']:
                devicedata['configoutput'], devicedata['configured'] = self.config_device(device, configcommands, devicedata['ip'])
                if devicedata['configured']:
                    devicedata['postconfigshrun'], devicedata['postconfigoutput'], devicedata['postconfigoutputcollected'] = self.post_config(device, commandset, devicedata['ip'])
                else:
                    devicedata['postconfigshrun'] = 'NA'
                    devicedata['postconfigoutput'] = 'NA'
                    devicedata['postconfigoutputcollected'] = False
            else:
                    devicedata['postconfigshrun'] = 'NA'
                    devicedata['postconfigoutput'] = 'NA'
                    devicedata['postconfigoutputcollected'] = False
                    devicedata['configoutput'] = 'NA'
                    devicedata['configured'] = False
        return devicedata


    def write_data(self, devicedatarx):

        devicedata = devicedatarx.copy()

        preconfigshrun = devicedata.pop('preconfigshrun', 'NA')
        preconfigoutput = devicedata.pop('preconfigoutput', 'NA')
        configoutput = devicedata.pop('configoutput', 'NA')
        postconfigshrun = devicedata.pop('postconfigshrun', 'NA')
        postconfigoutput = devicedata.pop('postconfigoutput', 'NA')

        with open(f'output/outputfiles/preconfig/{devicedata["ip"]}_preconfig_run.txt', 'w') as f:
            f.write(preconfigshrun)
        with open(f'output/outputfiles/preconfig/{devicedata["ip"]}_preconfig_extracommands.txt', 'w') as f:
            f.write(preconfigoutput)
        with open(f'output/outputfiles/configoutput/{devicedata["ip"]}_config.txt', 'w') as f:
            f.write(configoutput)
        with open(f'output/outputfiles/postconfig/{devicedata["ip"]}_postconfig_run.txt', 'w') as f:
            f.write(postconfigshrun)
        with open(f'output/outputfiles/postconfig/{devicedata["ip"]}_postconfig_extracommands.txt', 'w') as f:
            f.write(postconfigoutput)

        return devicedata

    def save_config(self, excludedips, devicedata):

        start_msg = '===> {} {}: {}'
        received_msg = '<=== {} {}: {}'

        tempdevicedata = {}
        tempdevicedata['device_type'] = devicedata['device_type']
        tempdevicedata['ip'] = devicedata['ip']
        tempdevicedata['username'] = devicedata['username']
        tempdevicedata['password'] = devicedata['password']
        tempdevicedata['secret'] = devicedata['secret']

        try:
            logging.info(start_msg.format(datetime.now(), 'Connection requested to', devicedata['ip']))
            device = netmiko.ConnectHandler(**tempdevicedata)
            device.enable()

        except:
            logging.info(received_msg.format(datetime.now(), 'Connection failed to', devicedata['ip']))
            devicedata['SavedConfig'] = False
            devicedata['startupconfig'] = 'unable to fetch startup config'

        else:
            logging.info(received_msg.format(datetime.now(), 'Connection established with', devicedata['ip']))

            if tempdevicedata['ip'] in excludedips:
                pass
                devicedata['SavedConfig'] = False
            else:
                try:
                    logging.info(start_msg.format(datetime.now(), 'Saving configuraiton on', devicedata['ip']))
                    device.save_config()
                    logging.info(received_msg.format(datetime.now(), 'Configuration saved on', devicedata['ip']))
                    devicedata['SavedConfig'] = True
                except:
                    logging.info(received_msg.format(datetime.now(), 'Unable to save config on', devicedata['ip']))
                    devicedata['SavedConfig'] = False
            try:
                logging.info(start_msg.format(datetime.now(), 'Collecting startup config from', devicedata['ip']))
                devicedata['startupconfig'] = device.send_command("show startup-config", strip_command=False)
                logging.info(received_msg.format(datetime.now(), 'Collected startup config from', devicedata['ip']))
            except:
                logging.info(received_msg.format(datetime.now(), 'Unable to collect startup config from', devicedata['ip']))
                devicedata['startupconfig'] = 'unable to fetch startup config'


    def main(self):
        print("=="*20)
        input("""Please confirm all the input data is saved to : input/result.csv,
input/commandlist.yaml, input/inputfiles/{device["ip"]}_config.txt.
Press RETURN to confirm""")

        deviceresultlist = []

        print("=="*20)
        print("Reading data from input/result.csv.")
        with open('input/result.csv') as f:
            logindatalist = list(csv.DictReader(f))

        print("=="*20)
        print("Reading data from input/commandlist.yaml.")
        with open('input/commandlist.yaml') as f:
            commandsetlist = yaml.safe_load(f)

        print("=="*20)
        print("Reading data from input/inputfiles/{device['ip']}_config.txt")
        for device in logindatalist:
            with open(f'input/inputfiles/{device["ip"]}_config.txt') as f:
                commandstring = f.read().strip()
                device['configcommands'] = commandstring.split('\n')

        print("=="*20)
        print("Performing actions on network devices")
        print("=="*20)
        with ThreadPoolExecutor(max_workers=5) as executor:
            result = list(executor.map(self.per_device_operations, logindatalist, repeat(commandsetlist)))
        print("=="*20)
        print("All necessary actions performed on network devices.")


        print("=="*20)
        print("Writing output data.")
        for device in result:
            deviceresult = self.write_data(device)
            deviceresultlist.append(deviceresult)

        print("=="*20)
        print("Writing output result data.")
        with open('output/result.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames = list(deviceresultlist[0].keys()), quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            writer.writeheader()
            for d in deviceresultlist:
            	writer.writerow(d)

        print("=="*20)
        print("Please perform manual checks before we save the configurations.")

        print("=="*20)
        print("Input IPs for which configuration is NOT to be save, Enter 'OK' one done.")
        excludedips = []
        while True:

            ip = input()
            if ip == 'OK':
                break
            else:
                excludedips.append(ip)

        print("=="*20)
        print("Saving configuration.")
        with open('output/result.csv') as f:
            devicedatalist = list(csv.DictReader(f))

        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.save_config, repeat(excludedips), devicedatalist)

        for device in devicedatalist:
            postconfigstartupconf = device.pop('startupconfig', 'NA')

            with open(f'output/outputfiles/postconfig/{device["ip"]}_postconfig_startup.txt', 'w') as f:
                f.write(postconfigstartupconf)

        print("=="*20)
        print("Writing output result data.")
        with open('output/result.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames = list(devicedatalist[0].keys()), quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            writer.writeheader()
            for d in devicedatalist:
            	writer.writerow(d)

        print("=="*20)
        input("All required changes have been made and relevant data has been saved to output files, Press Retrun to exit the script")
        print("=="*20)


        

if __name__ == '__main__':
    test = ConfPusher()
    test.main()
