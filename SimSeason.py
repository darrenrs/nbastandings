class ProgressBar:
	def __init__(self,msg,end,cnt,len,dc,pc):
		self.prefix = msg
		self.suffix = end
		self.total = int(cnt)
		self.length = int(len)
		self.doneChar = dc[:1]
		self.progChar = pc[:1]
		self.counter = 0
		self.complete = False
	def push(self):
		self.counter += 1
		if self.complete == True:
			return None
		elif self.counter == self.total:
			sys.stdout.write(self.prefix+' | ['+(self.doneChar*self.length)+'] 100.00% ')
			sys.stdout.write('\r\n')
			self.end()
		else:
			sys.stdout.write(self.prefix+' | ['+self.indicator(self.percentage(self.counter))+'] '+format(float(self.percentage(self.counter))*100,'.3f')+'%')
			sys.stdout.write('\r')
			sys.stdout.flush()
	def percentage(self,c):
		return c/self.total
	def indicator(self,p):
		currLen = round((float(p))*self.length)
		return (self.doneChar*currLen)+(self.progChar*(self.length-currLen))
	def end(self):
		print(self.suffix)
		self.complete = True

def setupConfig():
	os.chdir(os.path.dirname(__file__))
	
	try: # Attempt to open the config file
		open(_CFGFILENAME,'r')
	
	except FileNotFoundError: # There is no config file!
		print('\nNo config file found at {}'.format(_CFGFILENAME))
		print('Default settings will be used.')
		
		setupLoad(False) # Vars will be loaded from base defaults.
		
	else:
		try: # Attempt to process the config file
			_CONFIG.read(_CFGFILENAME)
		
		except configparser.ParsingError: # The file is corrupt.
			print('\nConfig file at {} is corrupt!'.format(_CFGFILENAME))
			print('Default settings will be used.')
			
			setupLoad(False) # Vars will be loaded from base defaults.
			
		else:
			global _CFGDATALOAD
			_CFGDATALOAD = True # Mark that the file is valid.
			
			setupLoad(True) # Vars will be loaded from config data.
			
def setupLoad(t):
	if not t: # The config file did not load successfully
		for key, val in zip(_SS_DEFAULTSETTINGKEYS, _SS_DEFAULTSETTINGVALS): # Iterate through the default keys and values
			globals()[key] = val # Set variables as globals
	
	else:
		# Manually set all globals.
		try:
			globals()['_SS_DATASRC'] = _CONFIG['Project']['DataSource']
			globals()['_SS_DATASRCFN'] = _CONFIG['Project']['DataSourceFile']
			globals()['_SS_EXPORT'] = _CONFIG['Project']['FileName']
			globals()['_SS_SIMCNT'] = abs(_CONFIG['Project'].getint('Simulate'))
			globals()['_SS_DODOWNLD'] = _CONFIG['Project'].getboolean('DownloadFile')
			globals()['_SS_SHOWPB'] = _CONFIG['Visual'].getboolean('ProgressBar')
			globals()['_SS_NAME'] = _CONFIG['Visual']['Name']
			globals()['_SS_SHOWOUTPUT'] = _CONFIG['Visual'].getboolean('ShowOutput')
			globals()['_SS_TCREATE'] = _CONFIG['Build'].getint('TimestampCreate')
			globals()['_SS_TUPDATE'] = _CONFIG['Build'].getint('TimestampUpdate')
			globals()['_SS_BUILD'] = _CONFIG['Build']['VersionString']
			globals()['_SS_PBCPROG'] = _CONFIG['Visual']['ProgBarIncompleteChar']
			globals()['_SS_PBCCMPT'] = _CONFIG['Visual']['ProgBarDoneChar']
		except KeyError as error:
			print('A critical key in the configuration file is missing:\n {}'.format(error))
			exit()

def initWelcome():
	global _CFGDATALOAD # Load the global state for this variable.
	
	# From this point on, we will welcome the user and print the config data.	
	if _CFGDATALOAD:
		print('\nWelcome to {}!'.format(_SS_NAME))
		
	print('\nThis program will simulate the remainder of the current NBA season a certain number of times. The results will be in a CSV file.')
	
	if _CFGDATALOAD:
		print('\nCreate Date\t{}'.format(datetime.fromtimestamp(_SS_TCREATE, pytz.timezone('America/Denver')).isoformat()))
		print('Update Date\t{}'.format(datetime.fromtimestamp(_SS_TUPDATE, pytz.timezone('America/Denver')).isoformat()))
		print('Version\t\t{}'.format(_SS_BUILD))
		
	print('\nData Source\t{}'.format(_SS_DATASRC))
	print('Data Source To\t{}'.format(_SS_DATASRCFN))
	print('File Name\t{}'.format(_SS_EXPORT))
	print('Simulations\t{}'.format(_SS_SIMCNT))
	print('Show Prog Bar\t{}'.format(_SS_SHOWPB))
	
