#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# This script reads a JSON yield file and produces the corresponding plots in
# standard CMS style using the cmstyle package.
#
# Usage:
#   python3 makePlot.py --infile <input.json> [options]
#
# Options:
#   --infile <input.json>   Path to the JSON yield file.
#   --save                  Save the plots to disk.
#   --ratio                 Include a Data/Background ratio panel.
#   --noleg                 Suppress the plot legend.
#
# Example usage:
#
#   python3 makePlot.py --infile level2_ShapeAnalysis/yields/yield_203.json
#   python3 makePlot.py --infile level2_ShapeAnalysis/yields/yield_203.json --save --ratio
#
# -----------------------------------------------------------------------------

import argparse
import json
import os
import ROOT
from array import array
import cmsstyle

# --------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Make stacked histogram plots from JSON nominal yields.")
    parser.add_argument("--infile", required=True,            help="Path to input JSON file.")
    parser.add_argument("--save",   action="store_true",      help="Save as PNG in the same directory as the JSON.")
    parser.add_argument("--ratio",  action="store_true",      help="Include a ratio pad (defaults to False).")
    parser.add_argument("--noleg",  action="store_true",      help="Does not include a legend (defaults to False).")
    parser.add_argument("--run",    type=str,   default=None, help="Run label (example: 'Run 2').")
    parser.add_argument("--lumi",   type=float, default=None, help="Integrated luminosity in fb^-1 (example: 138.0).")
    parser.add_argument("--energy", type=float, default=None, help="Center of mass energy in TeV (example: 13.0).")
    args = parser.parse_args()
    
    ROOT.gROOT.SetBatch(args.save)
    ROOT.TH1.AddDirectory(False) ## Prevent garbage collection issues

    ## Load JSON data
    with open(args.infile, 'r') as f: data = json.load(f)
    decorations = {
        "dy":    {"color": "#bd1f01", "displayname": "DY"},
        "qcd":   {"color": "#ffa90e", "displayname": "QCD"},
        "ttbar": {"color": "#3f90da", "displayname": "t#bar{t}+X"},
        "st":    {"color": "#92dadd", "displayname": "Single t"},
        "vv":    {"color": "#e76300", "displayname": "VV"},
        "vvv":   {"color": "#a96b59", "displayname": "VVV"},
        "higgs": {"color": "#832db6", "displayname": "Higgs"},
        "wjets": {"color": "#94a4a2", "displayname": "W+jets/#gamma"},
        "rare":  {"color": "#b9ac70", "displayname": "Rare"}
    }
    filename_base = os.path.splitext(os.path.basename(args.infile))[0]
    outdir = os.path.dirname(os.path.abspath(args.infile))

    ## Iterate through all Signal Regions in the JSON
    for sr_name, sr_data in data.items():
        if "bin_edges" not in sr_data or "processes" not in sr_data:
            print(f"Skipping key {sr_name}, does not appear to be a valid region.")
            continue

        bin_edges = sr_data["bin_edges"]
        processes = sr_data["processes"]
        bins = array('d', bin_edges)
        num_bins = len(bins) - 1
        h_data = None
        h_sig = None
        bkgs = {}
        
        ## Append sr_name to TH1 names to ensure they are unique across the loop
        h_tot = ROOT.TH1D(f"total_bkg_{sr_name}", "total_bkg", num_bins, bins)

        for proc_name, proc_data in processes.items():
            yields = proc_data["yields"]
            errors = proc_data["errors"]

            h = ROOT.TH1D(f"{proc_name}_{sr_name}", proc_name, num_bins, bins)
            for i, (y, e) in enumerate(zip(yields, errors)):
                h.SetBinContent(i + 1, y)
                h.SetBinError(i + 1, e)

            signame = ""
            if proc_name == "data_obs":       h_data = h
            elif proc_name.startswith("vll"): h_sig, signame = h, proc_name
            else:
                bkgs[proc_name] = h
                h_tot.Add(h)

        ## Construct PLOTDICT dictionary to interface with plotting function
        plotdict = {
            "sr_name": sr_name,
            "unblind": (h_data is not None),
            "lumi": args.lumi,
            "run": args.run,
            "energy": args.energy,
            "name": f"{filename_base}_{sr_name}",
            "bkgs": bkgs,
            "total_bkg": h_tot,
            "data": h_data,
            "signals": {signame: h_sig} if h_sig else {},
            "sig_configs": {
                signame: {"color": ROOT.kRed, "label": "Signal"}
            } if h_sig else {}
        }

        ## Generate Plot for this SR
        make_one_plot_from_plotdict(
            plotdict,
            decorations,
            outdir=outdir,
            do_legend=not args.noleg,
            do_ratio=args.ratio,
            do_save=args.save
        )

