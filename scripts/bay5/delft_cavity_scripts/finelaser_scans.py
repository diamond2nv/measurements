"""
Script that uses the fine laserscan fromt he cavity scan manager
sweeping parameters
"""
import msvcrt

cav_scan_manager = qt.instruments['cavity_scan_manager']


def sweep_nr_adwin_cycles_per_point(start_cycles,stop_cycles,nr_points,wavemeter_integration_in_ms=200):
    cav_scan_manager.set_cycle_duration(3000) #10 us per point
    cav_scan_manager.set_wait_cycles(1)
    cav_scan_manager.set_use_wavemeter(True)

    wavemeter_cycles = int(wavemeter_integration_in_ms*100) #convert to units of 10 us 

    if start_cycles<wavemeter_cycles:
        print 'WARNING: increase number of cycles'
        return

    ADC_averaging_cycles = np.linspace(start_cycles,stop_cycles,nr_points)
    print ADC_averaging_cycles

    for i,c in enumerate(ADC_averaging_cycles):
        cav_scan_manager.set_ADC_averaging_cycles(c)
        cav_scan_manager.set_file_tag('sweep_ADC_avg_cycles_'+str(int(c)))
        cav_scan_manager.get_file_tag()
        qt.msleep(1)
        cav_scan_manager.start_finelaser()
        qt.msleep(0.2) #this waiting time has to be long enough for the cav_scan_manager to know you started the task = 0.2
        if (msvcrt.kbhit() and (msvcrt.getch() == 'q')):
            break
        print 'finished laserscan %d out of %d'%(i+1,nr_points)

if __name__ == '__main__':
    start_cycles = 50000
    stop_cycles = 300000
    sweep_nr_adwin_cycles_per_point(start_cycles,stop_cycles,6,wavemeter_integration_in_ms=210)