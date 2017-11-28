def move_fine_piezos(step=0.001):

    piezos = ['jpe_fine_tuning_1','jpe_fine_tuning_2','jpe_fine_tuning_3']

    curr_voltages = [adwin.get_dac_voltage(p) for p in piezos]
    target_voltages = [adwin.get_dac_voltage(p)+step for p in piezos]
    adwin.linescan(piezos,curr_voltages, target_voltages, int(step/0.0001), 1, value='none')