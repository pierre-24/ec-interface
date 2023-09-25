# Documentation of the `ec-interface` package

1. [Purpose](#purpose)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Contribute](#contribute)
5. [Who?](#who)

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
   
   You might also want to increase the value of `NELM` (it may be more difficult to converge those calculations, especially with PCM) and `NBANDS` (all bands might get occupied as you add electrons).
2. A `POSCAR` file (which contains a slab geometry) and its corresponding `POTCAR`.
   [PAW potentials](https://www.vasp.at/wiki/index.php/Available_PAW_potentials) are strongly recommended.
3. A `KPOINTS` file.
4. A `ec_interface.yml` file (see below).

To adjust the inter-slab distance, you can use `ei-set-vacuum`, which creates a new geometry while enforcing vacuum size (i.e., the size of the last lattice vector).
For example, to adjust the vacuum size to 25 Å:
```bash
mv INCAR INCAR_old
ei-set-vacuum INCAR_old -v 25.0 -o INCAR
```
The new geometry is saved in `INCAR`.
There should be enough vacuum to get an accurate value for the reference (vacuum) potential, which is used to compute the work function.
Note that the slab is z-centered by the procedure.

Then, create a `ec_interface.yml`.
You can start from the following:
```yaml
ne_zc: 21        # this is the number of electrons in your system
ne_added: 0.05   # number of electron (charge) to add
ne_removed: 0.05 # number of electron to remove
step: 0.01       # step for adding/removing electrons
```

The value of `ne_zc` is the number of electrons that your system normally contains (zero charge).
Check, e.g., for `NELECT` in a preliminary VASP output.

Adjust `step`: it should be of ~10⁻⁴ e Å⁻², to be multiplied by twice the slab surface, as recommended in [10.1021/acs.jctc.5b00170](https://dx.doi.org/10.1021/acs.jctc.5b00170).
Then, pick a value for `ne_added` and `ne_removed`, which should be a multiple of `step`. 
Note that their values depend on the capacitance of your system... But they should not be large, since the corresponding change of potential should be within the acceptable range (see, e.g., [10.1088/1361-648X/ac0207](https://dx.doi.org/10.1088/1361-648X/ac0207) for more details).

Finally, you can create the inputs for the calculation using:
```bash
ei-make-directories
```
The parameters are read from `ec_interface.yml`.
Use the `-v` option to get details about the creation of the different directories.

Note that by default, the `POSCAR`, `POTCAR` and `KPOINTS` files are referred to by using symlinks, as they should be the same for all calculations.
If you prefer that those files are copied, use `-c`.

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

At the end of the procedure, a `ec_results.csv` file should be created, which contains the following columns:
+ The charge added or removed to the system;
+ The free energy (equal to `E0` in `OSZICAR`);
+ Fermi energy (equal to the value of `E-Fermi` in `OUTCAR`);
+ The reference potential (almost equal to the value of `FERMI_SHIFT` reported by VASPsol);
+ The (absolute) work function corresponding to the amount of charge added/removed (you might want to shift those value w.r.t. a reference such as the SHE);
+ The corresponding grand potential value.

Please refer to [10.1021/acs.jctc.1c01237](https://doi.org/10.1021/acs.jctc.1c01237) (and reference therein) for different information that you can extract from those data, such as the capacitance, etc.

### 4. Example

See [this archive](https://drive.google.com/file/d/1TkLHsbzXJz_slb6X06r1NbkHko73-fin/view?usp=drive_link), which contains an example of calculation on a Li (100) slab using the PBM approach, inspired by [10.1021/acs.jctc.1c01237](https://doi.org/10.1021/acs.jctc.1c01237).
It gives the following curve:

![](https://i.ibb.co/PCmfBGh/work-function-vs-grand-potential.jpg)

A capacitance of 0.0535 e/V is extracted from this curve using its second derivative.
Due to the strong anharmonicity (the curve is clearly not symmetric around PZC), the actual value should be a little smaller.

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