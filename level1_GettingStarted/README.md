# Getting Started

This module contains the simplest possible CMS Combine datacards. It serves as a "Hello World" example and introduces the basic structure of a Combine datacard before adding systematic uncertainties, multiple search regions, or shape analyses.

A datacard is a plain text file describing the statistical model that CMS Combine will use. It contains the observed event yields, the expected signal and background yields, and (in more realistic examples) systematic uncertainties and references to ROOT histograms.

## 101: Explaining a datacard

The example datacard, `datacard_101.txt` contains only the minimal essential information:

```text
imax 1
jmax 1
kmax 0
bin          SR1
observation  26
bin          SR1          SR1
process      vll          ttbar
process      0            1
rate         5.2          23.8
```
The actual file also contains several commented lines beginning with `#`, explaining what each section means.

Consider a single search region (`SR1`). Two processes contribute to it, with expected yields shown in the following table.

| Process      | Yield |
|--------------|------:|
| vll (signal) | 5.2   |
| ttbar        | 23.8  |

An observation of 26 events in the data naturally leads to two questions:
-   **Physics:** What can be concluded from these event yields? Is the observed data consistent with the background-only hypothesis, or is there evidence for a signal?
-   **Technical:** How is this information provided to CMS Combine so that it can perform the statistical inference?

Setting the physics aside to focus on the technical implementation, a Combine datacard is organized into several sections.
```text
imax 1
jmax 1
kmax 0
```
These three lines tell Combine the size of the statistical model.
- `imax` = number of analysis bins (channels, or signal regions; in this case, 1)
- `jmax` = number of background processes (in this case, 1)
- `kmax` = number of nuisance parameters (in this case, 0)

```text
bin          SR1
observation  26
```
This section defines:
- the name of the analysis bin(s) (in this case, only `SR1`)
- the number of observed events in data in each bin (in this case, `26`).

```text
bin          SR1          SR1
process      vll          ttbar
process      0            1
rate         5.2          23.8
```
This section defines the expected event yields. The first row specifies which analysis bin each process belongs to. The second row gives the process names. The third row assigns process IDs. Note that:
-   signal processes must have IDs **≤ 0**
-   background processes must have IDs **> 0**

Finally, the `rate` row gives the expected event yields before any statistical inference is performed. The ordering of every row must be consistent. The first column always corresponds to the signal (`vll`) and the second column to the background (`ttbar`).

## Limit calculation

### "Hello World" of CMS Combine

The limit is calculated using the _Asymptotic approximation_.

```bash
combine -M AsymptoticLimits datacard_101.txt
```
> Note: if this causes segmentation fault, try the two step process:
> ```bash
> text2workspace.py datacard_101.txt -o workspace.root
> combine -M AsymptoticLimits workspace.root
> ```
The output should look like this.

```text
<<< Combine >>>
<<< v10.6.1 >>>

>>> Method used is AsymptoticLimits

 -- AsymptoticLimits ( CLs ) --
Observed Limit: r < 2.4496
Expected  2.5%: r < 1.0714
Expected 16.0%: r < 1.4548
Expected 50.0%: r < 2.0938
Expected 84.0%: r < 3.0535
Expected 97.5%: r < 4.2830
```
Besides printing the results, Combine also creates a ROOT file:
```text
higgsCombineTest.AsymptoticLimits.mH120.root
```

The filename is historical—the `mH120` part does **not** imply that the signal has a mass of 120 GeV.

The output can be interpreted as follows. CMS Combine introduces a **signal strength parameter**, denoted by **r**. Instead of changing the signal yield directly, Combine scales the predicted signal according to:
```
Predicted signal = r × (nominal signal prediction)
```
Therefore,
- r = 0 means no signal,
- r = 1 corresponds to the nominal signal prediction,
- r > 1 corresponds to a larger signal than predicted.

The reported limit is therefore a **limit on r**, not directly on the number of signal events.

In this example, `Observed Limit: r < 2.4496` means that signal strengths larger than 2.45 times the nominal prediction are excluded at a 95% confidence level. Since the nominal signal corresponds to 5.2 events, this roughly translates to excluding signal contributions larger than 2.45 × 5.2 = 12.7 events. Because the nominal signal corresponds to r = 1, it is not excluded. In other words, this analysis does not have sufficient sensitivity to exclude the nominal signal hypothesis.

To summarize:
-   `Observed Limit: r < 1` means the nominal signal hypothesis is **excluded** at the 95% CL.
-   `Observed Limit: r > 1` means the nominal signal hypothesis is **not excluded**.

