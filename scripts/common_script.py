#!/usr/bin/python
import os

"""A set of handy functions for IT scripts. """

DEBUG = False

def call_system(command):
	print command
	if DEBUG: return True
	return os.system(command) == 0