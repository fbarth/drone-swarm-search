import matplotlib.pyplot as plt
import numpy as np

def draw_matrix(matrix: np.matrix):
    length = len(matrix)
    _, ax = plt.subplots()

    for i in range(length):
        
        for j in range(length):
            _ = ax.text(
                j, i, matrix[i, j], ha="center", va="center", color="w"
            )

    ax.matshow(matrix)
    plt.show()