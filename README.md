# CMS-Combine tutorial

<div align="center">

![WIP](https://img.shields.io/badge/Warning-Work_in_Progress-FF3000?style=for-the-badge&logo=git&logoColor=white&labelColor=333333)

</div>

![ROOT](https://img.shields.io/badge/ROOT-6.36-yellow) ![Python](https://img.shields.io/badge/Python-3.10.18-3776AB?logo=python&logoColor=white) ![Boost](https://img.shields.io/badge/Boost-1.91.0-FF9900?logo=c%2B%2B&logoColor=white) ![Eigen](https://img.shields.io/badge/Eigen-5.0.1-E34326) ![VDT](https://img.shields.io/badge/VDT-0.4.6-7A7A7A)

The CMS-Combine tool is a robust software package based on [RooStats](https://twiki.cern.ch/twiki/bin/view/RooStats/WebHome) and [RooFit](https://root.cern/manual/roofit/), utilized extensively for statistical analysis. Originally developed within the Higgs Physics Analysis Group (PAG), its usage has since become widespread across the CMS collaboration. Typically, Combine is executed within the CMSSW framework. 

This repository provides a workflow to build and run Combine **locally**. All dependencies in this guide are compiled using `cmake`/`make` and installed directly into your home directory (`$HOME`). This avoids the need for `sudo` access, making the setup fully compatible with high-performance clusters where you may lack root or administrator privileges.

🔗 Official Documentation: [HiggsAnalysis-CombinedLimit](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/)

## 📚 Tutorial structure

This repository is structured into progressively complex levels, mimicking the actual workflow of developing a CMS analysis. The tutorials progress from basic counting experiments to multi-region shape-based analyses with nuisance parameters. Each level is contained within its own directory. Each directory contains a dedicated README file detailing the concepts, along with the necessary datacards, ROOT files, and executable run scripts.

- **[level1_GettingStarted](./level1_GettingStarted):** Introduces the basic structure of a CMS Combine datacard. Starting from a simple counting experiment, it gradually adds multiple backgrounds, multiple signal regions, and automatic MC statistical uncertainties, while demonstrating the most commonly used Combine commands.

![More to be added](https://img.shields.io/badge/More%20to%20be%20added-yellow?style=for-the-badge)

To get the most out of these tutorials, I recommend progressing through the directories in numerical order. 

1. 📂 **Navigate** to the specific directory.
2. 📖 **Read** the local `README.md` file for the step-by-step instructions and theoretical context for that level.
3. 🔍 **Inspect** the provided `datacard.txt` and any associated `.root` files to understand their structure.
4. ⚙️ **Execute** the provided scripts to run the Combine commands locally and analyze the output limits and significance.

## 🛠️Setting up Combine locally

### Get the dependencies first!

Before building Combine itself, you need to install its dependencies. We will install everything into a local directory (e.g., `$HOME/local`) to maintain an isolated, user-level environment.

- **ROOT** <br>
I highly recommend staying in the exact same environment where ROOT is built to avoid system path and Python-related conflicts. Pick a Conda environment and install ROOT using the following guides:
	- [Installing Miniconda](https://phazarik.github.io/pages/tools-for-noobs.html#setting-up-miniconda) [this ensures Python path compatibility]
	- [Building ROOT](https://phazarik.github.io/pages/tools-for-noobs.html#setting-up-root) [Can be installed in the `base` environment]
	> **⚠️ Important:** Installing Combine requires ROOT's MathMore library. For this, ROOT needs to be built using the `-Dmathmore=ON` option. If you alredy have ROOT, you can check whether this library by doing the following.
	```bash
	root-config --features
	ls $HOME/root_install/lib/libMathMore*
	```
	> If you can't find the MathMore library, rebuild ROOT like this.
	```bash
	cd $HOME/root_build
	cmake $HOME/root_src -DCMAKE_INSTALL_PREFIX=$HOME/root_install -Dmathmore=ON
	make -j8 ## Use all available CPUs for speed
	make install
	```
- **Boost**  <br>
Combine uses the Boost library for parsing command-line options. Download the latest .tar.gz source from the Boost release page ([https://www.boost.org/releases/latest/](https://www.boost.org/releases/latest/)). Move it to your home area, extract it, and build using the following commands. It takes a couple of minutes.
	```bash
	tar -xzvf boost_1_91_0.tar.gz
	cd boost_1_91_0/
	bash bootstrap.sh                 # creates a binary named b2
	./b2 install --prefix=$HOME/local # installs in home area
	```
	
- **Eigen**  <br>
Used for linear algebra operations within `CMSInterferenceFunc` and `RooSplineND`. Download and install from GitLab.
	```bash
	git clone https://gitlab.com/libeigen/eigen.git
	cd eigen/
	mkdir build && cd build
	cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/local
	make -j8     # Use all available CPUs for speed
	make install # Might take 15-20 minutes
	```
	> This is a slow build step (~15-20 minutes). The compiler verbosity is minimal, so it may appear stuck at 0% for a long time before suddenly jumping to 33%. Be patient.
	
- **VDT [optional]**  <br>
VDT provides fast, vectorized math functions. Download and install from GitHub.
	```bash
	git clone https://github.com/dpiparo/vdt.git
	cd vdt/
	mkdir build && cd build
	cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/local -DCMAKE_POLICY_VERSION_MINIMUM=3.5
	# hack: VDT requires older cmake version
	make -j8 # Use all available CPUs for speed
	make install
	```
### Install CMS-combine

⚠️Make sure that ROOT's MathMore library is available [read the ROOT section carefully]. <br>
✅Once all dependencies are ready, you can clone Combine directly from GitHub and compile as follows.
```bash
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git
cd HiggsAnalysis-CombinedLimit/
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/local -DCMAKE_PREFIX_PATH="$HOME/local;$HOME/root_install"
# In case you did not install VDT, use the -DUSE_VDT=FALSE option here
# It may also complain about missing GTest library.
# It's not necessary; we are not uging the google test library.
cmake --build . -j8  # Use all available CPUs for speed
```
Once the build is complete, the binary is created in the `build/bin` directory. Update the system path variables in the `.bashrc` by including the following lines.
```bash
export PATH=$HOME/HiggsAnalysis-CombinedLimit/build/bin:$PATH
export LD_LIBRARY_PATH=$HOME/HiggsAnalysis-CombinedLimit/build/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$HOME/HiggsAnalysis-CombinedLimit/build/python:$PYTHONPATH
```
Done!<br>
Verify the installation by running the following.
```bash
combine --help
```

---
I hope this guide makes navigating Combine outside of CMSSW a bit easier. If you encounter any issues, have suggestions for improvements, or just want to discuss CMS data analysis, feel free to reach out!

**Prachurjya Hazarika** <br>
![IISER](https://img.shields.io/badge/IISER-Pune-white?labelColor=d80001) ![CMS](https://img.shields.io/badge/CMS-CERN-white?labelColor=00319b)
