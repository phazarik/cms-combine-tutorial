#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Extracts shape histograms from ROOT files to generate CMS Combine datacards 
# (.txt) for signal/background processes and their systematic uncertainties.
#
# Input format required: 
#   ROOT file(s) containing TH1D/TH1F histograms. Histograms must strictly follow 
#   the naming convention '<Region>_<Process>' for nominal yields, and 
#   '<Region>_<Process>_<SystName>Up/Down' for shape systematic variations. 
#   The file must include a histogram ending in '_data_obs' to successfully 
#   identify signal regions.
#
# Output: 
#   CMS Combine datacard text file(s) (.txt) containing observation yields, 
#   expected process rates mapped to Combine IDs, evaluated shape and lnN 
#   systematic uncertainty directives, and autoMCStats directives.
#
# Usage: 
#       python3 writeDatacardsFromShapes.py
#       python3 writeDatacardsFromShapes.py -i shapes/shape_example.root
# -----------------------------------------------------------------------------

import os, argparse
import glob
import natsort
import ROOT

RED, YELLOW = "\033[31m", "\033[33m"
RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert shape ROOT files to Combine Datacards.")
    parser.add_argument("-i", "-in", "-input", "-infile", "-file", 
                        dest="input_file", help="Specific input ROOT file to process")
    args = parser.parse_args()

    indir = "shapes"

    ## Use argparse input if provided; otherwise, glob all files
    if args.input_file: root_files = [args.input_file]
    else:
        root_files = glob.glob(os.path.join(indir, "shape_*.root"))
        root_files = natsort.natsorted(root_files) ## alphanumeric sorting
        
    if not root_files:
        print(f"{RED}[ERROR] No shape files found.{RESET}")
        return

    ## Process each root file and save datacards in the current directory
    for infile in root_files:
        filename = os.path.basename(infile)
        outfile = filename.replace("shape", "datacard").replace("root", "txt")
        process_shape_to_datacard(infile, outfile)
        
