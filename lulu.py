import numpy as np
import matplotlib.pyplot as plt


x = np.array([1, 2, 3], dtype=float)
y = np.array([2, 3, 5], dtype=float)

def loss(w, b):
    # w y b pueden ser escalares o matrices (50x50)
    # Les agregamos una dimension extra al final para que "alineen" con x (3,)
    y_pred = w[..., None] * x + b[..., None]  # forma: (50,50,3)
    return np.mean((y_pred - y)**2, axis=-1)  # promedio en los datos, queda (50,50)

W, B = np.meshgrid(np.linspace(-3, 3, 50), np.linspace(-3, 3, 50))
Z = loss(W, B)

# Gráfica 3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(W, B, Z, cmap='viridis')
plt.show()