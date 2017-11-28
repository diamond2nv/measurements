import os
qt.current_setup='cav1'
qt.reload_current_setup = os.path.join(qt.config['startdir'],"cav1_scripts/setup_cav1.py")

qt.get_setup_instrument = lambda x: qt.instruments[x] \
    if qt.config['instance_name'][-3:] == qt.current_setup \
    else qt.instruments[x+'_'+qt.current_setup]

#print 'loading setup tools...'
#rom measurement.scripts.lt3_scripts.tools import stools
#reload(stools)
#qt.stools=stools

print 'reload all modules...'
execfile(os.path.join(qt.config['startdir'],"reload_all.py"))

####
print 'reload all measurement parameters and calibrations...'
from measurement.scripts.cav1_scripts.setup import msmt_params as mcfg
reload(mcfg)
qt.exp_params=mcfg.cfg
####
print 'configure the setup-specific hardware...'
# set all the static variables for lt3
#execfile(os.path.join(qt.config['startdir'],'lt3_scripts/setup/sequence.py'))

# set all the static variables for lt3
execfile(os.path.join(qt.config['startdir'],'cav1_scripts/setup/cav1_statics.py'))
