#!/usr/bin/env python3

import argparse
from itertools import repeat
from concurrent.futures import ThreadPoolExecutor
import netmiko
import time
import csv
from getpass import getpass
import logging
from datetime import datetime
import time

class Login():

	logging.basicConfig(format = '%(threadName)s %(name)s %(levelname)s: %(message)s',level=logging.INFO)

	parser = argparse.ArgumentParser()
	parser.add_argument('-f', action='store', dest = 'firmware',
	 	default='cisco_ios', help="To determine the default firmware type")
	firmware = parser.parse_args().firmware

	#to check if a particular ip can we logged into using the usernames and passwords for SSH enaled clients
	def ssh_login(self, devicedata, username, password, secret):

		sent_msg = '===> {} {}:{}'
		rcvd_msg = '<=== {} {}:{}'

		if devicedata['device_type']:
			pass
		else:
			devicedata['device_type'] = self.firmware

		try:
			logging.info(sent_msg.format(datetime.now(), 'Connecting to device', devicedata['ip']))
			device = netmiko.ConnectHandler(**devicedata, username = username, password = password, secret = secret)
			device.enable()
		except:
			logging.info(rcvd_msg.format(datetime.now(), 'Unable to log into', devicedata['ip']))
			return False
		else:
			logging.info(rcvd_msg.format(datetime.now(), 'Login successful to', devicedata['ip']))
			device.disconnect()
			return True

	def save_output(self, inputdata, loginresult):
		outputfile = []

		result = zip(inputdata, loginresult)

		for device, deviceresult in result:
			device['login'] = deviceresult
			outputfile.append(device)

		with open('loginresult.csv', 'w') as f:
		    writer = csv.DictWriter(f, fieldnames = list(outputfile[0].keys()), quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
		    writer.writeheader()
		    for d in outputfile:
		        writer.writerow(d)

	def main(self):
		logindata = []
		loginresult = []

		input("Login data will be collected from 'logindata.csv'. ")

		with open('logindata.csv') as f:
			logindata = list(csv.DictReader(f))

		print('=='*20)
		username = input("Enter the username: ")
		print('=='*20)
		password = getpass("Enter the password: ")
		print('=='*20)
		secret = getpass("Enter the enable password if any: ")

		#trying to login into SSH enaled devices.
		print('=='*20)
		print("Trying to login into devices.")
		print('=='*20)
		with ThreadPoolExecutor(max_workers=5) as executor:
			loginresult = list(executor.map(self.ssh_login, logindata, repeat(username), repeat(password), repeat(secret)))

		self.save_output(logindata, loginresult)

		print("Script result stored in 'loginresult.csv'.")
		input("Script complete, press RETURN to exit")

if __name__ == "__main__":
	test = Login()
	test.main()