def updateDataSrc():
	if _SS_SHOWOUTPUT: # Gets initial start time for download
		print('\nPreparing download of data source.')
		
		_BEGINTIME = time.time()
		
		print('Downloading data source ...')
	
	try:
		urllib.request.urlretrieve(_SS_DATASRC, _SS_DIRNAME+_SS_DATASRCFN)
	
	except urllib.error.HTTPError as error: # Handle HTTP status codes
		print('\nThe file was unable to download:\n[{}] {}'.format(error.code,error.reason))
		exit()
		
	except urllib.error.URLError as error: # Handle generic network errors
		print('\nThe file was unable to download correctly:\n{}'.format(error.reason))
		exit()
		
	except PermissionError as error: # Most likely the file is open, preventing it from being written to. Could also be an attrib error.
		print('\nThe file appears to be open on your system! Close it!')
		exit()
	
	if _SS_SHOWOUTPUT: # Gets end time for download and prints elapsed time & network speed.
		_ENDTIME = time.time()
		_ELAPSEDTIME = _ENDTIME-_BEGINTIME
		_FILESIZE = os.path.getsize(_SS_DIRNAME+_SS_DATASRCFN)
		print('Download completed successfully. ({:.3f} seconds, {:.2f} kB/s)'.format(_ELAPSEDTIME,(_FILESIZE/_ELAPSEDTIME)/1024))

'''
	Creates the volatile storage that will eventually be dumped to the csv file.
	Right now, all values are set to 0, because no simulations have yet occurred.
	
	It also creates the list of games to simulate.
'''

def createStorage():
	if _SS_SHOWPB:
		_PB_LISTS = ProgressBar('Creating volatile storage ...','Storage created!\n',_SS_TEAMCOUNT,36,_SS_PBCCMPT,_SS_PBCPROG)
	
	for s in _SS_ALLTEAMIDS: # Loop through all teams
		_TEAMWINS[s] = [0,0] # Idx 0 stores the current wins, Idx 1 stores the simulated wins per simulation.
		_SEEDPOS[s] = {"1":0,"2":0,"3":0,"4":0,"5":0,"6":0,"7":0,"8":0,"9":0,"10":0,"11":0,"12":0,"13":0,"14":0,"15":0} # Each key denotes a seed. The value is how many times that was simulated total.
		_WINTTL[s] = 0 # Stores the total simulated wins.
		_MINMAX[s] = [83,-1] # Idx 0 stores the minima wins, Idx 1 stores the maxima wins. The constant values are set to 83/-1 or -1/83 so the first season trial is able to modify the values correctly. 
		
		if _SS_SHOWPB:
			_PB_LISTS.push()

'''
	Computes ALL games that have been marked as completed. This function overrides date control.
'''

def games2Sim():
	if _SS_SHOWPB:
		_PB_GMS2S = ProgressBar('Getting schedules         ...','Schedules created!\n',len(range(_FGIDXSSN,_CSVLINES)),36,_SS_PBCCMPT,_SS_PBCPROG)

	for g in range(_FGIDXSSN,_CSVLINES):
		if str(_CSV['score1'][g]) == 'nan':
			_GAMES2SIM.append(g)
			
		if _SS_SHOWPB:
			_PB_GMS2S.push()
	
'''
	Processes the current win records of all teams by looping through played games.
	Win records are entered into the zeroth index per team key in _TEAMWINS.
'''

def currentWinRecords():
	if _SS_SHOWPB:
		_PB_WINRC = ProgressBar('Processing win records    ...','Win records processed!\n',len(list(range(_FGIDXSSN, _FGIDXSIMDAY))),36,_SS_PBCCMPT,_SS_PBCPROG)
	
	for w in range(_FGIDXSSN, _FGIDXSIMDAY): # Loop through all played games
		if int(_CSV['score1'][w]) > int(_CSV['score2'][w]): # Check if home team scored more than away team
			_TEAMWINS[_CSV['team1'][w]][0] += 1 # Yes, give the home team a win
		else:
			_TEAMWINS[_CSV['team2'][w]][0] += 1 # No, give the away team a win
		
		if _SS_SHOWPB:
			_PB_WINRC.push()
		
