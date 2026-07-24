# Shape Analysis

This module introduces shape analyses in CMS Combine. At this stage, we are excluding systematic uncertainties to focus entirely on the mechanics of building shape-based datacards from underlying kinematic distributions.

Let's clarify the distinction between signal regions and bins. In the previous Level 1 examples, we looked at counting experiments where we considered `SR1` and `SR2`. While "adding a new bin" in those examples, we were essentially just increasing the number of distinct signal regions. 

Moving forward, let's be careful with our notation. In this exercise, we will stick to the following convention:

- `SR1`, `SR2`, etc., denote distinct **signal regions** defined by different event selections.
- `bin1`, `bin2`, etc., denote **bins** of a kinematic variable (a shape) *within* the same SR.

Different SRs can have different binning structures for their respective variables.

## Input configurations

To bridge the gap between counting and shape experiments, the Level 1 counting examples (`101`, `102`, and `103`) have been written as JSON configuration files: `yield_201.json`, `yield_202.json`, and `yield_203.json`. These carry the same fundamental information, but they now explicitly carry the statistical error along with the yield (for now, we consider statistical uncertainties only). 

An additional file, `yield_204.json`, has been included to demonstrate a combined configuration that carries the three signal regions from `201`, `202`, and `203` simultaneously. These input files are located in the `yields/` directory.

## Converting yields to shapes

To perform a shape analysis, Combine requires the input distributions to be stored as histograms in a ROOT file. We use the `convertYieldsToShapes.py` script to handle this transition. This script reads the input JSON configurations from the `yields/` directory and generates the corresponding ROOT histograms, saving them directly into the `shapes/` directory. Individual files can be processed using the `-i` argument; otherwise, it processes all files in the `yields/` directory.
```bash
python3 convertYieldsToShapes.py -i yields/yield_203.json
```
The output file has the following internal layout:
```text
TFile** shapes/shape_203.root
 TFile* shapes/shape_203.root
  KEY: TH1D     SR_data_obs;1   SR_data_obs
  KEY: TH1D     SR_dy;1         SR_dy
  KEY: TH1D     SR_ttbar;1      SR_ttbar
  KEY: TH1D     SR_vv;1         SR_vv
  KEY: TH1D     SR_vll;1        SR_vll
```
**Note on Naming Conventions:**

-   The naming scheme `<SRname>_<process>` for Monte Carlo (MC) is highly convenient for automated mapping later.
-   The `_data_obs` suffix is strict and compulsory for the data histogram in Combine.
-   This specific example packages the identical total yields split across two bins inside each histogram, mimicking the physical information of the `datacard_103.txt` counting experiment.

## Writing datacards

Once the ROOT histograms are created, the next step is to write the text datacards that reference these shapes. The `writeDatacardsFromShapes.py` script automates this process. It reads the generated `.root` files in the `shapes/` directory and constructs the Combine datacard syntax, mapping the physics processes to their respective histograms. Individual files can be processed using the `-i` argument; otherwise, it processes all files in the `shapes/` directory.
```bash
python3 writeDatacardsFromShapes.py -i shapes/shape_203.root
```
The output datacard looks like this:
```text
imax 1
jmax 3
kmax *

# SHAPES -------------------------------------
shapes * * shapes/shape_203.root $CHANNEL_$PROCESS $CHANNEL_$PROCESS_$SYSTEMATIC

# OBSERVATION ---------------------------------
bin          SR
observation  54

# BINS ----------------------------------------
bin          SR       SR       SR       SR

# PROCESSES -----------------------------------
process      vll      dy       ttbar    vv
process      0        1        2        3

# RATES ---------------------------------------
rate         8.6      11.0     30.4     3.4

* autoMCStats 10 1 1
```

### Key Differences: counting vs. shape-datacards

Comparing this new shape-based datacard to the multi-bin counting experiment from the previous module (`datacard_103.txt`), several critical shifts in how Combine interprets the model can be identified:

