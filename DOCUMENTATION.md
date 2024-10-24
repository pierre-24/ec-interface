# Documentation of the `ec-interface` package

1. [Purpose](#purpose)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Geometry manipulation tools](#useful-tools)
5. [Contribute](#contribute)
6. [Who?](#who)

## Purpose

The purpose of this package is to facilitate the computation of electrochemical (EC) interfaces with VASP.
In particular, it allows computing grand potential variation curves.

It is inspired by [this code](https://gitlab.com/icgm-d5/EC-Interfaces/) written by Arthur Hagopian and Jean-Sebastien Filhol and published with [10.1021/acs.jctc.1c01237](https://doi.org/10.1021/acs.jctc.1c01237).
The procedure is similar, with the following differences:

+ The number of electrons, charge added and charge removed are stored in a file, called `ec_interface.yml`.
+ To get more precision, the code looks into `vaspout.h5` for some results (number of electrons, free and fermi energies), so [it requires to compile VASP with `-DVASP_HDF5`](https://www.vasp.at/wiki/index.php/Makefile.include#HDF5_support_.28strongly_recommended.29).
+ The procedure to locate the reference potential is slightly different (this should not affect the results).
+ A way to plot the graph is not provided, but the `ec_results.csv` file will allow you to plot the results and make further analysis.

## Installation

To use this package, you need to have a running VASP version, compiled [with HDF5 support](https://www.vasp.at/wiki/index.php/Makefile.include#HDF5_support_.28strongly_recommended.29) (`-DVASP_HDF5`).
This code has been tested with VASP 6.3.2 and 6.4.1.
If you want to perform liquid phase calculations (either with the Poisson-Boltzmann or Homogeneous Background approaches), you also need to compile VASP with [VASPsol](https://github.com/henniggroup/VASPsol) (by following the instructions in their repository).

Finally, to install this package, you need a running Python 3 installation (Python >= 3.10 recommended), and

```bash
pip3 install git+https://github.com/pierre-24/ec-interface.git
```

Note: as this script install programs, you might need to add them (such as `$HOME/.local/bin`, if you use `--user`) to your `$PATH`.

## Usage

The following paragraph contains the standard way of getting a grand potential curve, with some tips and tricks along the way.

### 1. Prepare inputs

To perform an EC interface calculation, you need the following files in the same directory:

1. An `INCAR` file. In order to compute the information required for the EC calculation, it should at least contain the following instructions:
   ```
   LCHARG = .TRUE.
   LVHAR = .TRUE.
   LVTOT = .TRUE.
   ```
   
   In practice, the following parameters are a good starting point:
   ```
   !! convergence and precision both needs to be strict
   EDIFF = 1E-6
   PREC = Acurate
   !! parameters required for EC calculations:
   LCHARG = .TRUE.  ! Create CHGCAR
   LVHAR = .TRUE.   ! Create LOCPOT
   LVTOT = .TRUE.   ! Include VXC
   !! solvatation (optional)
   LSOL = .TRUE.    ! Enable solvatation with VASPsol
   EB_K = 80.0      ! dielectric constant of the solvent  
   TAU = 0.0        ! neglect cavitation energy
   NC_K = 1E-5      ! critical density parameter
   SIGMA_K = 0.6    ! Cavity shape parameter (default)
   LAMBDA_D_K = 1.5 ! for PBM, remove if HBM.
   ```
   Refer to [the VASP manual](https://www.vasp.at/wiki/index.php/The_VASP_Manual), [10.1021/acs.jctc.1c01237](https://doi.org/10.1021/acs.jctc.1c01237), and the [VASPsol](https://github.com/henniggroup/VASPsol/blob/master/docs/USAGE.md) documentation for more details on these parameters and their values.
   
   You might also want to increase the value of `NELM` (it may be more difficult to converge those calculations, especially with PCM), `NBANDS` (all bands might get parrtially occupied as you add electrons), and `LREAL` (as VASP is generally complaining).
2. A `POSCAR` file (which contains a slab geometry) and its corresponding `POTCAR` (that you can generate with `ei-create-potcar`, see below).
   [PAW potentials](https://www.vasp.at/wiki/index.php/Available_PAW_potentials) are strongly recommended.

   **It is assumed that the C lattice vector matches the Z axis.**
3. A `KPOINTS` file.
4. A `ec_interface.yml` file (see below).

You can get info about a slab by runnning `ei-check-slab`:
```bash
ei-check-slab POSCAR
```
Among others, the interslab distance (i.e., the vacuum between two repetition of the slab) should be adjusted (see [10.1021/acs.jctc.5b00170](https://dx.doi.org/10.1021/acs.jctc.5b00170)).
See [below](#geometry-manipulation-tools) for a tool to do so.
Note that there should be enough vacuum to get an accurate value for the reference (vacuum) potential, which is used to compute the work function.

You can generate the `POTCAR` file using `ei-create-potcar`:
````bash
ei-create-potcar POSCAR -p /path/to/potpaw/
````
where `/path/to/potpaw` is the directory containing [all PAW potentials](https://www.vasp.at/wiki/index.php/Available_PAW_potentials) (`H`, `H_AE`, etc).
If your `POSCAR` contains atoms for which you want to use an alternate potential, use `-P` with a comma separated list of `symbol=potential`, *e.g.*, `-P Li=Li_sv,C=C_h`.

You can get the number of electron that your system contains with `ei-get-nzc`:
```bash
ei-get-nzc POSCAR POTCAR
```

Then, create a `ec_interface.yml`.
You can start from the following:
```yaml
ne_zc: 21        # this is the number of electrons in your system
ne_added: 0.05   # number of electron (charge) to add
ne_removed: 0.05 # number of electron to remove
step: 0.01       # step for adding/removing electrons
additional: []   # (optional) additional points, if required
```

The value of `ne_zc` is the number of electrons that your system normally contains (zero charge).
Check, e.g., for `NELECT` in a preliminary VASP output, or the output of `ei-get-nzc`.

Adjust `step`: it should be ~10⁻⁴ e Å⁻², to be multiplied by (twice) the slab surface, as recommended in [10.1021/acs.jctc.5b00170](https://dx.doi.org/10.1021/acs.jctc.5b00170).
Then, pick a value for `ne_added` and `ne_removed`, which should be a multiple of `step`. 
Note that their values depend on the capacitance of your system... But they should not be large, since the corresponding change of potential should be within the acceptable range (see, e.g., [10.1088/1361-648X/ac0207](https://dx.doi.org/10.1088/1361-648X/ac0207) for more details).

Finally, you can create the inputs for the calculation using:
```bash
ei-make-directories
```
Note that by default, the `POSCAR`, `POTCAR` and `KPOINTS` files are referred to by using symlinks, as they should be the same for all calculations.
The parameters are read from `ec_interface.yml`. Additional options are:
+ `-v`: to get details about the creation of the different directories,
+ `-f`: force the re-creation of directories if existing, and
+ `-c`: copy file inside created directories, instead of using symlinks to do so.

### 2. Run VASP

Run VASP in each and every directory that was created in the previous step.
If you are curious, you will notice that the difference between directories is the value of `NELECT`, which sets the number of electrons in the calculation.

### 3. Extract the results

If every calculation went well, just run:
```bash
ei-extract-data
```
The parameters are read from `ec_interface.yml`.
Use the `-v` option to get details about extraction.

At the end of the procedure, a `ec_results.h5` file should be created, containing the different data (number of electrons, free and fermi energies, vacuum and average potentials) in binary form.

Furthermore, in each directory, you'll find a `charge_density_xy_avg.csv` and a `local_potential_xy_avg.csv` file, which contains a XY-average of the `CHGCAR` and `LOCPOT` file, respectively: the first column contains the Z coordinates, the second correspond to the XY-averaged value times unit volume, while the third contains the plain XY-averaged value.
Note that you can also use `ei-xy-average` to get the same information:

```bash
ei-xy-average CHGCAR > chg.csv
```

For `CHGCAR`, to count the electrons in certain regions, you can also use:

```bash
ei-charge-intg CHGCAR
```

This program will select regions (in the z-direction) of low and high electron occupations and integrate over those.
Option `-t` (threshold) allow to change the threshold for the detection of low/high regions.

### 4. Computing the free electrochemical energy (FEE)

Finally, run:
```bash
ei-compute-fee > results.csv
```
The parameters are read from `ec_interface.yml`, while the data are read from `ec_results.h5`.
Different options can be used to compute the FEE with different methods, see below.

At the end of the procedure, a `results.csv` file (containing tab-separated data) should be created, which contains the following dataset, with:
+ The number of electrons in the calculation (`NELECT` in `INCAR`);
+ The free energy (equal to `E0` in `OSZICAR`);
+ The vacuum potential (almost equal to the value of `FERMI_SHIFT` reported by VASPsol);
+ Fermi energy (equal to the value of `E-Fermi` in `OUTCAR`);
+ The average potential of the unit cell.

And then another dataset, with:
+ The charge added or removed to the system;
+ The (absolute) work function, as `vacuum_potential - fermi_energy`;
+ The relative potential versus reference, `work_function - ref` (`ref=4.5V` by default, your can change this value with `--ref`);
+ The corresponding grand potential value. By default, it is computed as `free_energy - dn * fermi_energy`.
  
  **Note:** this might not be the correct free electrochemical energy you are looking for, and other methods are available: see [this document](white_paper/potential.pdf) for more information (TL;DR: use either `--pbm` or `--hbm xxx`, where `xxx` is the fraction of active electrons).
  
  **Note:** the average potential should be about 0 at PZC. If it is not the case, you might want to use `--shift-avg` to set average to 0.

Please refer to [10.1039/c9cp06684e](https://doi.org/10.1021/10.1039/c9cp06684e) (and reference therein) for different information that you can extract from those data, such as the surface capacitances, the fukui functions, etc.

### 5. Example

See [this archive](https://drive.google.com/file/d/1TkLHsbzXJz_slb6X06r1NbkHko73-fin/view?usp=sharing), which contains an example of calculation on a Li (100) slab using the PBM approach, inspired by [10.1021/acs.jctc.1c01237](https://doi.org/10.1021/acs.jctc.1c01237).
It gives the following curve:

![](https://i.ibb.co/hW1DsHJ/work-function-vs-grand-potential.jpg)

A capacitance of 0.0535 e/V is extracted from this curve using its second derivative.
Due to the strong anharmonicity (the curve is clearly not symmetric around PZC), the actual value should be a little smaller.

## Useful tools

To manipulate the geometries, it is generally recommended to use tools such as [ASE](https://wiki.fysik.dtu.dk/ase/) or [pymatgen](https://pymatgen.org/) to manipulate the geometries.
However, `ec-interface` comes with a few handy (tough simple) tools to perform routine operations.
Use them with care!

+ To adjust the interslab distance, you can use `ei-set-vacuum`, which creates a new geometry while enforcing vacuum size (i.e., the size of the last lattice vector).
  For example, to adjust the vacuum size to 25 Å:
  ```bash
  mv POSCAR POSCAR_old
  ei-set-vacuum POSCAR_old -v 25.0 -o POSCAR
  ```
  The new geometry is saved in `POSCAR`. Note that the slab is z-centered by the procedure.
+ To turn an XYZ geometry into POSCAR, you can use `ei-to-vasp-geometry`:
  ```bash
  ei-to-vasp-geometry molecule.xyz --lattice=10,10,10 -o POSCAR
  ```
  It comes with a few options, such as `--lattice` to set the lattice vectors and `--sort` to group atoms types (so that it is easier to create the POTCAR).
+ To merge two POSCARs, you can use `ei-merge-poscar`:
  ```bash
  ei-to-vasp-geometry POSCAR_cell POSCAR_substrate --shift=5,5,7 -o POSCAR
  ```
  It allows to merge two geometries. 
  The lattice of the first geometry (here `POSCAR_cell`) is used in the final one.
  The `--shift` option allows to reposition the second molecule in the first.
  Note that `Selective dynamics` information are kept.

Furthermore, since the idea is to compute the properties for different number of electrons, an insightful byproduct are the [Fukui functions](https://en.wikipedia.org/wiki/Fukui_function).
In particular, $f(r) = \rho_{N+\Delta N}(r)-\rho_n(r)$, which can be computed from [`CHGCAR`](https://www.vasp.at/wiki/index.php/CHGCAR) files with:

```bash
ei-fukui EC_20.000/CHGCAR EC_20.050/CHGCAR -d 0.05 -o CHGCAR_fukui
```

where the `-d` argument gives the value of $\Delta N$, the first `CHGCAR` is the reference density ( $\rho_N(r)$ ), and the second is the one with an additional amount of electrons ( $\rho_{N+\Delta N}(r)$ ).
If the `-s` option is used, a [symmetric difference formula](https://en.wikipedia.org/wiki/Numerical_differentiation) is used, and the first file must then contain $\rho_{N-\Delta N}(r)$.
In both case, the resulting `CHGCAR_fukui` file contains the Fukui function for $\rho_N(r)$. 
It might be visualized with, *e.g.*, the [VESTA](https://jp-minerals.org/vesta/en/) software.

## Contribute

Contributions, either with [issues](https://github.com/pierre-24/ec-interface/issues) or [pull requests](https://github.com/pierre-24/ec-interface/pulls) are welcomed.

### Install

If you want to contribute, this is the usual deal: 
start by [forking](https://guides.github.com/activities/forking/), then clone your fork and use the following install procedures instead.

```bash
cd ec-interface

# definitely recommended in this case: use a virtualenv!
python -m venv virtualenv
source venv/bin/activate

# install also dev dependencies
make install
```

### Tips to contribute

+ A good place to start is the [list of issues](https://github.com/pierre-24/ec-interface/issues).
  In fact, it is easier if you start by filling an issue, and if you want to work on it, says so there, so that everyone knows that the issue is handled.

+ Don't forget to work on a separate branch.
  Since this project follows the [git flow](http://nvie.com/posts/a-successful-git-branching-model/), you should base your branch on `main`, not work in it directly:

    ```bash
    git checkout -b new_branch origin/main
    ```
 
+ Don't forget to regularly run the linting and tests:

    ```bash
    make lint
    make test
    ```
    
    Indeed, the code follows the [PEP-8 style recommendations](http://legacy.python.org/dev/peps/pep-0008/), checked by [`flake8`](https://flake8.pycqa.org/en/latest/).
    Having an extensive test suite is also a good idea to prevent regressions.

+ Pull requests should be unitary, and include unit test(s) and documentation if needed. 
  The test suite and lint must succeed for the merge request to be accepted.


## Who?

My name is [Pierre Beaujean](https://pierrebeaujean.net), and I have a Ph.D. in quantum chemistry from the [University of Namur](https://unamur.be) (Belgium).
I'm the main (and only) developer of this project, used in our lab.
I use VASP in the frame of my post-doctoral research in order to study batteries and solid electrolyte interphrase, and I developed this project to ease my life.
