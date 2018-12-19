# Virtual adwin instrument, adapted from rt2 to fit lt2, dec 2011 
import os
import types
import qt
import numpy as np
import time
from lib import config
import logging

class adwin():
    def __init__(self, name, adwin, processes={}, 
            process_subfolder='', 
            use_cfg=True, **kw):

        self.physical_adwin = adwin
        self.process_dir = os.path.join(qt.config['adwin_programs'], 
                process_subfolder)
        self.processes = processes
        self.default_processes = kw.get('default_processes', [])

        
        self._last_loaded_process = '' #this flag prevents double loading of processes.
        self.add_function('get_latest_process')
        self.add_function('set_latest_process')
        # self.add_parameter('dacs',
        #     type = types.IntType)
        # self.add_parameter('adcs',
        #     type = types.IntType)


        self.dacs = kw.get('dacs', {}) 
        self.adcs = kw.get('adcs', {})

        self.use_cfg = use_cfg

        self._dac_voltages = {}
        for d in self.dacs:
            self._dac_voltages[d] = 0.
       
        # the accessible functions
        
        # initialization
        self.add_function('boot')
        self.add_function('load_programs')
        self.add_function('init_data')

        # tools
        self.add_function('get_process_status')
        
        self.add_function('process_path')

        # automatically generate process functions
        self._make_process_tools(self.processes)

        if not 'remote' in self.get_tags():

            # set up config file
            if self.use_cfg:
                cfg_fn = os.path.abspath(os.path.join(qt.config['ins_cfg_path'], name+'.cfg'))
                if not os.path.exists(cfg_fn):
                    _f = open(cfg_fn, 'w')
                    _f.write('')
                    _f.close()

                self.ins_cfg = config.Config(cfg_fn)     
                self.load_cfg()
                self.save_cfg()

            if kw.get('init', False):
                self.load_programs()

    ### config management
    def load_cfg(self, set_voltages=False):
        if self.use_cfg:
            params = self.ins_cfg.get_all()
            if 'dac_voltages' in params:
                for d in params['dac_voltages']:
                    if set_voltages:
                        self.set_dac_voltage((d, params['dac_voltages'][d]))
                    else:
                        self._dac_voltages[d] = params['dac_voltages'][d]

    def save_cfg(self):
        if self.use_cfg:
            self.ins_cfg['dac_voltages'] = self._dac_voltages

    ### end config management
    def boot(self):
        self.physical_adwin.Boot()
        self.load_programs()
        self.init_data()  
            
    def init_data(self):
        if 'init_data' in self.processes:
            self.start_init_data(load=True)
        
    def process_path(self, procname):
        pfile = self.processes[procname]['file']
        return os.path.join(self.process_dir, pfile)
    
    # automatic creation of process management/access tools from the 
    # process dictionary
    def _make_process_tools(self, proc):
        for p in proc:
            if not('no_process_start' in proc[p]):
                self._make_load(p, proc[p]['file'], proc[p]['index'])
                self._make_start(p, proc[p]['index'], proc[p])
                self._make_stop(p, proc[p]['index'])
                self._make_is_running(p, proc[p]['index'])
            self._make_get(p, proc[p])
            self._make_set(p, proc[p])

    def _make_load(self, pn, fn, pidx):
        funcname = 'load_' + pn
        while hasattr(self, funcname):
            funcname += '_'

        def f():
            """
            this function is generated automatically by the logical
            adwin driver.
            """

            if self.physical_adwin.Process_Status(pidx):
                self.physical_adwin.Stop_Process(pidx)
            self.physical_adwin.Load(os.path.join(self.process_dir, fn))
            
            return True
        
        f.__name__ = funcname
        setattr(self, funcname, f)
        self.add_function(funcname)

        return True

    def _log_warning(self,message):
        logging.warning(self.get_name() +': ' + str(message))

    def _make_start(self, pn, pidx, proc):

        funcname = 'start_' + pn
        while hasattr(self, funcname):
            funcname += '_'

        def f(timeout=None, stop=True, load=True, 
                stop_processes=[], **kw):

            """
            this function is generated automatically by the logical
            adwin driver.
            

            kw args:
            - load : load the process first (default: False)
            - stop_processes : list of processes (numbers or names) that
              are stopped before starting this one.

            all other kws are interpreted as parameters for the process (as defined
            in the process dictionary).
            PAR and FPAR parmeters (old style) have no default at the moment, 
            DATA param (new style) defaults are specified in the process 
            dictionary.
            """

            for p in stop_processes:
                if type(p) == str:
                    if p in self.processes:
                        try:
                            getattr(self, 'stop_'+p)()
                        except:
                            self._log_warning('cannot stop process %s' % p)
                    else:
                        'unknown process %s' % p
                elif type(p) == int:
                    try:
                        self.physical_adwin.Stop_Process(p)
                    except:
                        self._log_warning('cannot stop process %s' % p)
                else:
                    self._log_warning('cannot figure out what process %s is' % p)


            if self.physical_adwin.Process_Status(pidx):
                self.physical_adwin.Stop_Process(pidx)
            if load:
                getattr(self, 'load_'+pn)()
            
            if timeout != None:
                _t0 = time.time()
                while self.physical_adwin.Process_Status(pidx):
                    if time.time() > _t0+timeout:
                        self._log_warning('Timeout while starting ADwin process %d (%s)' \
                                % (pidx, pn))
                        return False
                    time.sleep(.001)

            if 'params_long' in proc:
                pls = np.zeros(len(proc['params_long']), dtype=int)
                for i,pl in enumerate(proc['params_long']):
                    pls[i] = kw.pop(pl[0], pl[1])
                self.physical_adwin.Set_Data_Long(pls, 
                        proc['params_long_index'], 1, 
                        len(proc['params_long']))

            if 'params_float' in proc:
                pfs = np.zeros(len(proc['params_float']), dtype=float)
                for i,pf in enumerate(proc['params_float']):
                    pfs[i] = kw.pop(pf[0], pf[1])
                self.physical_adwin.Set_Data_Float(pfs, 
                        proc['params_float_index'], 1, 
                        len(proc['params_float']))

            if 'include_cr_process' in proc:
                cr_params_long=self.processes[proc['include_cr_process']]['params_long']
                pls = np.zeros(len(cr_params_long), dtype=int)
                for i,pl in enumerate(cr_params_long):
                    pls[i] = kw.pop(pl[0], pl[1])
                self.physical_adwin.Set_Data_Long(pls, 
                        self.processes[proc['include_cr_process']]['params_long_index'], 1, 
                        len(cr_params_long))

                cr_params_float = self.processes[proc['include_cr_process']]['params_float']
                pfs = np.zeros(len(cr_params_float), dtype=float)
                for i,pf in enumerate(cr_params_float):
                    pfs[i] = kw.pop(pf[0], pf[1])
                self.physical_adwin.Set_Data_Float(pfs, 
                        self.processes[proc['include_cr_process']]['params_float_index'], 1, 
                        len(cr_params_float))

            setfunc = getattr(self, pn+'_setfunc_name')
            getattr(self, setfunc)(**kw)

            self.physical_adwin.Start_Process(pidx)
            return True

        f.__name__ = funcname
        setattr(self, funcname, f)
        self.add_function(funcname)

        return True

    def _make_stop(self, pn, pidx):
        funcname = 'stop_' + pn
        while hasattr(self, funcname):
            funcname += '_'

        def f():
            """
            this function is generated automatically by the logical
            adwin driver.
            """
            if self.physical_adwin.Process_Status(pidx):
                self.physical_adwin.Stop_Process(pidx)
            
            return True

        f.__name__ = funcname
        setattr(self, funcname, f)
        self.add_function(funcname)
        
        return True
    
    def _make_is_running(self, pn, pidx):
        funcname = 'is_' + pn + '_running'
        while hasattr(self, funcname):
            funcname += '_'

        def f():
            """
            this function is generated automatically by the logical
            adwin driver.
            """
            return bool(self.physical_adwin.Process_Status(pidx))

        f.__name__ = funcname
        setattr(self, funcname, f)
        self.add_function(funcname)


    def _make_get(self, pn, proc):
        funcname = 'get_' + pn + '_var'
        while hasattr(self, funcname):
            funcname += '_'

        def f(name, *arg, **kw):
            """
            this function is generated automatically by the logical
            adwin driver.

            returns a value belonging to an adwin process, which can be either
            a PAR, FPAR or DATA element. What is returned is specified by
            the name of the variable.

            It is also possible to get all pars or fpars belonging to a process, by 
            setting name = 'par' or 'fpar'

            known keywords:
            - start (integer): if DATA is returned, the start index of the
              array. default is 1.
            - length (integer): if DATA is returned, the length of the array
              needs to be specified. default is 1.
            """
            
            start = kw.get('start', 1)
            length = kw.get('length', 1)
            
            if not 'par' in proc:
                proc['par'] = {}
            if not 'fpar' in proc:
                proc['fpar'] = {}
            if not 'data_long' in proc:
                proc['data_long'] = {}
            if not 'data_float' in proc:
                proc['data_float'] = {}

            if name in proc['par']:
                if type(proc['par'][name]) in [list, tuple]:
                    return [ self.physical_adwin.Get_Par(i) for i in \
                            proc['par'][name] ]
                else:
                    return self.physical_adwin.Get_Par(proc['par'][name])
            elif name in proc['fpar']:
                if type(proc['fpar'][name]) in [list, tuple]:
                    return [ self.physical_adwin.Get_FPar(i) for i in \
                            proc['fpar'][name] ]
                else:
                    return self.physical_adwin.Get_FPar(proc['fpar'][name])
            elif name in proc['data_long']:
                if type(proc['data_long'][name]) in [list, tuple]:
                    return [ self.physical_adwin.Get_Data_Long(
                        i, start, length) for i in proc['data_long'][name] ]
                else:
                    return self.physical_adwin.Get_Data_Long(
                            proc['data_long'][name], start, length)
            elif name in proc['data_float']:
                if type(proc['data_float'][name]) in [list, tuple]:
                    return [ self.physical_adwin.Get_Data_Float(
                        i, start, length) for i in proc['data_float'][name] ]
                else:
                    return self.physical_adwin.Get_Data_Float(
                            proc['data_float'][name], start, length)
            else:
                if name == 'par':
                     return [ (key, self.physical_adwin.Get_Par(proc['par'][key])) \
                             for key in proc['par'] ]
                elif name == 'fpar':
                    return [ (key, self.physical_adwin.Get_FPar(proc['fpar'][key])) \
                            for key in proc['fpar'] ]
                else:
                    if 'include_cr_process' in proc:
                        return getattr(self, 'get_'+proc['include_cr_process']+'_var')(name,*arg,**kw)
                    self._log_warning('Cannot get var: Unknown variable: ' + str(name))
                    return False

        f.__name__ = funcname
        setattr(self, funcname, f)
        self.add_function(funcname)

        return True

    def _make_set(self, pn, proc):
        funcname = 'set_' + pn + '_var'
        while hasattr(self, funcname):
            funcname += '_'
        setattr(self, pn + '_setfunc_name', funcname)
        
        def f(**kw):
            """
            this function is generated automatically by the logical
            adwin driver.

            sets all given PARs and FPARs, specified as kw-args by their names
            as defined in the process dictionary.

            if the kw name corresponds to an adwin data set, the data is set from start=1
            up to the length of the array supplied. If the kw name correspnds to multiple adwin data
            sets, a list or tuple of arrays matching the number of adwin data sets must be supplied.
            """
            start = kw.pop('start', 1)
            
            if not 'par' in proc:
                proc['par'] = {}
            if not 'fpar' in proc:
                proc['fpar'] = {}
            if not 'data_long' in proc:
                proc['data_long'] = {}
            if not 'data_float' in proc:
                proc['data_float'] = {}

            for var in kw:
                if var in proc['par']:
                    self.physical_adwin.Set_Par(proc['par'][var], kw[var])
                elif var in proc['fpar']:
                    self.physical_adwin.Set_FPar(proc['fpar'][var], kw[var])
                elif var in proc['data_long']:
                    if type(proc['data_long'][var]) in [list, tuple]:
                        if len(proc['data_long'][var])==len(kw[var]):
                            for i,j in enumerate(proc['data_long'][var]):
                                self.physical_adwin.Set_Data_Long(
                                    kw[var][i],j, 1, len(kw[var][i]))
                        else:
                            self._log_warning('Value for parameter %s has wrong length to set multiple adwin data.' % var )

                    else:
                        self.physical_adwin.Set_Data_Long(kw[var],
                                proc['data_long'][var], 1, len(kw[var]))
                elif var in proc['data_float']:
                    if type(proc['data_float'][var]) in [list, tuple]:
                        if len(proc['data_float'][var])==len(kw[var]):
                            for i,j in enumerate(proc['data_float'][var]):
                                self.physical_adwin.Set_Data_Float(
                                    kw[var][i],j, 1, len(kw[var][i]))
                        else:
                            self._log_warning('Value for parameter %s has wrong length to set multiple adwin data.' % var )

                    else:
                        self.physical_adwin.Set_Data_Float(kw[var],
                                proc['data_float'][var], 1, len(kw[var]))
                else:
                    if 'include_cr_process' in proc:
                        getattr(self, 'set_'+proc['include_cr_process']+'_var')(**kw)
                    else:
                        self._log_warning('Parameter %s is not defined, and cannot be set.' % var)
        
        f.__name__ = funcname
        setattr(self, funcname, f)
        self.add_function(funcname)

        return True
    
    
    def stop_process(self,process_nr):
        self.physical_adwin.Stop_Process(process_nr)

    def get_process_status(self, name):
        return self.physical_adwin.Process_Status(
                self.processes[name]['index'])

    def wait_for_process(self, name):
        while bool(self.get_process_status(name)):
            time.sleep(0.005)
        return

    def load_programs(self):
        for p in self.processes.keys():
            if p in self.default_processes:
                self.physical_adwin.Load(
                        os.path.join(self.process_dir, 
                            self.processes[p]['file']))

    ###
    ### Additional functions, for convenience, etc.
    ### FIXME ultimately, most of these functions should not be used and go out;
    ### the automatically generated functions should suffice, plus usage of
    ### of scripts
    
    # dacs
    def get_dac_channels(self):
        return self.dacs.copy()

    def get_adc_channels(self):
        return self.adcs.copy()

    def set_dac_voltage(self, (name, value), timeout=1, **kw):
        if 'set_dac' in self.processes:
            self.start_set_dac(dac_no=self.dacs[name], 
                    dac_voltage=value, timeout=timeout, **kw)
            self._dac_voltages[name] = value
            self.save_cfg()
            return True
        else:
            print 'Process for setting DAC voltage not configured.'
            return False

    def get_dac_voltage(self, name):
        return self._dac_voltages[name]
    
    def get_dac_voltages(self, names):
        return [ self.get_dac_voltage(n) for n in names ] 

    def get_adc_voltage(self, name):
        self.start_read_adc (adc_no = adc_no)
        return self.get_read_adc_var('adc_voltage')
   
    # counter
    def set_simple_counting(self, int_time=1, avg_periods=100,
            single_run=0, **kw):
        
        if not 'counter' in self.processes:
            print 'Process for counting not configured.'
            return False

        self.start_counter(load=True, stop=True,
                set_integration_time=int_time, 
                set_avg_periods=avg_periods,
                set_single_run=single_run)

    def get_countrates(self):
        #if not 'counter' in self.processes:
        #    print 'Process for counting not configured.'
        #    return False

        #if self.is_counter_running():
        return self.get_counter_var('get_countrates')
            
    
    def get_last_counts(self):
        if not 'counter' in self.processes:
            print 'Process for counting not configured.'
            return False

        return self.get_counter_var('get_last_counts', start=1, length=4)        
 
