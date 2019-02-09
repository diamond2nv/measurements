### Instrument class to control the Newport Conex CC controller. 
### in M1, three of these are used to control the magnet X-Y-Z position
### 2016-06

from instrument import Instrument
import visa, time


class NewportConexCcError(Exception):
    pass

class NewportConexCC(Instrument):
    def __init__(self, name, address=0, axis = 1):
        Instrument.__init__(self, name)

        try:
            if int(address):
                address = ('COM%d' % int(address))
        except ValueError:
            if address[0:3].lower() == 'com':
                pass
            else:
                raise NewportConexCcError('''invalid serial port specified.
                 Use 'COM1' or '1''')

        self._address = address
        self._rm = visa.ResourceManager()
        self._visa = self._rm.open_resource(self._address, baud_rate=921600, data_bits=8, 
                                            stop_bits = visa.constants.StopBits.one, 
                                            parity = visa.constants.Parity.none, 
                                            flow_control=visa.constants.VI_ASRL_FLOW_XON_XOFF)
        self.axis = axis

    def __del__(self):
        self.Close()

    def Close(self): #unknown function
        return self._visa.close()

    def Read(self):
        return self._visa.read().rstrip().lstrip()
        
    def Write(self, string, axis = None):
        if axis is not None:
            string = str(self.axis) + string
        self._visa.write(string+'\n\r')

    def Query(self, string, axis = None, removeString = True):
        self.Write((string + '?'), axis = axis)
        answer = self.Read()
        if removeString:
            answer = answer[(len(string) + 1):].rstrip()
        return answer

    def Help(self): #Does not yet return text in organized fashion
        
        ''' Gives the visa comments to communicate with the Newport Conex CC.
        These are used in the instrument NewportConexCC.py

        Example for connecting USB device on port COM4:
            stage = NewportConexCC('name_x_stage', 'ASRL4::INSTR')
            stage.ExecuteHomeSearch()
            stage.SetAbsolutePosition = (1.23)      # move to 1.23 mm
            
            stage.Close()
        For the time being, use the source for documentation'''

    def Version(self):
        return self.Query('VE', axis = '', ).lstrip()
        
    def StopMotion(self):
        self.Write('ST', axis = '', )

    def ResetController(self):
        self.Write('RS', axis = self.axis)

    def ResetControllerAddress(self):
        self.Write('RS##', axis = '')

    def ExecuteHomeSearch(self):
        self.Write('OR', self.axis)

    def GetConfigurationParameters(self):
        #doesnt work? THT &
        configuration = ()
        self.Write('ZT')
        time.sleep(0.025)
        if visa.vpp43.get_attribute(self._visa.vi, visa.VI_ATTR_ASRL_AVAIL_NUM) > 0:
            configuration = self.Read()
        return configuration

    def GetStatus(self):
        statusCode = self.Query('TS', axis = '', removeString = False).rstrip().lstrip()
        if (len(statusCode) > 2) and statusCode[0:3] == ('%sTS' % self.axis):
            status = ControllerStates[statusCode[-2:]]
            errorMap = statusCode[3:-2]
            print 'Reported status code is: %s - %s' % (statusCode[3:], status)
            if int(errorMap, 16) != 0:
                raise NewportConexCcError('Newport Conex reported error: %s - See documentation for error(s)' % errorMap)
        else:
            raise NewportConexCcError('no status reply received')
        return (status, errorMap)

    def GetErrorString(self, error):
        return self.Query(('TB' + error), self.axis)

    def GetLastError(self):
        return self.Query('TE', self.axis)

    # def GetPosition(self):
    #     return float(self.Query('TP', self.axis))

    def SetAcceleration(self, acceleration):
        self.Write(('AC%.6f' % acceleration), self.axis)

    def GetAcceleration(self):
        acceleration = self.Query('AC', self.axis)
        return float(acceleration)

    def SetBacklashCompensation(self, backlash):
        self.Write(('BA%.6f' % backlash), self.axis)

    def GetBacklashCompensation(self):
        backlash = self.Query('BA', self.axis)
        return float(backlash)

    def SetHysteresisCompensation(self, hysteresis):
        self.Write(('BH%.6f' % hysteresis), self.axis)

    def GetHysteresisCompensation(self):
        hyst = self.Query('BH', self.axis)
        return float(hyst)

    def SetDriverVoltage(self, voltage):
        self.Write(('DV%.3f' % voltage), self.axis)
    def GetDriverVoltage(self):
        return float(self.Query('DV', self.axis))

    def SetLowPassFrequency(self, frequency):
        self.Write(('FD%.6f' % frequency), self.axis)
    def GetLowPassFrequency(self):
        return float(self.Query('FD', self.axis))

    def SetFollowingErrorLimit(self, limit):
        self.Write(('FE%.6f' % limit), self.axis)
    def GetFollowingErrorLimit(self):
        return float(self.Query('FE', self.axis))

    def SetFrictionCompensation(self, fcValue):
        self.Write(('FF%.3f' % fcValue), self.axis)
    def GetFollowingErrorLimit(self):
        return float(self.Query('FF', self.axis))

    def SetHomeSearchType(self, searchType):
        self.Write(('HT' + str(searchType)), self.axis)
    def GetHomeSearchType(self):
        return float(self.Query('HT', self.axis))

    def SetStageIdentifier(self, stageIdentifier):
        self.Write(('ID' + str(stageIdentifier[0:31])), self.axis)
    def GetStageIdentifier(self):
        return self.Query('ID', self.axis)

    def SetJerkTime(self, jerkTime):
        self.Write(('JR%.4f' % jerkTime), self.axis)
    def GetJerkTime(self):
        return float(self.Query('JR', self.axis))

    def SetProportionalGain(self, proportionalGain):
        self.Write(('KP%.6f' % proportionalGain), self.axis)
    def GetIntegralGain(self):
        return float(self.Query('KP', self.axis))

    def SetIntegralGain(self, integralGain):
        self.Write(('KI%.6f' % integralGain), self.axis)
    def GetIntegralGain(self):
        return float(self.Query('KI', self.axis))

    def SetDerivativeGain(self, derivativeGain):
        self.Write(('KD%.6f' % derivativeGain), self.axis)
    def GetDerivativeGain(self):
        return float(self.Query('KD', self.axis))

    def SetVelocityFeedForward(self, velocityFeedForward):
        self.Write(('KV%.6f' % velocityFeedForward), self.axis)
    def GetVelocityFeedForward(self):
        return float(self.Query('KV', self.axis))

