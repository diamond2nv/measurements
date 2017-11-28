import qt
import time
import numpy as np
import msvcrt

tau_dict = {
                0 : "10mus",
                1 : "30mus",
                2 : "100mus",
                3 : "300mus",
                4 : "1ms",
                5 : "3ms",
                6 : "10ms",
                7 : "30ms",
                8 : "100ms",
                9 : "300ms",
                10 : "1s",
                11 : "3s",
                12 : "10s",
                13 : "30s",
                14 : "100s",
                15 : "300s",
                16 : "1ks",
                17 : "3ks",
                18 : "10ks",
                19 : "30ks"
                }

ins_lockin = qt.instruments['lockin']
frq_start = 10 #Hz
frq_stop = 6e3 #Hz
pts = 500
avg_pts=1

int_time_s = tau_dict[ins_lockin.get_tau()]
int_time_s=int_time_s.replace('s','')
int_time_s=int_time_s.replace('mu','e-6')
int_time_s=int_time_s.replace('m','e-3')
int_time_s=int_time_s.replace('k','e3')
int_time = float(int_time_s)
print 'integration time', int_time

dat = qt.Data(name= 'lockin_freq_sweep')
dat.add_coordinate('Frequency [Hz]')
dat.add_value('Amplitude [V]')
dat.add_value('Phase [deg]')
dat.create_file()
plt = qt.Plot2D(dat, 'rO', name='lockin_sweep', coorddim=0, valdim=1, 
        clear=True)
plt.add_data(dat, coorddim=0, valdim=2,right=True)
       


freqs = np.linspace(frq_start,frq_stop,pts)
Rs = np.zeros(pts)
Ps = np.zeros(pts)
qt.mstart()
for j in range(avg_pts):
    for i,f in enumerate(freqs):
        if (msvcrt.kbhit() and (msvcrt.getch() == 'q')): 
            break
        ins_lockin.set_frequency(f)
        time.sleep(0.1)
        qt.msleep(int_time)
        Rs[i] += ins_lockin.get_R()
        Ps[i] += ins_lockin.get_P()

        dat.add_data_point(f,Rs[i],Ps[i])
qt.mend()
dat.close_file()
plt.save_png(dat.get_filepath()+'png')