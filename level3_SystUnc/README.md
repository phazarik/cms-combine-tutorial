# Systematic Uncertainties

The first section described simple counting experiments using only text datacards. The second section transitioned those same examples to use shape files, with the datacards pointing directly to the underlying ROOT histograms. In this module, we take the final step for this baseline setup: incorporating systematic uncertainties into those shape files and datacards.

## Modifying the shape files

To evaluate shape uncertainties, CMS Combine requires alternate templates that represent the kinematic distribution shifted by $\pm 1$ standard deviation of the systematic source. Taking a multi-SR example, the ROOT file `shape_304.root` is modified as follows:
```
TFile**         shapes/shape_304.root
 TFile*         shapes/shape_304.root
  KEY: TH1F     SR301_data_obs;1        SR301_data_obs
  KEY: TH1F     SR301_ttbar;1   SR301_ttbar
  KEY: TH1F     SR301_ttbar_CMS_eff_e_idUp;1    SR301_ttbar_CMS_eff_e_idUp
  KEY: TH1F     SR301_ttbar_CMS_eff_e_idDown;1  SR301_ttbar_CMS_eff_e_idDown
  KEY: TH1F     SR301_ttbar_CMS_scale_jUp;1     SR301_ttbar_CMS_scale_jUp
  KEY: TH1F     SR301_ttbar_CMS_scale_jDown;1   SR301_ttbar_CMS_scale_jDown
  KEY: TH1F     SR301_vll;1     SR301_vll
  KEY: TH1F     SR301_vll_CMS_eff_e_idUp;1      SR301_vll_CMS_eff_e_idUp
  KEY: TH1F     SR301_vll_CMS_eff_e_idDown;1    SR301_vll_CMS_eff_e_idDown
  KEY: TH1F     SR301_vll_CMS_scale_jUp;1       SR301_vll_CMS_scale_jUp
  KEY: TH1F     SR301_vll_CMS_scale_jDown;1     SR301_vll_CMS_scale_jDown
... repreated for other SRs
```
> Combine only requires the nominal values of the up/down variations. I am lazy, and I did not bother to put the statistical uncertainties in these Up/Down histograms. Real life histograms always have these statitsical uncertainties; don't worry about them for now.

## Modifying the datacard

To instruct Combine to utilize these new variations, the text datacard is expanded with a dedicated systematics block:
```
imax 3
jmax 3
kmax *

# SHAPES -------------------------------------
shapes * * shapes/shape_304.root $CHANNEL_$PROCESS $CHANNEL_$PROCESS_$SYSTEMATIC

# OBSERVATION ---------------------------------
bin          SR301    SR302    SR303
observation  26       33       54

# BINS ----------------------------------------
bin          SR301    SR301    SR301    SR301    SR302    SR302    SR302    SR302    SR303    SR303    SR303    SR303

# PROCESSES -----------------------------------
process      vll      dy       ttbar    vv       vll      dy       ttbar    vv       vll      dy       ttbar    vv
process      0        1        2        3        0        1        2        3        0        1        2        3

# RATES ---------------------------------------
rate         5.2      0.0      23.8     0.0      5.2      6.8      18.3     2.1      8.6      11.0     30.4     3.4

# SYSTEMATICS -----------------------------------
CMS_eff_e_id           shape -        -        -        -        -        1        -        -        -        1        -        -
CMS_scale_j            shape 1        -        1        -        1        1        1        1        1        1        1        1
CMS_xsec_vv            lnN   -        -        -        -        -        -        -        1.10     -        -        -        1.10
lumi                   lnN   1.05     -        1.05     -        1.05     1.05     1.05     1.05     1.05     1.05     1.05     1.05
* autoMCStats 10 1 1
```

### What are the new parts?

The introduction of the `# SYSTEMATICS` section dictates how uncertainties are applied across different bins and processes. Notice that there are two distinctly different types of uncertainties modeled here:

-   **Shape-based uncertainties:** The `shape` keyword tells Combine to look inside the defined ROOT file for the `Up` and `Down` templates. These represent uncertainties that fundamentally alter the kinematic profile of a distribution, often causing events to migrate from one bin to another. Common examples include experimental effects like Jet Energy Scale (JES) and Jet Energy Resolution (JER), or theoretical effects like parton shower and PDF variations.
    -  A value of **`1`** means the systematic is active for that specific column (process/region). Combine will map to the corresponding `Up` and `Down` histograms and apply a morphing algorithm during the fit.
    -  A value of **`-`** (dash) means the uncertainty does not apply to that process in that region. Combine will ignore it completely.
    -  In this exercise, the mapping and application of these shape directives are handled dynamically while preparing the datacard using the `writeDatacardsFromShapes.py` script.
        
-   **Log-normal uncertainties:** Unlike shape morphing, `lnN` uncertainties apply purely to the _normalization_ (total rate) of a process without altering its underlying kinematic shape. Because they only scale the yield up or down, they do not require alternate histograms to be stored in the shape files. In this example:
    -  A value like **`1.05`** represents a flat 5% symmetric uncertainty applied globally (e.g., for the `lumi` uncertainty). 
    -  A value like **`1.10`** represents a 10% uncertainty applied selectively (e.g., `CMS_xsec_vv` applied only to the `vv` background column).
    
## Know your systematic uncertainties!

Adding systematics to a datacard is mechanically simple, but requires careful physical checks. Keep the following cautions and Combine-specific behaviors in mind:

-   **MC statistical noise:** Always plot and visually inspect the `Up` and `Down` shape variations against the nominal histogram. If the variation is mostly jagged Monte Carlo statistical fluctuations instead of a real physical shift, it feeds noise into the fit. This can artificially over-constrain the uncertainty or cause the fit to fail.
    
-   **Auto-pruning:** Combine has built-in safeguards. If the `Up` and `Down` histograms in the ROOT file are mathematically identical to the nominal shape, Combine silently ignores the systematic and drops the nuisance parameter to save computing time.
    
-   **Negative bins:** Aggressive shape variations or negative weights from NLO samples can push a bin's yield below zero. Combine usually floors these to a tiny positive number, but severe cases can crash the workspace compilation or cause bad fits. Careful binning is required to manage these negative events.
    
-   **Large asymmetries:** Huge differences between up and down variations can cause fit problems. It is acceptable to manually increase one or both variations to help the fit succeed, as claiming a larger uncertainty is a more conservative approach.
    
-   **Directional shifts:** Sometimes both variations move in the same direction or shift in unexpected ways. This can happen for real physical reasons, and it is important to investigate and understand the root cause.

## Exercises

1. This setup is identical to the previous chapter, except for the added systematics. Repeat the limit calculations and fit diagnostics to see how systematic uncertainties impact the final limits.
    
2. Convert the new datacard to a workspace using `text2workspace.py` and print the entries using `w->Print()` in a ROOT session. Notice how the new nuisance parameters are represented internally compared to the `autoMCStats` parameters.
    
3. Go crazy! Manually edit the datacard to change the systematic variations to absurd values. Observe where Combine breaks or how the fit behaves.

## Advanced use cases

The following sections detail more advanced operations available in Combine. It is recommended to create a workspace first (using `text2workspace.py`) to test these features. For comprehensive documentation, refer to the [official combine documentation](https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/part3/nonstandard/).

### Pulls and impacts

Impact plots are essential for understanding which systematic uncertainties most strongly affect the parameter of interest (POI), typically the signal strength $r$. This workflow performs an initial fit, scans each nuisance parameter individually to compute its "pull" (how much the data shifts the parameter from its pre-fit expectation), and measures its "impact" on the final limit.
```bash
combineTool.py -M Impacts -d workspace.root -m 800 --doInitialFit --robustFit 1
combineTool.py -M Impacts -d workspace.root -m 800 --robustFit 1 --doFits --parallel 16
combineTool.py -M Impacts -d workspace.root -m 800 -o impacts.json
plotImpacts.py -i impacts.json -o impacts_plot
```

### Goodness of fit 

A goodness of fit (GOF) test evaluates how well the expected model describes the observed data. The saturated model algorithm is commonly used for shape-based analyses. It calculates a test statistic for the observation and compares it against a distribution built from generated pseudo-experiments (toys).

