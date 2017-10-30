
import visa
import numpy as np
import logging
from analysis.libs.tools import toolbox


class RS_SMBV100A():
    '''
    This is the python driver for the Rohde&Schwarz SMBV100A
    signal generator
    '''

    def __init__(self, address, reset=False, max_cw_pwr=-20, log_level = logging.INFO):
    	self.log = logging.getLogger(__name__)
    	self.log.setLevel(log_level)

    	self.log.info(__name__ + ' : Initializing instrument')
    	if (toolbox.validate_ip (address)):
    		self._ip = address
    		self._address = 'TCPIP::'+self._ip+'::inst0::INSTR'
    	else:
    		self._address = address

    	try:
    		rm = visa.ResourceManager()
    		self._vi = rm.open_resource(self._address, timeout=3, read_termination='\n')
    	except Exception as e:
    		print 'Impossible to connect to device! ', e
    	self._max_pow = -30

    def get_instr_type(self):
    	return "RF_source"

    def reconnect (self):
    	try:
    		rm = visa.ResourceManager()
    		self._vi = rm.open_resource(self._address, timeout=3, read_termination='\n')
    		print 'Connection to device established: ', self._vi.ask('*IDN?')
    	except Exception as e:
    		print 'Impossible to connect to device!', e

    def reset(self):
        '''
        Resets the instrument to default values
        '''
        self.log.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        self.get_all()

    def get_frequency (self):
        '''
        Returns the frequency setting forthe instrument [in Hz]
        '''
    	return float (self._vi.ask('SOUR:FREQ?'))

    def set_frequency (self, frequency):
        '''
        Set frequency of device. Input: frequency (float) = frequency in Hz
        '''
        self.log.debug(__name__ + ' : setting frequency to %s GHz' % frequency)
        self._visainstrument.write('SOUR:FREQ %e' % frequency)

    def get_power (self):
        '''
        Returns the power setting forthe instrument [in dBm]
        '''
    	return float (self._vi.ask('SOUR:POW?'))

    def set_power(self,power):
        '''
        Set output power of device. Input: power (float) = output power in dBm
        '''
       	self.log.debug(__name__ + ' : setting power to %s dBm' % power)
        
        if self.get_pulse_modulation() == 'off' and power > self.get_max_cw_pwr():
            self.log.warning(__name__ + ' : power exceeds max cw power; power not set.')
            raise ValueError('power exceeds max cw power. The pulse modulation is off')           
        else:
            self._vi.write('SOUR:POW %e' % power)

    def set_max_cw_pwr(self, pwr):
        self._max_cw_pwr = pwr
        if self.get_power() > pwr and self.get_pulse_modulation() == 'off' and self.get_status() == 'on':  
            self.set_status('off')
            self.log.warning(__name__ + ' : power exceeds max cw power; RF off')
            raise ValueError('power exceeds max cw power')
        return

    def get_status(self):
       	'''
        Returns the instrument status [on/off]
        '''
    	stat = self._vi.ask(':OUTP:STAT?')

        if stat == '1':
            return 'on'
        elif stat == '0':
            return 'off'
        else:
            print len(stat)
            raise ValueError('Output status not specified : %s' % stat)

    def get_pulse_modulation (self):
    	'''
        Returns the status of the pulse-modulation [on/off]
        '''    	
    	self.log.debug(__name__ + ' : reading pulse modulation status from instrument')
    	stat = self._vi.ask(':SOUR:PULM:STAT?')

        if stat == '1':
            return 'on'
        elif stat == '0':
            return 'off'
        else:
            raise ValueError('Pulse modulation status not specified : %s' % stat)

    def set_pulse_modulation (self, value):
        '''
        Switch external pulse modulation

        Input:
            value (string) : 'on' or 'off'

        Output:
            None
        '''
        self.log.debug(__name__ + ' : setting external pulse modulation to "%s"' % value)
        
        if self.get_status() == 'on' and value == 'off' and self.get_power() > self.get_max_cw_pwr():
            self.log.warning(__name__ + ' : power exceeds max cw power; pulm status not set.')
            raise ValueError('power exceeds max cw power')
        
        if value.upper() in ('ON', 'OFF'):
            value = value.upper()
        else:
            raise ValueError('set_pulse_modulation(): can only set on or off')
        self._vi.write(':PULM:SOUR EXT')
        self._vi.write(':SOUR:PULM:STAT %s' % value)

    def get_iq_status(self):
    	self.log.debug(__name__ + ' : reading IQ modulation status from instrument')
        stat = self._vi.ask('IQ:STAT?')

        if stat == '1':
            return 'on'
        elif stat == '0':
            return 'off'
        else:
            raise ValueError('IQ modulation status not specified : %s' % stat)

    def set_iq(self,iq):
        '''
        Switch external IQ modulation

        Input:
            iq (string) : 'on' or 'off'

        Output:
            None
        '''
        self.log.debug(__name__ + ' : setting external IQ modulation to "%s"' % iq)
        if iq.upper() in ('ON', 'OFF'):
            iq = iq.upper()
        else:
            raise ValueError('set_iq(): can only set on or off')
        self._vi.write('IQ:SOUR ANAL')
        self._vi.write('IQ:STAT %s'%iq)


    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        self.log.info(__name__ + ' : reading all settings from instrument')
        print 'Source status: ', self.get_status()
        print 'Frequency: ', self.get_frequency()*1e-9, ' GHz'
        print 'Power: ', self.get_power(), ' dBm'

    def set_mode(self, mode):
        '''
        Change mode to list sweep or continuous
        '''
        self._vi.write('SOUR:FREQ:MODE %s'%mode)

    def enable_list_mode(self):
        self._vi.write('SOUR:FREQ:MODE LIST')

    def enable_list_step_mode(self):
        self._vi.write('SOUR:LIST:MODE STEP')

    def set_list_ext_trigger_source(self):
        self._vi.write('SOUR:LIST:TRIG:SOUR ext')

    def enable_ext_freq_sweep_mode(self):
        self._vi.write('SOUR:SWE:FREQ:MODE STEP')
        self._vi.write('SOUR:SWE:FREQ:SPAC LIN')
        self._vi.write('TRIG:FSW:SOUR EXT')
        self._vi.write('SOUR:FREQ:MODE SWE')

    def reset_sweep(self):
        self._vi.write('SOUR:SWE:RES:ALL')

    def reset_list_mode(self):
        self._vi.write('SOUR:LIST:RES')

    def learn_list(self):
        self._vi.write('SOUR:LIST:LEAR')

    def _create_list(self, start, stop, unit, number_of_steps):
        flist_l = numpy.linspace(start, stop, number_of_steps)
        flist_s = ''
        k=0
        for f_el in flist_l:
            if k is 0:
                flist_s = flist_s + '%s%s'%(int(flist_l[k]),unit)
            else:
                flist_s = flist_s + ', %s%s'%(int(flist_l[k]),unit)
            k+=1
        return flist_s

    def reset_list(self):
        self._vi.write('ABOR:LIST')

    def load_fplist(self, fstart, fstop, funit , pstart, pstop, punit, number_of_steps):
        self._vi.write('SOUR:LIST:SEL "list_%s_%s_%s"'%(fstart, fstop, number_of_steps))

        flist = self._create_list(fstart, fstop, funit, number_of_steps)
        plist = self._create_list(pstart, pstop, punit, number_of_steps)

        self._vi.write('SOUR:LIST:FREQ '+flist)
        self._vi.write('SOUR:LIST:POW '+plist)

    def perform_internal_adjustments(self,all_f = False,cal_IQ_mod=True):
        status=self.get_status()
        self.off()
        if all_f:
            s=self._vi.ask('CAL:ALL:MEAS?')
        else:
            s=self._vi.ask('CAL:FREQ:MEAS?')
            print 'Frequency calibrated'
            s=self._vi.ask('CAL:LEV:MEAS?')
            print 'Level calibrated'
            if cal_IQ_mod:
                self.set_iq('on')
                s=self._vi.ask('CAL:IQM:LOC?')
                print 'IQ modulator calibrated'
        
        self.set_status('off')
        self.set_pulm('off')
        self.set_iq('off')
        sleep(0.1)    


    def set_sweep_frequency_start(self, frequency):
        '''
        Set start frequency of sweep. Input: frequency (float) = frequency in Hz
        '''
        self.log.debug(__name__ + ' : setting sweep frequency start to %s GHz' % frequency)
        self._vi.write('SOUR:FREQ:STAR %e' % frequency)

    def set_sweep_frequency_stop(self, frequency):
        '''
        Set stop frequency of sweep. Input: frequency (float) = frequency in Hz
        '''
        self.log.debug(__name__ + ' : setting sweep frequency stop to %s GHz' % frequency)
        self._vi.write('SOUR:FREQ:STOP %e' % frequency)

    def set_sweep_frequency_step(self, frequency):
        '''
        Set step frequency of sweep. Input: frequency (float) = frequency in Hz
        '''
        self.log.debug(__name__ + ' : setting sweep frequency step to %s GHz' % frequency)
        self._vi.write('SOUR:SWE:FREQ:STEP:LIN %e' % frequency)

    def get_errors(self):
        '''
        Get all entries in the error queue and then delete them.

        Input:
        	None

        Output:
            errors (string) : 0 No error, i.e the error queue is empty.
                              Positive error numbers denote device-specific errors.
                              Negative error numbers denote error messages defined by SCPI
        '''
        self.log.debug(__name__ + ' : reading errors from instrument')
        stat = self._vi.ask('SYSTem:ERRor:ALL?')
        return stat

    def get_error_queue_length(self):
        '''
        Get all entries in the error queue and then delete them.

        Input:
            None

        Output:
            errors (string) : 0 No error, i.e the error queue is empty.
                              Positive error numbers denote device-specific errors.
                              Negative error numbers denote error messages defined by SCPI
        '''
        self.log.debug(__name__ + ' : reading errors from instrument')
        count = self._visainstrument.ask('SYSTem:ERRor:COUNt?')
        return int(count)

    # shortcuts
    def turn_off(self):
        self.set_status('off')

    def turn_on(self):
        self.set_status('on')