'''
	Controls the simulation of each season. There are several steps to the process for each individual season:
	
	1. Creates a random float for each game that is to be simulated.
	2. Checks if said float is greater than the win probability for the home team.
	3. If it is, then the away team won, and they are given a win.
	4. Otherwise, the home team won; they are given a win instead.
	5. Enters another function and begins to sort the data.
	6. After the data is sorted and the season completes, resets the data in order to simulate a brand new season.
'''

def simulateIndividualSeason():
	if _SS_SHOWPB:
		_PB_SIMSS = ProgressBar('Simulating seasons        ...','Seasons simulated!\n',_SS_SIMCNT,36,_SS_PBCCMPT,_SS_PBCPROG)
	
	for s in range(_SS_SIMCNT):
		_RANDOM = []
		for rg in range(len(_GAMES2SIM)):
			_RANDOM.append(random()) # Create a random float for each game that is to be simulated.
		for rn in range(len(_GAMES2SIM)):
			if _RANDOM[rn] > float(_CSV['carmelo_prob1'][_GAMES2SIM[rn]]): # Check who won the game
				_TEAMWINS[_CSV['team2'][_GAMES2SIM[rn]]][1] += 1 # Float greater than probability, so away team wins
			else:
				_TEAMWINS[_CSV['team1'][_GAMES2SIM[rn]]][1] += 1 # Float less than probability, so home team wins
		
		seasonDataSum(_TEAMWINS) # Sort & sum season data
		
		if _SS_SHOWPB:
			_PB_SIMSS.push()
			
		for rs in range(len(_TEAMWINS)): # Reset the win values for the next season.
			_TEAMWINS[_SS_ALLTEAMIDS[rs]][1] = 0

def seasonDataSum(w):
	_WTEAM = {}
	_WSORT = {}
	_ETEAM = {}
	_ESORT = {}
	
	for cs in range(_SS_TEAMCOUNT):
		_SSNWINS = w[_SS_ALLTEAMIDS[cs]][0] + w[_SS_ALLTEAMIDS[cs]][1]
		if _SS_CONFERENCE[cs]:
			_WTEAM[_SS_ALLTEAMIDS[cs]] = _SSNWINS
		else:
			_ETEAM[_SS_ALLTEAMIDS[cs]] = _SSNWINS
	
	# The following solution must be credited to Mark on StackOverflow. Thanks, Mark!
	# https://stackoverflow.com/a/2258273
	_WSORT = sorted(_WTEAM.items(), key=lambda x: x[1], reverse=True) # Sorts the WC teams by wins (returns a tuple)
	_ESORT = sorted(_ETEAM.items(), key=lambda x: x[1], reverse=True) # Sorts the EC teams by wins (returns a tuple)
	
	# Convert back to a dict
	_WSORT = dict(_WSORT)
	_ESORT = dict(_ESORT)
	
	# Add the current seed positions to the seed position master
	for sp in range(_SS_TEAMSPERCONF):
		_SEEDPOS[list(_WSORT.keys())[sp]][str(sp+1)] += 1
		_SEEDPOS[list(_ESORT.keys())[sp]][str(sp+1)] += 1
	
	# Add the season win total to the win master
	for wt in range(_SS_TEAMSPERCONF):
		_WINTTL[list(_WSORT.keys())[wt]] += _WSORT[list(_WSORT.keys())[wt]]
		_WINTTL[list(_ESORT.keys())[wt]] += _ESORT[list(_ESORT.keys())[wt]]
		
	# If the win count was an extreme, update the value in _MINMAX to reflect it.
	# This function will require some explaining.
	for mm in _SS_ALLTEAMIDS:
		if _SS_CONFERENCE[_SS_ALLTEAMIDS.index(mm)] == 0: # Checks the conference. If true, then team mm is in the East.
			if _ESORT[list(_ESORT.keys())[list(_ESORT.keys()).index(mm)]] < _MINMAX[mm][0]: # Checks if the current wins is less than the minima.
				_MINMAX[mm][0] = _ESORT[list(_ESORT.keys())[list(_ESORT.keys()).index(mm)]] # Set the minima to the current wins.
			if _ESORT[list(_ESORT.keys())[list(_ESORT.keys()).index(mm)]] > _MINMAX[mm][1]: # Checks if the current wins is greater than the maxima. The reason elif is not used is because the first season has it being both the min/max.
				_MINMAX[mm][1] = _ESORT[list(_ESORT.keys())[list(_ESORT.keys()).index(mm)]] # Set the maxima to the current wins.
			
		else: # Team mm is in the West.
			if _WSORT[list(_WSORT.keys())[list(_WSORT.keys()).index(mm)]] < _MINMAX[mm][0]:
				_MINMAX[mm][0] = _WSORT[list(_WSORT.keys())[list(_WSORT.keys()).index(mm)]]
			if _WSORT[list(_WSORT.keys())[list(_WSORT.keys()).index(mm)]] > _MINMAX[mm][1]:
				_MINMAX[mm][1] = _WSORT[list(_WSORT.keys())[list(_WSORT.keys()).index(mm)]]
			
			
		
