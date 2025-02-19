import pyclipper
import matplotlib.pyplot as plt

subj = ((180, 200), (260, 200), (260, 150),(180,200))

pco = pyclipper.PyclipperOffset()
pco.AddPath(subj, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)

solution = pco.Execute(5.0)
solution = solution[0]
solution.append(solution[0])
offsetted = zip(*solution)
xo,yo = offsetted

x, y = zip(*subj)



plt.plot(x,y)
plt.plot(xo,yo)
plt.show()

# solution (a list of paths): [[[253, 193], [187, 193], [187, 157], [253, 157]]]