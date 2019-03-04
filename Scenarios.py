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
		for key, val in zip(_SC_DEFAULTSETTINGKEYS, _SC_DEFAULTSETTINGVALS): # Iterate through the default keys and values
			globals()[key] = val # Set variables as globals
	
	else:
		# Manually set all globals.
		globals()['_SC_DATASRC'] = _CONFIG['Project']['DataSource']
		globals()['_SC_DATASRCFN'] = _CONFIG['Project']['DataSourceFile']
		globals()['_SC_GAMESAHEAD'] = abs(_CONFIG['Project'].getint('GamesSimulate'))
		globals()['_SC_DODOWNLD'] = _CONFIG['Project'].getboolean('DownloadFile')
		globals()['_SC_SHOWPB'] = _CONFIG['Visual'].getboolean('ProgressBar')
		globals()['_SC_NAME'] = _CONFIG['Visual']['Name']
		globals()['_SC_SHOWOUTPUT'] = _CONFIG['Visual'].getboolean('ShowOutput')
		globals()['_SC_TCREATE'] = _CONFIG['Build'].getint('TimestampCreate')
		globals()['_SC_TUPDATE'] = _CONFIG['Build'].getint('TimestampUpdate')
		globals()['_SC_BUILD'] = _CONFIG['Build']['VersionString']
		globals()['_SS_PBCPROG'] = _CONFIG['Visual']['ProgBarIncompleteChar']
		globals()['_SS_PBCCMPT'] = _CONFIG['Visual']['ProgBarDoneChar']
		globals()['_SC_TEAMS'] = list()
		
		for t in _SC_ALLTEAMIDS: # Loop through all teams
			if _CONFIG['Teams'].getboolean(t): # If the team is set to True in the config, append it to the team list.
				_SC_TEAMS.append(t)

def initWelcome():
	global _CFGDATALOAD # Load the global state for this variable.
	
	# From this point on, we will welcome the user and print the config data.	
	if _CFGDATALOAD:
		print('\nWelcome to {}!'.format(_SC_NAME))
		
	print('\nThis program will simulate all possible scenarios for the next several games for each team. You can define the amount of games and the teams to simulate.')
	
	if _CFGDATALOAD:
		print('\nCreate Date\t{}'.format(datetime.fromtimestamp(_SC_TCREATE, pytz.timezone('America/Denver')).isoformat()))
		print('Update Date\t{}'.format(datetime.fromtimestamp(_SC_TUPDATE, pytz.timezone('America/Denver')).isoformat()))
		print('Version\t\t{}'.format(_SC_BUILD))
		
	print('\nData Source\t{}'.format(_SC_DATASRC))
	print('Data Source To\t{}'.format(_SC_DATASRCFN))
	print('Games Ahead\t{}'.format(_SC_GAMESAHEAD))
	print('Show Prog Bar\t{}'.format(_SC_SHOWPB))
	
def updateDataSrc():
	if _SC_SHOWOUTPUT: # Gets initial start time for download
		print('\nPreparing download of data source.')
		
		_BEGINTIME = time.time()
		
		print('Downloading data source ...')
	
	try:
		urllib.request.urlretrieve(_SC_DATASRC, _SC_DIRNAME+_SC_DATASRCFN)
	
	except urllib.error.HTTPError as error: # Handle HTTP status codes
		print('\nThe file was unable to download:\n[{}] {}'.format(error.code,error.reason))
		exit()
		
	except urllib.error.URLError as error: # Handle generic network errors
		print('\nThe file was unable to download correctly:\n{}'.format(error.reason))
		exit()
		
	except PermissionError as error: # Most likely the file is open, preventing it from being written to. Could also be an attrib error.
		print('\nThe file appears to be open on your system! Close it!')
		exit()
	
	if _SC_SHOWOUTPUT: # Gets end time for download and prints elapsed time & network speed.
		_ENDTIME = time.time()
		_ELAPSEDTIME = _ENDTIME-_BEGINTIME
		_FILESIZE = os.path.getsize(_SC_DIRNAME+_SC_DATASRCFN)
		print('Download completed successfully. ({:.3f} seconds, {:.2f} kB/s)'.format(_ELAPSEDTIME,(_FILESIZE/_ELAPSEDTIME)/1024))

def teamGames(t):
	if _SC_SHOWPB:
		_PB_TEAMG = ProgressBar('Processing games          ...','Games to simulate processed!\n',len(list(range(_FGIDXSIMDAY, _CSVLINES))),36,_SS_PBCCMPT,_SS_PBCPROG)

	for g in range(_FGIDXSIMDAY, _CSVLINES):
		if len(_TEAMGAMES) < _SC_GAMESAHEAD:
			if _CSV['team1'][g] == t:
				_TEAMGAMES.append([g,_CSV['carmelo_prob1'][g],0])
			elif _CSV['team2'][g] == t:
				_TEAMGAMES.append([g,_CSV['carmelo_prob2'][g],1])
				
		if _SC_SHOWPB:
			_PB_TEAMG.push()