def blankFile():
	try:
		open(_SS_DIRNAME+_SS_EXPORT,'w').close() # Blanks file for re-writing
	
	except PermissionError: # Most likely the file is open, preventing it from being written to. Could also be an attrib error. Because data may have been processing for a while, we give an option to retry.
		print('\nThe file appears to be open on your system!')
		input('Hit <ENTER> to attempt a re-write, or <CTRL+C> to cancel.')
		blankFile()
	
def writeCsv():
	_WINCOUNTS = []
	_ESORT = []
	_WSORT = []
	_LSORT = []
	
	_WINCOUNTS = sorted(_WINTTL.items(), key=lambda x: x[1], reverse=True) # Sorts all teams by total win count (returns a tuple)
	_WINCOUNTS = dict(_WINCOUNTS) # And... back to a dictionary.
	
	for k in list(_WINCOUNTS.keys()): # Create the conference team lists that will appear in the csv file.
		if _SS_CONFERENCE[_SS_ALLTEAMIDS.index(k)]: # Team is in the West
			_WSORT.append(k)
		else: # Team is in the East
			_ESORT.append(k)
	_LSORT = _ESORT + _WSORT # Merge the conferences for the master list.
	
	try:
		with open(_SS_DIRNAME+_SS_EXPORT,'a') as f: # Open the file as append.
			for c in range(0,2): # Iterate for each conference.
				if not c: # Start with the East; the y-intercept for range is 0 (idx 0-14)
					nc = 0
				else: # End with the West; the y-intercept for range is 15 (idx 15-29)
					nc = _SS_TEAMSPERCONF
				
				for head in range(0,_SS_TEAMSPERCONF): # Write the header row first
					if head == 0: # First cell must be 'Team'
						f.write('Team,'+_LSORT[head+nc]+',')
					elif head == 14: # If it's the last one, append a linebreak at the end
						f.write(_LSORT[head+nc]+'\n')
					else: # Otherwise, just write the team name
						f.write(_LSORT[head+nc]+',')
				
				for rows in range(0,_SS_TEAMSPERCONF):
					f.write(str(rows+1)+',')
					for teams in range(0,15):
						if teams == 14:
							f.write('{0:.4f}'.format(((_SEEDPOS[_LSORT[teams+nc]][str(rows+1)]/_SS_SIMCNT)*100))+'%\n')
						else:
							f.write('{0:.4f}'.format(((_SEEDPOS[_LSORT[teams+nc]][str(rows+1)]/_SS_SIMCNT)*100))+'%,')
				
				for wins in range(0,_SS_TEAMSPERCONF):
					if wins == 0:
						f.write('Wins,'+str(_WINTTL[_LSORT[wins+nc]]/_SS_SIMCNT)+',')
					elif wins == 14:
						f.write(str(_WINTTL[_LSORT[wins+nc]]/_SS_SIMCNT)+'\n')
					else:
						f.write(str(_WINTTL[_LSORT[wins+nc]]/_SS_SIMCNT)+',')
				
				for max in range(_SS_TEAMSPERCONF):
					if not max:
						a1 = 'Maxima,'
						a2 = ','
					elif max == _SS_TEAMSPERCONF-1:
						a1 = ''
						a2 = '\n'
					else:
						a1 = ''
						a2 = ','
					f.write(a1+str(_MINMAX[_LSORT[max+nc]][1])+a2)
				
				for min in range(_SS_TEAMSPERCONF):
					if not min:
						a1 = 'Minima,'
						a2 = ','
					elif min == _SS_TEAMSPERCONF-1:
						a1 = ''
						a2 = '\n'
					else:
						a1 = ''
						a2 = ','
					f.write(a1+str(_MINMAX[_LSORT[min+nc]][0])+a2)
				
				f.write('\n\n')
	except PermissionError: # Most likely the file is open, preventing it from being written to. Could also be an attrib error. Because data may have been processing for a while, we give an option to retry.
		print('\nThe file appears to be open on your system!')
		input('Hit <ENTER> to attempt a re-write, or <CTRL+C> to cancel.')
		writeCsv()
		