- **The `shapes` block:** The introduction of the `shapes` line instructs Combine to look inside a ROOT file for its inputs. The general syntax follows `shapes [process] [channel] [file] [histogram_mapping] [systematics_mapping]`. The `* *` indicates this rule applies to all processes and all channels.

- **The file path:** The exact relative path `shapes/shape_203.root` is explicitly defined. This is highly important when combining multiple datacards later (e.g., combining different data-taking years or analysis categories). Combine searches for the ROOT file exactly where this path points, relative to the execution directory.

- **Histogram mapping (`$CHANNEL_$PROCESS`):** These tokens act as dynamic variables. Combine replaces `$CHANNEL` with the column name defined in the `bin` row (e.g., `SR`) and `$PROCESS` with the name from the `process` row (e.g., `vll`, `dy`). This automatically maps datacard columns to the `<SRname>_<process>` histograms created inside the ROOT file.

- **Systematics mapping (`$CHANNEL_$PROCESS_$SYSTEMATIC`):** This trailing string defines the naming convention for shape-based systematic uncertainties (e.g., searching for `SR_vll_JESUp` and `SR_vll_JESDown` histograms). While systematics are excluded at this stage, establishing this syntax is necessary for when they are incorporated later.

- **`imax` drops from 2 to 1:** In the counting card, every individual histogram bin is treated as an independent analysis channel (`imax 2`). In the shape card, the entire distribution belongs to a single signal region, meaning `imax` is **1**. The actual binning details are handled internally by the ROOT histogram structure.

- **Simplified Structure:** Because the binning is outsourced to the ROOT file, the datacard does not need to explicitly duplicate columns for every single bin. The rows represent the **integrated** values across the full shape, drastically reducing clutter. 

- **The `rate` values must match:** The `rate` row represents the integrated total yield of the process across the entire shape. It is crucial that this number **matches the exact integral** of the corresponding ROOT histogram. If a different rate is provided in the datacard, Combine automatically scales the entire histogram so its integral matches the text datacard rate. 

- **`kmax *` behavior:** In both instances, **`kmax *`** instructs Combine to dynamically calculate the total number of systematic uncertainties defined in the card. In the shape card, this becomes even more vital as it accommodates both normalization uncertainties and shape variations without requiring manual tracking.

## Why shapes?

Shifting from standard counting experiments to a shape analysis provides significant statistical and practical benefits:

1. **Preservation of Kinematic Information:** A counting experiment collapses an entire distribution into a single scalar value (or a few wide blocks), completely discarding the structural features of the data. Shape analysis leverages localized variations—such as a narrow resonance peak sitting on top of a smooth background distribution.
    
2. **Enhanced Signal-to-Background Discrimination:** Background processes frequently cluster in specific kinematic regions (e.g., low mass or low transverse momentum). By binning the shape finely, Combine isolates bins where the signal-to-background ratio is exceptionally high, heavily boosting the overall statistical sensitivity of the search.
    
3. **Control of Systematics:** When systematic variations are added to shapes, Combine does not simply scale the normalization up and down; it interpolates morphing effects across the entire distribution. This allows background shapes to be constrained using data sidebands directly inside the fit, reducing the impact of large theoretical or experimental uncertainties.
    
4. **Scale-Invariant Datacards:** As an analysis expands from a 2-bin setup to a 100-bin setup to achieve better resolution, a counting datacard becomes an unreadable, thousands-of-columns-wide file. In contrast, a shape datacard remains exactly the same size regardless of how many bins the underlying histogram contains.

## 204: Multiple signal regions in one ROOT file

