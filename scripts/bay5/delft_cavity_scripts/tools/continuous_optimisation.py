import qt
import time
import msvcrt
import os
import h5py
import sys



def contopt(interval,max_time):
    green_aom = qt.instruments['GreenAOM']
    opt_ins = qt.instruments['optimiz0r']
    opt1d_ins = qt.instruments['opt1d_counts']
    mos_ins = qt.instruments['master_of_space']
    aborted=False
    x=1
    green_aom.set_power(100e-6)

    d = qt.Data(name='optimize')
    d.add_coordinate('t (s)')

    d.add_coordinate('x (um)')
    d.add_coordinate('y (um)')
    d.add_coordinate('z (um)')
    t_start = time.clock()

    # d.create_file(filepath=os.path.splitext(self.h5data.filepath())[0]+'.dat')

    while aborted==False:
        qt.msleep(3)
        opt_ins.optimize(dims=['z','y','x'], cycles = 1, int_time = 100, cnt=1)
        
        new_x=mos_ins.get_x()
        new_y=mos_ins.get_y()
        new_z=mos_ins.get_z()
        # print new_x,new_y,new_z

        t0=time.clock()

        d.add_data_point(t0,new_x, new_y, new_z)

        while abs(t0-time.clock())<interval:
            qt.msleep(1)
            if (msvcrt.kbhit() and (msvcrt.getch() == 'q')):
                aborted=True
                break

        if abs(t_start-time.clock())>max_time:
            print 'I reached max time -- aborting! '
            aborted=True
            break

        if aborted==True:
            break
        x=x+1


    d.close_file()
    green_aom.turn_off()
