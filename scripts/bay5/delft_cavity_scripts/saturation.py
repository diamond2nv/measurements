import time
import qt
import data
from analysis.lib.fitting import fit, common
from numpy import *
import msvcrt

#measurement parameters
name = 'Hans_sil4'#'The111No2_enlarged_SIL2_DM_off'
steps=16
max_power=996e-6       #[w]
counter=1    #number of counter
PQ_count=False   # counting with the HH, assumes apd on channel 0
bg_x=-1.5         #delta x position of background [um]
bg_y=1.0            #delta y position of background [um]

#instruments
if PQ_count:
    current_PQ_ins=qt.instruments['TH_260N']

current_aom = qt.instruments['GreenAOM']
#current_aom = qt.instruments['PulsedAOM']
current_mos = qt.instruments['master_of_space']
current_adwin = qt.instruments['adwin']

current_power = current_aom.get_power()

counters.set_is_running(True)

x = linspace(0,max_power,steps)
y_NV = zeros(steps,dtype = float)
y_BG = zeros(steps,dtype = float)

current_x = current_mos.get_x()
current_y = current_mos.get_y()

current_aom.set_power(0)
time.sleep(1)
br=False
for i,pwr in enumerate(x):
    if (msvcrt.kbhit() and (msvcrt.getch() == 'q')): 
        br = True
        break
    current_aom.set_power(pwr)
    time.sleep(1)
    if not PQ_count:
        y_NV[i] = current_adwin.get_countrates()[counter-1]
    else:
        y_NV[i] = getattr(current_PQ_ins,'get_CountRate'+str(counter-1))()
    print 'step %s, counts %s'%(i,y_NV[i])
        
current_mos.set_x(current_x + bg_x)
current_mos.set_y(current_y + bg_y)
current_aom.set_power(0)
time.sleep(1)
if not br:
    for i,pwr in enumerate(x):
        if (msvcrt.kbhit() and (msvcrt.getch() == 'q')): break
        current_aom.set_power(pwr)
        time.sleep(1)
        if not PQ_count:
            y_BG[i] = current_adwin.get_countrates()[counter-1]
        else:
            y_BG[i] = getattr(current_PQ_ins,'get_CountRate'+str(counter-1))()
        print 'step %s, counts %s'%(i,y_BG[i])
       
 
x_axis = x*1e6

A, sat = max(y_NV-y_BG), .5*max_power*1e6
fitres = fit.fit1d(x_axis,y_NV-y_BG, common.fit_saturation, 
        A, sat, do_print=True, do_plot=False, ret=True)

dat = qt.Data(name='Saturation_curve_'+name)
dat.create_file()
dat.add_coordinate('Power [uW]')
dat.add_value('Counts [Hz]')
dat.add_value('Counts fitted [Hz]')
dat.add_value('NV Counts [Hz]')
dat.add_value('Background Counts [Hz]')
plt = qt.Plot2D(dat, 'rO', name='Saturation curve', coorddim=0, valdim=1, clear=True)
plt.add_data(dat, coorddim=0, valdim=2)
fd = zeros(len(x_axis))    
if type(fitres) != type(False):
    fd = fitres['fitfunc'](x_axis)
    plt.set_plottitle(dat.get_time_name()+', Sat. cts: {:d}, sat. pwr: {:.2f} uW'.format(int(fitres['params_dict']['A']),fitres['params_dict']['xsat']))
else:
    print 'could not fit calibration curve!'
    
current_mos.set_x(current_x)
current_mos.set_y(current_y)

dat.add_data_point(x_axis,y_NV-y_BG,fd,y_NV,y_BG)
plt.set_legend(False)

plt.save_png(dat.get_filepath()+'png')
dat.close_file()


current_aom.set_power(current_power)


print 'Done with saturation scan!'