# Starts the program if executing from a file.
if __name__ == '__main__':
	try: # Attempt to import modules. This needs to be done before we even define constants.
		import configparser
		import os
		import sys
		import time
		import pytz
		import urllib
		import pandas as pd
		from random import random
		from datetime import datetime, timedelta
		
	except ImportError as error: # A module is missing? We can't run the program correctly.
		print('\nUnfortunately, you do not yet support this program, as this module is missing:\n{}'.format(error.name)) # Inform the user of the missing module
		print('\nPlease enter "pip install {}" into your shell to run this program!'.format(error.name)) # Suggest the PIP command to install the module
		
		exit(1)
	
	_CONFIG = configparser.ConfigParser() # Instantiate the configparser.
	
	_CFGFILENAME = 'SimSeason.ini' # The name of the config file.
	_CFGDATALOAD = False # Has the config file loaded yet?
	
	_SS_ALLTEAMIDS = ['ATL','BOS','BRK','CHI','CHO','CLE','DAL','DEN','DET','GSW','HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK','OKC','ORL','PHI','PHO','POR','SAC','SAS','TOR','UTA','WAS'] # All team IDs
	_SS_CONFERENCE = [0,0,0,0,0,0,1,1,0,1,1,0,1,1,1,0,0,1,1,0,1,0,0,1,1,1,1,0,1,0] # 0 is Eastern Conference, 1 is Western Conference
	_SS_DEFAULTSETTINGKEYS = ['_SS_DATASRC','_SS_DATASRCFN','_SS_EXPORT','_SS_SIMCNT','_SS_DODOWNLD','_SS_SHOWOUTPUT','_SS_SHOWPB','_SS_PBCPROG','_SS_PBCCMPT'] # Default setting keys, in case the config file is nonexistent. Do not change for any reason, or the program will fail.
	_SS_DEFAULTSETTINGVALS = ['https://projects.fivethirtyeight.com/nba-model/nba_elo.csv','SimSeasonData.csv','SimSeasonOut.csv',1000,True,True,True,'#',' '] # Default setting values, in case the config file is nonexistent. You can manually change these values to specify defaults.
	_SS_DIRNAME = os.path.dirname(__file__)+'\\' # The running directory
	
	_SS_TEAMCOUNT = len(_SS_ALLTEAMIDS) # Constant, the amount of teams
	_SS_TEAMSPERCONF = int(int(_SS_TEAMCOUNT)/2) # Constant, the amount of teams per conference.
	
	setupConfig() # Pull the config data from the INI file.
	
	if _SS_SHOWOUTPUT: # Only show the intro text if that option is enabled.
		initWelcome() # Begin to inform the user what this program does.
	
	if _SS_DODOWNLD: # Only download new file if specified.
		updateDataSrc() # Download the data source from FiveThirtyEight's servers.
	else:
		if not os.path.exists(_SS_DIRNAME+_SS_DATASRCFN):
			print('\nNo data source detected. Set DownloadFile to True in the config!')
			exit()
	
	_CSV = pd.read_csv(_SS_DIRNAME+_SS_DATASRCFN) # Open the data source with Pandas. The argument is specified so we can detect unplayed games (NaNs).
	
	_FIRSTSIMDAY = datetime.now().strftime('%Y-%m-%d') # Sets the first day to simulate games. If CurrentDay is True, start tomorrow. If CurrentDay is False, start today.
	_CSVLINES = len(_CSV['season'].values.tolist()) # The amount of lines in the data source.
	_FGSET = False # Stores if the first game index is set.
	while not _FGSET:
		try:
			_FGIDXSIMDAY = (_CSV['date'].values.tolist()).index(_FIRSTSIMDAY) # The index of the first game to simulate.
		except ValueError:
			_FIRSTSIMDAY = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') # If date is unassignable, attempt to go back a day.
		else:
			_FGSET = True
			
	_FGIDXSSN = (_CSV['season'].values.tolist()).index(_CSV.iloc[(_CSV['date'].values.tolist()).index(_FIRSTSIMDAY)]['season']) # The index of the first game on the season.
	_GAMES2SIM = [] # Stores all the games IDs to simulate
	_TEAMWINS = dict() # Stores the current and simulate win record of each team
	_SEEDPOS = dict() # Stores each seed frequency for every team
	_WINTTL = dict() # Stores the total amount of wins for every team across simulations
	_MINMAX = dict() # Stores the minima and maxima of win count across all simulations.
	
	print('')
	
	createStorage()
	
	games2Sim()
	
	currentWinRecords()
	
	simulateIndividualSeason()
	
	blankFile()		
	
	writeCsv()
	
	if _SS_SHOWOUTPUT:
		if _CFGDATALOAD:
			print('\nThanks for using {}!'.format(_SS_NAME))
		else:
			print('\nGoodbye!')
		print('\n(C) 2018-19 Darren R. Skidmore')