To further clarify the distinction between signal regions and individual histogram bins, the configuration `yield_204.json` combines the physics information from `201`, `202`, and `203` into three separate signal regions: `SR201`, `SR202`, and `SR203`. 
```bash
python3 convertYieldsToShapes.py -i yields/yield_204.json
python3 writeDatacardsFromShapes.py -i shapes/shape_204.root
```
Inspecting the structural layout of the generated ROOT file reveals that all histograms are self-contained within a single file:
```text
TFile** shapes/shape_204.root
 TFile* shapes/shape_204.root
  KEY: TH1D     SR201_data_obs;1        SR201_data_obs
  KEY: TH1D     SR201_ttbar;1   SR201_ttbar
  KEY: TH1D     SR201_vll;1     SR201_vll
  KEY: TH1D     SR202_data_obs;1        SR202_data_obs
  KEY: TH1D     SR202_dy;1      SR202_dy
  KEY: TH1D     SR202_ttbar;1   SR202_ttbar
  KEY: TH1D     SR202_vv;1      SR202_vv
  KEY: TH1D     SR202_vll;1     SR202_vll
  KEY: TH1D     SR203_data_obs;1        SR203_data_obs
  KEY: TH1D     SR203_dy;1      SR203_dy
  KEY: TH1D     SR203_ttbar;1   SR203_ttbar
  KEY: TH1D     SR203_vv;1      SR203_vv
  KEY: TH1D     SR203_vll;1     SR203_vll
```
The resulting shape-based datacard scales to handle all three regions simultaneously:
```text
imax 3
jmax 3
kmax *

# SHAPES -------------------------------------
shapes * * shapes/shape_204.root $CHANNEL_$PROCESS$CHANNEL_$PROCESS_$SYSTEMATIC

# OBSERVATION ---------------------------------
bin          SR201    SR202    SR203
observation  26       33       54

# BINS ----------------------------------------
bin          SR201    SR201    SR201    SR201    SR202    SR202    SR202    SR202    SR203    SR203    SR203    SR203

# PROCESSES -----------------------------------
process      vll      dy       ttbar    vv       vll      dy       ttbar    vv       vll      dy       ttbar    vv
process      0        1        2        3        0        1        2        3        0        1        2        3

# RATES ---------------------------------------
rate         5.2      0.0      23.8     0.0      5.2      6.8      18.3     2.1      8.6      11.0     30.4     3.4

* autoMCStats 10 1 1
```
### What are the changes?

-   **Simultaneous mapping via `$CHANNEL`:** Even though the datacard structure looks more complex, the single `shapes` rule still holds. The `$CHANNEL` variable dynamically matches `SR201`, `SR202`, and `SR203` as defined in the `bin` rows, mapping each column to its precise histogram inside `shape_204.root`.
    
-   **`imax` represents independent regions:** The `imax` parameter is set to **3** because there are three separate search regions. Crucially, each of these three regions can contain an arbitrary number of internal bins inside their respective ROOT histograms, but they only take up one channel block per region in the text card.
    
-   **Handling zero-yield processes:** In `SR201`, certain processes (`dy` and `vv`) have a rate of `0.0` (because there were absent in the `201` example). In a purely text-based counting card, handling missing processes across different blocks requires careful, asymmetric column structuring. Here, the structure remains perfectly uniform; the script simply enters a rate of `0.0` (and the corresponding ROOT file omits the empty histograms), which Combine processes correctly without crashing.
    
Attempting to implement this exact multi-region, multi-bin setup using a text-only counting experiment would be exceedingly difficult and error-prone, as it would require expanding the datacard horizontally by every single bin of every single signal region and manually matching every rate and statistical error block.

### Inspecting the RooWorkspace: autoMCStats

