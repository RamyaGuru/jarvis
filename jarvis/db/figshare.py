"""
Downloads files from Figshare.

Main page: https://figshare.com/authors/Kamal_Choudhary/4445539
"""

import zipfile
import tempfile
import os
import numpy as np
import io
import json
import requests
from jarvis.db.jsonutils import loadjson
from jarvis.io.vasp.outputs import Vasprun
from jarvis.io.vasp.inputs import Poscar
from jarvis.io.wannier.outputs import WannierHam


def datasets(dataset=""):
    """Get collection of dataset names and URLs."""
    if dataset == "dft_2d":
        # Ref: https://www.nature.com/articles/s41524-020-00440-1
        url = "https://ndownloader.figshare.com/files/22471019"
        js_tag = "jdft_2d-4-26-2020.json"
        print("Obtaining 2D dataset ...")
    elif dataset == "dft_3d":
        # Ref: https://www.nature.com/articles/s41524-020-00440-1
        url = "https://ndownloader.figshare.com/files/22471022"
        js_tag = "jdft_3d-4-26-2020.json"
        print("Obtaining 3D dataset ...")
    elif dataset == "stm_2d":
        # Ref: https://www.nature.com/articles/s41597-021-00824-y
        link_1 = "https://ndownloader.figshare.com/files/21884952"
        r_jpg = requests.get(link_1)
        z = zipfile.ZipFile(io.BytesIO(r_jpg.content))
        link_2 = "https://ndownloader.figshare.com/files/21893379"
        r_json = requests.get(link_2).content
        latts = json.loads(r_json)
        namelist = z.namelist()
        pos_bias = []
        neg_bias = []

        for i in namelist:
            values = mpimg.imread(io.BytesIO((img_str)), format="jpg")
            # img=Image(values=values)
            jid = i.split("/")[-1].split("_")[0]
            bias = i.split("/")[-1].split("_")[1].split(".jpg")[0]
            lat_system = latts[jid]
            if bias == "pos":
                info = {}
                info["jid"] = jid
                info["image_values"] = values
                info["lat_type"] = lat_system
                pos_bias.append(info)
            if bias == "nef":
                info = {}
                info["jid"] = jid
                info["image_values"] = values
                info["lat_type"] = lat_system
                neg_bias.append(info)
            return pos_bias, neg_bias

        print("Obtaining 2D STM dataset ...")
    elif dataset == "cfid_3d":
        # Ref: https://doi.org/10.1103/PhysRevMaterials.2.083801
        url = "https://ndownloader.figshare.com/files/22470818"
        js_tag = "jml_3d-4-26-2020.json"
        print("Obtaining JARVIS-3D CFID dataset 37k...")
    elif dataset == "mp_3d":
        # Ref: https://doi.org/10.1063/1.4812323
        url = "https://ndownloader.figshare.com/files/24979850"
        js_tag = "CFID_mp_desc_data_84k.json"
        print("Obtaining Materials Project-3D CFID dataset 84k...")
    elif dataset == "mp_3d_2020":
        # Ref: https://doi.org/10.1063/1.4812323
        url = "https://ndownloader.figshare.com/files/26791259"
        js_tag = "all_mp.json"
        print("Obtaining Materials Project-3D CFID dataset 127k...")
    elif dataset == "megnet":
        # Ref: https://doi.org/10.1021/acs.chemmater.9b01294
        url = "https://ndownloader.figshare.com/files/26724977"
        js_tag = "megnet.json"
        print("Obtaining MEGNET-3D CFID dataset 69k...")
    elif dataset == "oqmd_3d":
        # Ref: https://www.nature.com/articles/npjcompumats201510
        url = "https://ndownloader.figshare.com/files/24981170"
        js_tag = "CFID_OQMD_460k.json"
        print("Obtaining OQMD-3D CFID dataset 460k...")
    elif dataset == "oqmd_3d_no_cfid":
        # Ref: https://www.nature.com/articles/npjcompumats201510
        url = "https://ndownloader.figshare.com/files/26790182"
        js_tag = "all_oqmd.json"
        print("Obtaining OQMD-3D  dataset 800k...")
    elif dataset == "twod_matpd":
        # Ref: https://www.nature.com/articles/s41597-019-0097-3
        url = "https://ndownloader.figshare.com/files/26789006"
        js_tag = "twodmatpd.json"
        print("Obtaining 2DMatPedia dataset 6k...")
    elif dataset == "qm9":
        # Ref: https://www.nature.com/articles/sdata201422
        url = "https://ndownloader.figshare.com/files/25159592"
        js_tag = "qm9_data_cfid.json"
        print("Obtaining QM9-molecule CFID dataset 134k...")
    elif dataset == "aflow1":
        # Ref: https://doi.org/10.1016/j.commatsci.2012.02.005
        url = "https://ndownloader.figshare.com/files/25453256"
        js_tag = "CFID_AFLOW1.json"
        print("Obtaining AFLOW-1 CFID dataset 400k...")
    elif dataset == "aflow2":
        # Ref: https://doi.org/10.1016/j.commatsci.2012.02.005
        url = "https://ndownloader.figshare.com/files/25453265"
        js_tag = "CFID_AFLOW2.json"
        print("Obtaining AFLOW-2 CFID dataset 400k...")
    elif dataset == "arXiv":
        # Ref: https://www.kaggle.com/Cornell-University/arxiv
        url = "https://ndownloader.figshare.com/files/26804795"
        js_tag = "arXivdataset.json"
        print("Obtaining arXiv dataset...")
    elif dataset == "cord19":
        # Ref:https://github.com/usnistgov/cord19-cdcs-nist
        url = "https://ndownloader.figshare.com/files/26804798"
        js_tag = "cord19.json"
        print("Obtaining CORD19 dataset...")
    elif dataset == "raw_files":
        # Ref: https://www.nature.com/articles/s41524-020-00440-1
        url = "https://ndownloader.figshare.com/files/25295732"
        js_tag = "figshare_data-10-28-2020.json"
        print("Obtaining raw io files...")
    else:
        ValueError("Dataset doesnt exist", dataset)
    return url, js_tag