# linescan
    def linescan(self, dac_names, start_voltages, stop_voltages, steps, 
            px_time, value='counts', scan_to_start=False, blocking=False, 
            abort_if_running=True):
        """
        Starts the multidimensional linescan on the adwin. 
        
        Arguments:
                
        dac_names : [ string ]
            array of the dac names
        start_voltages, stop_voltages: [ float ]
            arrays for the corresponding start/stop voltages
        steps : int
            no of steps between these two points, incl start and stop
        px_time : int
            time in ms how long to measure per step
        value = 'counts' : string id
            one of the following, to indicate what to measure:
            'counts' : let the adwin measure the counts per pixel
            'none' : adwin only steps
            'counts+suppl' : counts per pixel, plus adwin will record
                the value of FPar #2 as supplemental data
            'counter_process' : counts per pixel attained from counting process
                which should be running on the adwin simultanious

            in any case, the pixel clock will be incremented for each step.
        scan_to_start = False : bool
            if True, scan involved dacs to start first
            right now, with default settings of speed2px()

        blocking = False : bool
            if True, do not return until finished

        abort_if_running = True : bool
            if True, check if linescan is running, and if so, quit right away
        
        """

        if abort_if_running and self.is_linescan_running():
            return
               
        if scan_to_start:
            _steps,_pxtime = self.speed2px(dac_names, start_voltages)
            self.linescan(dac_names, self.get_dac_voltages(dac_names),
                    start_voltages, _steps, _pxtime, value='none', 
                    scan_to_start=False)
            while self.is_linescan_running():
                time.sleep(0.005)
            for i,n in enumerate(dac_names):
                self._dac_voltages[n] = start_voltages[i]
                self.save_cfg()
            
            # stabilize a bit, better for attocubes
            time.sleep(0.05)

        p = self.processes['linescan']
        dacs = [ self.dacs[n] for n in dac_names ] 

        # set all the required input params for the adwin process
        # see the adwin process for details
        self.physical_adwin.Set_Par(p['par']['set_cnt_dacs'], len(dac_names))
        self.physical_adwin.Set_Par(p['par']['set_steps'], steps)
        self.physical_adwin.Set_FPar(p['fpar']['set_px_time'], px_time)

        self.physical_adwin.Set_Data_Long(np.array(dacs), p['data_long']\
                ['set_dac_numbers'],1,len(dac_names))

        self.physical_adwin.Set_Data_Float(start_voltages, 
                p['data_float']['set_start_voltages'], 1, len(dac_names))
        self.physical_adwin.Set_Data_Float(stop_voltages, 
                p['data_float']['set_stop_voltages'], 1, len(dac_names))
    
        # what the adwin does on each px is int-encoded
        px_actions = {
                'none' : 0,
                'counts' : 1,
                'counts+suppl' : 2,
                'counter_process' : 3,
                }
        self.physical_adwin.Set_Par(p['par']['set_px_action'],px_actions[value])
        self.physical_adwin.Start_Process(p['index'])
        
        if blocking:
            while self.is_linescan_running():
                time.sleep(0.005)
        
        # FIXME here we might lose the information about the current voltage,
        # if the scan is not finished properly
        for i,n in enumerate(dac_names):
            self._dac_voltages[n] = stop_voltages[i]

        self.save_cfg()

    def speed2px(self, dac_names, target_voltages, speed=50000, pxtime=5,
            minsteps=10):
        """
        Parameters:
        - dac_names : [ string ]
        - end_voltages : [ float ], one voltage per dac
        - speed : float, (mV/s)
        - pxtime : int, (ms)
        - minsteps : int, never return less than this number for steps
        """
        current_voltages = self.get_dac_voltages(dac_names)
        maxdiff = max([ abs(t-current_voltages[i]) for i,t in \
                enumerate(target_voltages) ])
        steps = int(1e6*maxdiff/(pxtime*speed)) # includes all unit conversions

        return max(steps, minsteps), pxtime

    def get_linescan_counts(self, steps):
        p = self.processes['linescan']
        c = []
        
        for i in p['data_long']['get_counts']:

            #disregard the first value (see adwin program)
            c.append(self.physical_adwin.Get_Data_Long(i, 1, steps+1)[1:])
        return c

    def get_linescan_supplemental_data(self, steps):
        p = self.processes['linescan']
        return self.physical_adwin.Get_Data_Float(
                p['data_float']['get_supplemental_data'], 1, steps+1)[1:]
        
    def get_linescan_px_clock(self):
        p = self.processes['linescan']
        return self.physical_adwin.Get_Par(p['par']['get_px_clock'])

    # end linescan            
   
    def get_xyz_U(self):
        return self.get_dac_voltages(['atto_x','atto_y','atto_z'])

    def move_to_xyz_U(self, target_voltages, speed=5000, blocking=False):
        
        current_voltages = self.get_xyz_U()
        dac_names = ['atto_x','atto_y','atto_z']
        steps, pxtime = self.speed2px(dac_names, target_voltages, speed)
        self.linescan(dac_names, current_voltages, target_voltages,
                steps, pxtime, value='none', scan_to_start=False,
                blocking=blocking)
        return

    def move_to_dac_voltage(self, dac_name, target_voltage, speed=5000, 
            blocking=False):

        current_voltage = self.get_dac_voltage(dac_name)
        steps, pxtime = self.speed2px([dac_name], [target_voltage], speed)
        self.linescan([dac_name], [current_voltage], [target_voltage],
                steps, pxtime, value='none', scan_to_start=False,
                blocking=blocking)


    def measure_counts(self, int_time):
        self.start_counter(set_integration_time=int_time, set_avg_periods=1, set_single_run= 1)
        while self.is_counter_running():
            time.sleep(0.01)
        return self.get_last_counts()

        #XXXXXXXXXXXXXX functions related to adwin latest process removed by Bas 
        # before. Now the purify scrip does not work, I put them back.
        # To fix later. Anais - 11-10-2016
    def get_latest_process(self):
        return self._last_loaded_process

    def set_latest_process(self,fn):
        self._last_loaded_process = fn
        return 
