
import numpy as np
import pylab as plt

#load the array of counts
a = np.load('C:/Research/HDscan3.npz')
counts = a['counts']
xPos = a['xPos']
yPos = a['yPos']

#plot is using matplotlib
plt.pcolor(xPos, yPos, counts)
plt.colorbar()
plt.show()