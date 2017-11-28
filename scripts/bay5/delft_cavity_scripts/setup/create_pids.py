if False:

    _setctrl_nf_freq = lambda x: qt.instruments['adwin'].set_dac_voltage(('newfocus_freqmod',x))
    _getval_nf_freq = lambda: qt.instruments['adwin'].read_photodiode()
    _getctrl_nf_freq=  lambda: qt.instruments['adwin'].get_dac_voltage('newfocus_freqmod')
    pidnffrq = qt.instruments.create('pidnffrq', 'pid_controller_v4', 
            set_ctrl_func=_setctrl_nf_freq , get_val_func=_getval_nf_freq , get_ctrl_func=_getctrl_nf_freq, 
            ctrl_minval=-10., ctrl_maxval=10.)

if False:
    _setctrl_nf_freq = lambda x: qt.instruments['physical_adwin'].Set_FPar(71,x)
    _getval_nf_freq =  lambda: qt.instruments['physical_adwin'].Get_FPar(73)
    _getctrl_nf_freq=  lambda: qt.instruments['physical_adwin'].Get_FPar(71)
    pidnffrq = qt.instruments.create('pidnffrq', 'pid_controller_v4', 
            set_ctrl_func=_setctrl_nf_freq , get_val_func=_getval_nf_freq , get_ctrl_func=_getctrl_nf_freq, 
            ctrl_minval=-9., ctrl_maxval=9.)

if False:
    _setctrl_nf_freq = lambda x: qt.instruments['master_of_cavity'].set_fine_piezo_voltages(x,x,x)
    _getval_nf_freq =  lambda: qt.instruments['physical_adwin'].Get_FPar(73)
    _getctrl_nf_freq=  lambda: qt.instruments['master_of_cavity'].get_fine_piezo_voltages()[0]
    pidnffrq = qt.instruments.create('pidnffrq', 'pid_controller_v4', 
            set_ctrl_func=_setctrl_nf_freq , get_val_func=_getval_nf_freq , get_ctrl_func=_getctrl_nf_freq, 
            ctrl_minval=3.5, ctrl_maxval=4.5)

if True:
    _setctrl_nf_freq = lambda x: qt.instruments['physical_adwin'].Set_FPar(71,x)
    _getval_nf_freq =  lambda: qt.instruments['physical_adwin'].Get_FPar(73)
    _getctrl_nf_freq=  lambda: qt.instruments['physical_adwin'].Get_FPar(71)
    _setfrq_coarse = lambda x: qt.instruments['master_of_cavity'].set_fine_piezo_voltages(x,x,x)
    _getfrq_coarse = lambda: qt.instruments['master_of_cavity'].get_fine_piezo_voltages()[0]
    pidnffrq = qt.instruments.create('pidnffrq', 'pid_controller_v4', 
            set_ctrl_func_coarse=_setfrq_coarse, get_ctrl_func_coarse=_getfrq_coarse, \
            set_ctrl_func=_setctrl_nf_freq , get_val_func=_getval_nf_freq , get_ctrl_func=_getctrl_nf_freq, 
            ctrl_minval=-9., ctrl_maxval=9.,ctrl_minval_coarse=3.5,ctrl_maxval_coarse=4.5)