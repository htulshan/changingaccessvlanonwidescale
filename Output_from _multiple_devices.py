#!/usr/bin/env python3

from getpass import getpass
import argparse
from itertools import repeat
from concurrent.futures import ThreadPoolExecutor
import netmiko
import csv
import yaml
import logging
from datetime import datetime
import time

class OutputFromMultipleDevices():

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action = 'store', dest = 'firmware',
        default = 'cisco_ios', help='To determine the default firmware type')
    firmware = parser.parse_args().firmware

    logging.basicConfig(format = '%(threadName)s %(name)s %(levelname)s: %(message)s',level=logging.INFO)

    def login_and_collect_outputs(self, devicedata, username, password, secret, commandset):

        devicedata['device_type'] = self.firmware if devicedata['device_type'] is '' else devicedata['device_type']

        start_msg = '===> {} {}: {}'
        received_msg = '<=== {} {}: {}'

        path = f"collectingoutput/{devicedata['ip']}_output.txt"

        try:
            logging.info(start_msg.format(datetime.now(), 'Connection requested to', devicedata['ip']))
            device = netmiko.ConnectHandler(**devicedata, username = username, password = password, secret = secret)
            device.enable()
        except:
            logging.info(received_msg.format(datetime.now(), 'Connection failed to', devicedata['ip']))

            with open(path, 'w') as f:
                f.write('Unable to login\n')

            return False, False #login, collectedoutput

        else:
            collectedoutputs = True

            logging.info(received_msg.format(datetime.now(), 'Connection established with', devicedata['ip']))
            logging.info(start_msg.format(datetime.now(), 'Collecting output from', devicedata['ip']))

            output = ''
            for command in commandset:
                try:
                    output += f"{device.send_command(command)}\n"
                except:
                    output += f"{command}\nFalse\n"
                    collectedoutputs = False

            device.disconnect()
            logging.info(received_msg.format(datetime.now(), 'Collected outputs from', devicedata['ip']))

            with open(path, 'w') as f:
                f.write(output)

            return True, collectedoutputs #login, collectedoutput

    def save_output(self, logindata, result):
        outputfile = []

        data = zip(logindata, result)

        for device, resulttemp in data:
            device['login'], device['collectedoutput'] = resulttemp
            outputfile.append(device)

        with open('collectingoutputresult.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames = list(outputfile[0].keys()), quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            writer.writeheader()
            for d in outputfile:
                writer.writerow(d)


    def main(self):
        logindata = []
        commandset = []

        with open('logindata.csv') as f:
            logindata = list(csv.DictReader(f))

        print('=='*20)
        username = input("Enter the username: ")
        print('=='*20)
        password = getpass("Enter the password: ")
        print('=='*20)
        secret = getpass("Enter the enable password if any: ")
        print("=="*20)

        print('Reading show command.')
        with open('commandset.yaml') as f:
            commandset = yaml.safe_load(f)

        print("=="*20)
        print('Connecting to devices and collecting outputs.')
        with ThreadPoolExecutor(max_workers=5) as executor:
            result = list(executor.map(self.login_and_collect_outputs, logindata, repeat(username), repeat(password), repeat(secret), repeat(commandset)))

        self.save_output(logindata, result)
        input("Script complete, press RETURN to exit")


if __name__ == "__main__":
    test = OutputFromMultipleDevices()
    test.main()
