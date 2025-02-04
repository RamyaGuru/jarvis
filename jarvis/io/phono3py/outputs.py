#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 15 21:34:38 2021

@author: rlg3

Module for post-processing phono3py output
kappa-mxxx.hdf, jdos-mxxx-gy-tz.hdf, phono3py_disp.yaml


Notes for inputs.py:
    tags : generate automatically from the inputs.py. Include info about
    isotope scattering, boundary scattering, etc.

Think I should initialize a Phonopy object to run these.
    
Might need a mesh_dict from phonon.get_mesh_dict() so that I have the phonon
bandstructure properties

Add function for mode gruneisen from third order force constants
"""

import h5py
from jarvis.core.specie import Specie
from jarvis.io.phonopy.outputs import (
    total_dos,
    get_Phonopy_obj,
    get_spectral_heat_capacity,
)
import numpy as np
import spglib
import matplotlib.pyplot as plt

from phonopy.harmonic.force_constants import similarity_transformation
from phono3py.phonon.grid import BZGrid, get_grid_points_by_rotations


"""
Constants 
"""
kB = 1.38064852e-23
hbar = 1.0545718e-34
Na = 6.0221409e23
kappa_unit_conversion = 6.358245562444196


def gruneisen_approximation(vt, vl):
    x = vt / vl
    return (3 / 2) * (3 - 4 * x ** 2) / (1 + 2 * x ** 2)


class Kappa:
    def __init__(
        self,
        filename="",
        mesh=None,
        total_dos_dat="",
        temperatures=None,
        kappa_format="scalar_xx",  # need this?
        composition=None,
        tags=None,
    ):
        """

        Parameters
        ----------
        filename : string,required
            Name of kappa-mxxxx.hdf file. The default is "".
        temperatures : list, optional
            List of temperatures to use for post-processing. Default is None.
            If None, uses all temperatures computed in thermal
            conductivity run.
        kappa_format : string, optional
            Desired kappa output format. The default is 'scalar_xx'.
            Other choices : "tensor" or ...
        composition : Composition object of jarvis.core.composition, optional
            Composition object for material used in property calculation.
            The default is None.
        tags : string, optional
        Descriptors of thermal conductivity calculation. The default is None.
        """
        f = h5py.File(filename, "r")
        self.dict = dict(f)
        if temperatures:
            self.temperatures = temperatures
        else:
            self.temperatures = list(self.dict["temperature"])
        self.composition = composition
        self.tags = tags
        self.n_qpoint = np.shape(f["qpoint"])[0]
        self.total_dos = total_dos_dat
        self.kappa_format = kappa_format

    def to_dict(self):
        return self.dict

    def kappa(self, T):
        if T not in self.temperatures:
            raise Exception("Kappa not evaluated at this temperature.")
        T_indx = self.temperatures.index(T)
        if self.kappa_format == "tensor":
            return self.dict["kappa"][T_indx]
        if self.kappa_format == "scalar_xx":
            return self.dict["kappa"][T_indx][0]


class JDOS:
    def __init__(self, phonopy_obj, directory, mesh=[1, 1, 1], temperature=None):
        """
        Parameters
        ----------
        directory : string, required
            DESCRIPTION. The default is "".
        qpoints : TYPE, optional
            DESCRIPTION. The default is None.
        temperature : integer, optional
        Temperature for a weighted JDOS calculation. The default is None. When
        None, unweighted JDOS is computed.

        """
        self.mesh = mesh
        self.temperature = temperature
        self.directory = directory
        self.phonopy_obj = phonopy_obj
        self.phonopy_obj.run_mesh(mesh, with_group_velocities=True)
        self.phonopy_obj.run_total_dos(use_tetrahedron_method=True)
        self.mesh_dict = phonopy_obj.get_mesh_dict()

    def select_jdos(self):
        """
        Post-processing script to select JDOS values corresponding to 
        actual phonon modes.

        """

        def get_gridpts(self):
            """
            Generates list of gridpoint indices for JDOS calculation
            """
            latt_vecs = self.phonopy_obj.get_primitive().get_cell()
            positions = self.phonopy_obj.get_primitive().get_scaled_positions()
            atom_type = self.phonopy_obj.get_primitive().get_atomic_numbers()
            cell = (latt_vecs, positions, atom_type)
            mapping, grid = spglib.get_ir_reciprocal_mesh(
                self.mesh, cell, is_shift=[0, 0, 0]
            )
            return mapping

        gridpt_list = get_gridpts(self)
        gridpt_uids = np.unique(gridpt_list)

        """
        Dictionary stores JDOS spectrum for each irreducible q-point
        key : irreducible grid point index
        value : JDOS spectrum [frequency, N1 process, N2 process]
        """
        jdos_ir = np.zeros([len(gridpt_uids), len(self.mesh_dict["frequencies"][0])])

        for g, gp in enumerate(gridpt_uids):
            if self.temperature is not None:
                file = (
                    self.directory
                    + "jdos-m"
                    + "".join(str(m) for m in self.mesh)
                    + "-g"
                    + str(gp)
                    + "-t"
                    + str(self.temperature)
                    + ".dat"
                )
            else:
                file = (
                    self.directory
                    + "jdos-m"
                    + "".join(str(m) for m in self.mesh)
                    + "-g"
                    + str(gp)
                    + ".dat"
                )
            data = np.genfromtxt(file, dtype="float")
            freq = data[:, 0]
            N2 = data[:, 1] + data[:, 2]
            indices = np.digitize(
                self.mesh_dict["frequencies"][g], freq
            )  # select freqeuncy bin of branch frequency
            # JDOS values for each irreducible q-point
            jdos_ir[g] = np.array(
                [(N2[i] + N2[i - 1]) / 2 for i in indices]
            )  # average the ceiling and floor of the bin
        return jdos_ir

    def get_gv_outer_product(self, mesh=[1, 1, 1]):
        """
        Returns 3x3 vg X vg matrix for each irreducible q-point
        Inspired by the get_gv_by_gv method in Conductivity class of phono3py
    
        Parameters
        ----------
        phonon_obj : TYPE
            DESCRIPTION.
    
        Returns
        -------
        None.
    
        NEED TO WORK ON THIS METHOD
        """
        phonon_obj = self.phonopy_obj
        phonon_obj.run_mesh(mesh, with_group_velocities=True)
        mesh_dict = phonon_obj.get_mesh_dict()
        gv_obj = phonon_obj._group_velocity
        nbranches = np.shape(mesh_dict["group_velocities"])[1]
        gv_by_gv = np.zeros((len(mesh_dict["qpoints"]), nbranches, 3, 3))
        gv_sum2 = np.zeros((len(mesh_dict["qpoints"]), nbranches, 6))

        for qindx in range(len(mesh_dict["qpoints"])):
            rec_lat = gv_obj._reciprocal_lattice
            rotations_cartesian = np.array(
                [
                    similarity_transformation(rec_lat, r)
                    for r in gv_obj._symmetry._pointgroup_operations
                ],
                dtype="double",
                order="C",
            )
            gv = gv_obj.group_velocities[qindx]

            for r in rotations_cartesian:
                gv_rot = np.dot(gv, r.T)
                gv_by_gv[qindx] += [np.outer(r_gv, r_gv) for r_gv in gv_rot]
                bzgrid = BZGrid(
                    phonon_obj.mesh._mesh,
                    gv_obj._reciprocal_lattice,
                    phonon_obj._primitive.cell,
                )
            rotation_map = get_grid_points_by_rotations(
                phonon_obj._mesh.ir_grid_points[qindx], bzgrid,
            )
            # Need to decide if this makes sense
            gv_by_gv[qindx] /= len(rotation_map) // len(np.unique(rotation_map))
            gv_by_gv[qindx] /= nbranches  # Still doesn't seem required to have this
            for j, vxv in enumerate(([0, 0], [1, 1], [2, 2], [1, 2], [0, 2], [0, 1])):
                gv_sum2[qindx, :, j] = gv_by_gv[qindx, :, vxv[0], vxv[1]]
        return gv_sum2

    # For spectral quantities that need to be scaled by DOS: kappa, Cp
    def mode_to_spectral_wtd(self, mode_prop):
        """
        Converts modal to spectral properties. Properties are weighted by
        the phonon density-of-states. DOS-weighting is required for heat capacity.
        """
        self.phonopy_obj.run_total_dos()
        # Get tetrahedron mesh object
        thm = self.phonopy_obj._total_dos._tetrahedron_mesh
        thm.set(
            value="I", frequency_points=self.phonopy_obj._total_dos._frequency_points
        )
        spectral_prop = np.zeros_like(self.phonopy_obj._total_dos._frequency_points)
        for i, iw in enumerate(thm):
            spectral_prop += np.sum(
                iw * mode_prop[i] * self.phonopy_obj._total_dos._weights[i], axis=1
            )
        return spectral_prop

    def mode_to_spectral_unwtd(self, mode_prop):
        """
        Converts modal to spectral properties without using the weights for
        k-point degeneracy. Required for conversion of mode_kappa.
        """
        self.phonopy_obj.run_total_dos()
        # Get tetrahedron mesh object
        thm = self.phonopy_obj._total_dos._tetrahedron_mesh
        thm.set(
            value="I", frequency_points=self.phonopy_obj._total_dos._frequency_points
        )
        spectral_prop = np.zeros_like(self.phonopy_obj._total_dos._frequency_points)
        for i, iw in enumerate(thm):
            spectral_prop += np.sum(iw * mode_prop[i], axis=1)
        return spectral_prop

    #    For spectral quantities that do not need to be scaled by DOS: gamma, vg
    def mode_to_spectral(self, mode_prop):
        """
        Converts modal to spectral quanitites. These quantities are NOT scaled
        by the phonon DOS and must be normalized by the phonon DOS.
        """
        spectral_wtd = self.mode_to_spectral_wtd(mode_prop)
        dos = self.mode_to_spectral_wtd(np.ones_like(mode_prop))
        return spectral_wtd / dos

    # Weighted JDOS should work? Maybe write separate method?
    def linewidth_from_jdos(
        self, spectral_jdos, atoms, vs, grun=0.8, T=300, plot=False
    ):
        """
        Calculate the phonon linewidth using semi-empirical expression that
        utilizes the joint density-of-states.

        Parameters
        ----------
        spectral_jdos : TYPE
           Currently only takes unweighted jdos values.
        atoms : Atoms
        vs : float
            Sound velocity. (Group velocity may be more accurate?)
        gamma : float, optional
            Gruneisen parameter. The default is 0.8
        T : float, optional
            Temperature. The default is 300.

        """
        prefactor = np.pi * kB * T / 6 / 3  # Added the factor of 3!!
        freq_pts = self.phonopy_obj._total_dos._frequency_points
        species = [Specie(i) for i in atoms.elements]
        N = len(species)
        avgM = sum([species[j].atomic_mass / Na / 1e3 for j in range(N)]) / N
        spectral_2Gamma = (
            prefactor * (grun ** 2 / (avgM * vs ** 2)) * freq_pts ** 2 * spectral_jdos
        )
        if plot:
            plt.figure()
            plt.plot(freq_pts, spectral_2Gamma)
            plt.xlabel("Frequency (THz)")
            plt.ylabel(r"2$\Gamma$ (THz)")
        return spectral_2Gamma

    def kappa_from_linewidth(self, spectral_2Gamma, component="xx", T=300, plot=False):
        """
        Currently only works for scalar_xx kappa format
        """
        ij_dict = {"xx": 0, "yy": 1, "zz": 2, "yz": 3, "xz": 4, "xy": 5}
        freq_pts = self.phonopy_obj._total_dos._frequency_points
        find_zeros = np.argwhere(np.isnan(spectral_2Gamma))
        # freq_pts = np.delete(freq_pts, find_zeros)

        mode_vg2 = self.get_gv_outer_product(self.mesh)
        mode_vg2_ij = mode_vg2[:, :, ij_dict[component]]
        spectral_vg2 = self.mode_to_spectral(mode_vg2_ij)
        spectral_Cp = get_spectral_heat_capacity(
            self.phonopy_obj, self.mesh, T, weighted=False, plot=True
        )
        # spectral_2Gamma = np.delete(spectral_2Gamma, find_zeros)
        # spectral_vg2_red = np.delete(spectral_vg2, find_zeros)
        # spectral_Cp = np.delete(spectral_Cp, find_zeros)
        # print(spectral_Cp)
        # print(spectral_2Gamma)
        # print(spectral_vg2)
        spectral_kappa = (
            kappa_unit_conversion * spectral_vg2 * (1 / spectral_2Gamma) * spectral_Cp
        )
        print(spectral_kappa)
        #        red_freq_pts = np.delete(freq_pts, find_zeros)
        if plot:
            # Kappa
            plt.figure()
            plt.plot(freq_pts, spectral_kappa)
            plt.xlabel("Frequency (THz)")
            plt.ylabel(r"$\kappa$ (W/m$\cdot$K$\cdot$THz)")
            # Squared Group Velocity
            plt.figure()
            plt.plot(freq_pts, spectral_vg2)
            plt.scatter(self.mesh_dict["frequencies"], mode_vg2_ij, s=2)
            plt.xlabel("Frequency (THz)")
            plt.ylabel(r"v$^2$ (THz$^2\cdot\AA^2$)")
        return spectral_kappa


if __name__ == "__main__":
    kappa_Si = Kappa(
        "Si-testing/kappa-m111111.hdf5",
        total_dos_dat="../phonopy/Si-testing/total_dos.dat",
    )
    RT_kappa = kappa_Si.kappa(300.0)
    from jarvis.core.atoms import Atoms

    test_dir = "Si-testing/phono3py-example-Si-PBEsol/"
    pos = test_dir + "POSCAR-unitcell"
    atoms = Atoms.from_poscar(pos)
    phonon_obj = get_Phonopy_obj(
        atoms,
        phonopy_yaml=test_dir + "phono3py.yaml",
        FC_file=test_dir + "fc2.hdf5",
        scell=np.array([[2, 0, 0], [0, 2, 0], [0, 0, 2]]),
    )
    jdos_dir = "Si-testing/unweighted_jdos/"
    jdos = JDOS(phonon_obj, directory=jdos_dir, mesh=[11, 11, 11])
    jdos_ir = jdos.select_jdos()
    spectral_jdos = jdos.mode_to_spectral(jdos_ir)

    spectral_2Gamma = jdos.linewidth_from_jdos(spectral_jdos, atoms, vs=6084, plot=True)
    spectral_kappa = jdos.kappa_from_linewidth(spectral_2Gamma, plot=True)
