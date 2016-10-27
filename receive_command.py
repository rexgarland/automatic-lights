import imaplib, smtplib, email, getpass
import os, re, threading, pickle, sys
import time, datetime
import numpy as np

import light_control

RECEIVEDFILE = 'received_email_ids.dat'

def isintstring(s):
	try:
		assert type(s) is str
		int(s)
		return True
	except:
		return False

def isemailidlist(l):
	if type(l) is not list:
		return False
	else:
		if not all([(len(str(s))==4 and isintstring(s)) for s in l]):
			return False
		else:
			return True

def get_log_dict():
	"""Method for loading the log dict. Returns the log dict with guaranteed 'last_update' and 'received_ids' elements."""
	try:
		with open(RECEIVEDFILE, 'r') as f:
			log_dict = pickle.load(f)
		assert type(log_dict) is dict
	except:
		# set initial last_update to a year ago
		log_dict = {'last_update': datetime.datetime.now()-datetime.timedelta(days=365), 'received_ids': []}
	try:
		assert type(log_dict['last_update']) is datetime.datetime
	except:
		log_dict['last_update'] = datetime.datetime.now()-datetime.timedelta(days=365)
	if not isemailidlist(log_dict['received_ids']):
		log_dict['received_ids'] = []
	return log_dict

def write_log_dict(log_dict):
	assert type(log_dict) is dict
	assert isemailidlist(log_dict['received_ids'])
	assert type(log_dict['last_update']) is datetime.datetime
	with open(RECEIVEDFILE, 'w') as f:
		pickle.dump(log_dict, f)

def write_read_email_ids(emailids):
	"""Records a list of email ids "emailids" that have been fetched and read."""
	log_dict = get_log_dict()
	for emailid in emailids:
		if str(emailid) not in log_dict['received_ids']:
			log_dict['received_ids'] += [str(emailid)]
	write_log_dict(log_dict)

def get_new_email_ids(server):
	"""Returns a list of email ids of emails on the imap server "server" from my cellphone that haven't been fetched yet."""
	server.select("INBOX")
	log_dict = get_log_dict()
	last_update = datetime.datetime.strftime(log_dict['last_update'], '%d-%b-%Y')
	resp, items1 = server.search(None, 'FROM', '"3109244701@txt.att.net"', 'SINCE', last_update) # you could filter using the IMAP rules here (check http://www.example-code.com/csharp/imap-search-critera.asp)
	resp, items2 = server.search(None, 'FROM', '"3109244701@mms.att.net"', 'SINCE', last_update)
	items = items1[0].split() + items2[0].split()
	return [item for item in items if item not in log_dict['received_ids']] # only consider emails that haven't been checked

def message_from_id(emailid, imapserver):
	"""Returns the message string from an email with email id "emailid" on server "imapserver"."""
	imapserver.select("INBOX")
	resp, data = imapserver.fetch(str(emailid), "(RFC822)") # fetching the mail, "`(RFC822)`" means "get the whole stuff", but you can ask for headers only, etc
	email_body = data[0][1] # get the mail content
	return email.message_from_string(email_body) # parsing the mail content to get a mail object

def log(server):
	"""Fetches responses from the server that contain flashcard additions from the user.
	Flashcard additions are signaled in the user's text message by prefixing the text message with a filename on the first line.
	Returns a card_updates dict {filename: cards}, where cards is a list of tuples (front_text, back_text)."""
	read_email_ids = []

	reviews = []; card_updates = {}; frequency_updates = {}

	new_email_ids = get_new_email_ids(server)
	for emailid in new_email_ids:
		message = message_from_id(emailid, server)
		if 'Subject' not in message.keys(): # email threads initiated by a cellphone will not have a subject line
			print message
			light_control.turn_light_off()
		read_email_ids += [emailid]
	write_read_email_ids(read_email_ids)


class Receive(object):
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.server = None
		self.abort = False
		try:
			self.update_server()
		except Exception as e:
			print e
			self.abort = True
		light_control.setup()

	def update_server(self):
		if not self.server:
			self.server = imaplib.IMAP4_SSL("imap.gmail.com")
		if self.server.state!='AUTH':
			self.server = imaplib.IMAP4_SSL("imap.gmail.com")
			self.server.login(self.username, self.password)

	def run(self):
		while not self.abort:
			time.sleep(2)
			try:
				self.update_server()
			except:
				print "Error: smtp authentication failed. Check login information."
				self.abort = True
			log(self.server)

if __name__=='__main__':
	USERNAME = getpass.getpass("Enter your Gmail username: ")
	PASSWORD = getpass.getpass("Enter your Gmail password: ")
	receiver = Receive(USERNAME, PASSWORD)
	receiver.run()