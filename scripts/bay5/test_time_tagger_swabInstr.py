"""
    examples for TimeTagger, an OpalKelly based single photon counting library
    Copyright (C) 2013-2015  Helmut Fedder helmut@swabianinstruments.com

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from TimeTagger import createTimeTagger, Combiner, Coincidence, Counter, Countrate, Correlation, TimeDifferences, TimeTagStream, TimeTagStreamBuffer, Scope, Event, CHANNEL_UNUSED
from time import sleep
from pylab import *

# create a timetagger instance
tagger = createTimeTagger()
tagger.reset();

# simple counter on channels 0 and 1 with 1 ms binwidth (1e9 ps) and 2000 successive values
print ("****************************************")
print ("*** Demonstrate a counter time trace ***")
print ("****************************************")
print ("")
print ("Create counters on channels 0 and 1 with 1 ms binwidth and 1000 points.")
print ("")
count = Counter(tagger, channels=[0,1], binwidth=int(1e9), n_values=int(1000))


# apply the built in test signal (~0.8 to 0.9 MHz) to channels 0 and 1
print ("Enabling test signal on channel 0.")
print ("")
tagger.setTestSignal(0, True)
sleep(.5)
print ("Enabling test signal on channel 1.")
print ("")
tagger.setTestSignal(1, True)
sleep(.5)

# wait until the 1000 values should be filled
# we should see the calibration signal turning on in the time trace

# retrieve the current buffer
data = count.getData()

# plot the result
figure()
plot(count.getIndex()/1e12, data[0]*1e-3, label='channel 0')
plot(count.getIndex()/1e12, data[1]*1e-3, label='channel 1')
xlabel('Time [s]')
ylabel('Countrate [MHz]')
ylim(0.,4.)
legend()
title('Time trace of the click rate on channel 0 and 1')
text(0.1,2,'The built in test signal (~ 800 to 900 kHz) is applied first to channel 0\nand 0.5 s later to channel 1.')
tight_layout()
show()

# cross correlation between channels 0 and 1
# binwidth=1000 ps, n_bins=3000, thus we sample 3000 ns
# we should see the correlation delta peaks at a bit more than 1000 ns distance
print ("*************************************")
print ("*** Demonstrate cross correlation ***")
print ("*************************************")
print ("")
print ("Create a cross correlation on channels 0 and 1 with 1 ns binwidth and 3000 points.")
print ("")
corr = Correlation(tagger, channel_1=0, channel_2=1, binwidth=1000, n_bins=3000)
sleep(1)
figure()
plot(corr.getIndex()/1e3, corr.getData())
xlabel('Time [ns]')
ylabel('Clicks')
title('Cross correlation between channel 0 and 1')
text(-1400,300000,"""
The built in test signal is applied
to channel 0 and channel 1.
The peak distance corresponds to
the period of the test signal.
""")
text(100,300000,"""
Note: the decreasing peak heights
and broadening of the peaks
reflects the jitter of the built in
test signal, which is much larger
than the instrument jitter.
""")
tight_layout()
show()

# cross correlation between channels 0 and 1
# binwidth=10 ps, n_bins=400, thus we sample 4 ns
# The standard deviation of the peak
# is the root mean square sum of the
# input jitters of channels 0 and 1
print ("Create a cross correlation on channels 0 and 1 with 10 ps binwidth and 100 points.")
print ("")
corr = Correlation(tagger, channel_1=0, channel_2=1, binwidth=10, n_bins=400)
sleep(2)
figure()
plot(corr.getIndex(), corr.getData())
title('High res cross correlation showing <60 ps instrument jitter')
text(-1500,80000,"""
The half width of the peak is
sqrt(2) times the instrument jitter.
The shift of the peak from zero
is the propagation delay of the
built in test signal.
""")
xlabel('Time [ps]')
ylabel('Clicks')
tight_layout()
show()

propagation_delay = int(abs(corr.getIndex()[corr.getData().argmax()]))

print ("************************************")
print ("*** Demonstrate virtual channels ***")
print ("************************************")
print ("")
print ("Create a virtual channel that contains all tags of channel 0 and channel 1.")
print ("")
ch0_or_ch1 = Combiner(tagger, channels=[0,1])
print ("The virtual channel was assigned the channel number %i." % ch0_or_ch1.getChannel())
print ("")
print ("Create a virtual channel that contains coincidence clicks of channel 0 and channel 1 within a +-%i ps window." % propagation_delay)
print ("")
ch0_and_ch1 = Coincidence(tagger, channels=[0,1], window=propagation_delay)
print ("The virtual channel was assigned the channel number %i." % ch0_and_ch1.getChannel())
print ("")
print ("Create a countrate on channel 0 and the virtual channels.")
print ("")
countrate = Countrate( tagger, channels=[0, ch0_or_ch1.getChannel(), ch0_and_ch1.getChannel()] )
sleep(1)
print ("Count rates\n  channel 0:    %i counts / s\n  ch0 and ch1: %i counts / s\n  coincidences: %i counts / s." % tuple(countrate.getData()))
print ("")
print ("""
Here, we have used a coincidence window that coincides just with the propagation delay
between ch0 and ch1. Due to jitter, approximately half of the coincidence counts
fall outside of this coincidence range. Therefore the coincidence countrate is
approximately half of the original count rate.
""")
print ("")



print ("***********************************")
print ("*** Demonstrate synchronization ***")
print ("***********************************")
print ("")
print ("Create an average count rate on channel 0.")
rate = Countrate(tagger, channels=[0])
print ("")
print ("Disable the test signal and wait.")
tagger.setTestSignal(0, False)
tagger.setTestSignal(1, False)
sleep(1)
print ("")
print ("Enable the test signal, clear the data, wait 500 ms, read the data.")
print ("")
tagger.setTestSignal(0, True)
rate.clear()
sleep(0.5)
rate_no_sync = rate.getData()
print ("Disable the test signal and wait.")
tagger.setTestSignal(0, False)
sleep(1)
print ("")
print ("Enable the test signal, clear the data, sync, wait 500 ms, read the data.")
print ("")
tagger.setTestSignal(0, True)
tagger.sync()
rate.clear()
sleep(0.5)
rate_sync = rate.getData()
print ("Count rate\n  without sync: %i counts / s\n  with sync: %i counts / s" % (rate_no_sync[0], rate_sync[0]))
print ("")
print ("""
The execution of the 'sync' method ensures that all settings are actually
applied (in this case the activation of test signal) and the USB buffer is
flushed. I.e., after a 'sync' call, we are sure not to receive time tags that
were generated in the past. In this demonstration, we turn on the test signal
and subsequently record the average click rate. One may expect to obtain
the original click rate of the test signal. However, data transmission is never
instantaneous and therefore we include a time span when the test signal was not
yet turned on. Consequently, the average click rate is reduced compared to the
actual value. By inserting a "sync" call before we start recording, the
behavior is changed and we ensure that we are not processing past time tags.
Therefore, the average corresponds to the physical click rate.
""")

print ("*****************************")
print ("*** Demonstrate filtering ***")
print ("*****************************")
print ("")
print ("Enabling event filter.")
tagger.setConditionalFilter([0],[7])
print ("")
print ("Enabling test signal on channel 0 and channel 7.")
print ("")
tagger.setTestSignal(0, True)
tagger.setTestSignal(7, True)
rate = Countrate(tagger, channels=[0,7])
tagger.sync()
rate.clear()
sleep(1)
print ("Count rates\n  channel 0: %i counts / s\n  channel 7: %i counts / s" % tuple(rate.getData()))
print ("")
print ("Disabling test signal on channel 0.")
print ("")
tagger.setTestSignal(0, False)
tagger.sync()
rate.clear()
tagger.setFilter(False)
sleep(1)
print ("Count rates\n  channel 0: %i counts / s\n  channel 7: %i counts / s" % tuple(rate.getData()))
print ("")
print ("""
Here, we have used the event filter between channel 0 and channel 7 to suppress time tags on channel 7. The filter drops time tags on
channel 7 unless they were preceded by a tag on channel 0. First, since the 
tags are simultaneous on both channels, but there is a finite jitter the count
rate on channel 7 is reduced by some amount. Now, as we disable the test signal
on channel 0, all time tags on channel 7 are suppressed and a count rate of 0
is measured, even though the test signal is active. The filtering is useful to
tame signals with data rates > 8 MHz such as synchronization signals from
pulsed lasers in fluorescence lifetime measurements.
""")

# disable the internal test signal on channels 0 and 1
print ("Disable test signals on channel 0 and 1.")
print ("")
tagger.setTestSignal(0, False)
tagger.setTestSignal(1, False)

print ("*****************************************")
print ("*** Demonstrate trigger level control ***")
print ("*****************************************")
print ("")
print ("Disable test signals and filter.")
print ("")
tagger.setTestSignal(0, False)
tagger.setTestSignal(1, False)
tagger.setTestSignal(7, False)
# set the trigger levels on channel 0 and 1 to 0.5 V
# (this is the default value at startup)
print ("Set trigger levels on channel 0 and 1 to 0.5 volts.")
print ("")
tagger.setTriggerLevel(0, 0.5)
tagger.setTriggerLevel(1, 0.5)
tagger.sync()
sleep(1)

print ("**************************************")
print ("*** Access the raw time tag stream ***")
print ("**************************************")
print ("")
print ("Enable test signals.")
print ("")
tagger.setTestSignal([0, 1], True)
tagger.sync()
# create a buffer which contains up to 1M tags 
# FIXME: named arguments not possible for TimeTagStream - this will be available in the next release (I need Markus or another C++/SWIG expert for this)
stream = TimeTagStream(tagger, 1000000, [0, 1])
sleep(0.5)
# to receive the data we have to create a buffer object first
buffer = TimeTagStreamBuffer()
stream.getData(buffer)
print ("Total number of tags stored in the buffer: " + str(buffer.size));
print ("Show the first 10 tags");
for i in range(min(buffer.size, 10)):
    print("  time in ps: " + str(buffer.tagTimestamps[i]) + " signal recieved on channel: "  + str(buffer.tagChannels[i]))
print ("")

sleep(1)

print ("*****************************")
print ("*** Digital scope example ***")
print ("*****************************")
print ("")
print ("Enable test signals.")
print ("")
channel = 0
scope = Scope(tagger, event_channels=[channel], trigger_channel=channel, window_size=10000000, n_traces=1, n_max_events=1000)
tagger.sync()
sleep(0.5)
edges = scope.getData();

#number of edges received
edgesSize = size(edges[channel][:])

print ("Received " + str(edgesSize) + " edges for channel 0.")
print ("")

# edge states: 0: unknown, 1:falling, 2: rising
# FIXME: take Enum State.UNKNOWN, .... instead of hard coded numbers
if (edgesSize > 0) & (edges[channel][0].state != 0):
    #every edge is represented as two x,y points
    x = [0] * edgesSize * 2
    y = [0] * edgesSize * 2
    for i in range(edgesSize):
        x[i*2] = edges[channel][i].time
        y[i*2] = edges[channel][i].state == 2
        x[i*2+1] = edges[channel][i].time
        y[i*2+1] = edges[channel][i].state == 1
            
    figure()
    plot(array(x)/1000000.,y)
    title('Digital Scope - trace of channel 0 (test signal)')
    ylim(-0.1, 1.1)
    xlabel('Time [ns]')
    ylabel('Signal')
    gca().set_yticks([0, 1])
    show()