def data(dataset="dft_2d"):
    """Provide main function to download datasets."""
    url, js_tag = datasets(dataset)
    # r = requests.get(url)
    # z = zipfile.ZipFile(io.BytesIO(r.content))
    # data = json.loads(z.read(js_tag).decode("utf-8"))

    # r = requests.get(url)
    # z = zipfile.ZipFile(io.BytesIO(r.content))
    # wdat = z.read(js_tag).decode("utf-8")
    # fd, path = tempfile.mkstemp()
    # with os.fdopen(fd, "w") as tmp:
    #    tmp.write(wdat)
    # data = loadjson(path)

    path = str(os.path.join(os.path.dirname(__file__), js_tag))
    if not os.path.isfile(path):
        zfile = str(os.path.join(os.path.dirname(__file__), "tmp.zip"))
        r = requests.get(url)
        f = open(zfile, "wb")
        f.write(r.content)
        f.close()

        with zipfile.ZipFile(zfile, "r") as zipObj:
            # zipObj.extract(path)
            zipObj.extractall(os.path.join(os.path.dirname(__file__)))
        os.remove(zfile)
    data = loadjson(path)
    return data


def get_jid_data(jid="JVASP-667", dataset="dft_2d"):
    """Get info for a jid and dataset."""
    d = data(dataset)
    for i in d:
        if i["jid"] == jid:
            return i


def get_ff_eneleast():
    """Get JARVIS-FF related data."""
    jff1 = str(os.path.join(os.path.dirname(__file__), "jff1.json"))
    if not os.path.isfile(jff1):
        r = requests.get("https://ndownloader.figshare.com/files/10307139")
        f = open(jff1, "wb")
        f.write(r.content)
        f.close()
    data_ff1 = loadjson(jff1)
    return data_ff1


# Raw I/O files on figshare repository
fls = data("raw_files")


def get_wann_electron(jid="JVASP-816"):
    """Download electron WTBH if available."""
    w = ""
    ef = ""
    for i in fls["WANN"]:
        if i["name"].split(".zip")[0] == jid:
            r = requests.get(i["download_url"])
            z = zipfile.ZipFile(io.BytesIO(r.content))
            wdat = z.read("wannier90_hr.dat").decode("utf-8")
            js_file = jid + ".json"
            js = z.read(js_file).decode("utf-8")
            fd, path = tempfile.mkstemp()
            with os.fdopen(fd, "w") as tmp:
                tmp.write(wdat)
            w = WannierHam(path)
            fd, path = tempfile.mkstemp()
            with os.fdopen(fd, "w") as tmp:
                tmp.write(js)
            d = loadjson(path)
            ef = d["info_mesh"]["efermi"]
            fd, path = tempfile.mkstemp()
            pos = z.read("POSCAR").decode("utf-8")
            with os.fdopen(fd, "w") as tmp:
                tmp.write(pos)
            atoms = Poscar.from_file(path).atoms
    return w, ef, atoms


def get_wann_phonon(jid="JVASP-1002", factor=15.633302):
    """Download phonon WTBH if available."""
    # Requires phonopy
    from jarvis.io.phonopy.outputs import get_phonon_tb

    for i in fls["FD-ELAST"]:
        if isinstance(i, dict):
            if i["name"].split(".zip")[0] == jid:
                r = requests.get(i["download_url"])
                z = zipfile.ZipFile(io.BytesIO(r.content))
                vrun_path = z.read("vasprun.xml").decode("utf-8")
                fd, path = tempfile.mkstemp()
                with os.fdopen(fd, "w") as tmp:
                    tmp.write(vrun_path)
                vrun = Vasprun(path)
                fc = vrun.phonon_data()["force_constants"]
                atoms = vrun.all_structures[0]
                # print(atoms)
                # atoms = Atoms.from_poscar(pos)
                # print(atoms)
                fd, path = tempfile.mkstemp()
                get_phonon_tb(fc=fc, atoms=atoms, out_file=path, factor=factor)
                # cvn = Spacegroup3D(atoms).conventional_standard_structure
                w = WannierHam(path)
                return w, atoms


def get_hk_tb(k=np.array([0, 0, 0]), w=[]):
    """Get Wannier TB Hamiltonian."""
    nr = w.R.shape[0]
    hk = np.zeros((w.nwan, w.nwan), dtype=complex)
    kmat = np.tile(k, (nr, 1))
    exp_ikr = np.exp(1.0j * 2 * np.pi * np.sum(kmat * w.R, 1))
    temp = np.zeros(w.nwan ** 2, dtype=complex)
    for i in range(nr):
        temp += exp_ikr[i] * w.HR[i, :]
    hk = np.reshape(temp, (w.nwan, w.nwan))
    hk = (hk + hk.T.conj()) / 2.0
    return hk


"""
if __name__ == "__main__":

    data_2d = data(dataset='dft_2d')
    print('2d',len(data_2d))
    data_3d = data(dataset='dft_3d')
    print('3d',len(data_3d))
    data_ml = data(dataset='cfid_3d')
    print('cfid3d',len(data_ml))
    data_ff = get_ff_eneleast()
    print ('ff',len(data_ff))
"""
