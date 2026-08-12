#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# This script makesillustrative representation of the asymptotic CLs procedure
# used by CMS Combine for setting upper limits.
#
# The script produces:
#   1. Test-statistic distributions for the signal+background and
#      background-only hypotheses, with the observed test statistic and
#      corresponding p-values.
#   2. A CLs scan as a function of the tested signal strength r, showing
#      the corresponding upper limits at different confidence levels.
#
# What to tweak:
#   - mean_sb_nominal, std_sb : Signal+background test-statistic distribution.
#   - mean_b, std_b           : Background-only test-statistic distribution.
#   - q_obs                   : Observed test statistic.
#   - cls_thresholds          : CLs thresholds used to determine limits.
#   - r_scan                  : Range and granularity of the r-scan.
#   - Plot ranges, labels, and output filenames can be modified in the
#     plotting functions if needed.
# -----------------------------------------------------------------------------

import matplotlib
matplotlib.use('Agg')  # Fixes WSL/no-display errors
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

def main():
    ## This illustration reflects the asymptotic CLs procedure used in combine.
    ## When setting upper limits, the tested hypothesis H0 is signal+background.
    ## Under H0, the profile likelihood ratio test statistic q_mu peaks at 0.
    ## The alternative hypothesis H1 is background-only, which peaks at higher q_mu.
    
    mean_sb_nominal, std_sb = 0.0, 1.0  ## signal+background (H0): peaks at 0
    mean_b, std_b = 2.5, 1.0            ## background-only (H1): peaks at high q
    q_obs = 2.0                         ## observed test statistic
    
    cls_thresholds = [0.10, 0.05, 0.01]
    r_scan = np.linspace(0, 3.0, 500)

    setup_cms_style()
    plot_distributions(mean_b, mean_sb_nominal, std_b, std_sb, q_obs)
    plot_cls_scan(mean_b, mean_sb_nominal, std_b, std_sb, q_obs, cls_thresholds, r_scan)

# -----------------
# Style & Plotting
# -----------------

def setup_cms_style():
    plt.rcParams['figure.figsize'] = (7.0, 6.5)
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    plt.rcParams['xtick.top'] = True
    plt.rcParams['ytick.right'] = True
    plt.rcParams['axes.linewidth'] = 1.2
    plt.rcParams['font.size'] = 12
    plt.rcParams['legend.frameon'] = True
    plt.rcParams['legend.facecolor'] = 'white'
    plt.rcParams['legend.framealpha'] = 1.0
    plt.rcParams['legend.edgecolor'] = 'white'

def plot_distributions(m_b, m_sb_nom, std_b, std_sb, q_obs):

    fig, ax = plt.subplots()
    xmin, xmax = -3.5, 6.6
    q = np.linspace(xmin, xmax, 500)
    pdf_b = norm.pdf(q, loc=m_b, scale=std_b)
    pdf_sb = norm.pdf(q, loc=m_sb_nom, scale=std_sb)
    ## p_sb and p_b are BOTH right tails
    p_sb = 1.0 - norm.cdf(q_obs, loc=m_sb_nom, scale=std_sb)
    p_b = 1.0 - norm.cdf(q_obs, loc=m_b, scale=std_b)
    ## CLs divides by (1 - p_b)
    cls_nominal = p_sb / (1.0 - p_b)
    
    ax.plot(q, pdf_b,  color='tab:blue', ls='-', lw=2, label=r'Background-only, $f(q_{\mu}\,|\,b)$')
    ax.plot(q, pdf_sb, color='tab:red',  ls='--',lw=2, label=r'Signal+background, $f(q_{\mu}\,|\,s{+}b)$')
    ax.axvline(q_obs,  color='black',    ls=':', lw=2, label=fr'Observed $q_{{\mu}}^{{\mathrm{{obs}}}} = {q_obs:.2f}$')
    #ax.axvline(m_b,     color='tab:blue',ls=':', lw=1, alpha=0.5)
    #ax.axvline(m_sb_nom, color='tab:red',ls=':', lw=1, alpha=0.5)
    q_shade_sb = np.linspace(q_obs, 5.5, 200)
    ax.fill_between(q_shade_sb, norm.pdf(q_shade_sb, loc=m_sb_nom, scale=std_sb),
                    color='tab:red', alpha=0.3, label=fr'$p_{{s+b}} = {p_sb:.3f}$')
    q_shade_b = np.linspace(q_obs, 5.5, 200)
    ax.fill_between(q_shade_b, norm.pdf(q_shade_b, loc=m_b, scale=std_b),
                    color='tab:blue', alpha=0.3, label=fr'$p_b = {p_b:.3f}$')
    ax.text(0.02, 0.97,
            fr'$\mathrm{{CL}}_s = p_{{s+b}}/(1-p_b) = {cls_nominal:.3f}$',
            transform=ax.transAxes, va='top', ha='left', fontsize=11,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.85, edgecolor='white'))

    ax.set_ylim(0, 0.55)
    ax.set_xlim(xmin, xmax)
    ax.set_xlabel(r'Test statistic $q_{\mu}$ (higher $\to$ background-like)')
    ax.set_ylabel('Probability density')
    ax.legend(loc='upper right', fontsize=9)
    plt.tight_layout()
    plt.savefig('test_statistic.png', dpi=300)

def plot_cls_scan(m_b, m_sb_nom, std_b, std_sb, q_obs, thr_list, r_vals):

    ## Scan CL_s(r) over the tested signal strength r.
    p_b = 1.0 - norm.cdf(q_obs, loc=m_b, scale=std_b)
    mean_at_r = m_b + r_vals * (m_sb_nom - m_b)
    p_sb = 1.0 - norm.cdf(q_obs, loc=mean_at_r, scale=std_sb)
    CLs = p_sb / (1.0 - p_b)

    fig, ax = plt.subplots()
    ax.plot(r_vals, CLs, color='black', lw=2.0, label=r'$\mathrm{CL}_s(r)$')
    #ax.axhline(1.0, color='0.6', lw=1, ls='-')
    #ax.axvline(1.0, color='0.4', lw=1.2, ls='-.', label='Nominal signal ($r=1$)')

    colors = ['tab:green', 'black', 'tab:red']
    r_limits = {}
    
    for i, thr in enumerate(thr_list):
        r_lim = np.interp(thr, CLs[::-1], r_vals[::-1])
        r_limits[thr] = r_lim
        cl_pct = int(round((1 - thr) * 100))
        r_label = rf'{cl_pct}% CL: $r^{{{cl_pct}\%}}_{{\mathrm{{limit}}}} = {r_lim:.2f}$'
        ax.axhline(thr, color=colors[i], ls='--', lw=1.3, alpha=0.7)
        ax.scatter([r_lim], [thr], color=colors[i], zorder=5, label=r_label)
        ax.axvline(r_lim, color=colors[i], ls=':', lw=1, alpha=0.5)

    ax.axvspan(r_limits[0.05], r_vals[-1], color='gray', alpha=0.15,
               label=fr'Excluded at 95\% CL ($r > {r_limits[0.05]:.2f}$)'.replace(r'\%', '%'))

    ax.set_ylim(0, 0.5)
    ax.set_xlim(0, 3.0)
    ax.set_xlabel(r'Tested signal strength $r$')
    ax.set_ylabel(r'$\mathrm{CL}_s$')
    ax.legend(loc='upper right', fontsize=9.5)
    plt.tight_layout()
    plt.savefig('cls_limits.png', dpi=300)

if __name__ == "__main__": main()
