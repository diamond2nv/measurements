import qt
import measurement.lib.measurement2.measurement as m2
reload(m2)

class Lockin_Dac_Adc(m2.AdwinControlledMeasurement):

    adwin_process = 'lockin_dac_adc'
    
    def run(self):
        self.start_adwin_process(stop_processes=['counter'])

    def stop(self):
        self.stop_adwin_process()
        self.finish()

if __name__ == '__main__':
    m=Lockin_Dac_Adc('test1')
    m.adwin = qt.instruments['adwin']
    
    
    m.params['output_dac_channel'] = m.adwin.get_dac_channels()['newfocus_freqmod']
    m.params['input_adc_channel']  = 16 
    m.params['modulation_bins']    = 200 #number of
    m.params['error_averaging'] = 50
    m.params['modulation_amplitude'] = 0.15 #V
    m.params['modulation_frequency'] = 600 #Hz
    print 'aprox. read_interval:', 1./m.params['modulation_frequency'] * m.params['error_averaging']

    m.autoconfig()
    m.run()

