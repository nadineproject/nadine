#!/usr/bin/python

import os
import sys
import glob
from settings import *

java_dir = "py4j_gateway"
java_file = "USAePayBridge"

def needCompile():
	if not os.path.exists(java_dir + "/" + java_file + ".class"):
		return True
	if "-c" in sys.argv:
		return True
	return False

def getClasspath():
	cwd = os.getcwd()
	classpath = cwd + "/" + java_dir + "/"
	for jar in glob.glob(java_dir + "/*.jar"):
		classpath += ":" + cwd + "/" + jar
	return classpath

def main():
	cp = getClasspath()
	#print("classpath: " + cp)
	
	if needCompile():
		print("Compiling java class")
		compile_command = "javac -cp '" + cp + "' " + java_dir + "/" + java_file + ".java"
		#print compile_command
		if os.system(compile_command) > 0:
			print("Could not compile the java class!")
			return
	
	launch_command = "java -cp '" + cp + "' " + java_file + " " + USA_EPAY_URL + " " + USA_EPAY_KEY2 + " " + USA_EPAY_PIN2
 	#print launch_command
	os.system(launch_command)

if __name__ == '__main__':
        main()
