"""
Cavity script for photodiode measurement
SvD 12-2016
"""
import qt
execfile(qt.reload_current_setup)

import measurement.lib.measurement2.measurement as m2

from measurement.lib.measurement2.adwin_pd import pd_msmt


def scan_laser_freq(name):
    #m = m2.AdwinControlledMeasurement('a')
    m = pd_msmt.AdwinPhotodiode('LaserScan_'+name)

    m.params.from_dict(qt.exp_params['protocols']['AdwinPhotodiode'])
    m.params.from_dict(qt.exp_params['protocols']['AdwinPhotodiode']['laserfrq_scan'])

    m.params['start_voltage'] = 0
    m.params['end_voltage'] = 0.3

    m.params['nr_scans']=1
    m.params['nr_steps']=5


    m.params['voltage_step'] = abs((m.params['end_voltage'] - m.params['start_voltage']))/float(m.params['nr_steps']-1)
    m.params['start_voltage_1'] = m.params['start_voltage']
    m.params['start_voltage_2'] = m.params['start_voltage']
    m.params['start_voltage_3'] = m.params['start_voltage']

    m.params['scan_to_start'] = True

    #useful derived parameters useful for analysis
    m.params['nr_ms_per_point'] = m.params['ADC_averaging_cycles']/m.params['save_cycles']

    dac_channels = [m.params['DAC_ch_1']]
    m.params['dac_names'] = ['newfocus_freqmod']
    m.params['start_voltages'] = [m.params['start_voltage']]

    m.run()

    m.save('laserscan')
    m.finish()



def scan_cavity_length(name):
    m = photodiode_msmt.AdwinPhotodiode('LengthScan_'+name)

    m.params.from_dict(qt.exp_params['protocols']['AdwinPhotodiode'])
    m.params.from_dict(qt.exp_params['protocols']['AdwinPhotodiode']['cavlength_scan'])

    m.params['start_voltage'] = 0
    m.params['end_voltage'] = 0.3

    m.params['nr_scans']=1
    m.params['nr_steps']=11

    m.params['voltage_step'] = abs((m.params['end_voltage'] - m.params['start_voltage']))/float(m.params['nr_steps']-1)
    m.params['start_voltage_1'] = m.params['start_voltage']
    m.params['start_voltage_2'] = m.params['start_voltage']
    m.params['start_voltage_3'] = m.params['start_voltage']

    #derived parameters useful for analysis
    m.params['nr_ms_per_point'] = m.params['ADC_averaging_cycles']/m.params['save_cycles']

    dac_channels = [m.params['DAC_ch_1']]
    m.params['dac_names'] = ['jpe_fine_tuning_1','jpe_fine_tuning_2','jpe_fine_tuning_3']
    m.params['start_voltages'] = [m.params['start_voltage'],m.params['start_voltage'],m.params['start_voltage']]

    m.run()
    m.save('lengthscan')
    m.finish()

if __name__ == '__main__':
    scan_laser_freq('test')