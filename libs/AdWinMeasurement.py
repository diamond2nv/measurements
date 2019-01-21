
import sys,os,time,shutil,inspect
import logging
import msvcrt
import gobject
import pprint

import numpy as np

import qt
import hdf5_data as h5
from tools import data_object as DO

class AdwinControlledMeasurement(DO.DataObjectHDF5):
    
    mprefix = 'AdwinMeasurement'
    adwin_dict = adwins_cfg.config
    adwin_process = ''
    adwin_processes_key = ''

    def __init__(self, name, save=True):
        self.adwin_process_params = MeasurementParameters('AdwinParameters')
    
    def start_adwin_process(self, load=True, stop_processes=[]):
        proc = getattr(self.adwin, 'start_'+self.adwin_process)
        proc(load=load, stop_processes=stop_processes,
                **self.adwin_process_params.to_dict())
        print 'starting ADwin process', self.adwin_process
    
    def stop_adwin_process(self):
        func = getattr(self.adwin, 'stop_'+self.adwin_process)
        return func()

    def save_adwin_data(self, name, variables):
        grp = h5.DataGroup(name, self.h5data, 
                base=self.h5base)
        
        for v in variables:
            name = v if type(v) == str else v[0]
            data = self.adwin_var(v)
            if data != None:
                grp.add(name,data=data)

        # save all parameters in each group (could change per run!)
        self.save_params(grp=grp.group)  

        # then save all specific adwin params, overwriting other params
        # if double
        adwinparams = self.adwin_process_params.to_dict()
        for k in adwinparams:
            grp.group.attrs[k] = adwinparams[k]

        self.h5data.flush()

    def autoconfig(self):
        '''
        Fills the adwin process parameters (called params_long and params_float in the 
        adwin config file, ../lib/config/adwins.py) from the measurement params dictionary.
        Throws an exception if it cannot find one of the keys there.

        If the adwin process has a 'include_cr_process' flag in the config, the 
        corresponding cr_process parameters are also set from the measurement params dictionary.

        '''
        for key,_val in self.adwin_dict[self.adwin_processes_key][self.adwin_process]['params_long']:
            self.set_adwin_process_variable_from_params(key)

        for key,_val in self.adwin_dict[self.adwin_processes_key][self.adwin_process]['params_float']:            
            self.set_adwin_process_variable_from_params(key)

        if 'include_cr_process' in self.adwin_dict[self.adwin_processes_key][self.adwin_process]:
            for key,_val in self.adwin_dict[self.adwin_processes_key][self.adwin_dict[self.adwin_processes_key][self.adwin_process]['include_cr_process']]['params_long']:              
                self.set_adwin_process_variable_from_params(key)
            for key,_val in self.adwin_dict[self.adwin_processes_key][self.adwin_dict[self.adwin_processes_key][self.adwin_process]['include_cr_process']]['params_float']:              
                self.set_adwin_process_variable_from_params(key)
    
    def set_adwin_process_variable_from_params(self,key):
        try:
            # Here we can do some checks on the settings in the adwin
            if np.isnan(self.params[key]):
                logging.error('Adwin process variable {} contains NAN'.format(key))
                raise Exception('')
            self.adwin_process_params[key] = self.params[key]
        except:
            logging.error("Cannot set adwin process variable '%s'" \
                    % key)
            raise Exception('Adwin process variable {} has not been set \
                                in the measurement params dictionary!'.format(key))
            
    def adwin_process_running(self):
        func = getattr(self.adwin, 'is_'+self.adwin_process+'_running')
        return func()

    def adwin_var(self, var):
        v = var
        getfunc = getattr(self.adwin, 'get_'+self.adwin_process+'_var')
        if type(v) == str:
                return getfunc(v)
        elif type(v) == tuple:
            if len(v) == 2:
                return getfunc(v[0], length=v[1])
            elif len(v) == 3:
                return getfunc(v[0], start=v[1], length=v[2])
            else:
                logging.warning('Cannot interpret variable tuple, ignore: %s' % \
                        str(v))
        else:
            logging.warning('Cannot interpret variable, ignore: %s' % \
                    str(v))
        return None

    def adwin_set_var(self, var, data):
        setfunc = getattr(self.adwin, 'set_' + self.adwin_process + '_var')
        setfunc(**{var: data})

    def adwin_process_filepath(self):
        return self.adwin.process_path(self.adwin_process)

    def adwin_process_src_filepath(self):
        binpath = self.adwin_process_filepath()
        srcpath = os.path.splitext(binpath)[0] + '.bas'
        if not os.path.exists(srcpath):
            return None
        else:
            return srcpath

    def save_stack(self, depth=3):
        Measurement.save_stack(self, depth=depth)

        sdir = os.path.join(self.datafolder, self.STACK_DIR)
        adsrc = self.adwin_process_src_filepath()
        if adsrc != None:
            shutil.copy(adsrc, sdir)

