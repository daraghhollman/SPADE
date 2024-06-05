import matplotlib.pyplot as plt
import dataProcessing

class Panel:
    def __init__(self, data: Data) -> None:
        self.data = data


class Multipanel:
    def __init__(self, panels: list, panelIndices: list) -> None:
        """Panels contains a list of panel classes to be plotted at positions governed by panelIndices."""
        self.panels = panels
        self.panelIndices = panelIndices

    def Plot(self):
        fig, axes = plt.subplots(1, len(self.panels))

        for panel, panelIndex in zip(self.panels, self.panelIndices):
           
            panel.data.Plot(fig, axes[panelIndex])