def currentWinRecords(t):
	if _SC_SHOWPB:
		_PB_WINRC = ProgressBar('Processing win records    ...','Win records processed!\n',len(list(range(_FGIDXSSN, _FGIDXSIMDAY))),36,_SS_PBCCMPT,_SS_PBCPROG)
	
	for w in range(_FGIDXSSN, _FGIDXSIMDAY): # Loop through all played games
		if _CSV['team1'][w] == t: # The current team played a home game.
			if int(_CSV['score1'][w]) > int(_CSV['score2'][w]): # Check if current team scored more than opponent
				_CURRECORD[0] += 1 # Yes, give them a win
			else:
				_CURRECORD[1] += 1 # No, give them an L
		elif _CSV['team2'][w] == t: # The current team played an away game.
			if int(_CSV['score2'][w]) > int(_CSV['score1'][w]): # Check if current team scored more than opponent
				_CURRECORD[0] += 1 # Yes, give them a win
			else:
				_CURRECORD[1] += 1 # No, give them an L
			
		if _SC_SHOWPB:
			_PB_WINRC.push()

def allScenarios():
	if _SC_SHOWPB:
		_PB_ALLSC = ProgressBar('Computing all scenarios   ...','Scenarios processed!\n',len(_SCENSEEDS),36,_SS_PBCCMPT,_SS_PBCPROG)
	
	if len(_TEAMGAMES) < _SC_GAMESAHEAD:
		tgs = len(_TEAMGAMES)
	else:
		tgs = _SC_GAMESAHEAD
	
	for b in range(2**tgs):
		_SCENSEEDS.append(list(str(bin(b))[2:].zfill(tgs)))
		
	for g in _SCENSEEDS:
		winPcts = list()
		for idx, f in enumerate(g):
			if not float(f):
				winPcts.append(1-_TEAMGAMES[idx][1])
			else:
				winPcts.append(_TEAMGAMES[idx][1])
		_ALLSCEN.append(winPcts)
		
		if _SC_SHOWPB:
			_PB_ALLSC.push()
			
def allScenarioProbs():
	if _SC_SHOWPB:
		_PB_ALLSP = ProgressBar('Computing scen probs      ...','Scenario probabilities processes!\n',len(_SCENSEEDS),36,_SS_PBCCMPT,_SS_PBCPROG)
	
	for p in _ALLSCEN:
		_ALLSCENPROB.append(np.prod(np.array(p)))
		
		if _SC_SHOWPB:
			_PB_ALLSP.push()
		
def blankFile(t):
	try:
		open(_SC_DIRNAME+t+'.csv','w').close() # Blanks file for re-writing
	
	except PermissionError: # Most likely the file is open, preventing it from being written to. Could also be an attrib error. Because data may have been processing for a while, we give an option to retry.
		print('\nThe file appears to be open on your system!')
		input('Hit <ENTER> to attempt a re-write, or <CTRL+C> to cancel.')
		blankFile(t)
		
