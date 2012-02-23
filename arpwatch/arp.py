import time
from datetime import datetime, timedelta, date

def handle_uploaded_file(file):
	for chunk in file.chunks():
		print(chunk)