# ***************************** experiment which function is better for replacement with property/setter

    def SetHomeVelocity(self, velocity):
        self.Write(('OH%.3f' % velocity), self.axis)
    def GetHomeVelocity(self):
        return float(self.Query('OH', self.axis))

    def HomeVelocity2(self, velocity):
        if str(velocity) == '?':
            return float(self.Query('OH', self.axis))
        else:
            self.Write(('OH%.3f' % velocity), self.axis)

    # With error catching
    def HomeVelocity3(self, velocity):
        if is_number(velocity):
            self.Write(('OH' + ('%.3f' % velocity)), self.axis)
        elif (str(velocity) == '?'):
            return float(self.Query('OH', self.axis))
        else:
            raise NewportConexCCError('wrong velocity parameter specified')

    # experiment with raising error from list:
    def SetHomeVelocity5(self, velocity):
        self.Write(('OH%.3f' % velocity), self.axis)
    def GetHomeVelocity(self):
        velocity = self.Query('OH', self.axis)
        if velocity not in errorDict:    
            return float(velocity)
        else:
            raise NewportConexCCError(errorDict[error])
#  *********

    def SetHomeSearchTimeout(self, timeout):
        self.Write(('OH' + str(timeout)), self.axis)
    def GetHomeVelocity(self):
        return float(self.Query('OH', self.axis))

    def MoveAbsolute(self, position):
        self.Write(('PA%.6f' % position), self.axis)

    def MoveRelative(self, displacement):
        self.Write(('PR%.6f' % displacement), self.axis)

    # Get predicted motion time for a relative move
    def GetMotionTime(self, displacement):
        return float(self.Query(('PT%.6f' % displacement), self.axis))

    # Enter/Leave CONFIGURATION state
    def ChangeConfigurationState(self, state):
        try:
            (0, 1).index(float(state))
        except ValueError:
            raise NewportConexCcError('trying to set illegal configuration state: %s' % state)
        self.Write(('PW' + str(state)), self.axis)
    def GetConfigurationState(self):
        return self.Query('PW', self.axis)

    # Enter/Leave TRACKING state
    def SetTrackingState(self, state):
        try:
            (0, 1).index(float(state))
        except ValueError:
            raise NewportConexCcError('trying to set illegal tracking state: %s' % state)
        self.Write(('TK' + str(state)), self.axis)
    def GetTrackingState(self):
        return int(self.Query('TK', self.axis))

    def SetCurrentLimitMax(self, limit):
        self.Write(('QIL%.6f' % limit), self.axis)
    def GetCurrentLimitMax(self):
        return float(self.Write('QIL', self.axis))

    def SetCurrentLimitRms(self, limit):
        self.Write(('QIR%.6f' % limit), self.axis)
    def GetCurrentLimitRms(self):
        return float(self.Query('QIR'), self.axis)

    def SetCurrentLimitAvgPeriod(self, limit):
        self.Write(('QIT%.6f' % limit), self.axis)
    def GetCurrentLimitAvgPeriod(self):
        return float(self.Query('QIT'), self.axis)

    def SetControlLoopState(self, state):
        self.Write(('SC' + str(state)), self.axis)
    def GetControlLoopState(self):
        return self.Query('SC', self.axis)

    def SetNegativeLimit(self, limit):
        self.Write(('SL%.6f' % limit), self.axis)
    def GetNegativeLimit(self):
        return float(self.Query('SL', self.axis))

    def SetPositiveLimit(self, limit):
        self.Write(('SR%.6f' % limit), self.axis)
    def GetPositiveLimit(self):
        return float(self.Query('SR', self.axis))

    def SetEncoderIncrementValue(self, value):
        self.Write(('SU%.6f' % value), self.axis)
    def GetEncoderIncrementValue(self):
        return float(self.Query('SU', self.axis))

    def SetVelocity(self, value):
        self.Write(('VA%.4f' % value), self.axis)
    def GetVelocity(self):
        return float(self.Query('VA', self.axis))

    def GetPositionSetPoint(self):
        return float(self.Query('TH', self.axis))

    def GetPosition(self):
        return float(self.Query('TP', self.axis))


