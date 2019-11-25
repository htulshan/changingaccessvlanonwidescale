#!/usr/bin/env python3
""" to push configs to multiple devices """

import argparse
import netmiko
import csv
from datetime import datetime
import time
import yaml
from getpass import getpass

class ConfPusher():

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', action = 'store', dest = 'firmware',
        default = 'cisco_ios', help = 'to store the firmware of the devices')
    firmware = parser.parse_args().firmware

    def connecttodevice(self):
        self.devicedata['device_type'] = self.firmware if self.devicedata['device_type'] is '' else self.devicedata['device_type']

        try:
            print(f"{datetime.now()} ===> Connection requested to device: {self.devicedata['ip']}")
            self.device = netmiko.ConnectHandler(device_type = self.devicedata['device_type'], ip = self.devicedata['ip'],
                username = self.username, password = self.password, secret = self.secret)

            self.device.enable()

        except:
            print(f"{datetime.now()} <=== Connection failed to device: {self.devicedata['ip']}")
            self.device = {}
        else:
            print(f"{datetime.now()} <=== Connection successful to device: {self.devicedata['ip']}")

    def collectpreconfigoutput(self):
        output = ''

        try:
            print(f"{datetime.now()} ===> Collecting pre-config show command output from: {self.devicedata['ip']}")
            for i in self.commands:
                output += self.device.send_command(i, strip_prompt = False, strip_command = False)
        except:
            print(f"{datetime.now()} <=== Unable to collect pre-config show command output from: {self.devicedata['ip']}")
            output += "Unable to capture preconfig"
        else:
            print(f"{datetime.now()} <=== Collected pre-config show command output from: {self.devicedata['ip']}")
        with open(f"confpusher/{self.devicedata['ip']}_preconfig.txt", 'w') as f:
            f.write(output)

    def displayconfig(self):
        print("Config to be pushed to the device is:")

        for i in self.devicedata['config']:
            print(i)

    def configuredevice(self):
        output = ''

        try:
            print(f"{datetime.now()} ===> Configuring device : {self.devicedata['ip']}")
            output = self.device.send_config_set(self.devicedata['config'])
        except KeyboardInterrupt as e:
            print(f"{datetime.now()} <=== Unable to configure device: {self.devicedata['ip']}")
            output = 'Unable to configure device'
        else:
            print(f"{datetime.now()} <=== Configured device: {self.devicedata['ip']}")
            print(output)

        with open(f"confpusher/{self.devicedata['ip']}_configurationcli.txt", 'w') as f:
            f.write(output)

    def saveconfig(self):

        try:
            print(f"{datetime.now()} ===> Saving configuration on device: {self.devicedata['ip']}")
            self.device.save_config()
        except:
            print(f"{datetime.now()} <=== Unable to save configuration on device: {self.devicedata['ip']}")
        else:
            print(f"{datetime.now()} <=== Configuration saved on device: {self.devicedata['ip']}")

    def collectpostconfigoutput(self):
        output = ''

        try:
            print(f"{datetime.now()} ===> Collecting post-config show command output from: {self.devicedata['ip']}")
            for i in self.commands:
                output += self.device.send_command(i, strip_prompt = False, strip_command = False)
        except:
            print(f"{datetime.now()} <=== Unable to collect post-config show command output from: {self.devicedata['ip']}")
            output += "Unable to capture preconfig"
        else:
            print(f"{datetime.now()} <=== Collected post-config show command output from: {self.devicedata['ip']}")
        with open(f"confpusher/{self.devicedata['ip']}_postconfig.txt", 'w') as f:
            f.write(output)


    def main(self):
        devicedata = []
        configlist = []

        input("Login data will be collected from 'logindata.csv'")
        input("Configuration files fill be collected from 'configfiles/'")

        print('=='*20)
        self.username = input("Enter the username: ")
        print('=='*20)
        self.password = getpass("Enter the password: ")
        print('=='*20)
        self.secret = getpass("Enter the enable password if any: ")
        print("=="*20)

        with open('logindata.csv') as f:
            devicedata = list(csv.DictReader(f))

        with open('showcommands.yaml') as g:
            self.commands = yaml.safe_load(g)

        self.commands += ['show running-config', 'show startup-config']

        for i in devicedata:
            try:
                with open(f'configfiles/{i["ip"]}_config.txt') as f:
                    output = f.read()
            except:
                pass
            else:
                deviceconfig = output.split('\n')
                configlist.append({'device_type': i['device_type'], 'ip': i['ip'], 'config': deviceconfig})

        for i in configlist:
            self.devicedata = i
            self.connecttodevice()
            if self.device:
                self.collectpreconfigoutput()
                self.displayconfig()

                abort = input("Do you want to apply the config?[NO/yes]: ")
                if abort.lower() == 'yes':
                    self.configuredevice()

                    abort = input("Do you want to save the config?[NO/yes]: ")
                    if abort.lower() == 'yes':
                        self.saveconfig()

                    self.collectpostconfigoutput()

        print("Output file saved to 'confpusher/'")
        input("Script complete, press RETURN to exit")


if __name__ == '__main__':
    test = ConfPusher()
    test.main()