# --------------------------------------------------------
# Core Plotting Function
# --------------------------------------------------------
def make_one_plot_from_plotdict(plotdict, mc_cfg, outdir,  do_ratio, do_legend, do_save, do_log=False):

    global _extra_text_objects     
    sr_name = plotdict.get("sr_name", "SR")
    unblind = plotdict["unblind"]
    lumi    = plotdict.get("lumi", None)
    run     = plotdict.get("run", None)
    energy  = plotdict.get("energy", None)
    
    cmsstyle.setCMSStyle()
    cmsstyle.SetLumi(-1, run="")
    cmsstyle.SetEnergy(0, unit="")
    if lumi and run: cmsstyle.SetLumi(lumi, run=run)
    if energy:       cmsstyle.SetEnergy(energy)
    cmsstyle.SetExtraText("" if unblind else "Simulation")

    ## Read backgrounds
    bkgs, colors, labels = [], [], []
    for proc, cfg in mc_cfg.items():
        if proc in plotdict["bkgs"]:
            h_bkg = plotdict["bkgs"][proc]
            h_bkg.SetLineColor(ROOT.kBlack)
            h_bkg.SetLineWidth(0)
            bkgs.append(h_bkg)
            colors.append(ROOT.TColor.GetColor(cfg["color"]))
            labels.append(cfg["displayname"])

    if not bkgs: 
        print(f"No backgrounds found to plot for {plotdict['name']}.")
        return

    ## Sort stacks by integral
    items = list(zip(bkgs, colors, labels))
    items.sort(key=lambda x: x[0].Integral())
    bkgs, colors, labels = map(list, zip(*items))

    ## Total Background setup
    h_tot = plotdict["total_bkg"]
    h_tot.SetFillStyle(3345)
    h_tot.SetFillColor(12)
    h_tot.SetLineColor(ROOT.kBlack)
    h_tot.SetLineWidth(1)
    h_tot.SetMarkerSize(0)
    hs = cmsstyle.buildTHStack(bkgs, colors)

    ## Read data with Garwood Poisson errors
    h_data = plotdict.get("data")
    data_integral = 0
    if unblind and h_data:
        h_data.Sumw2(False)
        h_data.SetBinErrorOption(ROOT.TH1.kPoisson)
        h_data.SetMarkerStyle(ROOT.kFullCircle)
        h_data.SetMarkerSize(1.1)
        h_data.SetMarkerColor(ROOT.kBlack)
        h_data.SetLineColor(ROOT.kBlack)
        data_integral = h_data.Integral()

    ## Read and style merged signals
    sig_hists, sig_labels = [], []
    for i, (proc, h_sig) in enumerate(plotdict.get("signals", {}).items()):
        cfg = plotdict["sig_configs"][proc]
        h_sig.SetLineColor(cfg["color"])
        h_sig.SetLineStyle((i % 4) + 1)
        h_sig.SetLineWidth(2)
        h_sig.SetFillStyle(0)
        sig_hists.append(h_sig)
        sig_labels.append(cfg["label"])

    ## Prepare Canvas Scaling
    XTITLE = "Discriminating variable"
    ymax = h_tot.GetMaximum()
    if h_data: ymax = max(ymax, h_data.GetMaximum())
    ymax *= (1e5 if do_ratio else 1e6) if do_log else (2.0 if do_ratio else 1.4)
    ymin = 0.08 if do_log else 0.0

    if do_ratio:
        h_ratio_bkg, g_ratio_data = None, None
        yratiotitle = "Data / Bkg"

        if unblind and h_data:
            g_ratio_data = ROOT.TGraphAsymmErrors()
            pt_idx = 0
            for i in range(1, h_data.GetNbinsX() + 1):
                x = h_data.GetBinCenter(i)
                y = h_data.GetBinContent(i)
                if y == 0: continue ## Suppress zeroes

                ey_low  = h_data.GetBinErrorLow(i)
                ey_high = h_data.GetBinErrorUp(i)
                ex = h_data.GetBinWidth(i) / 2.0
                bkg_val = h_tot.GetBinContent(i)

                if bkg_val > 0:
                    g_ratio_data.SetPoint(pt_idx, x, y / bkg_val)
                    g_ratio_data.SetPointError(pt_idx, ex, ex, ey_low / bkg_val, ey_high / bkg_val)
                    pt_idx += 1

            g_ratio_data.SetMarkerStyle(20)
            g_ratio_data.SetMarkerSize(0.9)
            g_ratio_data.SetLineColor(ROOT.kBlack)
            g_ratio_data.SetMarkerColor(ROOT.kBlack)

        elif sig_hists:
            h_sig = sig_hists[0]
            h_sqrtB = h_tot.Clone("sqrtB")
            for i in range(1, h_sqrtB.GetNbinsX()+1):
                B = h_sqrtB.GetBinContent(i)
                err = h_sqrtB.GetBinError(i)
                if B > 0:
                    sqrt_B = B**0.5
                    h_sqrtB.SetBinContent(i, sqrt_B)
                    h_sqrtB.SetBinError(i, err / (2 * sqrt_B))
                else:
                    h_sqrtB.SetBinContent(i, 0)
                    h_sqrtB.SetBinError(i, 0)

            h_ratio_bkg = h_sig.Clone("s_over_sqrtb")
            h_ratio_bkg.Divide(h_sqrtB)
            h_ratio_bkg.SetLineColor(ROOT.kBlack)
            h_ratio_bkg.SetMarkerStyle(20)
            h_ratio_bkg.SetMarkerSize(0.9)
            yratiotitle = "S/#sqrt{B}"

        ymin_r = 0.0
        ymax_r = 2.0 if unblind else max(0.2, (h_ratio_bkg.GetMaximum()*1.2) if h_ratio_bkg else 2.0)
        c = cmsstyle.cmsDiCanvas(
            plotdict["name"], h_tot.GetXaxis().GetXmin(), h_tot.GetXaxis().GetXmax(),
            ymin, ymax, ymin_r, ymax_r, XTITLE, "Events / bin", yratiotitle
        )
        c.cd(1)
    else:
        c = cmsstyle.cmsCanvas(
            plotdict["name"], h_tot.GetXaxis().GetXmin(), h_tot.GetXaxis().GetXmax(),
            ymin, ymax, XTITLE, "Events / bin"
        )
    if do_log: ROOT.gPad.SetLogy()

    ## Text on top
    val, err = None, None
    label = ""
    if unblind and h_data:
        val, err = compute_data_over_bkg(h_data, h_tot)
        label = "Data / Bkg"
    elif not unblind and sig_hists:
        val, err = compute_s_over_sqrtb(sig_hists[0], h_tot)
        label = "S / #sqrt{B}"
        
    if val is not None:
        summary_txt = f"{label} = {val:.3f}"
        draw_extra_text(summary_txt, c, x=0.15, y=0.94, size=0.035)
    cmsstyle.UpdatePad(c)

    ## Draw Main Pad
    cmsstyle.cmsObjectDraw(hs, "HIST")
    cmsstyle.cmsObjectDraw(h_tot, "E2")
    h_tot_line = h_tot.Clone("h_tot_line")
    h_tot_line.SetFillStyle(0)
    cmsstyle.cmsObjectDraw(h_tot_line, "HIST SAME")
    if h_data: cmsstyle.cmsObjectDraw(h_data, "E0")
    for h in sig_hists: cmsstyle.cmsObjectDraw(h, "HIST SAME")

    ## Legend
    if do_legend:
        legpos, legsize = ((0.57, 0.65, 0.92, 0.88), 0.030) if do_ratio else ((0.52, 0.68, 0.92, 0.90), 0.026)
        leg = cmsstyle.cmsLeg(legpos[0], legpos[1], legpos[2], legpos[3], textSize=legsize, columns=2)
        if h_data: cmsstyle.addToLegend(leg, (h_data, f"Data ({int(data_integral)})", "pe"))
        for h, lbl in reversed(list(zip(bkgs, labels))): cmsstyle.addToLegend(leg, (h, f"{lbl} ({int(h.Integral())})", "f"))
        cmsstyle.addToLegend(leg, (h_tot, "Unc. (stat)", "f"))
        for h, lbl in zip(sig_hists, sig_labels): cmsstyle.addToLegend(leg, (h, f"{lbl} ({int(h.Integral())})", "l"))
        leg.Draw()

    evt_text = f"{sr_name}"
    if do_ratio: y_evt = 0.79 if unblind else 0.73
    else:        y_evt = 0.81 if unblind else 0.75
    draw_extra_text(evt_text, c, x=0.18, y=y_evt, size=0.04)

    ## Draw Ratio Pad
    if do_ratio:
        c.cd(2)
        if unblind and g_ratio_data:
            h_band = h_tot.Clone(f"ratio_band_{plotdict['name']}")
            h_band.SetDirectory(0)
            for i in range(1, h_band.GetNbinsX() + 1):
                B   = h_tot.GetBinContent(i)
                err = h_tot.GetBinError(i)
                h_band.SetBinContent(i, 1.0)
                if B > 0: h_band.SetBinError(i, err / B)
                else:     h_band.SetBinError(i, 0.0)
                
            cmsstyle.cmsObjectDraw(h_band, "E2")

            x_min = h_tot.GetXaxis().GetXmin()
            x_max = h_tot.GetXaxis().GetXmax()
            line = ROOT.TLine(x_min, 1.0, x_max, 1.0)
            line.SetLineStyle(2)
            line.SetLineWidth(1)
            line.Draw()
            cmsstyle.cmsObjectDraw(g_ratio_data, "PZ0")

        elif h_ratio_bkg:
            h_ratio_bkg.SetLineStyle(1)
            cmsstyle.cmsObjectDraw(h_ratio_bkg, "PE")

        cmsstyle.UpdatePad(c)
    cmsstyle.UpdatePad(c)

    ## Save logic
    if not do_save:
        ROOT.gROOT.SetBatch(False)
        c.Draw()
        input("Press Enter to continue to next plot...")
    else:
        filename = os.path.join(outdir, f"{plotdict['name']}.png").replace(" ", "_")
        c.SaveAs(filename)
        print(f">> File created: {filename}")

    _extra_text_objects.clear()

# --------------------------------------------------------
# Utilities
# --------------------------------------------------------
_extra_text_objects = []

def draw_extra_text(text, c, x=0.18, y=0.72, size=0.035):
    if not text.startswith("#font[42]{"): text = f"#font[42]{{{text}}}"
    extraLabel = ROOT.TLatex(x, y, text)
    extraLabel.SetNDC()
    extraLabel.SetTextFont(42)
    extraLabel.SetTextSize(size)
    cmsstyle.cmsObjectDraw(extraLabel)
    _extra_text_objects.append(extraLabel)

def compute_data_over_bkg(h_data, h_tot):
    d_sum = 0.0
    b_sum = 0.0
    for i in range(1, h_data.GetNbinsX() + 1):
        d = h_data.GetBinContent(i)
        b = h_tot.GetBinContent(i)
        if b > 0:
            d_sum += d
            b_sum += b
    return (d_sum / b_sum) if b_sum > 0 else 0.0, 0.0

def compute_s_over_sqrtb(h_sig, h_tot):
    S = h_sig.Integral()
    B = h_tot.Integral()
    return (S / (B**0.5)) if B > 0 else 0.0, 0.0

# --------------------------------------------------------
if __name__ == "__main__": main()