ControllerStates = {'0A': 'NOT REFERENCED from RESET', 
                    '0B': 'NOT REFERENCED from HOMING', 
                    '0C': 'NOT REFERENCED from CONFIGURATION', 
                    '0D': 'NOT REFERENCED from DISABLE', 
                    '0E': 'NOT REFERENCED from READY', 
                    '0F': 'NOT REFERENCED from MOVING', 
                    '10': 'NOT REFERENCED - NO PARAMETERS IN MEMORY', 
                    '14': 'CONFIGURATION', 
                    '1E': 'HOMING', 
                    '28': 'MOVING', 
                    '32': 'READY from HOMING', 
                    '33': 'READY from MOVING', 
                    '34': 'READY from DISABLE', 
                    '36': 'READY T from READY', 
                    '37': 'READY T from TRACKING', 
                    '38': 'READY T from DISABLE T', 
                    '3C': 'DISABLE from READY', 
                    '3D': 'DISABLE from MOVING', 
                    '3E': 'DISABLE from TRACKING', 
                    '3F': 'DISABLE from READY T', 
                    '46': 'TRACKING from READY T', 
                    '47': 'TRACKING from TRACKING'}

errorDict = {'A': 'Unknown message code or floating point controller address', 
             'B': 'Controller address not correct', 
             'C': 'Parameter missing or out of range', 
             'D': 'Execution not allowed', 
             'E': 'home sequence already started', 
             'G': 'Displacement out of limits', 
             'H': 'Execution not allowed in NOT REFERENCED state', 
             'I': 'Execution not allowed in CONFIGURATION state', 
             'J': 'Execution not allowed in DISABLE state', 
             'K': 'Execution not allowed in READY state', 
             'L': 'Execution not allowed in HOMING state', 
             'M': 'Execution not allowed in MOVING state', 
             'N': 'Current position out of software limit', 
             'P': 'Command not allowed in TRACKING state', 
             'S': 'Communication Time Out', 
             'U': 'Error during EEPROM access', 
             'V': 'Error during command execution'}
