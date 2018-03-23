import sys
import os
import numpy as np
import h5py
import socket

#hiii

#hostpc = os.getenv ('computername')
hostpc = socket.gethostname()

settings = {}

settings ['Dale-Mac'] = {
    'description': 'Dale Mac',
    'folder': "/Users/dalescerri/Documents/GitHub/Spins/",
    }
settings['BAY3-HP'] = {
	'description': 'Bay3 pc in DB2.17',
	'folder': "C:/Research/",
	}
settings['cristian-mint'] = {
	'description': 'Cristian - old TU Delft laptop',
	'folder': "/home/cristian/Work/bonato-lab/",
	}
settings['cristian-PC'] = {
	'description': 'Cristian - Thinkpad',
	'folder': "C:/Users/cristian/Research/QPL-code/",	
}	
settings['HWPC0526-EPS'] = {
	'description': 'Cristian - office pc',
	'folder': "H:/Research/bonato-lab/",
	}
settings['QPL-Compy'] = {
	'description': 'Bay 2 - small pc',
	'folder': "C:/Users/QPL/Desktop/LabSharedPrograms",
	}


print 'Loaded settings for: ', settings[hostpc]['description']
folder = settings[hostpc]['folder']
sys.path.append (folder)

folder = folder + '/measurements/'
sys.path.append (folder)
os.chdir (folder)