def writeCsv(t):
	if _SC_SHOWPB:
		_PB_WRITE = ProgressBar('Writing to {}.csv        ...'.format(t),'Success!\n',len(_ALLSCENPROB),36,_SS_PBCCMPT,_SS_PBCPROG)

	try:
		with open(_SC_DIRNAME+t+'.csv','a') as f: # Open the file as append.			
			f.write('Team: {},'.format(t))
			
			for h in range(len(_TEAMGAMES)):
				if h == len(_TEAMGAMES) - 1:
					s3 = ',Probability,Wins,Losses\n'
				else:
					s3 = ','
				
				if not float(_TEAMGAMES[h][2]):
					s1 = 'v '
					s2 = 'team2'
				else:
					s1 = '@ '
					s2 = 'team1'
				
				f.write('{}{} {}{}'.format(s1,_CSV[s2][_TEAMGAMES[h][0]],_CSV['date'][_TEAMGAMES[h][0]],s3))
				
			for r in range(len(_ALLSCENPROB)):
				f.write('{},'.format(str(r+1)))
				for w in range(len(_TEAMGAMES)):
					if not float(_SCENSEEDS[r][w]):
						f.write('L,')
					else:
						f.write('W,')
					
					if w == len(_TEAMGAMES) - 1:
						f.write('{},{},{}\n'.format('{:.12%}'.format(_ALLSCENPROB[r]),str(_CURRECORD[0] + _SCENSEEDS[r].count('1')),str(_CURRECORD[1] + _SCENSEEDS[r].count('0'))))
						
				if _SC_SHOWPB:
					_PB_WRITE.push()
				
	except PermissionError: # Most likely the file is open, preventing it from being written to. Could also be an attrib error. Because data may have been processing for a while, we give an option to retry.
		print('\nThe file appears to be open on your system!')
		input('Hit <ENTER> to attempt a re-write, or <CTRL+C> to cancel.')
		writeCsv(t)
		
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
		import numpy as np
		from random import random
		from datetime import datetime, timedelta
		
	except ImportError as error: # A module is missing? We can't run the program correctly.
		print('\nUnfortunately, you do not yet support this program, as this module is missing:\n{}'.format(error.name)) # Inform the user of the missing module
		print('\nPlease enter "pip install {}" into your shell to run this program!'.format(error.name)) # Suggest the PIP command to install the module
		
		exit(1)
	
	_CONFIG = configparser.ConfigParser() # Instantiate the configparser.
	
	_CFGFILENAME = 'Scenarios.ini' # The name of the config file.
	_CFGDATALOAD = False # Has the config file loaded yet?
	
	_SC_ALLTEAMIDS = ['ATL','BOS','BRK','CHI','CHO','CLE','DAL','DEN','DET','GSW','HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK','OKC','ORL','PHI','PHO','POR','SAC','SAS','TOR','UTA','WAS'] # All team IDs
	_SC_CONFERENCE = [0,0,0,0,0,0,1,1,0,1,1,0,1,1,1,0,0,1,1,0,1,0,0,1,1,1,1,0,1,0] # 0 is Eastern Conference, 1 is Western Conference
	_SC_DEFAULTSETTINGKEYS = ['_SC_DATASRC','_SC_DATASRCFN','_SC_TEAMS','_SC_GAMESAHEAD','_SC_DODOWNLD','_SC_SHOWOUTPUT','_SC_SHOWPB','_SS_PBCPROG','_SS_PBCCMPT'] # Default setting keys, in case the config file is nonexistent. Do not change for any reason, or the program will fail.
	_SC_DEFAULTSETTINGVALS = ['https://projects.fivethirtyeight.com/nba-model/nba_elo.csv','NBADAshared.csv',list(_SC_ALLTEAMIDS),10,True,True,True,'#',' '] # Default setting values, in case the config file is nonexistent. You can manually change these values to specify defaults.
	_SC_DIRNAME = os.path.dirname(__file__)+'\\' # The running directory
	
	_SC_TEAMCOUNT = len(_SC_ALLTEAMIDS) # Constant, the amount of teams
	_SC_TEAMSPERCONF = int(int(_SC_TEAMCOUNT)/2) # Constant, the amount of teams per conference.
	
	setupConfig() # Pull the config data from the INI file.
	
	if _SC_GAMESAHEAD > 22:
		print('\nYou cannot simulate more than 22 games at a time due to system constraints.')
		exit()
	
	if _SC_SHOWOUTPUT: # Only show the intro text if that option is enabled.
		initWelcome() # Begin to inform the user what this program does.
	
	if _SC_DODOWNLD: # Only download new file if specified.
		updateDataSrc() # Download the data source from FiveThirtyEight's servers.
	else:
		if not os.path.exists(_SC_DIRNAME+_SC_DATASRCFN):
			print('\nNo data source detected. Set DownloadFile to True in the config!')
			exit()
	
	_CSV = pd.read_csv(_SC_DIRNAME+_SC_DATASRCFN) # Open the data source with Pandas. The argument is specified so we can detect unplayed games (NaNs).
	
	_FIRSTSIMDAY = datetime.now().strftime('%Y-%m-%d') # Sets the first day to simulate games.
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
	
	for t in _SC_TEAMS:
		_SCENSEEDS = list() # Contains all individual scenarios
		_CURRECORD = [0,0] # The current record of the team. Index 0 is the wins, index 1 is the losses.
		_TEAMGAMES = list() # Lists all game IDs that are to be played by the team and their win probabilities.
		_ALLSCEN = list() # Contains all individual scenarios.
		_ALLSCENPROB = list() # Contains the probability of each scenario manifesting.
		
		if _SC_SHOWOUTPUT:
			print('Team: {}\n'.format(t))
		
		teamGames(t)
		
		currentWinRecords(t)
		
		allScenarios()
		
		allScenarioProbs()
		
		blankFile(t)
		
		writeCsv(t)
	
	if _SC_SHOWOUTPUT:
		if _CFGDATALOAD:
			print('\nThanks for using {}!'.format(_SC_NAME))
		else:
			print('\nGoodbye!')
		print('\n(C) 2018-19 Darren R. Skidmore')