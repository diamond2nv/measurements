# Tabor_WX2184.py class, to perform the communication between the Wrapper and the device
# Jacob Bakermans, <jacob.bakermans@gmail.com> 2016

from instrument import Instrument
import visa
from pyvisa import vpp43
import types
import logging
import struct
from time import sleep, localtime
from cStringIO import StringIO
import numpy as np
import math
import ctypes

# Additional imports from Tabor python library
import sys
import socket
import warnings

class Tabor_WX2184(Instrument):
    '''
    This is the python driver for the Tabor WX2184
    Arbitrary Waveform Generator

    USB address: USB0::0x168B::0x2184::0000214205

    Usage:
    Initialize with
    <name> = instruments.create('name', 'Tabor_WX2184', address='<GPIB address>',
        reset=<bool>, numpoints=<int>)
    '''

    def __init__(self, name, address, reset=False, clock=1e9):
        '''
        Initializes the WX2184.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        print 'Initializing'  
        
        # Set parameters
        self._address = address
        self._visainstrument = visa.instrument(self._address, timeout=20,)
        self._clock = clock

        # Add funcdions
        # self.add_function('reset')
        # self.add_function('clear_visa')
        # self.add_function('set_amplitude')
        # self.add_function('pulse')
        # self.add_function('pulse_pattern')
        # self.add_function('pulse_triggered')               
  
        # Reset
        if reset:
            self.reset()
        print 'Succes' 

    # Functions

    def clear_visa(self):
        self._visainstrument.clear()
        for i in range(5):
            try:
                self._visainstrument.read()
            except(visa.VisaIOError):
                #print 'reset complete'
                break

    def reset(self):
        print 'Reset? ', self._visainstrument.ask("*RST; *OPC?");
        logging.info(__name__ + ' : Resetting instrument')

    def set_amplitude(self):
        '''
        Sets amplitude of output signal from user input.
        Mainly used as test of communication with WX2184

        Input:
            None

        Output:
            None
        '''        

        print 'Enter a new amplitude.'

        newAmplitude = -1
        while (newAmplitude == -1):
            try:
                newAmplitude=float(raw_input('Voltage: '))
            except ValueError:
                print "Not a number"
                newAmplitude = -1

        newAmplitude = min(2,max(0,newAmplitude))
        logging.info(__name__ + ' : Set amplitude to ' + str(newAmplitude))
        print 'Set amplitude to ' + str(newAmplitude)
        self._visainstrument.write('VOLT:AMPL ' + str(newAmplitude))

    def pulse_pattern(self):
        '''
        Downloads pulse to WX2184 and repeats it continuously

        Input:
            None

        Output:
            None
        '''
        #data = np.array([[0.2, 0.4, 0.2],[0.5, 0.9, 0.1]])
        data = self._create_pulse(0.1,0.6,0.5,0.01);
        data = np.array([[-0.5, 0.8, 0.1],[0.1, 0.3, 0.2]])
        levels = data.shape[1];
        level = data[0,:];
        duration = data[1,:];
        channelNumber= 'CH2'

        # query for information of the AWG
        #data1 = self._visainstrument.ask('*IDN?')
        #print data1

        # Reset
        self._visainstrument.write('*RST')
        # Clear error que
        self._visainstrument.write('*CLS')
        # Selecting CH2 as the active channel
        self._visainstrument.write(':INST:SEL ' + channelNumber)
        # Choosing function mode Pattern
        self._visainstrument.write(':FUNC:MODE PATT')
        # Choosing to work with the Pattern/Pulse composer
        self._visainstrument.write(':PATT:MODE COMP')
        # Choosing the transitions between each level to be as fast as possible
        self._visainstrument.write(':PATT:COMP:TRAN:TYPE FAST')
        # Checking for Errors
        error = self._visainstrument.ask(':SYST:ERR?')
        print 'Error after initializing commands:', error  

        # In order to write the binary data, use the vpp43.write command.
        # instrument.write automatically appends the EOL message ('\r\n') to the command
        # This interrups the binary data block, so circumvent this feature by
        # using vpp43.write instead.
        len2 = str(levels*12)
        len1 = str(len(len2))
        vpp43.write(self._visainstrument.vi,':PATT:COMP:FAST:DATA#' + len1 + len2)        
        for k in xrange(0, levels):
            print 'downloading chunk %d' % k
            print str(struct.pack('f',level[k]))
            vpp43.write(self._visainstrument.vi,str(struct.pack('f', level[k])))
            sleep(0.2)          
            vpp43.write(self._visainstrument.vi,str(struct.pack('d', duration[k])))
            sleep(0.2)      

        # Checking for Errors
        error = self._visainstrument.ask(':SYST:ERR?')
        print 'Error after sending binary data:', error  

        # Output on
        self._visainstrument.write(':OUTP ON')
        # Creating an internal "Set device" command (bugfix by Tabor)
        self._visainstrument.write(':FUNC:MODE FIX')
        self._visainstrument.write(':FUNC:MODE PULSE')
        self._visainstrument.write(':FUNC:MODE PATT')
        self._visainstrument.write(':PATT:MODE COMP')

        # Checking for Errors
        error = self._visainstrument.ask(':SYST:ERR?')
        print 'Error after final commands:', error  
        # Wait for completion
        self._visainstrument.ask('*OPC?')  

    def output_off(self):
        print 'Output off? ', self._visainstrument.ask(":OUTP OFF; *OPC?");

    def run_example(self):
        '''Run the example
        
        :param inst: `pyvisa` instrument.
        :returns: zero upon success; negative-value upon error.
        '''
            
        #dwell_times = [ 1e-9, 800e-9, 1e-9, 800e-9, 800e-9, 1e-9, 800e-9, 5e-9 ]
        dwell_times = [ 1e-9, 200e-6, 100e-6, 200e-6, 200e-6, 100e-6, 200e-6, 7e-9 ]
        #dwell_times = [ 1e-9, 8e-8, 1e-9, 8e-8, 8e-8, 1e-9, 8e-8, 5e-9 ]
        volt_levels = [ 0.0,  0.1 , 2.0 , 0.1 , -0.1, -2.0, -0.1, 0.0]    

        data = self._create_pulse(0.1, 1.8, 5000e-9, 10e-9);
        # Add 0 in front of pulse sequence in order to trigger at 0 V
        data = np.hstack(([[0.0], [1e-9]],data));
        # Add a 0 behind pulse sequence to make sure the total length is divisible by 8e-9s
        print sum(data[1,:]);
        print np.mod(sum(data[1,:]), 8e-9);
        print round(np.mod(sum(data[1,:]), 8e-9)/1e-9);

        data = np.hstack((data,[[0.0], [8e-9 - round(np.mod(sum(data[1,:]), 8e-9)/1e-9) * 1e-9]]));

        print data 
           
        patt_table = zip(data[0,:],data[1,:]);#zip(volt_levels, dwell_times)
        
        point_time = '0.5e-9' # 0.5 nano-second i.e. 2-points per nano-second
        
        amplifier = 'HV'
        vpp   = 4.0  # v-peak-to-peak
        voffs = 0.0  # v-offset
        
        inst = self._visainstrument;
        
        # -------------------------------------------------------------------------   
        # Prepare the device for DC Composed-Pattern
        # -------------------------------------------------------------------------
        print
        print "Prepare the device for DC Composed-Pattern .. "
        
        _ = inst.ask("*RST; *OPC?")
        _ = inst.ask("*CLS; *OPC?")    
        
        for chan in (1,2):
            # Select active channel
            _ = inst.ask(":INST:SEL {0:d}; *OPC?".format(chan))            
            # Set output amplifier type:
            _ = inst.ask(":OUTP:COUP:ALL {0:s}; *OPC?".format(amplifier))        
            # Set the output amplifier's vpp:
            _ = inst.ask(":SOUR:VOLT:LEV:AMPL:{0:s} {1:f}; *OPC?".format(amplifier, vpp))
            # Set output amplifier's offset
            _ = inst.ask(":SOUR:VOLT:LEV:OFFS {0:f}; *OPC?".format(voffs))
        
        # Select channel 1
        _ = inst.ask(":INST:SEL 1; *OPC?")
        
        # Set External Trigger Mode (channels 1 & 2)
        _ = inst.ask(":INIT:CONT OFF; :INIT:GATE OFF; *OPC?")
        _ = inst.ask(":TRIG:SOUR EXT; :TRIG:LEV 0; *OPC?")

        # Set 10MHz reference clock to External 
        _ = inst.ask(":ROSC:SOUR EXT; *OPC?")
        _ = inst.ask(":ROSC:EXT:FREQ 10M; *OPC?")
        
        print inst.ask(":SYST:ERR?")
        _ = inst.ask("*CLS; *OPC?")
        

        # -------------------------------------------------------------------------
        # Download DC Composed-Pattern Table:
        # -------------------------------------------------------------------------
        print
        print "Download DC Composed-Pattern Table .. "
        
        ret_count = self.download_fast_pattern_table(inst, patt_table)
        if ret_count < 0:
            print
            print 'download_fast_pattern_table() = {0}'.format(ret_count)
            print
            return -1
        
        print inst.ask(":SYST:ERR?")
        _ = inst.ask("*CLS; *OPC?")
        
        # -------------------------------------------------------------------------
        # (Optionally) Set User-Defeined (rather than Auto) Sampling-Rate ..
        # -------------------------------------------------------------------------
        print
        print "(Optionally) Set User-Defeined (rather than Auto) Sampling-Rate .. "
        
        _ = inst.ask(":PATT:COMP:RES:TYPE USER; :PATT:COMP:RES {0}; *OPC?".format(point_time))
        
        print inst.ask(":SYST:ERR?")
        _ = inst.ask("*CLS; *OPC?")

        # -------------------------------------------------------------------------
        # Change the function mode to DC Composed-Pattern Mode (channels 1 & 2):
        # -------------------------------------------------------------------------
        print
        print "Change the function mode to DC Composed-Pattern Mode (channels 1 & 2) .. "
        
        _ = inst.ask(':FUNC:MODE PATT; :PATT:MODE COMP; :PATT:COMP:TRAN:TYPE FAST; *OPC?')    
        
        print inst.ask(":SYST:ERR?")
        _ = inst.ask("*CLS; *OPC?")
        
        # -------------------------------------------------------------------------
        # Turn outputs on ..
        # -------------------------------------------------------------------------
        print
        print "Turn Outputs ON .. "
        
        for chan in (2,1):
            _ = inst.ask(":INST:SEL {0:d}; :OUTP ON; *OPC?".format(chan))
            
        print inst.ask(":SYST:ERR?")
        print
        
        return 0

    def pulse_triggered(self, lowAmplitude,highAmplitude,lowDuration,highDuration):
        data = self._create_pulse(lowAmplitude, highAmplitude, lowDuration, highDuration);
        # Add 0 in front of pulse sequence in order to trigger at 0 V
        data = np.hstack(([[0.0], [1e-9]],data));
        # Add a 0 behind pulse sequence to make sure the total length is divisible by 8e-9s
        data = np.hstack((data,[[0.0], [8e-9 - round(np.mod(sum(data[1,:]), 8e-9)/1e-9) * 1e-9]]));

        print data 
           
        patt_table = zip(data[0,:],data[1,:]);
        
        point_time = '0.5e-9' # 0.5 nano-second i.e. 2-points per nano-second
        
        amplifier = 'HV'
        vpp   = 4.0  # v-peak-to-peak
        voffs = 0.0  # v-offset
        
        inst = self._visainstrument;
        
        # -------------------------------------------------------------------------   
        # Prepare the device for DC Composed-Pattern
        # -------------------------------------------------------------------------
        print
        print "Prepare the device for DC Composed-Pattern .. "
        
        _ = inst.ask("*RST; *OPC?")
        _ = inst.ask("*CLS; *OPC?")    
        
        for chan in (1,2):
            # Select active channel
            _ = inst.ask(":INST:SEL {0:d}; *OPC?".format(chan))            
            # Set output amplifier type:
            _ = inst.ask(":OUTP:COUP:ALL {0:s}; *OPC?".format(amplifier))        
            # Set the output amplifier's vpp:
            _ = inst.ask(":SOUR:VOLT:LEV:AMPL:{0:s} {1:f}; *OPC?".format(amplifier, vpp))
            # Set output amplifier's offset
            _ = inst.ask(":SOUR:VOLT:LEV:OFFS {0:f}; *OPC?".format(voffs))
        
        # Select channel 1
        _ = inst.ask(":INST:SEL 1; *OPC?")
        
        # Set External Trigger Mode (channels 1 & 2)
        _ = inst.ask(":INIT:CONT OFF; :INIT:GATE OFF; *OPC?")
        _ = inst.ask(":TRIG:SOUR EXT; :TRIG:LEV 0; *OPC?")

        # Set 10MHz reference clock to External 
        _ = inst.ask(":ROSC:SOUR EXT; *OPC?")
        _ = inst.ask(":ROSC:EXT:FREQ 10M; *OPC?")
        
        print inst.ask(":SYST:ERR?")
        _ = inst.ask("*CLS; *OPC?")
        

        # -------------------------------------------------------------------------
        # Download DC Composed-Pattern Table:
        # -------------------------------------------------------------------------
        print
        print "Download DC Composed-Pattern Table .. "
        
        ret_count = self.download_fast_pattern_table(inst, patt_table)
        if ret_count < 0:
            print
            print 'download_fast_pattern_table() = {0}'.format(ret_count)
            print
            return -1
        
        print inst.ask(":SYST:ERR?")
        _ = inst.ask("*CLS; *OPC?")
        
        # -------------------------------------------------------------------------
        # (Optionally) Set User-Defeined (rather than Auto) Sampling-Rate ..
        # -------------------------------------------------------------------------
        print
        print "(Optionally) Set User-Defeined (rather than Auto) Sampling-Rate .. "
        
        _ = inst.ask(":PATT:COMP:RES:TYPE USER; :PATT:COMP:RES {0}; *OPC?".format(point_time))
        
        print inst.ask(":SYST:ERR?")
        _ = inst.ask("*CLS; *OPC?")

        # -------------------------------------------------------------------------
        # Change the function mode to DC Composed-Pattern Mode (channels 1 & 2):
        # -------------------------------------------------------------------------
        print
        print "Change the function mode to DC Composed-Pattern Mode (channels 1 & 2) .. "
        
        _ = inst.ask(':FUNC:MODE PATT; :PATT:MODE COMP; :PATT:COMP:TRAN:TYPE FAST; *OPC?')    
        
        print inst.ask(":SYST:ERR?")
        _ = inst.ask("*CLS; *OPC?")
        
        # -------------------------------------------------------------------------
        # Turn outputs on ..
        # -------------------------------------------------------------------------
        print
        print "Turn Outputs ON .. "
        
        for chan in (2,1):
            _ = inst.ask(":INST:SEL {0:d}; :OUTP ON; *OPC?".format(chan))
            
        print inst.ask(":SYST:ERR?")
        print
        
        return 0

    def _create_pulse(self,lowAmplitude,highAmplitude,lowDuration,highDuration):
        '''
        Create pulse sequence data that looks like the one below. 
        Amplitude in V, duration in s.
                    __
                   |  |                         |
           ________|  |________                 |high amplitude
          |         __         | |low amplitude |
              high duration    |________    ________|
           _________                    |  |
               low duration             |__|
        
        Input:
            lowAmplitude, highAmplitude, lowDuration, highDuration

        Output:
            data (2x6 numpy array)
        '''       

        level = np.empty(6);
        duration = np.empty(6);
        level[0] = lowAmplitude;
        duration[0] = lowDuration;
        level[1] = highAmplitude;
        duration[1] = highDuration;
        level[2] = lowAmplitude;
        duration[2] = lowDuration;
        level[3] = -level[2];
        duration[3] = duration[2];
        level[4] = -level[1];
        duration[4] = duration[1];
        level[5] = -level[0];
        duration[5] = duration[0];
        data = np.vstack((level,duration));

        return data;

    def _list_udp_awg_instruments(self):
        '''
        Using UDP list all AWG-Instruments with LAN Interface
        
        :returns: two lists: 1. VISA-Resorce-Names 2. Instrument-IDN-Strings  
        '''
        BROADCAST = '255.255.255.255'
        UDPSRVPORT = 7501
        UPFRMPORT = 7502
        FRMHEADERLEN = 22
        FRMDATALEN = 1024
        FLASHLINELEN = 32
        #FLASHOPCODELEN  = 1
        
        vi_tcpip_resource_names = []
        vi_tcpip_resource_descs = []
        
        query_msg = bytearray([0xff] * FRMHEADERLEN)
        query_msg[0] = 'T'
        query_msg[1] = 'E'
        query_msg[2] = 'I'
        query_msg[3] = 'D'
        
        try:
            udp_server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
            udp_server_sock.bind(("0.0.0.0", UDPSRVPORT)) # any IP-Address
            udp_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, FRMHEADERLEN + FRMDATALEN)
            udp_server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
            
            # Send the query-message (to all) 
            udp_server_sock.sendto(query_msg, (BROADCAST, UPFRMPORT))
            
            # Receive responses
            udp_server_sock.settimeout(2)
            while True:
                try:
                    data, addr = udp_server_sock.recvfrom(FRMHEADERLEN + FRMDATALEN)
                    vi_tcpip_resource_names.append("TCPIP::{0}::5025::SOCKET".format(addr[0]))
                    
                    ii = FRMHEADERLEN
                    manuf_name = ''
                    model_name = ''
                    serial_nb = ''
                    fw_ver = ''
                    while ii + FLASHLINELEN <= len(data):
                        opcode = data[ii]
                        attr = data[ii + 1 : ii + FLASHLINELEN - 1]
                        attr.rstrip()
                        if opcode == 'D':
                            manuf_name = attr
                        elif opcode == 'I':
                            model_name = attr
                        elif opcode == 'S':
                            serial_nb = attr
                        elif opcode == 'F':
                            fw_ver = attr
                        
                        idn = '{0:s},{1:s},{2:s},{3:s}'.format(manuf_name,model_name,serial_nb,fw_ver)
                        vi_tcpip_resource_descs.append(idn)
                        ii = ii + FLASHLINELEN
                except socket.timeout:
                    break        
        except:
            pass
        
        return vi_tcpip_resource_names, vi_tcpip_resource_descs

    def _list_visa_resources(self, session, query='*'):
        '''List VISA Resources'''
        visa_resource_names = []
        find_list = None
        try:
            find_list, count, desc =  vpp43.find_resources(session, query) 
            
            if count > 0:
                visa_resource_names.append(desc)
                count = count - 1
            
            while count > 0:
                count = count - 1
                desc = vpp43.find_next(find_list)
                visa_resource_names.append(desc)
        except:
            wrn_msg = 'Failed to list VISA Resources\n{0}'.format(sys.exc_info())
            warnings.warn(wrn_msg)
            
        if find_list is not None:
            vpp43.close(find_list)
            
        return visa_resource_names

    def _select_visa_rsc_name(self, rsc_manager=None, title=None, interface_name=None):
        """Select VISA Resource name.
        
        The suportted interfaces names are: 'TCPIP', 'USB', 'GPIB', 'VXI', 'ASRL'
        
        :param rsc_manager: (optional) visa resource-manager.
        :param title: (optional) string displayed as title.
        :param interface_name: (optional) visa interface name.  
        :returns: the selected resource name (string).
        """
        
        if rsc_manager is None:
            rsc_manager = visa.ResourceManager()
        
        selected_rsc_name = None
        
        rsc_names = []
        rsc_descs = []
        num_rscs = 0
        
        intf_nb = 0
        if interface_name is not None:
            intf_map = { 'TCPIP' : 1, 'USB' : 2, 'GPIB' : 3, 'VXI' : 4, 'ASRL' : 5 }
            intf_nb = intf_map.get(interface_name, 0)
        
        while True:        
            #uit_flag = True
            rsc_names = []
            rsc_descs = []
            num_rscs = 0        
            
            if intf_nb in (1,2,3,4,5):
                choice = intf_nb
            else:
                if title is not None:
                    print
                    print title 
                    print '=' * len(title)  
                print    
                print "Select VISA Interface type:"
                print " 1. TCPIP"
                print " 2. USB"
                print " 3. GPIB"
                print " 4. VXI"
                print " 5. ASRL"
                print " 6. Enter VISA Resource-Name"
                print " 7. Quit"
                choice = self.prompt_msg("Please enter your choice [1:7]: ", "123467")
                try:
                    choice = int(choice)
                except:
                    choice = -1
                print        
        
            if choice == 1:
                print
                ip_str = self.prompt_msg("Enter IP-Address, or press[Enter] to search:  ",)
                print
                if len(ip_str) == 0:
                    print 'Searching AWG-Instruments ... '
                    rsc_names, rsc_descs = self._list_udp_awg_instruments()
                    print
                else:
                    try:
                        packed_ip = socket.inet_aton(ip_str)
                        ip_str = socket.inet_ntoa(packed_ip)
                        selected_rsc_name = "TCPIP::{0}::5025::SOCKET".format(ip_str)
                        break
                    except:
                        print
                        print "Invalid IP-Address"
                        print
                        continue          
            elif choice == 2:
                rsc_names = self._list_visa_resources(rsc_manager.session, "?*USB?*INSTR")
            elif choice == 3:
                rsc_names = self._list_visa_resources(rsc_manager.session, "?*GPIB?*INSTR")
            elif choice == 4:
                rsc_names = self._list_visa_resources(rsc_manager.session, "?*VXI?*INSTR")
            elif choice == 5:
                rsc_names = self._list_visa_resources(rsc_manager.session, "?*ASRL?*INSTR")
            elif choice == 6:
                resource_name = self.prompt_msg('Please enter VISA Resurce-Name: ')
                print
                if len(resource_name) > 0:
                    selected_rsc_name = resource_name
                    break
            elif choice == 7:
                break
            else:
                print
                print "Invalid choice"
                print
                continue          
            
            num_rscs = len(rsc_names) 
            if  num_rscs == 0:
                print
                print 'No VISA Resource was found!'
                yes_no = self.prompt_msg("Do you want to retry [y/n]: ", "yYnN")
                if yes_no in "yY":
                    continue
                else:
                    break
            elif num_rscs == 1 and choice != 1:
                selected_rsc_name = rsc_names[0]  
                break
            elif num_rscs > 1 or (num_rscs == 1 and choice == 1):
                if len(rsc_descs) != num_rscs:
                    rsc_descs = ["" for n in range(num_rscs)]
                    # get resources descriptions:        
                    for n, name in zip(range(num_rscs), rsc_names):
                        inst = None
                        try:
                            inst =rsc_manager.open_resource(name)
                            inst.read_termination = '\n'
                            inst.write_termination = '\n'
                            ans_str = inst.ask('*IDN?')
                            rsc_descs[n] = ans_str
                        except:
                            pass
                        if inst is not None:
                            try:
                                inst.close()
                                inst = None
                            except:
                                pass
                    
                print "Please choose one of the available devices:"
                for n, name, desc in zip(range(num_rscs), rsc_names, rsc_descs):
                    print " {0:d}. {1} ({2})".format(n+1, desc, name)
                print " {0:d}. Back to main menu".format(num_rscs+1)
                msg = "Please enter your choice [{0:d}:{1:d}]: ".format(1, num_rscs+1)
                valid_answers = [str(i+1) for i in range(num_rscs+1)]
                choice = self.prompt_msg(msg, valid_answers)
                
                try:
                    choice = int(choice) 
                except:
                    choice = num_rscs+1
            
                if choice == num_rscs+1:
                    continue
                else:
                    selected_rsc_name = rsc_names[choice - 1]
                    break
                
        return selected_rsc_name 

    def _init_vi_inst(self, inst, timeout_msec=10000, read_buff_size_bytes=4096, write_buff_size_bytes=4096):
        '''Initialize the given Instrument VISA Session
        
        :param inst: `pyvisa` instrument.
        :param timeout_msec: VISA-Timeout (in milliseconds)
        :param read_buff_size_bytes: VISA Read-Buffer Size (in bytes)
        :param write_buff_size_bytes: VISA Write-Buffer Size (in bytes)
        '''
        
        if inst is not None:
            inst.timeout = int(timeout_msec) 
            
            #read_buff_attr = inst._vpp43.get_attribute(inst.vi, visa.VI_READ_BUF)         
            try:
                inst._vpp43.set_attribute(inst.vi, visa.VI_READ_BUF, read_buff_size_bytes)
                inst.__dict__['read_buff_size'] = read_buff_size_bytes
            except:
                pass
            
            
            #write_buff_attr = inst._vpp43.get_attribute(inst.vi, visa.VI_WRITE_BUF)        
            try:
                inst._vpp43.set_attribute(inst.vi, visa.VI_WRITE_BUF, write_buff_size_bytes)
                inst.__dict__['write_buff_size'] = write_buff_size_bytes 
            except:
                pass
            
            
            inst.term_char = '\n'
            
            intf_type = None
            try:
                intf_type = inst._vpp43.get_attribute(inst.vi, visa.VI_ATTR_INTF_TYPE)
            except:
                pass  
            if intf_type in (visa.VI_INTF_USB, visa.VI_INTF_GPIB, visa.VI_INTF_TCPIP):
                try:
                    inst._vpp43.set_attribute(inst.vi, visa.VI_ATTR_WR_BUF_OPER_MODE, visa.VI_FLUSH_ON_ACCESS)
                    inst._vpp43.set_attribute(inst.vi, visa.VI_ATTR_RD_BUF_OPER_MODE, visa.VI_FLUSH_ON_ACCESS)
                    if intf_type == visa.VI_INTF_TCPIP:
                        inst._vpp43.set_attribute(inst.vi, visa.VI_ATTR_TERMCHAR_EN, visa.VI_TRUE) 
                except:
                    pass
            
            inst.clear()       
                    
    def open_session(self, resource_name = None, title_msg = None, vi_rsc_mgr = None, extra_init=True):
        '''Open VISA Session (optionally prompt for resource name).
        
        The `resource_name` can be either:
            1. Full VISA Resource-Name (e.g. 'TCPIP::192.168.0.170::5025::SOCKET')
            2. IP-Address (e.g. '192.168.0.170')
            3. Interface-Name (either 'TCPIP', 'USB', 'GPIB', 'VXI' or 'ASRL')
            4. None
        
        :param resource_name: the Resource-Name 
        :param title_msg: title-message (for the interactive-menu)
        :param vi_rsc_mgr: VISA Resource-Manager
        :param extra_init: should perform extra initialization
        :returns: `pyvisa` instrument.
        
        Example:
        
            >>> import pyte
            >>> 
            >>> # Connect to Arbitrary-Wave-Generator Instrument through TCPIP
            >>> # (the user will be asked to enter the instrument's IP-Address): 
            >>> inst = pyte.open_session(resource_name='TCPIP', title_msg='Connect to AWG Instrument')
            >>> 
            >>> # Connect to Digital-Multimeter through USB:
            >>> dmm = pyte.open_session(resource_name='USB', extra_init=False)
            >>> 
            >>> print inst.ask('*IDN?')
            >>> print dmm.ask('*IDN?')
            >>> 
            >>> # Do some work ..  
            >>> 
            >>> inst.close()
            >>> dmm.close()    
            
        '''
        
        inst = None
        try:
            
            if vi_rsc_mgr is None:
                vi_rsc_mgr = visa.ResourceManager()
            
            if resource_name is None:
                resource_name = self._select_visa_rsc_name(vi_rsc_mgr, title_msg)
            elif resource_name.upper() in ('TCPIP', 'USB', 'GPIB', 'VXI', 'ASRL'):
                resource_name = self._select_visa_rsc_name(vi_rsc_mgr, title_msg, resource_name.upper())
            else:
                try:
                    packed_ip = socket.inet_aton(resource_name)
                    ip_str = socket.inet_ntoa(packed_ip)
                    if resource_name == ip_str:
                        resource_name = "TCPIP::{0}::5025::SOCKET".format(ip_str)
                except:
                    pass        
            
            if resource_name is None:
                return None
            
            inst = visa.instrument(resource_name)        
            if extra_init and inst is not None:
                self._init_vi_inst(inst)
        except:
            print 'Failed to open "{0}"\n{1}'.format(resource_name, sys.exc_info())
        
        return inst

    def prompt_msg(self, msg, valid_answers = None):
        """Prompt message and return user's answer."""
        ans = raw_input(msg)
        if valid_answers is not None:
            count = 0
            while ans not in valid_answers:
                count += 1
                ans = raw_input(msg)
                if count == 5:
                    break;
        return ans

    def make_bin_dat_header(self, bin_dat_size, header_prefix=None):
        '''Make Binary-Data Header
        
        :param bin_dat_size: the binary-data total size in bytes.
        :param header_prefix: header-prefix (e.g. ":TRACe:DATA")
        :returns: binary-data header (string)
        '''
        bin_dat_size = int(bin_dat_size)
        dat_sz_str = "{0:d}".format(bin_dat_size)
        
        if header_prefix is None:
            header_prefix = ''
        
        bin_dat_header = '{0:s}#{1:d}{2:s}'.format(header_prefix, len(dat_sz_str), dat_sz_str)
        return bin_dat_header

    def get_visa_err_desc(self, err_code):
        '''Get description of the given visa error code.'''
        desc = 'VISA-Error {0:x}'.format(int(err_code))        
        return desc

    def write_raw_string(self, inst, wr_str):
        '''Write raw string to device (no termination character is added)
        
        :param inst: `pyvisa` instrument.
        :param wr_str:  the string to write.
        :returns: written-bytes count.
        '''
        ret_count = -1
        try:        
            #buf = bytearray(wr_str)
            #buf = ctypes.cast(wr_str, ctypes.POINTER(ctypes.c_ubyte * len(wr_str)))       
            ret_count = vpp43.write(inst.vi, wr_str)
        except:
            wrn_msg = 'write_raw_string(wr_str="{0:s}") failed:\n{1}'.format(wr_str, sys.exc_info())
            warnings.warn(wrn_msg)
            
        return ret_count

    def write_raw_bin_dat(self, inst, bin_dat, dat_size, max_chunk_size = 1024):
        """Write raw binary data to device.
        
        The binary data is sent in chunks of up to `max_chunk_size` bytes
        
        :param inst: `pyvisa` instrument.
        :param bin_dat: the binary data buffer.
        :param dat_size: the data-size in bytes.
        :param max_chunk_size: maximal chunk-size (in bytes).
        :returns: written-bytes count.
        """
        ret_count = 0
        try:
            num_items = 1
            if isinstance(bin_dat, np.ndarray):
                if bin_dat.ndim > 1:
                    bin_dat = bin_dat.flatten()
                num_items = len(bin_dat)
            elif isinstance(bin_dat, (list, tuple, bytearray)):
                num_items = len(bin_dat)            
                    
            if dat_size <= max_chunk_size or num_items <= 1:
                if isinstance(bin_dat, bytearray):
                    ret_count = vpp43.write(inst.vi, bin_dat.decode())
                elif isinstance(bin_dat, np.ndarray):
                    ret_count = vpp43.write(inst.vi, bin_dat.tostring())
                elif isinstance(bin_dat, (list, tuple)):
                    bin_dat = np.array(bin_dat)
                    ret_count = vpp43.write(inst.vi, bin_dat.tostring())
                else:
                    ret_count = vpp43.write(inst.vi, bin_dat)
            else:
                item_sz = dat_size / num_items
                items_chunk = max(max_chunk_size // item_sz, 1)
                offset = 0
                while offset < num_items and ret_count >= 0:
                    n = min(items_chunk, num_items - offset)
                    if isinstance(bin_dat, bytearray):
                        count = vpp43.write(inst.vi, bin_dat[offset:offset+n].decode())
                    elif isinstance(bin_dat, np.ndarray):
                        count = vpp43.write(inst.vi, bin_dat[offset:offset+n].tostring())
                    else:
                        b = np.array(bin_dat[offset:offset+n])
                        count = vpp43.write(inst.vi, b.tostring())
                    offset = offset + n
                    if count < 0:
                        ret_count = count
                    else:
                        ret_count = ret_count + count
                    
        except:
            wrn_msg = 'write_raw_bin_dat(dat_size={0}) failed:\n{1}'.format(dat_size, sys.exc_info())
            warnings.warn(wrn_msg)
                
        return ret_count

    def query_opc(self, inst, paranoia_level = 2):
        '''Query OPC from instrument.
        
        The supported paranoia levels are:
        0 - neither display warning nor raise error upon failure
        1 - display warning but do not raise error upon failure
        2 - raise error upon failure
        
        :param inst: `pyvisa` instrument.
        :param paranoia_level: paranoia-level [0:2]
        :returns: `True` if succeeded; otherwise `False`
        '''
        ok = False
        try:
            resp = inst.ask('*OPC?')
            if resp is not None:
                resp.rstrip('\n')
            
            if resp != '1':
                if paranoia_level > 0:
                    wrn_msg = 'QUERY="*OPC?", RESP="{0:s}"'.format(resp)
                    warnings.warn(wrn_msg)
                while len(resp) > 0:
                    try:
                        resp = inst.read()
                    except (visa.VisaIOError, visa.VisaIOWarning):
                        resp = ''
                resp = inst.ask('*OPC?')
                if resp is not None:
                    resp.rstrip('\n')
            
            if resp == '1':
                ok = True            
        except:
            pass
        
        if paranoia_level > 0 and not ok:
            if paranoia_level == 1:
                warnings.warn('Query OPC Failure')
            elif paranoia_level >= 2:
                raise NameError('Query OPC Failure')
        
        return ok

    def _pre_download_binary_data(self, inst, bin_dat_size=None):
        '''Pre-Download Binary-Data
        
        :param inst: `pyvisa` instrument. 
        :param bin_dat_size: the binary-data-size in bytes (can be omitted)
        :returns: the max write-chunk size (in bytes) and the original time-out (in msec)
        '''
        orig_timeout = inst.timeout
        try:
            max_chunk_size = inst.__dict__.get('write_buff_size', default=4096)
        except:
            max_chunk_size = 4096
        try:        
            intf_type = inst._vpp43.get_attribute(inst.vi, visa.VI_ATTR_INTF_TYPE)
            if intf_type == visa.VI_INTF_GPIB:
                _ = inst.write("*OPC?")
                for _ in range(2000):
                    status_byte = inst.stb
                    if (status_byte & 0x10) == 0x10:
                        break
                _ = inst.read()
                max_chunk_size = min(max_chunk_size, 30000)
                if bin_dat_size is not None and orig_timeout < bin_dat_size / 20:
                    inst.timeout = int(bin_dat_size / 20)
            else:
                max_chunk_size = min(max_chunk_size, 256000)
        except:
            pass
        
        return orig_timeout, max_chunk_size

    def _post_download_binary_data(self, inst, orig_timeout):
        '''Post-Download Binary-Data
        
        :param inst: `pyvisa` instrument. 
        :param orig_timeout: the original time-out (in msec)
        '''
        
        if orig_timeout is not None and inst.timeout != orig_timeout:
            inst.timeout = orig_timeout

    def download_binary_data(self, inst, pref, bin_dat, dat_size):
        """Download binary data to instrument.
        
        Notes:
          1. The caller needs not add the binary-data header (#<data-length>)
          2. The header-prefix, `pref`, can be empty string or `None`
        
        :param inst: `pyvisa` instrument.
        :param pref: the header prefix (e.g. ':TRACe:DATA').
        :param bin_dat: the binary data buffer.
        :param dat_size: the data-size in bytes.
        :returns: written-bytes count.
        
        Example:
            >>> import pyte
            >>> 
            >>> inst = pyte.open_session('192.168.0.170')
            >>> _ = inst.ask('*RST; *CLS; *OPC?') # reset the instrument
            >>> _ = inst.ask(':FUNC:MODE USER; *OPC?') # select arbirary-wave mode
            >>> _ = inst.ask(':FREQ::RAST 2GHz; *OPC?') # Set sampling-rate = 2GHz
            >>> 
            >>> # build sine-wave (single cycle) of 1024-points:
            >>> sin_wav = pyte.build_sine_wave(cycle_len=1024)
            >>> 
            >>> # download it to the active segment of the active channel:
            >>> pyte.download_binary_data(inst, 'TRAC:DATA', sin_wav, 1024 * 2)
            >>> 
            >>> _ = inst.ask(':OUTP ON; *OPC?') # turn on the active channel
            >>> print inst.ask(':SYST:ERR?')
            >>> inst.close()
        """
        ret_count = 0
        
        try:
            orig_timeout, max_chunk_size = self._pre_download_binary_data(inst, dat_size)
            
            try:            
                dat_header = self.make_bin_dat_header(dat_size, pref)
                ret_count = self.write_raw_string(inst, dat_header)
                
                if ret_count < 0:
                    wrn_msg = "Failed to write binary-data header"
                    warnings.warn(wrn_msg)
                else:
                    count = self.write_raw_bin_dat(inst, bin_dat, dat_size, max_chunk_size)
                    if count < 0:
                        ret_count = count
                        wrn_msg = "Failed to write binary-data"
                        warnings.warn(wrn_msg)
                    else:
                        ret_count = ret_count + count
            finally:
                self._post_download_binary_data(inst, orig_timeout)
        except:
            if ret_count >= 0:
                ret_count = -1
            wrn_msg = 'Error in download_binary_data(pref="{0}", dat_size={1}): \n{2}'.format(pref, dat_size, sys.exc_info()) 
            warnings.warn(wrn_msg)   
            
        opc = self.query_opc(inst, paranoia_level=1)
        if not opc:
            wrn_msg = 'Failed to Query OPC After Downloading Binary Data (pref="{0}", dat_size={1}).'.format(pref, dat_size)
            raise NameError(wrn_msg)
        
        return ret_count

    def download_binary_file(self, inst, pref, file_path, offset=0, data_size=None):
        """Download binary data from file to instrument.
        
        Notes:
          1. The caller needs not add the binary-data header (#<data-length>)
          2. The header-prefix, `pref`, can be empty string or `None`
        
        :param inst: `pyvisa` instrument.
        :param pref: the header prefix (e.g. ':TRACe:DATA').
        :param file_path: the file path.
        :param offset: starting-offset in the file (in bytes).
        :param data_size: data-size in bytes (`None` means all)
        :returns: written-bytes count.
        
        Example:
            >>> import pyte
            >>> import os
            >>> file_path = os.path.expanduser('~')
            >>> file_path = os.path.join(file_path, 'Documents')
            >>> file_path = os.path.join(file_path, 'sin.wav')
            >>> 
            >>> # build sine-wave (single cycle) of 1024-points:
            >>> sin_wav = pyte.build_sine_wave(cycle_len=1024)
            >>> # write it to binary file:
            >>> sin_wav.tofile(file_path)
            >>> 
            >>> # Later on ..
            >>> 
            >>> inst = pyte.open_session('192.168.0.170')
            >>> _ = inst.ask('*RST; *CLS; *OPC?') # reset the instrument
            >>> _ = inst.ask(':FUNC:MODE USER; *OPC?') # select arbirary-wave mode
            >>> _ = inst.ask(':FREQ::RAST 2GHz; *OPC?') # Set sampling-rate = 2GHz
            >>> 
            >>> # write wave-data from file to the active segment of the active channel:
            >>> pyte.download_binary_file(inst, file_path, 'TRAC:DATA')
            >>> 
            >>> _ = inst.ask(':OUTP ON; *OPC?') # turn on the active channel
            >>> print inst.ask(':SYST:ERR?')
            >>> inst.close()
        """
        ret_count = 0
        
        with open(file_path, mode='rb') as infile:    
            try:
                infile.seek(0,2) # move the cursor to the end of the file
                file_size = infile.tell()            
                
                if data_size is None:
                    data_size = file_size
                
                if offset + data_size > file_size:
                    data_size = max(0, file_size - offset)
                
                if data_size > 0:                
                    orig_timeout, max_chunk_size = self_pre_download_binary_data(inst, data_size)
                    
                    try:            
                        dat_header = self.make_bin_dat_header(data_size, pref)
                        ret_count = self.write_raw_string(dat_header)
                        
                        if ret_count < 0:
                            wrn_msg = "Failed to write binary-data header)"
                            warnings.warn(wrn_msg)
                        else:
                            infile.seek(offset) # move the cursor to the specified offset
                            
                            offset = 0
                            while offset < data_size and ret_count >= 0:
                                chunk_size = min(data_size - offset, 4096)
                                chunk = np.fromfile(infile, dtype=np.uint8, count=chunk_size)
                                count = self.write_raw_bin_dat(inst, chunk, chunk_size, max_chunk_size)
                                if count < 0:
                                    ret_count = count
                                    wrn_msg = "Failed to write binary-data "
                                    warnings.warn(wrn_msg)
                                else:
                                    ret_count = ret_count + count
                    finally:
                        _post_download_binary_data(inst, orig_timeout)
            except:
                if ret_count >= 0:
                    ret_count = -1
                wrn_msg = 'Error in download_binary_data(pref="{0}", data_size={1}): \n{2}'.format(pref, data_size, sys.exc_info()[0])    
                
            opc = self.query_opc(inst, paranoia_level=1)
            if not opc:
                wrn_msg = 'Failed to Query OPC After Downloading Binary Data (pref="{0}", data_size={1}).'.format(pref, data_size)
                raise NameError(wrn_msg)
        
        return ret_count

    def download_segment_lengths(self, inst, seg_len_list, pref=':SEGM:DATA'):
        '''Download Segments-Lengths Table to Instrument
        
        :param inst: `pyvisa` instrument.
        :param seg_len_list: the list of segments-lengths.
        :param pref: the binary-data-header prefix.
        :returns: written-bytes count.
        
        Example:
            The fastest way to download multiple segments to the instrument
            is to download the wave-data of all the segments, including the
            segment-prefixes (idle-points) of all segments except the 1st,
            into segment 1 (pseudo segment), and afterward download the 
            appropriate segment-lengths.
            
            >>> # Select segment 1:
            >>> _ = inst.ask(':TRACe:SELect 1; *OPC?') 
            >>>  
            >>> # Download the wave-data of all segments:
            >>> pyte.download_binary_data(inst, ':TRACe:DATA', wave_data, total_size)
            >>> 
            >>> # Download the appropriate segment-lengths list: 
            >>> seg_lengths = [ 1024, 1024, 384, 4096, 8192 ]
            >>> pyte.download_segment_lengths(inst, seg_lengths)    
        '''
        if isinstance(seg_len_list, np.ndarray):
            if seg_len_list.ndims != 1:
                seg_len_list = seg_len_list.flatten()
            if seg_len_list.dtype != np.uint32:
                seg_len_list = np.asarray(seg_len_list, dtype=np.uint32)
        else:
            seg_len_list = np.asarray(seg_len_list, dtype=np.uint32)
            if seg_len_list.ndims != 1:
                seg_len_list = seg_len_list.flatten()
        
        return self.download_binary_data(inst, pref, seg_len_list, seg_len_list.nbytes)

    def download_sequencer_table(self, inst, seq_table, pref=':SEQ:DATA'):
        '''Download Sequencer-Table to Instrument
        
        The sequencer-table, `seq_table`, is a list of 3-tuples
        of the form: (<repeats>, <segment no.>, <jump-flag>)
        
        :param inst: `pyvisa` instrument.
        :param seq_table: the sequencer-table (list of 3-tuples)
        :param pref: the binary-data-header prefix.
        :returns: written-bytes count.
        
        Example:
            >>> # Create Sequencer-Table:
            >>> repeats = [ 1, 1, 100, 4, 1 ]
            >>> seg_nb = [ 2, 3, 5, 1, 4 ]
            >>> jump = [ 0, 0, 1, 0, 0 ]
            >>> sequencer_table = zip(repeats, seg_nb, jump)
            >>> 
            >>> # Select sequence no. 1:
            >>>  _ = inst.ask(':SEQ:SELect 1; *OPC?') 
            >>> 
            >>> # Download the sequencer-table:
            >>> pyte.download_sequencer_table(inst, sequencer_table)
                
        '''
        
        tbl_len = len(seq_table)
        s = struct.Struct('< L H B x')
        s_size = s.size
        m = np.empty(s_size * tbl_len, dtype='uint8')
        for n in range(tbl_len):
            repeats, seg_nb, jump_flag = seq_table[n]
            s.pack_into(m, n * s_size, long(repeats), int(seg_nb), int(jump_flag))
        
        return self.download_binary_data(inst, pref, m, m.nbytes)

    def download_adv_seq_table(self, inst, adv_seq_table, pref=':ASEQ:DATA'):
        '''Download Advanced-Sequencer-Table to Instrument
        
        The advanced-sequencer-table, `adv_seq_table`, is a list of 3-tuples
        of the form: (<repeats>, <sequence no.>, <jump-flag>)
        
        :param inst: `pyvisa` instrument.
        :param seq_table: the sequencer-table (list of 3-tuples)
        :param pref: the binary-data-header prefix.
        :returns: vwritten-bytes count.
        
        Example:
            >>> # Create advanced-sequencer table:
            >>> repeats = [ 1, 1, 100, 4, 1 ]
            >>> seq_nb = [ 2, 3, 5, 1, 4 ]
            >>> jump = [ 0, 0, 1, 0, 0 ]
            >>> adv_sequencer_table = zip(repeats, seq_nb, jump)
            >>> 
            >>> # Download it to instrument
            >>> pyte.download_adv_seq_table(inst, adv_sequencer_table)       
        '''
        
        tbl_len = len(adv_seq_table)
        s = struct.Struct('< L H B x')
        s_size = s.size
        m = np.empty(s_size * tbl_len, dtype='uint8')
        for n in range(tbl_len):
            repeats, seq_nb, jump_flag = adv_seq_table[n]
            s.pack_into(m, n * s_size, long(repeats), int(seq_nb), int(jump_flag))
        
        return self.download_binary_data(inst, pref, m, m.nbytes)

    def download_fast_pattern_table(self, inst, patt_table, pref=':PATT:COMP:FAST:DATA'):
        '''Download Fast (Piecewise-flat) Pulse-Pattern Table  to Instrument
        
        The pattern-table, `patt_table`, is a list of 2-tuples
        of the form: (<voltage-level (volt)>, <dwell-time (sec)>)
        
        :param inst: `pyvisa` instrument.
        :param patt_table: the pattern-table (list of 2-tuples)
        :param pref: the binary-data-header prefix.
        :returns: written-bytes count.
        
        Note: 
            In order to avoid Settings-Conflict make sure you can find 
            a valid sampling-rate, `sclk`, such that the length in points
            of each dwell-time, `dwell-time*sclk` is integral number, and
            the total length in points is divisible by the segment-quantum
            (either 16 or 32 depending on the instrument model).
            Optionally set the point-time-resolution manually to `1/sclk`.
        
        Example:
            >>> import pyte
            >>> inst = pyte.open_session('192.168.0.170')
            >>> 
            >>> # Create fast-pulse pattern table:
            >>> volt_levels = [0.0 , 0.1 , 0.5 , 0.1 , -0.1, -0.5, -0.1, -0.05]
            >>> dwel_times =  [1e-9, 1e-6, 1e-9, 1e-6, 1e-6, 1e-9, 1e-6, 5e-9 ]
            >>> pattern_table = zip(volt_levels, dwel_times)
            >>> 
            >>> # Set Function-Mode=Pattern, Pattern-Mode=Composer, Pattern-Type=Fast:
            >>> _ = inst.ask(':FUNC:MODE PATT; :PATT:MODE COMP; :PATT:COMP:TRAN:TYPE FAST; *OPC?')
            >>> 
            >>> # Optionally set User-Defined (rather than Auto) point sampling time:
            >>> _ = inst.ask(':PATT:COMP:RES:TYPE USER; :PATT:COMP:RES 0.5e-9; *OPC?')
            >>> 
            >>> # Download the pattern-table to instrument:
            >>> pyte.download_fast_pattern_table(inst, pattern_table)    
            >>> 
            >>> inst.close()
        '''
        
        tbl_len = len(patt_table)
        s = struct.Struct('< f d')
        s_size = s.size
        m = np.empty(s_size * tbl_len, dtype='uint8')
        for n in range(tbl_len):
            volt_level, dwel_time = patt_table[n]        
            volt_level = float(volt_level)
            dwel_time = float(dwel_time)        
            s.pack_into(m, n * s_size, volt_level, dwel_time)
        
        return self.download_binary_data(inst, pref, m, m.nbytes)

    def download_linear_pattern_table(self, inst, patt_table, start_level, pref=':PATT:COMP:LIN:DATA'):
        '''Download Piecewise-Linear Pulse-Pattern to Instrument
        
        The pattern-table, `patt_table`, is a list of 2-tuples
        of the form: (<voltage-level (volt)>, <dwell-time (sec)>).
        
        Here the `vlotage-level` is the section's end-level.
        The section's start-lavel is the previous-section's end-level.    
        The argument `start_level` is the first-section's start-level. 
        
        :param inst: `pyvisa` instrument.
        :param patt_table: the pattern-table (list of 2-tuples)
        :param start_level: the (first-section's) start voltage level.
        :param pref: the binary-data-header prefix.
        :returns: written-bytes count. 
        
        Note: 
            In order to avoid Settings-Conflict make sure you can find 
            a valid sampling-rate, `sclk`, such that the length in points
            of each dwell-time, `dwell-time` * `sclk` is integral number, and
            the total length in points is divisible by the segment-quantum
            (either 16 or 32 depending on the instrument model).
            Optionally set the point-time-resolution manually to `1/sclk`.
        
        Example:
            >>> import pyte
            >>> inst = pyte.open_session('192.168.0.170')
            >>> 
            >>> # Create fast-pulse pattern table:
            >>> start_level = 0.0
            >>> volt_levels = [0.1 , 0.1 , 0.5 , 0.1 , -0.1, -0.1, -0.5, -0.1, 0.0  ]
            >>> dwel_times  = [1e-9, 1e-6, 1e-9, 1e-6, 4e-9, 1e-6, 1e-9, 1e-6, 1e-9 ]
            >>> pattern_table = zip(volt_levels, dwel_times)
            >>> 
            >>> # Set Function-Mode=Pattern, Pattern-Mode=Composer, Pattern-Type=Linear:
            >>> _ = inst.ask(':FUNC:MODE PATT; :PATT:MODE COMP; :PATT:COMP:TRAN:TYPE LIN; *OPC?')
            >>> 
            >>> # Optionally set User-Defined (rather than Auto) point sampling time:
            >>> _ = inst.ask(':PATT:COMP:RES:TYPE USER; :PATT:COMP:RES 0.5e-9; *OPC?')
            >>> 
            >>> # Download the pattern-table to instrument:
            >>> pyte.download_linear_pattern_table(inst, pattern_table, start_level)   
            >>> 
            >>> inst.close()
        '''
        
        tbl_len = len(patt_table)
        s = struct.Struct('< f d')
        s_size = s.size
        m = np.empty(s_size * tbl_len, dtype='uint8')
        for n in range(tbl_len):
            volt_level, dwel_time = patt_table[n]
            volt_level = float(volt_level)
            dwel_time = float(dwel_time)    
            s.pack_into(m, n * s_size, volt_level, dwel_time)
        
        if start_level is not None:
            start_level = float(start_level)
            _ = inst.ask(':PATT:COMP:LIN:STARt {0:f}; *OPC?'.format(start_level))
            
        return self.download_binary_data(inst, pref, m, m.nbytes)

    def build_sine_wave(self, cycle_len, num_cycles=1, phase_degree=0, low_level=0, high_level=2**14-1, dac_min=0, dac_max=2**14-1):
        '''Build Sine Wave
        
        :param cycle_len: cycle length (in points).
        :param num_cycles: number of cycles.
        :param phase_degree: starting-phase (in degrees)
        :param low_level: the sine low level.
        :param high_level: the sine high level.
        :param dac_min: DAC minimal value.
        :param dac_max: DAC maximal value.
        :returns: `numpy.array` with the wave data (DAC values)
        
        '''
        
        cycle_len = int(cycle_len)
        num_cycles = int(num_cycles)
        
        if cycle_len <= 0 or num_cycles <= 0:
            return None   
        
        wav_len = cycle_len * num_cycles
        
        phase = float(phase_degree) * math.pi / 180.0
        x = np.linspace(start=phase, stop=phase+2*math.pi, num=cycle_len, endpoint=False)
        
        zero_val = (low_level + high_level) / 2.0
        amplitude = (high_level - low_level) / 2.0
        y = np.sin(x) * amplitude + zero_val
        y = np.round(y)
        y = np.clip(y, dac_min, dac_max)    
        
        y = y.astype(np.uint16)
        
        wav = np.empty(wav_len, dtype=np.uint16)
        for n in range(num_cycles):
            wav[n * cycle_len : (n + 1) * cycle_len] = y
        
        return wav
        
    def build_triangle_wave(self, cycle_len, num_cycles=1, phase_degree=0, low_level=0, high_level=2**14-1, dac_min=0, dac_max=2**14-1):
        '''Build Triangle Wave
        
        :param cycle_len: cycle length (in points).
        :param num_cycles: number of cycles.
        :param phase_degree: starting-phase (in degrees)
        :param low_level: the triangle low level.
        :param high_level: the triangle high level.
        :param dac_min: DAC minimal value.
        :param dac_max: DAC maximal value.
        :returns: `numpy.array` with the wave data (DAC values)
        
        '''
        
        cycle_len = int(cycle_len)
        num_cycles = int(num_cycles)
        
        if cycle_len <= 0 or num_cycles <= 0:
            return None   
        
        wav_len = cycle_len * num_cycles
        
        phase = float(phase_degree) * math.pi / 180.0
        x = np.linspace(start=phase, stop=phase+2*math.pi, num=cycle_len, endpoint=False)
        
        zero_val = (low_level + high_level) / 2.0
        amplitude = (high_level - low_level) / 2.0
        y = np.sin(x)
        y = np.arcsin(y) * 2 * amplitude / math.pi + zero_val
        y = np.round(y)
        y = np.clip(y, dac_min, dac_max)    
        
        y = y.astype(np.uint16)
        
        wav = np.empty(wav_len, dtype=np.uint16)
        for n in range(num_cycles):
            wav[n * cycle_len : (n + 1) * cycle_len] = y
        
        return wav

    def build_square_wave(self, cycle_len, num_cycles=1, duty_cycle=50.0, phase_degree=0, low_level=0, high_level=2**14-1, dac_min=0, dac_max=2**14-1):
        '''Build Square Wave
        
        :param cycle_len: cycle length (in points).
        :param num_cycles: number of cycles.
        :param duty_cycle: duty-cycle (between 0% and 100%)
        :param phase_degree: starting-phase (in degrees)
        :param low_level: the triangle low level.
        :param high_level: the triangle high level.
        :param dac_min: DAC minimal value.
        :param dac_max: DAC maximal value.
        :returns: `numpy.array` with the wave data (DAC values)
        
        '''
        
        cycle_len = int(cycle_len)
        num_cycles = int(num_cycles)
        
        if cycle_len <= 0 or num_cycles <= 0:
            return None   
        
        wav_len = cycle_len * num_cycles
        
        duty_cycle = np.clip(duty_cycle, 0.0, 100.0)
        low_level = np.clip(low_level, dac_min, dac_max)
        high_level = np.clip(high_level, dac_min, dac_max)
        
        phase = float(phase_degree) * math.pi / 180.0
        x = np.linspace(start=phase, stop=phase+2*math.pi, num=cycle_len, endpoint=False)
        x = x <= 2 * math.pi * duty_cycle / 100.0
        y = np.full(x.shape, low_level)
        y[x] = high_level
        
        y = y.astype(np.uint16)
        
        wav = np.empty(wav_len, dtype=np.uint16)
        for n in range(num_cycles):
            wav[n * cycle_len : (n + 1) * cycle_len] = y
        
        return wav

    def make_combined_wave(self, wav1, wav2, dest_array, dest_array_offset=0, add_idle_pts=False, quantum=16):
        '''Make 2-channels combined wave from the 2 given waves
        
        The destination-array, `dest_array`, is either a `numpy.array` with `dtype=uint16`, or `None`.
        If it is `None` then only the next destination-array's write-offset offset is calculated.
        
        Each of the given waves, `wav1` and `wav2`, is either a `numpy.array` with `dtype=uint16`, or `None`.
        If it is `None`, then the corresponding entries of `dest_array` are not changed.
        
        :param wav1: the DAC values of wave 1 (either `numpy.array` with `dtype=uint16`, or `None`).
        :param wav2: the DAC values of wave 2 (either `numpy.array` with `dtype=uint16`, or `None`).    
        :param dest_array: the destination-array (either `numpy.array` with `dtype=uint16`, or `None`).
        :param dest_array_offset: the destination-array's write-offset.
        :param add_idle_pts: should add idle-points (segment-prefix)?
        :param quantum: the combined-wave quantum (usually 16 points)
        :returns: the next destination-array's write-offset offset.
        '''
        len1, len2 = 0,0    
        if wav1 is not None:
            len1 = len(wav1)
        
        if wav2 is not None:
            len2 = len(wav2)    
        
        wav_len = max(len1, len2)
        if 0 == wav_len:
            return dest_array_offset
        
        if wav_len % quantum != 0:
            wav_len = wav_len + (quantum - wav_len % quantum)
        
        tot_len = 2 * wav_len
        if add_idle_pts:
            tot_len = tot_len + 2 * quantum    
        
        if dest_array is None:
            return dest_array_offset + tot_len
        
        dest_len = len(dest_array)
        
        if min(quantum, len2) > 0:
            rd_offs = 0
            wr_offs = dest_array_offset
            if add_idle_pts:
                wr_offs = wr_offs + 2 * quantum    
            
            while rd_offs < len2 and wr_offs < dest_len:
                chunk_len = min((quantum, len2 - rd_offs, dest_len - wr_offs))
                dest_array[wr_offs : wr_offs + chunk_len] = wav2[rd_offs : rd_offs + chunk_len]
                rd_offs = rd_offs + chunk_len
                wr_offs = wr_offs + chunk_len + quantum
            
            if add_idle_pts:
                rd_offs = 0
                wr_offs = dest_array_offset 
                chunk_len = min(quantum, dest_len - wr_offs)
                if chunk_len > 0:
                    dest_array[wr_offs : wr_offs + chunk_len] = wav2[0]
        
        if min(quantum, len1) > 0:
            rd_offs = 0
            wr_offs = dest_array_offset + quantum
            if add_idle_pts:
                wr_offs = wr_offs + 2 * quantum    
            
            while rd_offs < len1 and wr_offs < dest_len:
                chunk_len = min((quantum, len1 - rd_offs, dest_len - wr_offs))
                dest_array[wr_offs : wr_offs + chunk_len] = wav1[rd_offs : rd_offs + chunk_len]
                rd_offs = rd_offs + chunk_len
                wr_offs = wr_offs + chunk_len + quantum
            
            if add_idle_pts:
                rd_offs = 0
                wr_offs = dest_array_offset + quantum 
                chunk_len = min(quantum, dest_len - wr_offs)
                if chunk_len > 0:
                    dest_array[wr_offs : wr_offs + chunk_len] = wav1[0]
        
        return dest_array_offset + tot_len
                
        
        
        
        

#### OLD STUFF ####
    # def tabor_test(self):
    #     levels = 8;
    #     dwell_times = np.array([ 1e-9, 1e-6, 1e-9, 1e-6, 1e-6, 1e-9, 1e-6, 5e-9 ], dtype=np.double)
    #     volt_levels = np.array([ 0.0,  0.1 , 2 , 0.1 , -0.1, -2, -0.1, -0.05], dtype=np.float32)
    #     channelNumber= 'CH2'

    #     point_time = '0.5e-9' # 0.5 nano-second i.e. 2-points per nano-second       
    #     amplifier = 'HV'
    #     vpp   = 4.0  # v-peak-to-peak
    #     voffs = 0.0  # v-offset

    #     # query for information of the AWG
    #     print 'AWG: ', self._visainstrument.ask('*IDN?')

    #     # Reset
    #     self._visainstrument.write('*RST')
    #     # Clear error que
    #     self._visainstrument.write('*CLS')

    #     # Select channel
    #     for chan in (1,2):
    #         # Select active channel
    #         print 'Active channel?', self._visainstrument.ask(":INST:SEL {0:d}; *OPC?".format(chan))            
    #         # Set output amplifier type:
    #         print 'Amplifier?', self._visainstrument.ask(":OUTP:COUP:ALL {0:s}; *OPC?".format(amplifier))        
    #         # Set the output amplifier's vpp:
    #         print 'Peak-to-peak Voltage?', self._visainstrument.ask(":SOUR:VOLT:LEV:AMPL:{0:s} {1:f}; *OPC?".format(amplifier, vpp))
    #         # Set output amplifier's offset
    #         print 'Offset Voltage?', self._visainstrument.ask(":SOUR:VOLT:LEV:OFFS {0:f}; *OPC?".format(voffs))
    #     # Select channel 1
    #     print 'Final channel?', self._visainstrument.ask(":INST:SEL 1; *OPC?")

    #     # Set Software Trigger Mode (channels 1 & 2)
    #     print 'Trigger mode?', self._visainstrument.ask(":INIT:CONT OFF; :INIT:GATE OFF; *OPC?")
    #     print 'Trigger level?', self._visainstrument.ask(":TRIG:LEV {0:f}; :TRIG:LEV?".format(volt_levels[0]))

    #     print self._visainstrument.ask(":ROSC:SOUR EXT; *OPC?")
    #     print self._visainstrument.ask(":ROSC:EXT:FREQ 10M; *OPC?")

    #     # Download data to WX2184
    #     len2 = str(levels*12)
    #     len1 = str(len(len2))
    #     vpp43.write(self._visainstrument.vi,':PATT:COMP:FAST:DATA#' + len1 + len2) 
    #     print ':PATT:COMP:FAST:DATA#' + len1 + len2       
    #     for k in xrange(0, levels):
    #         print 'downloading chunk %d' % k
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('f', volt_levels[k])))
    #         sleep(0.2)          
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('d', dwell_times[k])))
    #         sleep(0.2)      

    #     # Set sampling rate
    #     print self._visainstrument.ask(":PATT:COMP:RES:TYPE USER; :PATT:COMP:RES {0}; *OPC?".format(point_time))

    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after sending binary data:', error  

    #     # Set composed pulse pattern mode 
    #     print 'Pulse composer?', self._visainstrument.ask(':FUNC:MODE PATT; :PATT:MODE COMP; :PATT:COMP:TRAN:TYPE FAST; *OPC?')    

    #     # Switch output on on all channels
    #     for chan in (2,1):
    #         print 'Output on?', self._visainstrument.ask(":INST:SEL {0:d}; :OUTP ON; *OPC?".format(chan))

    #     # Checking for errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after final commands:', error                 

    #     # Wait for completion
    #     self._visainstrument.ask('*OPC?')          

    # def download_pulse_new(self):
    #     '''
    #     Downloads pulse to WX2184 and repeats it continuously

    #     Input:
    #         None

    #     Output:
    #         None
    #     '''
    #     #data = np.array([[0.2, 0.4, 0.2],[0.5, 0.9, 0.1]])
    #     data = self._create_pulse(0.1,0.6,0.5,0.01);
    #     data = np.array([[0.0, 1.9, 0.0, -1.9, 0.0],[79e-9, 5e-9, 400e-9, 5e-9, 79e-9]])
    #     levels = data.shape[1];
    #     level = data[0,:];
    #     duration = data[1,:];

    #     channelNumber= 'CH2'
    #     point_time = '0.5e-9' # 0.5 nano-second i.e. 2-points per nano-second       
    #     amplifier = 'HV'
    #     vpp   = 4.0  # v-peak-to-peak
    #     voffs = 0.0  # v-offset

    #     # query for information of the AWG
    #     #data1 = self._visainstrument.ask('*IDN?')
    #     #print data1

    #     # Reset
    #     self._visainstrument.write('*RST')
    #     # Clear error que
    #     self._visainstrument.write('*CLS')

    #     # Select channel
    #     for chan in (1,2):
    #         # Select active channel
    #         print 'Active channel?', self._visainstrument.ask(":INST:SEL {0:d}; *OPC?".format(chan))            
    #         # Set output amplifier type:
    #         print 'Amplifier?', self._visainstrument.ask(":OUTP:COUP:ALL {0:s}; *OPC?".format(amplifier))        
    #         # Set the output amplifier's vpp:
    #         print 'Peak-to-peak Voltage?', self._visainstrument.ask(":SOUR:VOLT:LEV:AMPL:{0:s} {1:f}; *OPC?".format(amplifier, vpp))
    #         # Set output amplifier's offset
    #         print 'Offset Voltage?', self._visainstrument.ask(":SOUR:VOLT:LEV:OFFS {0:f}; *OPC?".format(voffs))
    #     # Select channel 1
    #     print 'Final channel?', self._visainstrument.ask(":INST:SEL 1; *OPC?")

    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after initializing commands:', error  

    #     # Some random Tabor blabla
    #     print self._visainstrument.ask(":ROSC:SOUR EXT; *OPC?")
    #     print self._visainstrument.ask(":ROSC:EXT:FREQ 10M; *OPC?")       

    #     # In order to write the binary data, use the vpp43.write command.
    #     # instrument.write automatically appends the EOL message ('\r\n') to the command
    #     # This interrups the binary data block, so circumvent this feature by
    #     # using vpp43.write instead.
    #     len2 = str(levels*12)
    #     len1 = str(len(len2))
    #     vpp43.write(self._visainstrument.vi,':PATT:COMP:FAST:DATA#' + len1 + len2)        
    #     for k in xrange(0, levels):
    #         print 'downloading chunk %d' % k
    #         print str(struct.pack('f',level[k]))
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('f', level[k])))
    #         sleep(0.2)          
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('d', duration[k])))
    #         sleep(0.2)      

    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after sending binary data:', error  

    #     # Set sampling rate
    #     print self._visainstrument.ask(":PATT:COMP:RES:TYPE USER; :PATT:COMP:RES {0}; *OPC?".format(point_time))

    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after sending binary data:', error  

    #     # Set composed pulse pattern mode 
    #     print 'Pulse composer?', self._visainstrument.ask(':FUNC:MODE PATT; :PATT:MODE COMP; :PATT:COMP:TRAN:TYPE FAST; *OPC?')    

    #     # Switch output on on all channels
    #     for chan in (2,1):
    #         print 'Output on?', self._visainstrument.ask(":INST:SEL {0:d}; :OUTP ON; *OPC?".format(chan))

    #     # Clear error que
    #     self._visainstrument.write('*CLS')
    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after final commands:', error  
    #     # Wait for completion
    #     self._visainstrument.ask('*OPC?')          

    # def pulse_triggered(self):
    #     '''
    #     Downloads pulse to WX2184 and outputs it on trigger

    #     Input:
    #         None

    #     Output:
    #         None
    #     '''
    #     data = self._create_pulse(0.1, 1.8, 5000e-9, 1000e-9);
    #     # Add 0 in front of pulse sequence in order to trigger at 0 V
    #     data = np.hstack(([[0.0], [1e-9]],data));
    #     # Add a 0 behind pulse sequence to make sure the total length is divisible by 8e-9s
    #     print sum(data[1,:]);
    #     print np.mod(sum(data[1,:]), 8e-9);
    #     print round(np.mod(sum(data[1,:]), 8e-9)/1e-9);

    #     # CRASH if last value is 0.0! In example, it is -0.05
    #     data = np.hstack((data,[[0], [8e-9 - round(np.mod(sum(data[1,:]), 8e-9)/1e-9) * 1e-9]]));

    #     print data
    #     print 'OFFSET:', data[1,0] + data[1,1];

    #     #data = np.array([[0.0, 1.9, 0.0, -1.9, 0.05],[79e-9, 5e-9, 400e-9, 5e-9, 79e-9]])

    #     levels = data.shape[1];
    #     volt_levels = np.array(data[0,:], dtype = np.float32);
    #     dwell_times = np.array(data[1,:], dtype = np.double);
    #     channelNumber= 'CH2'

    #     point_time = '0.5e-9' # 0.5 nano-second i.e. 2-points per nano-second       
    #     amplifier = 'HV'
    #     vpp   = 4.0  # v-peak-to-peak
    #     voffs = 0.0  # v-offset

    #     # query for information of the AWG
    #     print 'AWG: ', self._visainstrument.ask('*IDN?')

    #     # Reset
    #     self._visainstrument.write('*RST')
    #     # Clear error que
    #     self._visainstrument.write('*CLS')

    #     # Select channel
    #     for chan in (1,2):
    #         # Select active channel
    #         print 'Active channel?', self._visainstrument.ask(":INST:SEL {0:d}; *OPC?".format(chan))            
    #         # Set output amplifier type:
    #         print 'Amplifier?', self._visainstrument.ask(":OUTP:COUP:ALL {0:s}; *OPC?".format(amplifier))        
    #         # Set the output amplifier's vpp:
    #         print 'Peak-to-peak Voltage?', self._visainstrument.ask(":SOUR:VOLT:LEV:AMPL:{0:s} {1:f}; *OPC?".format(amplifier, vpp))
    #         # Set output amplifier's offset
    #         print 'Offset Voltage?', self._visainstrument.ask(":SOUR:VOLT:LEV:OFFS {0:f}; *OPC?".format(voffs))
    #     # Select channel 1
    #     print 'Final channel?', self._visainstrument.ask(":INST:SEL 1; *OPC?")

    #     # Set Software Trigger Mode (channels 1 & 2)
    #     print 'Trigger mode?', self._visainstrument.ask(":INIT:CONT OFF; :INIT:GATE OFF; *OPC?")
    #     print 'Trigger level?', self._visainstrument.ask(":TRIG:LEV {0:f}; :TRIG:LEV?".format(volt_levels[0]))

    #     # Some random Tabor blabla
    #     print self._visainstrument.ask(":ROSC:SOUR EXT; *OPC?")
    #     print self._visainstrument.ask(":ROSC:EXT:FREQ 10M; *OPC?")

    #     # # Choosing function mode Pattern
    #     # self._visainstrument.write(':FUNC:MODE PATT')
    #     # # Choosing to work with the Pattern/Pulse composer
    #     # self._visainstrument.write(':PATT:MODE COMP')
    #     # # Choosing the transitions between each level to be as fast as possible
    #     # self._visainstrument.write(':PATT:COMP:TRAN:TYPE FAST')
    #     # # Checking for Errors
    #     # error = self._visainstrument.ask(':SYST:ERR?')
    #     # print 'Error after initializing commands:', error  

    #     # Download data to WX2184
    #     len2 = str(levels*12)
    #     len1 = str(len(len2))
    #     vpp43.write(self._visainstrument.vi,':PATT:COMP:FAST:DATA#' + len1 + len2) 
    #     print ':PATT:COMP:FAST:DATA#' + len1 + len2       
    #     for k in xrange(0, levels):
    #         print 'downloading chunk %d' % k
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('f', volt_levels[k])))
    #         sleep(0.2)          
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('d', dwell_times[k])))
    #         sleep(0.2)      

    #     # binDat = '';
    #     # for k in xrange(0, levels):
    #     #     binDat = binDat + str(struct.pack('f', volt_levels[k]));
    #     #     binDat = binDat + str(struct.pack('d', dwell_times[k]));
    #     # Tabors example util functions only work with pyvisa > 1.5
    #     # self._download_binary_data(self._visainstrument, ':PATT:COMP:FAST:DATA', binDat, levels*12);

    #     # Set sampling rate
    #     print self._visainstrument.ask(":PATT:COMP:RES:TYPE USER; :PATT:COMP:RES {0}; *OPC?".format(point_time))

    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after sending binary data:', error  

    #     # Set composed pulse pattern mode 
    #     print 'Pulse composer?', self._visainstrument.ask(':FUNC:MODE PATT; :PATT:MODE COMP; :PATT:COMP:TRAN:TYPE FAST; *OPC?')    

    #     # # Set output mode to triggered
    #     # self._visainstrument.write(':INITIATE:CONTINUOUS OFF')
    #     # print 'Continuous output?', self._visainstrument.ask(':INITIATE:CONTINUOUS?')     

    #     # # Set trigger to BUS to enable triggers over USB
    #     # self._visainstrument.write(':TRIG:SOUR:ADV EXT')
    #     # print 'Trigger?', self._visainstrument.ask(':TRIG:SOUR:ADV?')  

    #     # # Output on
    #     # self._visainstrument.write(':OUTP ON')

    #     # Switch output on on all channels
    #     for chan in (2,1):
    #         print 'Output on?', self._visainstrument.ask(":INST:SEL {0:d}; :OUTP ON; *OPC?".format(chan))

    #     # Checking for errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after final commands:', error  

    #     # # Send trigger to start pulse
    #     # for x in xrange(0,5):
    #     #     sleep(2) # Wait 2 seconds             
    #     #     print 'Trigger', str(x)       
    #     #     # Check for errors
    #     #     print 'Error after trigger: ', self._visainstrument.ask(':SYST:ERR?')                       

    #     # Wait for completion
    #     self._visainstrument.ask('*OPC?')  

    # def pulse_triggered_ext(self):
    #     data = np.array([[0, 0.5, 1, 0.5, -0.5, -1, -0.5, 0],[0.002, 0.003, 0.001, 0.003, 0.003, 0.001, 0.003, 0.002]])

    #     levels = data.shape[1];
    #     level = data[0,:];
    #     duration = data[1,:];
    #     channelNumber= 'CH2'

    #     # query for information of the AWG
    #     print 'AWG: ', self._visainstrument.ask('*IDN?')

    #     # Reset
    #     self._visainstrument.write('*RST')
    #     # Clear error que
    #     self._visainstrument.write('*CLS')
    #     # Selecting CH2 as the active channel
    #     self._visainstrument.write(':INST:SEL ' + channelNumber)
    #     # Choosing function mode Pattern
    #     self._visainstrument.write(':FUNC:MODE PATT')
    #     # Choosing to work with the Pattern/Pulse composer
    #     self._visainstrument.write(':PATT:MODE COMP')
    #     # Choosing the transitions between each level to be as fast as possible
    #     self._visainstrument.write(':PATT:COMP:TRAN:TYPE FAST')
    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after initializing commands:', error  

    #     # Download data to WX2184
    #     len2 = str(levels*12)
    #     len1 = str(len(len2))
    #     vpp43.write(self._visainstrument.vi,':PATT:COMP:FAST:DATA#' + len1 + len2)        
    #     for k in xrange(0, levels):
    #         print 'downloading chunk' + str(k) + '(' + str(level[k]) + ',' + str(duration[k]) + ')'
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('f', level[k])))
    #         sleep(0.2)          
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('d', duration[k])))
    #         sleep(0.2)      

    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after sending binary data:', error  
       
    #     print 'Looking for errors while setting trigger & sync...'
    #     # Stop continues mode
    #     self._visainstrument.write(':INIT:CONT OFF');
    #     print self._visainstrument.ask(':SYST:ERR?')
    #     # Setting the step to repeat only once
    #     self._visainstrument.write(':TRIG:COUN 1');
    #     print self._visainstrument.ask(':SYST:ERR?')
    #     # Setting the sensitivity level for a trigger
    #     self._visainstrument.write(':TRIG:LEV 0');
    #     print 'Trigger level: ', self._visainstrument.ask(':TRIG:LEV?')
    #     print self._visainstrument.ask(':SYST:ERR?')
    #     # Setting the trigger source to be external
    #     self._visainstrument.write(':TRIG:SOUR:ADV EXT');
    #     print self._visainstrument.ask(':SYST:ERR?')
    #     # Wait for completion
    #     print self._visainstrument.ask('*OPC?');

    #     self._visainstrument.write(':SEQ:ADV ONCE');
    #     self._visainstrument.ask(':SYST:ERR?')

    #     # Creating an internal "Set device" command
    #     self._visainstrument.write(':FUNC:MODE FIX');
    #     self._visainstrument.ask(':SYST:ERR?')
    #     self._visainstrument.write(':FUNC:MODE PULSE');
    #     self._visainstrument.ask(':SYST:ERR?')
    #     self._visainstrument.write(':FUNC:MODE PATT');
    #     self._visainstrument.ask(':SYST:ERR?')
    #     self._visainstrument.write(':PATT:MODE COMP');
    #     self._visainstrument.ask(':SYST:ERR?')
    #     # fprintf(obj1, ':SEQ:ADV ONCE');

    #     self._visainstrument.ask(':SYST:ERR?')
    #     # Wait for completion
    #     self._visainstrument.ask('*OPC?');

    #     self._visainstrument.write(':OUTP ON');

    #     self._visainstrument.ask(':SYST:ERR?')
    #     # Wait for completion
    #     self._visainstrument.ask('*OPC?');        
    
    # def _download_binary_data(self, inst, msg, bin_dat, dat_size):
    #     """Download binary data to device.
        
    #     Notes:
    #       1. The caller needs not add the binary-data header (#<data-length>)
    #       2. The preceding-message is usually a SCPI string (e.g :'TRAC:DATA')
        
    #     :param inst: `pyvisa` instrument.
    #     :param msg: the preceding string message.
    #     :param bin_dat: the binary data buffer.
    #     :param dat_size: the data-size in bytes.
    #     :returns: visa-error-code.
    #     """
        
    #     # intf_type = inst.get_visa_attribute(vc.VI_ATTR_INTF_TYPE)
    #     # if intf_type == vc.VI_INTF_GPIB:
    #     #     _ = inst.ask("*OPC?")
    #     #     for _ in range(2000):
    #     #         status_byte = inst.stb
    #     #         if (status_byte & 0x10) == 0x10:
    #     #             break
    #     #     _ = inst.read()
    #     #     max_chunk_size = 30000L
    #     #     orig_tmout = inst.timeout
    #     #     if orig_tmout < dat_size / 20:
    #     #         inst.timeout = long(dat_size / 20)
    #     # else:
    #     max_chunk_size = 256000L    
        
    #     dat_sz_str = "{0:d}".format(dat_size)
    #     dat_header = msg + " #{0:d}{1}".format(len(dat_sz_str), dat_sz_str)
        
    #     ret = 0L
    #     p_dat = ctypes.cast(dat_header, ctypes.POINTER(ctypes.c_byte))
    #     ul_sz = ctypes.c_ulong(len(dat_header))
    #     p_ret = ctypes.cast(ret, ctypes.POINTER(ctypes.c_ulong))
    #     err_code = vpp43.write(inst.vi, p_dat)
    #     # err_code = inst.visalib.viWrite(inst.session, p_dat, ul_sz, p_ret)
        
    #     if err_code < 0:
    #         print "Failed to write binary-data header. error-code=0x{0:x}".format(err_code)
    #         return err_code
        
    #     ul_sz = ctypes.c_ulong(dat_size)
    #     if isinstance(bin_dat, np.ndarray):
    #         p_dat = bin_dat.ctypes.data_as(ctypes.POINTER(ctypes.c_byte))
    #     else:
    #         p_dat = ctypes.cast(bin_dat, ctypes.POINTER(ctypes.c_byte))
        
    #     if dat_size <= max_chunk_size:
    #         err_code = vpp43.write(inst.vi, p_dat)
    #         # err_code = inst.visalib.viWrite(inst.session, p_dat, ul_sz, p_ret)
    #     else:
    #         wr_offs = 0
    #         while wr_offs < dat_size:
    #             chunk_sz = min(max_chunk_size, dat_size - wr_offs)
    #             ul_sz = ctypes.c_ulong(chunk_sz)
    #             ptr = ctypes.cast(ctypes.addressof(p_dat.contents) + wr_offs, ctypes.POINTER(ctypes.c_byte))
    #             err_code = vpp43.write(inst.vi, ptr)
    #             # err_code = inst.visalib.viWrite(inst.session, ptr, ul_sz, p_ret)
    #             if err_code < 0:
    #                 break
    #             wr_offs = wr_offs + chunk_sz
            
    #     #inst.clear()    
    #     if err_code < 0:
    #         print "Failed to write binary-data. error-code=0x{0:x}".format(err_code)
        
    #     return err_code

    # def _download_pulse(self, data):
    #     '''
    #     Downloads pulse sequence defined by data to WX2184.
    #     Data is a 2xn numpy array, where n is the number of levels.
    #     The first row contains the voltage for each level,
    #     the second row the duration of each level.

    #     Input:
    #         data (2xn numpy array) : pulse levels and durations

    #     Output:
    #         None
    #     '''
    #     # Initiate data arrays
    #     levels = data.shape[1];
    #     level = data[0,:];
    #     duration = data[1,:];

    #     # Choosing function mode Pattern
    #     self._visainstrument.write(':FUNC:MODE PATT')
    #     # Choosing to work with the Pattern/Pulse composer
    #     self._visainstrument.write(':PATT:MODE COMP')
    #     # Choosing the transitions between each level to be as fast as possible
    #     self._visainstrument.write(':PATT:COMP:TRAN:TYPE FAST')
    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after initializing commands:', error  

    #     # In order to write the binary data, use the vpp43.write command
    #     # instrument.write automatically appends the EOL message ('\r\n') to the command
    #     # This interrups the binary data block, so circumvent this feature by
    #     # using vpp43.write instead.
    #     len2 = str(levels*12)
    #     len1 = str(len(len2))
    #     print ':PATT:COMP:FAST:DATA#' + len2 + len1
    #     vpp43.write(self._visainstrument.vi,':PATT:COMP:FAST:DATA#' + len1 + len2)        
    #     for k in xrange(0, levels):
    #         print 'downloading chunk %d' % k
    #         print str(struct.pack('f',level[k]))
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('f', level[k])))
    #         sleep(0.2)          
    #         vpp43.write(self._visainstrument.vi,str(struct.pack('d', duration[k])))
    #         sleep(0.2)      

    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after sending binary data:', error  

    #     # Creating an internal "Set device" command (bugfix by Tabor)
    #     self._visainstrument.write(':FUNC:MODE FIX')
    #     self._visainstrument.write(':FUNC:MODE PULSE')
    #     self._visainstrument.write(':FUNC:MODE PATT')
    #     self._visainstrument.write(':PATT:MODE COMP')

    #     # Checking for Errors
    #     error = self._visainstrument.ask(':SYST:ERR?')
    #     print 'Error after final commands:', error  
    #     # Wait for completion
    #     self._visainstrument.ask('*OPC?')  

    #     print 'Success!'