> The 95% confidence level (CL) corresponda to a standard threshold adopted in particle physics for reporting exclusion limits. If a signal hypothesis fails the corresponding statistical test, it is said to be _excluded at the 95% CL_. For a more detailed discussion of confidence levels and the CL<sub>s</sub> method, see the official CMS Combine documentation and the paper by Cowan *et al.*, *Asymptotic formulae for likelihood-based tests of new physics*, Eur. Phys. J. C 71 (2011) 1554 ([arXiv:1007.1727](https://arxiv.org/abs/1007.1727)).

### Expected vs observed limits

The **observed limit** is computed using the actual observed event count (`26`). The **expected limits** are computed using an Asimov dataset (roughly speaking, assuming data = background prediction). The expected limit also comes with the 1σ and 2σ uncertainty bands, which are traditionally shown using the "Brazilian" color scheme.

| Output  | Meaning |
|---------|---------|
| 2.5%    | −2σ expected limit    |
| 16%     | −1σ expected limit    |
| 50%     | Median expected limit |
| 84%     | +1σ expected limit    |
| 97.5%   | +2σ expected limit    |

**Why expected limits?** Expected limits are computed by assuming that the observed data are exactly equal to the predicted background, _i.e._ there is no signal. They measure the intrinsic sensitivity of the analysis before looking at the data. Even if the data perfectly match the background prediction, the analysis can still exclude sufficiently large signal hypotheses.

After unblinding, the expected limits become a useful reference for interpreting the observed limits.
-   A small difference between the expected and observed limits is normal and is caused by statistical fluctuations.
-   A large difference may indicate the following:
    -   the presence of a signal (or an unusually large statistical fluctuation), or
    -   an issue with the background prediction, such as mismodeling or underestimated uncertainties.

Comparing the expected and observed limits is therefore one of the first sanity checks performed after unblinding.

### Things to try

Modifying the datacard and rerunning Combine is an effective way to build intuition about how statistical inference works. For example, observe how the limits change when:
- increase the observation from `26` to `35`,
- decrease it to `20`,
- increase the signal yield,
- increase the background yield.

---

### More options to play with

By default, Combine prints only the final results. To see more details about the internal calculations, increase the verbosity:
```bash
combine -M AsymptoticLimits datacard_101.txt -v 1
```
This prints additional information such as the best-fit value of the signal strength, likelihood minimization, CLs calculations, and intermediate values used during the limit determination. Increasing the verbosity further shows detailed RooFit output, minimization steps, and numerical information useful for debugging and understanding what Combine is doing internally. A complete understanding of all outputs is not required at this stage. The following options can also be explored.

#### Running a blinded test
Before looking at the observed data, it is common practice to compute only the expected limits. This is the standard workflow before unblinding an analysis. There are two commonly used options:
```bash
combine -M AsymptoticLimits datacard_101.txt --run blind
combine -M AsymptoticLimits datacard_101.txt -t -1
```
-   `--run blind` suppresses the observed limit and prints only the expected limits. This is useful for producing blinded results before the data are examined.
-   `-t -1` tells Combine to replace the observed data with an **Asimov dataset** (background-only expectation). Since an Asimov dataset contains no statistical fluctuations, the "observed" limit is nearly identical to the median expected limit. This option is commonly used for validation studies and debugging.
-
#### Best-fit signal strength (Fit Diagnostics)
A maximum-likelihood fit can be performed using `FitDiagnostics`. The output reports the best-fit value of the signal strength `r` and its uncertainty. In later examples with systematic uncertainties, this command also produces post-fit shapes, nuisance parameter pulls, constraints, and many other useful diagnostics.
```bash
combine -M FitDiagnostics datacard_101.txt
```
#### Likelihood fit

The `MultiDimFit` method performs a likelihood fit to the parameter(s) of interest. For this simple example, it reports only the best-fit value of `r`. In advanced cases, it can perform likelihood scans and confidence interval estimation.
```bash
combine -M MultiDimFit datacard_101.txt
```

### Creating a RooWorkspace

Internally, CMS Combine does not work directly with the text datacard. The datacard is first converted into a **RooWorkspace**, a ROOT object that stores the complete statistical model in a format understood by RooFit and RooStats. This includes the observables, model parameters, probability density functions (PDFs), datasets, and other objects needed for statistical inference. This conversion is performed using the following command:
```bash
text2workspace.py datacard_101.txt -o  workspace.root
```
The resulting `workspace.root` file contains a `RooWorkspace` named `w`. One advantage of creating the workspace explicitly is that the conversion needs to be done only once. All subsequent Combine commands can be run directly on the workspace, which is particularly convenient and time-saving for large analyses. It also allows inspection of the statistical model that Combine has built from the data card.

The workspace can be opened and printed in ROOT via the terminal:
```bash
root workspace.root
```
```cpp
root [0] w->ls()
root [1] w->Print()
```
The output is organized into several sections.

- **variables** contain the quantities used in the fit. Here,
  - `n_obs_binSR1` is the observed event count,
  - `n_exp_binSR1_proc_ttbar` is the expected background yield, and
  - `r` is the parameter of interest (signal strength).

- **p.d.f.s** contain the probability density functions describing the statistical model. In this simple counting experiment, the likelihood is built from a Poisson distribution. Separate PDFs are constructed for the signal-plus-background (`model_s`) and background-only (`model_b`) hypotheses.

- **functions** define derived quantities. For example,
  - `n_exp_binSR1` is the total expected yield (signal + background),
  - `n_exp_binSR1_bonly` is the expected yield under the background-only hypothesis, and
  - `ProcessNormalization` scales the signal yield by the signal strength parameter `r`.

- **datasets** contain the observed data used in the fit. Here, `data_obs` simply stores the observed event count.

- **named sets** group related objects. For example, `POI` identifies the parameter of interest (`r`), `observables` lists the measured quantities, and `nuisances` contains nuisance parameters (empty in this example).

- **generic objects** contain the `ModelConfig` objects used by RooStats to perform statistical inference.

## 102: Adding more backgrounds

The example can be made more realistic by introducing additional background processes. The datacard `datacard_102.txt` now contains three background processes contributing to the same search region (`SR1`).
```text
imax 1
jmax 3
kmax 0

# OBSERVATION ---------------------------------
bin          SR1
observation  33

# BINS ----------------------------------------
bin          SR1      SR1      SR1      SR1

# PROCESSES -----------------------------------
process      vll      ttbar    dy       vv
process      0        1        2        3

# RATES ---------------------------------------
rate         5.2      18.3     6.8      2.1
```
Compared to the previous example, only a few things have changed:
- `jmax` is now **3**, since there are three background processes (`ttbar`, `dy`, and `vv`).
-  The **process** and **rate** sections now contain one additional column for each new background.
- The **bin** row is repeated four times, once for each process, since all processes contribute to the same search region.
- The process IDs have been updated accordingly: - `0` for the signal (`vll`), - positive integers (`1`, `2`, `3`) for the three background processes.
- The observation has been changed to **33** events to reflect the new total expected yield.

Notice that the structure of the datacard is otherwise identical. Adding more processes simply means adding more columns while keeping the ordering consistent across the `bin`, `process`, and `rate` rows. All Combine commands introduced in the previous example work without any modification.

## 103: Adding more bins (signal regions)

Previous examples featured all processes contributing to a single search region (`SR1`). In a realistic analysis, data is typically divided into multiple search regions to improve sensitivity. The datacard `datacard_103.txt` introduces a second search region (`SR2`).
```text
imax 2
jmax 3
kmax *

# OBSERVATION ---------------------------------
bin          SR1      SR2
observation  33       21

# BINS ----------------------------------------
bin          SR1      SR1      SR1      SR1      SR2      SR2      SR2      SR2

# PROCESSES -----------------------------------
process      vll      ttbar    dy       vv       vll      ttbar    dy       vv
process      0        1        2        3        0        1        2        3

# RATES ---------------------------------------
rate         5.2      18.3     6.8      2.1      3.4      12.1     4.2      1.3

* autoMCStats 10 1 1
```
Compared to the previous example, the following changes have been made:
- `imax` is now **2**, since there are two analysis bins (`SR1` and `SR2`).
- The **observation** section now contains one observed event count for each search region.
- The **bin**, **process**, and **rate** sections now contain one set of processes for **each** search region. In other words, every process must be listed once per analysis bin.
- The process IDs remain unchanged. The signal is always assigned `0`, while the background processes keep their positive IDs. The same IDs are reused for every search region.
- kmax is set to **\***, which allows Combine to automatically calculate the nuisance parameters in the datacard. This will be important later when we deal with systematic uncertainties.
- `autoMCStats` has been enabled with the options `10 1 1`

### Automatic treatment of MC statistical uncertainties

The following line enables the automatic treatment of Monte Carlo (MC) statistical uncertainties:

```text
* autoMCStats 10 1 1
```

The finite size of simulated event samples introduces statistical uncertainties in the predicted event yields. Rather than defining these nuisance parameters manually, `autoMCStats` instructs Combine to create them automatically.

The three arguments have the following meaning:

- `10`: Threshold on the effective number of simulated events. Bins with fewer than 10 effective events receive an individual statistical nuisance parameter. Setting this value to `0` creates an individual nuisance parameter for every bin.
- `1`: Include statistical uncertainties for signal processes (`1` = yes, `0` = no).
- `1`: Include statistical uncertainties for background processes (`1` = yes, `0` = no).

In this example, however, the datacard is a **counting experiment** and does not contain any input histograms. Therefore, `autoMCStats` has no effect, and no additional nuisance parameters are created. The option is included here because it is almost always present in modern CMS shape analyses.

---
In summary, this introductory module covers the foundational mechanics of CMS Combine datacards for counting experiments, demonstrating how to define signal and background yields, assign process IDs, and perform statistical inference using tools like `AsymptoticLimits` and `FitDiagnostics`. By scaling from a single-bin model (`101`) to multi-background (`102`) and multi-bin search regions (`103`), it establishes the essential workflow for converting text datacards into a `RooWorkspace` via `text2workspace.py`, setting the stage for incorporating shape analyses and systematic uncertainties in subsequent modules.
