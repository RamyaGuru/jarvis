#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 16:29:33 2022

@author: rlg3

Silicon testing for the phono3py outputs file.
"""
from jarvis.io.phono3py.outputs import Kappa, JDOS
from jarvis.io.phonopy.outputs import (
    total_dos,
    get_Phonopy_obj,
    get_spectral_heat_capacity
)
import numpy as np
import matplotlib.pyplot as plt


from sklearn.metrics import mean_absolute_error


kappa_Si = Kappa(
    "kappa-m111111.hdf5", total_dos_dat="../../phonopy/Si-testing/total_dos.dat",
)
RT_kappa = kappa_Si.kappa(300.0)
from jarvis.core.atoms import Atoms

test_dir = "phono3py-example-Si-PBEsol/"
pos = test_dir + "POSCAR-unitcell"
atoms = Atoms.from_poscar(pos)
phonon_obj = get_Phonopy_obj(
    atoms,
    phonopy_yaml=test_dir + "phono3py.yaml",
    FC_file=test_dir + "fc2.hdf5",
    scell=np.array([[2, 0, 0], [0, 2, 0], [0, 0, 2]]),
)
jdos_dir = "unweighted_jdos/"

jdos = JDOS(phonon_obj, directory=jdos_dir, mesh=[11, 11, 11])
freq_pts = jdos.phonopy_obj._total_dos._frequency_points
jdos_ir = jdos.select_jdos()
spectral_jdos = jdos.mode_to_spectral(jdos_ir)
spectral_2Gamma = jdos.linewidth_from_jdos(spectral_jdos, atoms, vs=6084, plot=True)
spectral_kappa = jdos.kappa_from_linewidth(spectral_2Gamma, plot=True)

find_nan = np.argwhere(np.isnan(spectral_kappa))

spectral_kappa = np.delete(spectral_kappa, find_nan)
red_freq_pts = np.delete(freq_pts, find_nan)
cum_model_kappa = np.trapz(spectral_kappa, red_freq_pts)


"""
Print Spectral Quantities from the kappa hdf5 file
"""
# Kappa
spectral_kappa_ph3 = jdos.mode_to_spectral_unwtd(
    kappa_Si.dict["mode_kappa"][30, :, :, 0]
)
plt.figure()
plt.plot(freq_pts, spectral_kappa_ph3)
# plt.scatter(kappa_Si.dict['frequency'], kappa_Si.dict['mode_kappa'][30, :, :, 0])
plt.xlabel("Frequency (THz)")
plt.ylabel(r"$\kappa$ (W/m$\cdot$K$\cdot$THz)")
plt.xlim([0, 15])
plt.ylim([0, 30])

# Heat Capacity
spectral_Cp_ph3 = jdos.mode_to_spectral_wtd(kappa_Si.dict["heat_capacity"][30, :, :])
plt.figure()
plt.plot(freq_pts, spectral_Cp_ph3)
plt.xlabel("Frequency (THz)")
plt.ylabel(r"C (eV/K$\cdot$THz)")

# Squared Group Velocity
spectral_vg_ph3 = jdos.mode_to_spectral(np.array(kappa_Si.dict["gv_by_gv"][:, :, 0]))
plt.figure()
plt.plot(freq_pts, spectral_vg_ph3)
plt.xlabel("Frequency (THz)")
plt.ylabel(r"Phono3py Squared Group Velocity (THz$^2\cdot\AA^2$)")
plt.scatter(
    np.array(kappa_Si.dict["frequency"]),
    np.array(kappa_Si.dict["gv_by_gv"][:, :, 0]),
    s=2,
)


# Gamma
spectral_gamma = jdos.mode_to_spectral(np.array(kappa_Si.dict["gamma"][30, :, :]))
plt.figure()
plt.plot(freq_pts, 2 * spectral_gamma)
plt.xlabel("Frequency (THz)")
plt.ylabel(r"$2\Gamma$ (THz)")
# plt.scatter(
#     np.array(kappa_Si.dict["frequency"]),
#     np.array(kappa_Si.dict["gamma"][30, :, :]),
#     s=2,
# )


"""
Difference between model and DFT phonon linewidth
"""

find_nan = np.argwhere(np.isnan(spectral_2Gamma))
spectral_2Gamma = np.delete(spectral_2Gamma, find_nan)
spectral_gamma = np.delete(spectral_gamma, find_nan)
freq_pts = np.delete(freq_pts, find_nan)

plt.figure()
plt.plot(freq_pts, (spectral_2Gamma - (2 * spectral_gamma)))
plt.xlabel("Frequency (THz)")
plt.ylabel(r"2$\Gamma$ Difference")


mae_lifetime = mean_absolute_error(2 * spectral_gamma, spectral_2Gamma)


"""
Fetch binary thermal conductivity values
"""

kappa_InN_12 = Kappa(
    "/Users/rlg3/Documents/Jarvis/kappa/zincblende/InN/kappa-m121212.hdf5"
)

kappa_InN_16 = Kappa(
    "/Users/rlg3/Documents/Jarvis/kappa/zincblende/InN/kappa-m161616.hdf5"
)


kappa_InN_20 = Kappa(
    "/Users/rlg3/Documents/Jarvis/kappa/zincblende/InN/kappa-m202020.hdf5"
)
