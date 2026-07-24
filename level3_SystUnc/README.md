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
---
To summarize, this module covered the core mechanics of linking log-normal normalization effects and complex shape-morphing nuisance parameters to the statistical models. Dynamically filtering empty bins and mapping specific uncertainties to the correct backgrounds ensures that the datacard remains physically robust and computationally stable.
