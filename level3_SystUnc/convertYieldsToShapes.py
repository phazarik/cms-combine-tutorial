#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Converts JSON files containing yield data and uncertainties into ROOT 
# histogram (shape) files for statistical analysis, including systematic variations.
#
# Input format required: 
#   JSON file(s) containing yield and error arrays per bin. The JSON schema 
#   must include 'bin_edges' and 'processes' at the top level for each region.
#   Each individual process requires 'yields' and 'errors' arrays, and can 
#   optionally include a 'systematics' block containing 'Up' and 'Down' arrays.
#
# Output: 
#   ROOT file(s) (.root) containing TH1F histograms saved in the 'shapes/' directory.
#   - Nominal shapes: <Region>_<Process>
#   - Systematic shapes: <Region>_<Process>_<SystName>Up/Down
#
# Usage: 
#       python3 convertYieldsToShapes.py
#       python3 convertYieldsToShapes.py -i yields/yield_example.json
# -----------------------------------------------------------------------------

import os, json, argparse
import glob, array
import natsort
import ROOT
RED, YELLOW = "\033[31m","\033[33m"
RESET, BOLD, DIM = "\033[0m","\033[1m","\033[2m"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert yield JSONs to shape ROOT files.")
    parser.add_argument("-i", "-in", "-input", "-infile", "-file", 
                        dest="input_file", help="Specific input JSON file to process")
    args = parser.parse_args()

    indir  = "yields"
    outdir = "shapes"
    os.makedirs(outdir, exist_ok=True)

    ## Use argparse input if provided; otherwise, glob all files
    if args.input_file: json_files = [args.input_file]
    else:
        json_files = glob.glob(os.path.join(indir, "yield_*.json"))
        json_files = natsort.natsorted(json_files) ## alphanumeric sorting
    if not json_files:
        print(f"{RED}[ERROR] No yield files to process.{RESET}")
        return

    ## Process each file
    for infile in json_files:
        outfile = infile.replace("yield", "shape").replace("json", "root")
        process_yield_to_shape(infile, outfile)

# -----------------------------------------------------------------------
def process_yield_to_shape(infile, outfile):

    print(f"\n>> Processing {infile} -> {outfile}")
    with open(infile, 'r') as f: data = json.load(f)

    ## Write to TFile
    tfile = ROOT.TFile(outfile, "RECREATE")

    ## Iterate over all regions at the topmost hierarchy
    for region_name, region_data in data.items():
        ## JSON validation
        if "bin_edges" not in region_data or "processes" not in region_data:
            print(f"{RED}[ERROR] Invalid JSON schema in {infile} for {region_name}. Missing 'bin_edges' or 'processes'.{RESET}")
            continue

        ## Convert bin edges to a double array for TH1F
        edges = array.array('d', [float(x) for x in region_data["bin_edges"]])
        nbins = len(edges) - 1

        ## Organize the processes list:
        proc = region_data["processes"]
        has_data = "data_obs" in proc
        proc_sig = [p for p in proc if p.startswith("vll")]
        proc_bkg = [p for p in proc if p != "data_obs" and (not p.startswith("vll"))]
        proc_bkg.sort()

        proc_ordered = []
        if has_data: proc_ordered.append("data_obs")
        proc_ordered.extend(proc_bkg)
        proc_ordered.extend(proc_sig)

        print(f">> Region [{region_name}] Processes being added: {proc_ordered}")

        ## Calculate name lengths across the region for aligned debug statement
        pname_width_max = max(len(p) for p in proc_ordered) if proc_ordered else 0
        syst_width_max = 0
        for p in proc_ordered:
            if "systematics" in proc[p]:
                for s in proc[p]["systematics"]:
                    syst_width_max = max(syst_width_max, len(s) + 8)
        print(DIM + "-" * 50 + RESET) ## debug

        ## Itertate over processes
        for p in proc_ordered:
            content = proc[p]

            ## Validate process specific JSON schema
            if "yields" not in content or "errors" not in content:
                print(f"{RED}[ERROR] Missing yield/err. Check: {p} in {region_name}{RESET}")
                continue

            if len(content["yields"]) != nbins or len(content["errors"]) != nbins:
                print(f"{RED}[ERROR] Bins mismatch. Check: '{p}' in {region_name}. Expected {nbins}.{RESET}")
                continue

            # -------------------------------------------
            # Write ROOT histograms
            # -------------------------------------------

            ## Nominal
            hname = f"{region_name}_{p}"
            h = ROOT.TH1F(hname, hname, nbins, edges)
            h.Sumw2() 
            for i in range(nbins):
                h.SetBinContent(i + 1, float(content["yields"][i]))
                h.SetBinError(i + 1, float(content["errors"][i]))
            h.Write()

            ## Shape systematics, if any
            if "systematics" in content:
                for syst_name, syst_variations in content["systematics"].items():
                    for direction in ["Up", "Down"]:
                        if direction in syst_variations:
                            h_syst_name = f"{hname}_{syst_name}{direction}"
                            h_syst = ROOT.TH1F(h_syst_name, h_syst_name, nbins, edges)
                            for i in range(nbins):
                                h_syst.SetBinContent(i + 1, float(syst_variations[direction][i]))
                            h_syst.Write()

            # -------------------------------------------
            # Debug Print (grouped by bin)
            # -------------------------------------------
            for i in range(nbins):
                val = float(content["yields"][i])
                err = float(content["errors"][i])
                
                ## Print Nominal
                print(f"{DIM}{YELLOW}{p:<{pname_width_max}} | bin {i+1:<2} | "
                      f"nominal yield = {val:.2f} \u00b1 {err:.2f}{RESET}")

                ## Print Systematics directly underneath their respective nominal bin
                if "systematics" in content:
                    for syst_name, syst_variations in content["systematics"].items():
                        for direction in ["Up", "Down"]:
                            if direction in syst_variations:
                                syst = float(syst_variations[direction][i])
                                diff = ((syst - val) / val * 100.0) if val != 0 else 0.0
                                sign = "+" if diff >= 0 else ""
                                syst_label = f"└─ {syst_name} {direction}"
                                print(f"{DIM}   {syst_label:<{syst_width_max}} | "
                                      f"bin {i+1:<2} | yield = {syst:.2f} ({sign}{diff:.2f}%){RESET}")

        print(DIM+"-"*50+RESET)

    tfile.Close()
    print(f">> File created: {YELLOW}{outfile}{RESET}")

## Execution
if __name__ == "__main__": main()
