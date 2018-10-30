# -*- coding: utf-8 -*-

import pylab as np
import time
import sys
import visa

from measurements.libs import mapper_general as mgen

if sys.version_info.major == 3:
    from importlib import reload

reload(mgen)

########################################################################
#                      DEFAULT SCANNERS CLASSES                        #
########################################################################
# These classes should not be modified unless you know what you are
# doing For Scanner implementation, see the LAB SCANNERS CLASSES section
# below.

class ScannerCtrl (mgen.DeviceCtrl):

    """Default Scanner class which defines the mandatory functions to be
    present in any scanner class and gives them default behaviour. Also
    contains functions like move_smooth() which should mostly work the
    same way for any type of scanner
    
    Attributes: number_of_axes (int): number of axes/channels of the
        device smooth_delay (float): delay in seconds between each step
        of the move_smooth smooth_step (float): amplitude of each step
        for the move_smooth function string_id (str): string identifying
        the device. Used in error messages.
    """
    
    def __init__(self, channels=[], ids = None):
        """Initializes all scanner attributes with default values. In
        particular, it calculates the number of axes based on the number
        of channels and defines self.number_of_axes in function.
        
        Args:
            channels (list, optional): list of device channels.
        """
        self.smooth_step = 1.
        self.smooth_delay = 0.05
        self.string_id = 'Unknown scanner'

        if channels is None:
            self.number_of_axes = 0
        else:
            try:
                self.number_of_axes = len(channels)
            except TypeError:
                self.number_of_axes = len(list(channels))

        if ids is None:
            ids = ['scan_axis_'+str(i) for i in enumerate(channels)]         
            
        self._ids = ids

        try:
            channels = list(channels)
        except TypeError:
            channels = [channels]
        if channels == [None]:
            channels = []

        self._channels = channels
        self.number_of_axes = len(channels)
        self._dev_initialised = False
        self._dev_closed = True

    def __getitem__(self, key):
        """Gets an Saxis object with the corresponding axis number
        
        Args:
            key (int): axis number
        
        Returns:
            Saxis object: Saxis (Scanner axis) built from self.get,
                move, move_smooth, initialize and close functions.
        
        Raises:
            IndexError: if axis number is not an integer
            TypeError: if the axis is out of bounds (key >
                self.number_of_axes)
        """
        if type(key) is not int:
            raise TypeError('Axis number should be an integer.')
        if not 0 <= key < self.number_of_axes:
            raise IndexError('The addressed axis does not exist (out of bounds). ' +
                             f'This device has {self.number_of_axes} axes defined, ' +
                             f'you tried accessing axis {key}.')
        return Saxis(self, key)

    def __len__(self):
        """ Returns the number of axes on this scanner.
        
        Returns:
            int: number of axes
        """
        return self.number_of_axes

    def initialize(self, force=False):
        """ Opens the communication channel with the device. Should not
        be overloaded (overload _initialize() instead). By default, a
        flag will prevent multiple initialisations, so the function can
        be called repeatedly without raising errors.
        
        Args:
            force (bool, optional): will force initialization despite
                                    the flag
        """
        if force:
            self._dev_initialised = False
        if not self._dev_initialised:
            try:
                self._initialize()
            except visa.VisaIOError as err:
                self.visa_error_handling(err)
            self._dev_initialised = True
            self._dev_closed = False

    def _initialize(self):
        """ Initialize function which should be overloaded with the code
        to open the communication with the instrument. Called by
        initialize(). """
        pass

    def move(self, target, axis=0):
        """ Moves the specified axis to the target value. Should not
        be overloaded (overload _move() instead).
        
        Args:
            target (float): target position to move to
            axis (int, optional): axis number
        """
        if 0 <= axis < self.number_of_axes:
            self._move(target, axis)

    def _move(self, target, axis=0):
        """ Move function which should be overloaded with the code to
        move the specified axis to target. Called by move().
        
        Args:
            target (float): target position to move to
            axis (int, optional): axis number
        """
        pass

    def get(self, axis=0):
        """ Reads the current position of the specified axis. Should not
        be overloaded (overload _get() instead).
        
        Args:
            axis (int, optional): axis number
        
        Returns:
            float: current position of specified axis.
        """
        if 0 <= axis < self.number_of_axes:
            return self._get(axis)
        else:
            return None

    def _get(self, axis=0):
        """ Get function which should be overloaded with the code to get
        the current position of the specified axis. Called by get().
        
        Args:
            axis (int, optional): axis number
        
        Returns:
            float: current position of the specified axis.
        """
        return None

    def close(self):
        """ Closes the communication with the instrument. Should not be
        overloaded (overload _close() instead). """
        if not self._dev_closed:
            super().close()
            self._dev_closed = True

    def _close(self):
        """ Close function which should be overloaded with the code to
        close the communication with the instrument. Called by close().
        """
        pass

    def set_smooth_delay(self, value):
        """ Change the smooth movement delay between each step.
        
        Args:
            value (float): delay between each step of the smooth
                movement, in seconds.
        """
        self.smooth_delay = value

    def set_smooth_step(self, value):
        """ Change the smooth movement step.
        
        Args:
            value (float): step used for the smooth movement (device
                unit)
        """
        self.smooth_step = value

    def move_smooth(self, scanner_axes, targets=[]):
        """ Move smoothly the specified axis to the target. Should be
        called preferentially to move() when the step is big.
        IMPORTANT: Note this construction through the scanner object 
        allows the user to overloard move_smooth() for a specific 
        scanner.
        
        Args:
            scanner_axes (list): list of Saxis objects or ScannerCtrl
                object.
            targets (list, optional): list of target positions.
        """

        # move_smooth(scanner_axes=scanner_axes, targets=targets)
        
        for scanner_axis, target in zip(scanner_axes, targets):
            move_smooth_simple(scanner_axis, target)

    def close_error_handling(self):
        """ Warning message generated for an error at communication
        closure for this device. """
        print('WARNING: Scanners {} did not close properly.'.format(self.string_id))


