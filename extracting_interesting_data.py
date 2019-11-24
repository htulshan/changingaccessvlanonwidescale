#!/usr/bin/env python3
""" To generate variable list for config generation using jinja lib """

from getpass import getpass
import argparse
from itertools import repeat
from concurrent.futures import ThreadPoolExecutor
import netmiko
import csv
import logging
from datetime import datetime
import time


class GeneratingVaribalefiles():

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action = 'store', dest = 'firmware',
        default = 'cisco_ios', help='To determine the default firmware type')
    firmware = parser.parse_args().firmware

    logging.basicConfig(format = '%(threadName)s %(name)s %(levelname)s: %(message)s',level=logging.INFO)

    def login_and_collect_outputs(self, devicedata, username, password, secret, command):
        login = False
        collectedoutput = True

        devicedata['device_type'] = self.firmware if devicedata['device_type'] is '' else devicedata['device_type']

        start_msg = '===> {} {}: {}'
        received_msg = '<=== {} {}: {}'

        try:
            logging.info(start_msg.format(datetime.now(), 'Connection requested to', devicedata['ip']))
            device = netmiko.ConnectHandler(**devicedata, username = username, password = password, secret = secret)
            device.enable()

        except:
            logging.info(received_msg.format(datetime.now(), 'Connection failed to', devicedata['ip']))
            login = False
            collectedoutput = False

            return login, collectedoutput, []

        else:

            logging.info(received_msg.format(datetime.now(), 'Connection established with', devicedata['ip']))
            login = True
            logging.info(start_msg.format(datetime.now(), 'Collecting output from', devicedata['ip']))

            output = []
            try:
                output = device.send_command(command, use_textfsm=True)
                if type(output) is list:
                    pass
                else:
                    collectedoutput = False

            except:
                logging.info(received_msg.format(datetime.now(), 'Unable to collect output from', devicedata['ip']))
                collectedoutput = False

            device.disconnect()
            logging.info(received_msg.format(datetime.now(), 'Collected outputs from', devicedata['ip']))


            return login, collectedoutput, output

    def filter_data(self, logindata, output):

        tempdata = zip(logindata, output)
        filtereddata = []

        for device, data in tempdata:
            if data[0] and data[1] and data[2]:
                for interface in data[2]:
                    if interface['vlan'].isnumeric():
                        entry = {}
                        entry['ip'] = device['ip']
                        entry['interface'] = interface['port']
                        entry['vlan'] = interface['vlan']
                        filtereddata.append(entry)

        return filtereddata


    def save_output(self, logindata, result, filtereddata):
        outputfile = []

        data = zip(logindata, result)

        for device, resulttemp in data:
            device['login'], device['collectedoutput'], _ = resulttemp
            outputfile.append(device)

        with open('extractinginterestingdataresult.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames = list(outputfile[0].keys()), quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            writer.writeheader()
            for d in outputfile:
                writer.writerow(d)

        if filtereddata:
            with open('extractinginterestingdata.csv', 'w') as f:
                writer = csv.DictWriter(f, fieldnames = list(filtereddata[0].keys()), quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
                writer.writeheader()
                for d in filtereddata:
                    writer.writerow(d)


    def main(self):
        logindata = []
        command = "show interface status"

        with open('logindata.csv') as f:
            logindata = list(csv.DictReader(f))

        print('=='*20)
        username = input("Enter the username: ")
        print('=='*20)
        password = getpass("Enter the password: ")
        print('=='*20)
        secret = getpass("Enter the enable password if any: ")
        print("=="*20)

        print("=="*20)
        print('Connecting to devices and collecting outputs.')
        with ThreadPoolExecutor(max_workers=5) as executor:
            result = list(executor.map(self.login_and_collect_outputs, logindata, repeat(username), repeat(password), repeat(secret), repeat(command)))

        filtereddata = self.filter_data(logindata, result)

        self.save_output(logindata, result, filtereddata)

        input("Script complete, press RETURN to exit")


if __name__ == '__main__':
    test = GeneratingVaribalefiles()
    test.main()
