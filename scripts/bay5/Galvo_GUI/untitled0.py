import matplotlib.pyplot as plt

x = [3.9,3.9,7.16,11,12.3,14.5]
y = [8.2,8.4,1.2,1.1,1.1,0.5]
r = [75,91,65,80,70,75]

plt.ylabel('relative coupling efficiency (%)')
plt.xlabel('Distance from mode centre (V)')
plt.title('Efficiency against distance from mode centre')
#plt.plot(x,y,'ro')

plt.ylabel('BS ratio (%))')
plt.xlabel('Distance from mode centre (V)')
plt.title('BS ratio against distance from mode centre')
plt.plot(x,r,'bo')