To check the RooFit objects made by Combine, turn the shape datacard into a `RooWorkspace` file using `text2workspace.py`. Then open a ROOT session and run the `Print()` method:
```bash
text2workspace.py datacard_204.txt -o workspace_204.root
root workspace_204.root
```
```cpp
root [1] w->Print()
```
Looking at the text output shows the internal structure of the generated workspace:
1. **Created nuisance parameters (`variables`):** Combine creates a nuisance parameter and a global observable for every histogram bin that passes the threshold in the datacard:
	```text
	prop_binSR201_bin0, prop_binSR201_bin0_In, 
	prop_binSR202_bin0, prop_binSR202_bin0_In, 
	prop_binSR203_bin0, prop_binSR203_bin0_In, prop_binSR203_bin1, prop_binSR203_bin1_In
	```
	-  `prop_bin<SR>_bin<N>` is the active parameter used to scale the bin yield up or down during the fit.
	-  `prop_bin<SR>_bin<N>_In` is the global observable fixed to the nominal value (usually 1.0).
	-  Bins only receive these parameters if they pass the event threshold and setting criteria defined by the `autoMCStats` options.
	
2. **Error functions (`functions`):** Shape uncertainties are added to the templates using the `CMSHistErrorPropagator` class:
	```	
	CMSHistErrorPropagator::prop_binSR203[ x=CMS_th1x funcs=(shapeSig_vll_SR203_rebinPdf, ...) coeffs=(...) binpars=(prop_binSR203_bin0,prop_binSR203_bin1) ]
	```
	This class connects the original shapes to their bin parameters. During the fit, it shifts the bin yields up or down based on the value of the `prop_bin` parameters.

3. **Gaussian constraints (`p.d.f.s`):** To account for limited MC statistics, Combine creates Gaussian constraint functions:
	```
	SimpleGaussianConstraint::prop_binSR201_bin0_Pdf[ x=prop_binSR201_bin0 mean=prop_binSR201_bin0_In sigma=1 ] = 1
	SimpleGaussianConstraint::prop_binSR202_bin0_Pdf[ x=prop_binSR202_bin0 mean=prop_binSR202_bin0_In sigma=1 ] = 1
	SimpleGaussianConstraint::prop_binSR203_bin0_Pdf[ x=prop_binSR203_bin0 mean=prop_binSR203_bin0_In sigma=1 ] = 1
	SimpleGaussianConstraint::prop_binSR203_bin1_Pdf[ x=prop_binSR203_bin1 mean=prop_binSR203_bin1_In sigma=1 ] = 1
	```
	These functions add a penalty to the likelihood if the parameters drift too far from the original MC simulation values.

4. **Parameter grouping (`named sets`):** The separate parameters are put together into lists:
	```
	group_autoMCStats:(prop_binSR201_bin0,prop_binSR202_bin0,prop_binSR203_bin0,prop_binSR203_bin1)		
	ModelConfig_NuisParams:(prop_binSR201_bin0,prop_binSR202_bin0,prop_binSR203_bin0,prop_binSR203_bin1)
	```
	Mapping these parameters into the `group_autoMCStats` list lets Combine handle auto statistical uncertainties easily. Putting them in one group allows controlling all bin parameters at once (like freezing or profiling them during fits) without needing to manage each bin parameter manually.


## Exercises

1.  Repeat the Level 1 statistics exercises on these new shape-based datacards. Run `AsymptoticLimits` and `FitDiagnostics` to verify the statistical pipeline works exactly as it did for counting experiments.
    
2.  Convert a shape datacard into a workspace using `text2workspace.py` and inspect the output using the `w->Print()` method in a ROOT session. Observe how `autoMCStats` dynamically generates a dedicated nuisance parameter for every valid histogram bin under the hood.
    
3.  Compute the upper limits on the signal strength parameter ($\mu$) for the individual datacards (`201`, `202`, and `203`). Then, execute the limit calculation on the combined datacard (`204`) and compare the results. Note how combining orthogonal signal regions structures a tighter statistical constraint, improving the overall sensitivity.
    
---

To summarize, this shape module covered the basics of linking ROOT histograms to CMS Combine models while keeping the text files clean and easy to scale. The next level will introduce systematic uncertainties. It explores how to add both log-normal rate changes and complex shape-morphing nuisance parameters into the fit.
