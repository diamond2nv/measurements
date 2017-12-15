# -*- coding: utf-8 -*-

class DeviceCtrl():
    string_id = 'Unknown device'
    
    def visa_error_handling(self, err):
        if int(err.error_code) == -1073807343:
            print('\n##########  ATTENTION: '+
                  'Address of the {} does not match any device. You should'.format(self.string_id) +
                  ' check the address of the device or reset it.\n')
            raise
            
        elif int(err.error_code) == -1073807246:
            print('\n##########  ATTENTION: ' +
                  'The {} is busy. Did you close any other program using it?\n'.format(self.string_id))
            raise
        else:
            raise  

    def _close(self):
        pass

    def close(self):
        try:
            self._close()
        except:
            self.close_error_handling()

    def close_error_handling(self):
        print('WARNING: Device {} did not close properly.'.format(self.string_id))