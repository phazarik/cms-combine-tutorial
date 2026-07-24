#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Converts JSON files containing yield data and uncertainties into ROOT 
# histogram (shape) files for statistical analysis.
#
# Input format required: 
#   JSON file(s) containing yield and error arrays per bin. The JSON schema 
#   must include 'bin_edges' and 'processes' at the top level for each region,
#   and 'yields' and 'errors' arrays for each individual process.
#
# Output: 
#   ROOT file(s) (.root) containing TH1F histograms (named as <Region>_<Process>) 
#   saved in the 'shapes/' directory.
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

        pname_width_max = max(len(p) for p in proc_ordered) if proc_ordered else 0
        print(DIM + "-" * 50 + RESET) ## debug
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
            # Histogram naming convention: <SRname>_<proc>
            # -------------------------------------------
            hname = f"{region_name}_{p}"
            h = ROOT.TH1F(hname, hname, nbins, edges)
            h.Sumw2() ## Later, use Poisson error for data

            for i in range(nbins):
                val = float(content["yields"][i])
                err = float(content["errors"][i])
                h.SetBinContent(i + 1, val)
                h.SetBinError(i + 1, err)

                ## debug
                print(f"{DIM} {p:<{pname_width_max}} | bin {i+1:<2} | "
                      f"yield = {val:.2f} \u00b1 {err:.2f}{RESET}")
            h.Write()
        print(DIM+"-"*50+RESET)

    tfile.Close()
    print(f">> File created: {YELLOW}{outfile}{RESET}")

## Execution
if __name__ == "__main__": main()
