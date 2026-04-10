from cc3d.core.PySteppables import *

import random
import math


class MarblingInitializerSteppable(SteppableBasePy):
    def __init__(self, frequency=1):
        super().__init__(frequency)

    def start(self):
        # Fill domain with MUSCLE as a single tissue-like sheet (one cell)
        # Then seed many FAT_PROGENITOR cells inside it.

        # 1) Create a big MUSCLE cell covering almost entire lattice
        muscle = self.new_cell(self.MUSCLE)
        for x in range(10, self.dim.x - 10):
            for y in range(10, self.dim.y - 10):
                self.cell_field[x, y, 0] = muscle

        # 2) Seed fat progenitors as small circular islands
        # tune for "marbling density"
        n_seeds = 55
        r = 3

        for _ in range(n_seeds):
            cx = random.randint(20, self.dim.x - 21)
            cy = random.randint(20, self.dim.y - 21)

            fp = self.new_cell(self.FAT_PROGENITOR)
            for x in range(cx - r, cx + r + 1):
                for y in range(cy - r, cy + r + 1):
                    if 0 <= x < self.dim.x and 0 <= y < self.dim.y:
                        if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                            # embed inside muscle only
                            if self.cell_field[x, y, 0] and self.cell_field[x, y, 0].type == self.MUSCLE:
                                self.cell_field[x, y, 0] = fp

        # Optional: start with a few mature FAT cells (speckles)
        for _ in range(10):
            cx = random.randint(25, self.dim.x - 26)
            cy = random.randint(25, self.dim.y - 26)
            fat = self.new_cell(self.FAT)
            rr = 2
            for x in range(cx - rr, cx + rr + 1):
                for y in range(cy - rr, cy + rr + 1):
                    if 0 <= x < self.dim.x and 0 <= y < self.dim.y:
                        if (x - cx) ** 2 + (y - cy) ** 2 <= rr ** 2:
                            if self.cell_field[x, y, 0] and self.cell_field[x, y, 0].type == self.MUSCLE:
                                self.cell_field[x, y, 0] = fat


class MarblingDynamicsSteppable(SteppableBasePy):
    def __init__(self, frequency=10):
        super().__init__(frequency)

        # "Wagyu knobs"
        self.differentiation_threshold = 0.55  # nutrient level to trigger adipogenesis
        self.progenitor_to_fat_prob = 0.12     # probability per step once above threshold

        self.fat_growth_rate = 0.8            # add to target volume per step
        self.progenitor_growth_rate = 0.25

        # limit overgrowth
        self.max_fat_target = 160
        self.max_prog_target = 70

    def step(self, mcs):
        nutrient = self.field.NUTRIENT

        for cell in self.cell_list:

            # sample nutrient at COM
            x = int(cell.xCOM)
            y = int(cell.yCOM)
            z = 0
            local_n = nutrient[x, y, z]

            if cell.type == self.FAT_PROGENITOR:
                # mild growth
                if cell.targetVolume < self.max_prog_target:
                    cell.targetVolume += self.progenitor_growth_rate

                # differentiate if nutrient is high
                if local_n >= self.differentiation_threshold:
                    if random.random() < self.progenitor_to_fat_prob:
                        cell.type = self.FAT
                        # jump target volume to represent lipid loading
                        cell.targetVolume = max(cell.targetVolume, 85)

            elif cell.type == self.FAT:
                # fat expands more (marbling)
                if cell.targetVolume < self.max_fat_target:
                    cell.targetVolume += self.fat_growth_rate

            elif cell.type == self.MUSCLE:
                # keep muscle fairly stable; slight remodeling near fat if you want:
                # (optional) reduce target volume if surrounded by fat (simulate displacement)
                pass



def configure_simulation(sim):
    sim.register_steppable(steppable=MarblingInitializerSteppable(frequency=1))
    sim.register_steppable(steppable=MarblingDynamicsSteppable(frequency=10))