Notice the addition of `--setParameters r=0 --freezeParameters r` to enforce the background-only state:
```bash
combine -M GoodnessOfFit workspace.root -m 800 --algo saturated --setParameters r=0 --freezeParameters r -n _data_bkgonly
combineTool.py -M GoodnessOfFit workspace.root -m 800 --algo saturated --setParameters r=0 --freezeParameters r -n _toys_bkgonly -t 200 --toysFrequentist --parallel 8
combineTool.py -M CollectGoodnessOfFit --input higgsCombine_data_bkgonly.GoodnessOfFit.mH800.root higgsCombine_toys_bkgonly.GoodnessOfFit.mH800.*.root -m 800 -o gof_bkgonly.json
plotGof.py gof_bkgonly.json --statistic saturated --mass 800.0 --output gof_plot_bkgonly
```
> **Note on the mass parameter (`-m`):** The value `800` used in these commands is simply a dummy mass-name acting as a bookkeeping label. If omitted, Combine defaults to a built-in standard mass (often `120.0` or `160.0`, inherited from historical Higgs searches). When passing the custom mass to plotting scripts, explicitly adding `.0` (e.g., `800.0`) is required to match Combine's internal JSON key formatting.

### Fit diagnostics
The `FitDiagnostics` method performs a maximum likelihood fit and saves the detailed post-fit distributions, covariance matrices, and shapes. By default, it runs both a background-only fit (`fit_b`) and a signal+background fit (`fit_s`). Freezing the signal strength forces the model to strictly represent the background-only hypothesis, ensuring the saved shapes and pulls are completely devoid of signal contamination.

For standalone environments without a full CMSSW release, the necessary helper script for extracting nuisances must be downloaded directly before running the commands.
```bash
curl -O https://raw.githubusercontent.com/cms-analysis/HiggsAnalysis-CombinedLimit/main/test/diffNuisances.py
```
As with GOF, the dummy mass label `800` is carried through the commands:
```bash
combine -M FitDiagnostics workspace.root -m 800 --setParameters r=0 --freezeParameters r --saveShapes --saveWithUncertainties -n _bkgonly
python3 diffNuisances.py fitDiagnostics_bkgonly.root --all -g pulls_output_bkgonly.root
```
## Hyper-parameters

While Combine attempts to find optimal settings automatically, complex models frequently require manual tuning of the underlying MINUIT minimizer. Supplying explicit hyper-parameters ensures fits converge reliably without stalling or producing unphysical results.

-   **Signal Strength Boundaries (`--rMin` and `--rMax`):** By default, Combine allows the signal strength $r$ to float freely. Restricting this range prevents the minimizer from scanning extreme, unphysical negative cross-sections or wandering infinitely in background-only scenarios. A common baseline is `--rMin -10 --rMax 10`.
    
-   **Minimizer Strategy (`--cminDefaultMinimizerStrategy`):** This dictates the thoroughness of the MINUIT Hessian matrix calculation. A value of `0` prioritizes speed and is sufficient for basic limits. A value of `1` (or `2`) is more robust and is strongly recommended for `FitDiagnostics` to guarantee a healthy, accurate covariance matrix.
    
-   **Robust Hesse Calculation (`--robustHesse 1`):** Activating this flag forces a more rigorous evaluation of the second derivatives when calculating uncertainties. It significantly reduces the likelihood of the fit failing due to a non-positive-definite matrix.
    
-   **Fallback Algorithms (`--cminFallbackAlgo`):** If the primary minimizer (Migrad) fails to converge, providing backup routines allows Combine to recover gracefully. Passing a chain of fallbacks, such as `--cminFallbackAlgo Minuit2,Simplex,0:0.1`, instructs the tool to attempt the Simplex algorithm before entirely abandoning the fit.

---
To summarize, this module covered the core mechanics of linking log-normal normalization effects and complex shape-morphing nuisance parameters to the statistical models. Dynamically filtering empty bins and mapping specific uncertainties to the correct backgrounds ensures that the datacard remains physically robust and computationally stable.
