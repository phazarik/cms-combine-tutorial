#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Extracts shape histograms from ROOT files to generate CMS Combine datacards 
# (.txt) for signal and background processes.
#
# Input format required: 
#   ROOT file(s) containing TH1D histograms. Histograms must strictly follow 
#   the naming convention '<Region>_<Process>'. The file must include a 
#   histogram ending in '_data_obs' to successfully identify signal regions.
#
# Output: 
#   CMS Combine datacard text file(s) (.txt) containing observation yields, 
#   expected process rates mapped to Combine IDs, and autoMCStats directives.
#
# Usage: 
#       python3 convertShapesToDatacards.py
#       python3 convertShapesToDatacards.py -i shapes/shape_example.root
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

    # First pass: find all signal regions based on data_obs
    for k in keys:
        if k.endswith("_data_obs"):
            sr_name = k.replace("_data_obs", "")
            sr_set.add(sr_name)

    # Second pass: find all processes belonging to those regions
    for k in keys:
        if k.endswith("_data_obs"): continue
        for sr in sr_set:
            if k.startswith(sr + "_"):
                pname = k[len(sr)+1:] # Strip the SR name and the underscore
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

        ## autoMCStats option
        f.write(f"* autoMCStats 10 1 1\n")

    tfile.Close()
    print(f">> Datacard created: {YELLOW}{outfile}{RESET}")

## Execution
if __name__ == "__main__": main()
