import numpy as np

cfg={}

sample_name = 'test'
NV_name = 'none'
name=sample_name+'_'+NV_name
cfg['protocols'] = {'current':name}

cfg['protocols']['AdwinPhotodiode']={
        'ADC_channel'      :       16, #'photodiode'
        'sync_ch'           :       21, #'montana_sync'#
        'wait_cycles'       :       1,
        'scan_auto_reverse' :       False, #'if nr_scans>1, perform saw-tooth'
        'use_sync'          :       False, #'whether to use the montana sync'
        'delay_us'          :       0, #number of delay cycles
        'scan_to_start'     :       True,
        }

cfg['protocols']['AdwinPhotodiode']['cavlength_scan']={
        'DAC_ch_1'           :       1, #'jpe_fine_tuning_1'
        'DAC_ch_2'           :       2, #'jpe_fine_tuning_2'
        'DAC_ch_3'           :       3, #'jpe_fine_tuning_3'
        'cycle_duration'     :       1000, #running at 300 kHz
        'ADC_averaging_cycles':      10,
        'save_cycles'        :       300, #save every ms at 300 kHz
        'scan_to_start_speed':       2000,#in mV/s
        }

cfg['protocols']['AdwinPhotodiode']['laserfrq_scan']={
        'DAC_ch_1'           :       5, #'newfocus_freqmod'
        'DAC_ch_2'           :       0, #no dac_ch_2
        'DAC_ch_3'           :       0, #no sac_ch_2
        'cycle_duration'     :       3000, #running at 100 kHz, to enable ADC averaging 
        'ADC_averaging_cycles':     100000, #average one second per point
        'save_cycles'        :       100, #save every ms at 100 kHz
        'scan_to_start_speed':       2000,#in mV/s
        }