# -----------------------------------------------------------------------
def process_shape_to_datacard(infile, outfile):

    print(f"\n>> Processing {infile} -> {outfile}")
    tfile = ROOT.TFile.Open(infile, "READ")
    if not tfile or tfile.IsZombie():
        print(f"{RED}[ERROR] Failed to open {infile}{RESET}")
        return

    ## Extract list of process keys from the ROOT file contents
    keys = [k.GetName() for k in tfile.GetListOfKeys()]

    ## Discover all unique Signal Regions (SRs) and Processes
    sr_set = set()
    proc_set = set()

    ## First pass: find all signal regions based on data_obs
    for k in keys:
        if k.endswith("_data_obs"):
            sr_name = k.replace("_data_obs", "")
            sr_set.add(sr_name)

    ## Second pass: find all processes belonging to those regions
    for k in keys:
        if k.endswith("_data_obs"): continue

        ## Skip systematic histograms
        if k.endswith("Up") or k.endswith("Down"): continue
        
        for sr in sr_set:
            if k.startswith(sr + "_"):
                pname = k[len(sr)+1:] ## Strip the SR name and the underscore
                proc_set.add(pname)
                break

    if not sr_set:
        print(f"{RED}[ERROR] No valid data_obs histograms found in {infile}.{RESET}")
        tfile.Close()
        return

    ## Alphanumeric sorting for SR bins (SR1, SR2, ...)
    sr_list = natsort.natsorted(list(sr_set))

    ## Separate signals and backgrounds to maintain order
    proc_sig = [p for p in proc_set if p.startswith("vll")]
    proc_bkg = [p for p in proc_set if not p.startswith("vll")]
    proc_bkg.sort()
    proc_ordered = proc_sig + proc_bkg

    ## Map process names to Combine IDs (Signals <= 0, Backgrounds > 0)
    proc_ids = {}
    for idx, p in enumerate(proc_sig): proc_ids[p] = -idx
    for idx, p in enumerate(proc_bkg): proc_ids[p] = idx + 1

    with open(outfile, "w") as f:
        ## Header setup
        f.write(f"imax {len(sr_list)}\n")
        f.write(f"jmax {len(proc_ordered) - 1}\n")
        f.write(f"kmax *\n\n")

        ## SHAPES section - pointing Combine to your ROOT shapes
        f.write(f"# SHAPES -------------------------------------\n")
        f.write(f"shapes * * {infile} $CHANNEL_$PROCESS $CHANNEL_$PROCESS_$SYSTEMATIC\n\n")

        ## OBSERVATION section
        f.write(f"# OBSERVATION {('-' * 33)}\n")
        obs_line = f"bin          " + " ".join(f"{sr:<8}" for sr in sr_list) + "\n"

        obs_yields = []
        for sr in sr_list:
            h_data = tfile.Get(f"{sr}_data_obs")
            obs_yields.append(str(int(h_data.Integral())))

        val_line = f"observation  " + " ".join(f"{y:<8}" for y in obs_yields) + "\n\n"
        f.write(obs_line)
        f.write(val_line)

        ## BINS section
        f.write(f"# BINS {('-' * 40)}\n")
        bin_expanded = []
        for sr in sr_list:
            bin_expanded.extend([sr] * len(proc_ordered))
        f.write(f"bin          " + " ".join(f"{b:<8}" for b in bin_expanded) + "\n\n")

        ## PROCESSES section
        f.write(f"# PROCESSES {('-' * 35)}\n")
        proc_line_names = []
        proc_line_ids = []
        for _ in sr_list:
            proc_line_names.extend(proc_ordered)
            proc_line_ids.extend([str(proc_ids[p]) for p in proc_ordered])

        f.write(f"process      " + " ".join(f"{p:<8}" for p in proc_line_names) + "\n")
        f.write(f"process      " + " ".join(f"{i:<8}" for i in proc_line_ids) + "\n\n")

        ## RATES section
        f.write(f"# RATES {('-' * 39)}\n")
        rate_line_vals = []
        for sr in sr_list:
            for p in proc_ordered:
                h_mc = tfile.Get(f"{sr}_{p}")
                rate_val = h_mc.Integral() if h_mc else 0.0
                rate_line_vals.append(f"{rate_val:.1f}")
        f.write(f"rate         " + " ".join(f"{r:<8}" for r in rate_line_vals) + "\n\n")

        # ----------------------------------------------------
        # USER CONTROL ON SYSTEMATICS
        # Control which background to pick for shape and lnN.
        # If not mentioned, applies to all.
        # ----------------------------------------------------
        apply_shape = {
            "CMS_eff_e_id": ["dy"]
        }
        syst_lnn = {
            "lumi": 1.05,        ## ->  5% luminosity uncertainty
            "CMS_xsec_vv": 1.10  ## -> 10% cross-section uncertainty to VV
        }
        apply_ln = {
            "CMS_xsec_vv": ["vv"] ## -> Entry must match in the previous dict
        }

        # ------------------------------------------------------
        # Shape-systematics
        # Find shape files that carry systematic variations.
        # If found, include them here
        #--------------------------------------------------------
        f.write(f"# SYSTEMATICS {('-' * 35)}\n")
        
        syst_names = set()
        for k in keys:
            if k.endswith("Up"):
                base_name = k[:-2] # Strip 'Up'
                down_name = base_name + "Down"
                ## Make sure that corresponding down also exists. Otherwise print a warning and skip
                if down_name not in keys:
                    print(f"{RED}[SKIPPING] Found {k} but missing matching {down_name}.{RESET}")
                    continue
                for p in proc_set:
                    if f"_{p}_" in base_name:
                        syst_name = base_name.split(f"_{p}_")[1]
                        syst_names.add(syst_name)
                        break

        ## Write shape directives
        max_len = max([len(s) for s in list(syst_names) + list(syst_lnn.keys())] + [20]) + 2

        for syst in sorted(syst_names):
            syst_line_vals = []
            
            for sr in sr_list:
                for p in proc_ordered:
                    h_nom = tfile.Get(f"{sr}_{p}")
                    h_up  = tfile.Get(f"{sr}_{p}_{syst}Up")
                    h_dn  = tfile.Get(f"{sr}_{p}_{syst}Down")
                    yield_nom = h_nom.Integral() if h_nom else 0.0
                    yield_up  = h_up.Integral()  if h_up  else 0.0
                    yield_dn  = h_dn.Integral()  if h_dn  else 0.0

                    ## Filter 1: If a syst is mentioned in 'apply_shape',
                    ## only apply to the backgrounds mentioned in the list
                    if syst in apply_shape and p not in apply_shape[syst]:
                        syst_line_vals.append("-")
                        continue
                        
                    ## Filter 2: If the nominal yield is zero, write "-"
                    if yield_nom <= 0:
                        syst_line_vals.append("-")
                        continue
                        
                    ## Filter 3: If the variations are too small, write "-"
                    if yield_up < 0.0001 or yield_dn < 0.0001:
                        syst_line_vals.append("-")
                        continue
                    
                    ## If filters reject all the "bad" behavior, write "1"
                    syst_line_vals.append("1")

            ## Write to datacard only if at least one entry is "1"
            if all(v == "-" for v in syst_line_vals): print(f"{DIM}[SKIPPING] All '-' row for: '{syst}{RESET}")
            else: f.write(f"{syst:<{max_len}} shape " + " ".join(f"{v:<8}" for v in syst_line_vals) + "\n")

        # ------------------------------------------------------
        # Log normal-systematics
        # If found, include them here
        #--------------------------------------------------------

        ## Same logic as shape uncertainty applied to lnN
        max_len = max([len(s) for s in list(syst_names) + list(syst_lnn.keys())] + [20]) + 2
        
        for syst, val in sorted(syst_lnn.items()):
            syst_line_vals = []
            val_str = f"{val:.2f}"

            for sr in sr_list:
                for p in proc_ordered:
                    h_nom = tfile.Get(f"{sr}_{p}")
                    nom_yield = h_nom.Integral() if h_nom else 0.0
                    
                    ## Filter 1: If restricted in apply_ln
                    if syst in apply_ln and p not in apply_ln[syst]:
                        syst_line_vals.append("-")
                        continue
                        
                    ## Filter 2: Nominal yield zero
                    if nom_yield <= 0:  # <--- Changed yield_nom to nom_yield
                        print(f"{DIM}[Skipping] {syst}: Nominal is zero for {sr}_{p}{RESET}")
                        syst_line_vals.append("-")
                        continue

                    ## If filters reject all the "bad" behavior, write the value
                    syst_line_vals.append(val_str)
                    
            ## Write to datacard only if at least one entry is "1"
            if all(v == "-" for v in syst_line_vals): print(f"{DIM}[SKIPPING] All '-' row for: '{syst}{RESET}")
            else: f.write(f"{syst:<{max_len}} lnN   " + " ".join(f"{v:<8}" for v in syst_line_vals) + "\n")

        ## autoMCStats option comes at the very end
        f.write(f"* autoMCStats 10 1 1\n")
    
    tfile.Close()
    print(f">> Datacard created: {YELLOW}{outfile}{RESET}")

## Execution
if __name__ == "__main__": main()
