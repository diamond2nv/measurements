
import numpy as np
import pylab as plt

#load the array of counts
a = np.load('C:/Research/test.npz')
counts = a['counts']
xPos = a['xPos']
yPos = a['yPos']

#plot is using matplotlib
plt.pcolor(xPos, yPos, data)
plt.axis('equal')
plt.colorbar()
plt.show()