class Saxis():

    """ Saxis is meant for "Scanner axis" and provides a virtual
    axis/channel abstraction from ScannerCtrl that we call an s-axis. It
    is normally constructed in the __getitem__() method of a ScannerCtrl
    object, i.e. it is constructed and returned when calling scanner[1],
    for example. Saxis gets the initialize, move, move_smooth, get and
    close methods from the ScannerCtrl object which generated it,
    meaning it becomes virtually independent from the ScannerCtrl object
    and can handle the device being initialised/closed – redundancy
    flags prevent any multiple calls of initialize() or close() to cause
    errors.
    
    Attributes:
        axis (int): axis number (in the scanner object)
        scanner (ScannerCtrl): scanner device of which this axis is a
            member.
    """
    
    def __init__(self, scanner, axis):
        """ Recovers the mother ScannerCtrl object and axis number.
        
        Args:
            scanner (int): axis number (in the scanner object)
            axis (ScannerCtrl): scanner device of which this axis is a
                member.
        """
        self.axis = axis
        self.scanner = scanner

    def move(self, target):
        """ Moves s-axis to target.
        
        Args:
            target (float): target position to move to.
        """
        self.scanner.move(target=target, axis=self.axis)

    def get(self):
        """ Reads current position of the s-axis.
        
        Returns:
            float: current position of the s-axis.
        """
        return self.scanner.get(axis=self.axis)

    def move_smooth(self, target):
        """ Moves smoothly s-axis to target. See move_smooth() for more.
        
        Args:
            target (float): target position to move to.
        """
        self.scanner.move_smooth(scanner_axes=[self], targets=[target])

    def initialize(self):
        """ Initializes the communication with the instrument. """
        self.scanner.initialize()

    def close(self):
        """ Closes the communication with the instrument. """
        self.scanner.close()


def move_smooth(scanner_axes, targets=[]):
    """ Moves s-axes smoothly to target positions. The function
        calculates the most efficient trajectory through the different
        positions, moving all axes silmutaneously with their respective
        smooth_step and using the longest smooth_delay among the s-axes.
    
    Args:
        scanner_axes (Saxis list): list of s-axes to move
        targets (list, optional): list of floats, respective target
            positions for the s-axes
    """
    pass

def move_smooth_simple(scanner_axis, target):
    """ Moves one s-axis smoothly to target position.
    
    Args:
        scanner_axis (Saxis): s-axis to move
        target (float): target position for the s-axis
    """
    pass


class GalvoDummy (ScannerCtrl):
    def __init__(self, chX='/Dev1/ao0', chY='/Dev1/ao1', start_pos=[0,0], 
                     conversion_factor=1., min_limit= 0., max_limit= 5., ids = None):
        super().__init__(channels=[chX, chY], ids=ids)
        self.string_id = 'Galvo scanners controlled by NI box AO'
        self.conversion_factor = conversion_factor

        self.smooth_step = 1
        self.smooth_delay = 0.05
        
        self._min_limit = min_limit
        self._max_limit = max_limit

        self._curr_pos = [pos for channel, pos in zip(self._channels, start_pos)]

    def _initialize(self):
        pass

    def _move(self, target, axis=0):
        self._curr_pos[axis] = target

    def _get(self, axis=0):
        return self._curr_pos[axis]
         
    def set_range (self, min_limit, max_limit):
        self._min_limit = min_limit
        self._max_limit = max_limit

    def _close(self):
        pass


