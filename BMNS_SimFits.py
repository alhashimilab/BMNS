import os, sys
import numpy as np
import pandas as pd
import itertools as it
import BMNS_Errors as bme
import BMNS_SimR1p as sim
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib as mpl
from matplotlib.backends.backend_pdf import PdfPages

#########################################################################
# BMNS_SimFits : Simulates R1rho fit curves given parameters
#########################################################################
class SimFit:
  def __init__(self):
    # o R1rho array
    # -- 0 Offset (Hz)
    # -- 1 SLP (Hz)
    # -- 2 R1rho
    # -- 3 R1rho error
    # -- 4 R2eff
    # -- 5 R2eff_err
    # -- 6 Preexponential
    self.R1pV = []

    # o Mag Sim array
    # -- 0  Peff : effective mag proj along avg effective
    # -- 1  Peff_err : err from corruption of Peff
    # -- 2  PeffA : mag proj along A-state effective
    # -- 3  PeffB : mag proj along B-state effective
    # -- 4  PeffC : mag proj along C-state effective
    # -- 5  Mxa : x-comp of A-state at time t
    # -- 6  Mya : y-comp of A-state at time t
    # -- 7  Mza : z-comp of A-state at time t
    # -- 8  Mxb : x-comp of B-state at time t
    # -- 9  Myb : y-comp of B-state at time t
    # -- 10 Mzb : z-comp of B-state at time t
    # -- 11 Mxc : x-comp of C-state at time t
    # -- 12 Myc : y-comp of C-state at time t
    # -- 13 Mzc : z-comp of C-state at time t
    # -- 14 time
    self.magVecs = []

    # o Eigenvalue array
    # -- 0  offset Hz
    # -- 1  SLP Hz
    # -- 2  w1-ax : eigenval 1 of state A, x-comp
    # -- 3  w2-ay : eigenval 2 of state A, y-comp
    # -- 4  w3-az : eigenval 3 of state A, z-comp
    # -- 5  w4-bx : eigenval 1 of state B, x-comp
    # -- 6  w5-by : eigenval 2 of state B, y-comp
    # -- 7  w6-bz : eigenval 3 of state B, z-comp
    # -- 8  w7-cx : eigenval 1 of state C, x-comp
    # -- 9  w8-cy : eigenval 2 of state C, y-comp
    # -- 10 w9-cz : eigenval 3 of state C, z-comp
    self.eigVals = []
    # Current directory
    self.curDir = os.getcwd()
    # -- Simulation SLPs and Offsets numpy array -- #
    # Col0 = Offsets
    # Col1 = SLPs
    self.sloff = None
    self.slon = None
    self.slonoff = None
    self.rhoerr = 0.0 # Noise corruption pct for R1p values
    self.rhomc = 500  # Number of monte carlo iterations for noise corruption

    # -- Simulation Decaying Intensity values -- #
    self.vdlist = np.linspace(0.0, 0.25, 51)
    self.decerr = 0.0 # Noise corruption pct for intensities
    self.decmc = 500  # Number of monte carlo iterations for noise corruption

    # -- Plotting variables and their attributes -- #
    self.pltvar = {
      "plot" : "line", # Plot type - symbol or lines or both
      "line" : ["-", 1.5], # Line type
      "symbol" : ["o", 10], # Symbol type
      "r1p_x" : [None, None], # Lower, upper limits of x-dimension R1p
      "r1p_y" : [None, None], # Lower, upper limits of y-dimension R1p
      "r2eff_x" : [None, None], # Lower, upper limits of x-dimension R2eff
      "r2eff_y" : [None, None], # Lower, upper limits of y-dimension R2eff
      "on_x" : [None, None], # Lower, upper limits of x-dimension OnRes
      "on_y" : [None, None], # Lower, upper limits of y-dimension OnRes
      "size" : [None, None], # Size of plots
      "axis_fs" : [16, 16], # Plots axes font size
      "label_fs" : [18, 18] # Label axes font size
      }
    # -- BM Parameter variables and their values -- #
    self.fitpars = {
      "lf" : 0.0, # MHz
      "alignmag" : "auto", # Mag alignment
      "te" : 0.0, # Kelvin
      "pa" : 0.0, # Probability
      "pb" : 0.0, # Probability
      "pc" : 0.0, # Probability
      "dwb" : 0.0, # ppm
      "dwc" : 0.0, # ppm
      "kexab" : 0.0,
      "kexac" : 0.0,
      "kexbc" : 0.0,
      "k12" : 0.0,
      "k21" : 0.0,
      "k13" : 0.0,
      "k31" : 0.0,
      "k23" : 0.0,
      "k32" : 0.0,
      "r1" : 0.0,
      "r2" : 0.0,
      "r1b" : 0.0,
      "r2b" : 0.0,
      "r1c" : 0.0,
      "r2c" : 0.0
    }

  #########################################################################
  # simFit - Simulates R1rho values at self-given SLPs/offsets using
  #          self-given parameters
  #########################################################################
  def simFit(self):
    # Simulate R1p, R2eff, vectors, eigenvalues, etc at different SLP offsets
    for of, sl in zip(self.slonoff[:,0], self.slonoff[:,1]):
      a, b, c = sim.BMSim(self.fitpars, -of, sl, self.vdlist, self.decerr, self.decmc,
                          self.rhoerr, self.rhomc)
      self.R1pV.append(a)
      self.magVecs.append(b)
      self.eigVals.append(c)
    # Convert all lists to numpy arrays
    self.R1pV = np.asarray(self.R1pV)
    self.R1pV = np.append(self.slonoff, self.R1pV, axis=1)
    self.magVecs = np.asarray(self.magVecs).astype(np.float64)
    self.eigVals = np.asarray(self.eigVals).astype(np.float64)

  #########################################################################
  # plotR1p - Writes out R1rho values
  #########################################################################
  def writeR1p(self, outp):
    outR1p = os.path.join(outp, "sim-r1p.csv")
    r1phdr = "offset,slp,r1p,r1p_err,r2eff,r2eff_err,prexp"
    np.savetxt(outR1p, self.R1pV, delimiter=',', header=r1phdr, comments='')

  #########################################################################
  # plotR1p - Writes out magnetization vectors and eigenvalues
  #########################################################################
  def writeVecVal(self, outvec, outev):
    hdr = "Peff,Peff_err,PeffA,PeffB,PeffC,Mxa,Mya,Mza,Mxb,Myb,Mzb,Mxc,Myc,Mzc,time"
    # Write out magnetization vectors
    for n,i in zip(self.R1pV, self.magVecs):
      of, sl = n[0], n[1]
      magp = os.path.join(outvec, "%s_%s.csv" % (of, sl))
      np.savetxt(magp, i, delimiter=',', header=hdr, comments='')

    eigvp = os.path.join(outev, "sim-eigenvalues.csv")
    hdr = "offset,slp,w1,w2,w3,w4,w5,w6,w7,w8,w9"
    np.savetxt(eigvp, self.eigVals, delimiter=',', header=hdr, comments='')

  #########################################################################
  # plotDec - Plots monoexponential decays
  #########################################################################
  def plotDec(self, figp):
    # output path
    figp = os.path.join(figp, "sim-decaycurves.pdf")
    # Define PDFPages object for multipage decay plots
    pp = PdfPages(figp)

    for n, d in zip(self.R1pV, self.magVecs):
      # Values of R1p/R1rho_err for sim fit line and title
      A, R1p, R1p_err = n[6], n[2], n[3]
      of, sl = n[0], n[1]
      # -- Define figure -- #
      fig = plt.figure()
      plt.errorbar(d[:,14], d[:,0], yerr=d[:,1], fmt='o')
      # Simulate x-values for plotting trendline
      if 101 < len(d[:,14]):
        simX = np.linspace(d[:,14].min(), d[:,14].max(), 51)
      else:
        simX = d[:,14]
      # Plot simulated trend-line
      plt.plot(simX, sim.ExpDecay(simX, A, R1p), c='red')
      # Define plot limits
      plt.xlim(0.0, d[:,14].max()*1.05)
      plt.ylim(0.0, 1.1)
      # # -- Set a title -- #
      plt.title(r'$R_{1\rho}=%0.1f\pm%0.1f\,s^{-1}\quad\omega_1=%0.0f\,Hz\quad\Omega_{eff}=%0.0f\,Hz$'
                % (R1p, R1p_err, sl, of), size=16)
      # -- Set axes labels -- #
      plt.xlabel(r'$Seconds$', size=self.pltvar['label_fs'][0])
      plt.ylabel(r'$Intensity$', size=self.pltvar['label_fs'][1])
      # -- Set axes font sizes -- #
      rcParams.update({'font.size': self.pltvar['axis_fs'][0]})
      pp.savefig()
      plt.close(fig)
      plt.clf()

    pp.close()
  #########################################################################
  # plotR1p - Plots R1rho values
  #########################################################################
  def plotR1p(self, figp):
    # Find unique SLPs for on/off-res
    if self.sloff is not None:
      uoffslp = sorted(list(set(self.sloff[:,1])))

    mpl.rcParams['pdf.fonttype'] = 42
    mpl.rcParams['font.sans-serif'] = 'arial'
    # # Remove onres values from self.R1pV array
    # offv = self.R1pV[self.R1pV[:,0] != 0.]
    # Sort array of R1rho/R2eff values by offset
    #  This is needed to remove plotting artifacts
    offv = self.R1pV[self.R1pV[:,0].argsort()]
    # Split (N, 7) array in to a (M, N, 7) array, where
    #  M = unique offsets
    offv = np.array([offv[offv[:,1] == x] for x in uoffslp])
    ##### Start decorating plot #####
    # -- Define figure -- #
    fig = plt.figure(figsize=(self.pltvar['size'][0], self.pltvar['size'][1]),
                     dpi=60)
    # -- Define Colormap -- #
    colormap = plt.cm.jet
    plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 1, offv.shape[0])])

    # -- Start plotting -- #
    for n in offv:
      of = n[:,0]/1e3
      if self.pltvar['plot'] == "symbol":
        plt.errorbar(of, n[:,2], yerr=n[:,3], fmt=self.pltvar['symbol'][0],
                 markersize=self.pltvar['symbol'][1], label=int(n[2][1]))
      elif self.pltvar['plot'] == "line":
        plt.plot(of, n[:,2], self.pltvar['line'][0],
                 linewidth=self.pltvar['line'][1], label=int(n[2][1]))
      elif self.pltvar['plot'] == "both":
        plot = plt.errorbar(of, n[:,2], yerr=n[:,3], fmt=self.pltvar['symbol'][0],
                 markersize=self.pltvar['symbol'][1], label=int(n[2][1]))
        plt.plot(of, n[:,2], self.pltvar['line'][0],
                 linewidth=self.pltvar['line'][1], c=plot[0].get_color())
    ##### Start decorating plot #####
    # # -- Set a title -- #
    # plt.title(r'$R_{1\rho}$', size=18)
    # -- Set legends -- #
    legend = plt.legend(title=r'$\omega\,2\pi^{-1}\,{(Hz)}$', numpoints=1, fancybox=True)
    plt.setp(legend.get_title(), fontsize=self.pltvar['axis_fs'][1])
    # -- Set axes labels -- #
    plt.xlabel(r'$\Omega\,2\pi^{-1}\,{(kHz)}$', size=self.pltvar['label_fs'][0])
    plt.ylabel(r'$R_{1\rho}\,(s^{-1})$', size=self.pltvar['label_fs'][1])
    # -- Set axes font sizes -- #
    rcParams.update({'font.size': self.pltvar['axis_fs'][0]})
    # -- Set X-axes limits -- #
    if self.pltvar['r1p_x'][0] is None:
      xmin = self.R1pV[:,0].min() * 1.05
    else:
      xmin = self.pltvar['r1p_x'][0]
    if self.pltvar['r1p_x'][1] is None:
      xmax = self.R1pV[:,0].max() * 1.05
    else:
      xmax = self.pltvar['r1p_x'][1]    
    plt.xlim(xmin/1e3, xmax/1e3)
    # -- Set Y-axes limits -- #
    if self.pltvar['r1p_y'][0] is None:
      ymin = 0.0
    else:
      ymin = self.pltvar['r1p_y'][0]
    if self.pltvar['r1p_y'][1] is None:
      ymax = self.R1pV[:,2].max() * 1.05
    else:
      ymax = self.pltvar['r1p_y'][1]    
    plt.ylim(ymin, ymax)
    # -- Write out figure -- #
    figp = os.path.join(figp, "sim-R1rho-OffRes.pdf")
    plt.savefig(figp, transparent=True)
    plt.close(fig)
    plt.clf()

  #########################################################################
  # plotR2eff - Plots R1rho values
  #########################################################################
  def plotR2eff(self, figp):
    # Find unique SLPs for on/off-res
    if self.sloff is not None:
      uoffslp = sorted(list(set(self.sloff[:,1])))

    mpl.rcParams['pdf.fonttype'] = 42
    mpl.rcParams['font.sans-serif'] = 'arial'
    # # Remove onres values from self.R1pV array
    # offv = self.R1pV[self.R1pV[:,0] != 0.]
    # Sort array of R1rho/R2eff values by offset
    #  This is needed to remove plotting artifacts
    offv = self.R1pV[self.R1pV[:,0].argsort()]
    # Split (N, 7) array in to a (M, N, 7) array, where
    #  M = unique offsets
    offv = np.array([offv[offv[:,1] == x] for x in uoffslp])

    ##### Start decorating plot #####
    # -- Define figure -- #
    fig = plt.figure(figsize=(self.pltvar['size'][0], self.pltvar['size'][1]),
                     dpi=60)
    # -- Define Colormap -- #
    colormap = plt.cm.jet
    plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 1, offv.shape[0])])

    # -- Start plotting -- #
    for n in offv:
      of = n[:,0]/1e3
      if self.pltvar['plot'] == "symbol":
        plt.errorbar(of, n[:,4], yerr=n[:,5], fmt=self.pltvar['symbol'][0],
                 markersize=self.pltvar['symbol'][1], label=int(n[2][1]))
      elif self.pltvar['plot'] == "line":
        plt.plot(of, n[:,4], self.pltvar['line'][0],
                 linewidth=self.pltvar['line'][1], label=int(n[2][1]))
      elif self.pltvar['plot'] == "both":
        plot = plt.errorbar(of, n[:,4], yerr=n[:,5], fmt=self.pltvar['symbol'][0],
                 markersize=self.pltvar['symbol'][1], label=int(n[2][1]))
        plt.plot(of, n[:,4], self.pltvar['line'][0],
                 linewidth=self.pltvar['line'][1], c=plot[0].get_color())
    ##### Start decorating plot #####
    # # -- Set a title -- #
    # plt.title(r'$R_{1\rho}$', size=18)
    # -- Set legends -- #
    legend = plt.legend(title=r'$\omega\,2\pi^{-1}\,{(Hz)}$', numpoints=1, fancybox=True)
    plt.setp(legend.get_title(), fontsize=self.pltvar['axis_fs'][1])
    # -- Set axes labels -- #
    plt.xlabel(r'$\Omega\,2\pi^{-1}\,{(kHz)}$', size=self.pltvar['label_fs'][0])
    plt.ylabel(r'$R_{2}+R_{ex}\,(s^{-1})$', size=self.pltvar['label_fs'][1])
    # -- Set axes font sizes -- #
    rcParams.update({'font.size': self.pltvar['axis_fs'][0]})
    # -- Set X-axes limits -- #
    if self.pltvar['r2eff_x'][0] is None:
      xmin = self.R1pV[:,0].min() * 1.05
    else:
      xmin = self.pltvar['r2eff_x'][0]
    if self.pltvar['r2eff_x'][1] is None:
      xmax = self.R1pV[:,0].max() * 1.05
    else:
      xmax = self.pltvar['r2eff_x'][1]    
    plt.xlim(xmin/1e3, xmax/1e3)
    # -- Set Y-axes limits -- #
    if self.pltvar['r2eff_y'][0] is None:
      ymin = 0.0
    else:
      ymin = self.pltvar['r2eff_y'][0]
    if self.pltvar['r2eff_y'][1] is None:
      ymax = self.R1pV[:,4].max() * 1.05
    else:
      ymax = self.pltvar['r2eff_y'][1]    
    plt.ylim(ymin, ymax)
    # -- Write out figure -- #
    figp = os.path.join(figp, "sim-R2eff.pdf")
    plt.savefig(figp, transparent=True)
    plt.close(fig)
    plt.clf()

  #########################################################################
  # plotOnRes - Plots R1rho values
  #########################################################################
  def plotOnRes(self, figp):
    # Find unique SLPs for on/off-res
    if self.slon is not None:
      uoffslp = sorted(list(set(self.sloff[:,1])))

    mpl.rcParams['pdf.fonttype'] = 42
    mpl.rcParams['font.sans-serif'] = 'arial'
    # # Remove onres values from self.R1pV array
    # offv = self.R1pV[self.R1pV[:,0] != 0.]
    # Sort array of R1rho/R2eff values by offset
    #  This is needed to remove plotting artifacts
    n = self.R1pV
    n = n[n[:,0] == 0.]
    n = n[n[:,1].argsort()]
    ##### Start decorating plot #####
    # -- Define figure -- #
    fig = plt.figure(figsize=(self.pltvar['size'][0], self.pltvar['size'][1]),
                     dpi=60)
    # -- Define Colormap -- #
    colormap = plt.cm.jet
    plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 1, n.shape[0])])

    # -- Start plotting -- #
    if self.pltvar['plot'] == "symbol":
      plt.errorbar(n[:,1], n[:,2], yerr=n[:,3], fmt=self.pltvar['symbol'][0],
               markersize=self.pltvar['symbol'][1])
    elif self.pltvar['plot'] == "line":
      plt.plot(n[:,1], n[:,2], self.pltvar['line'][0],
               linewidth=self.pltvar['line'][1])
    elif self.pltvar['plot'] == "both":
      plot = plt.errorbar(n[:,1], n[:,2], yerr=n[:,3], fmt=self.pltvar['symbol'][0],
               markersize=self.pltvar['symbol'][1])
      plt.plot(n[:,1], n[:,2], self.pltvar['line'][0],
               linewidth=self.pltvar['line'][1], c=plot[0].get_color())
    ##### Start decorating plot #####
    # -- Set axes labels -- #
    plt.xlabel(r'$\Omega\,2\pi^{-1}\,{(kHz)}$', size=self.pltvar['label_fs'][0])
    plt.ylabel(r'$R_{2}+R_{ex}\,(s^{-1})$', size=self.pltvar['label_fs'][1])
    # -- Set axes font sizes -- #
    rcParams.update({'font.size': self.pltvar['axis_fs'][0]})
    # -- Set X-axes limits -- #
    if self.pltvar['on_x'][0] is None:
      xmin = n[:,1].min() * 1.05
    else:
      xmin = self.pltvar['on_x'][0]
    if self.pltvar['on_x'][1] is None:
      xmax = n[:,1].max() * 1.05
    else:
      xmax = self.pltvar['on_x'][1]    
    plt.xlim(xmin, xmax)
    # -- Set Y-axes limits -- #
    if self.pltvar['on_y'][0] is None:
      ymin = 0.0
    else:
      ymin = self.pltvar['on_y'][0]
    if self.pltvar['on_y'][1] is None:
      ymax = self.R1pV[:,2].max() * 1.05
    else:
      ymax = self.pltvar['on_y'][1]    
    plt.ylim(ymin, ymax)
    # -- Write out figure -- #
    figp = os.path.join(figp, "sim-R1p-OnRes.pdf")
    plt.savefig(figp, transparent=True)
    plt.close(fig)
    plt.clf()

  #########################################################################
  # PreSim - Reads argument command line and checks for all required
  #          parameters and maps them to class values
  #  Input:
  #   - argv with input path
  #  Output:
  #   -
  #########################################################################
  def PreSim(self, argv):
    # Get path to input file
    inpPath = os.path.join(self.curDir, argv[2])
    self.prRawInp(inpPath)

  #########################################################################
  # prRawInp - Parse Raw input file
  #  Input:
  #   - Path to raw input file
  #  Result:
  #   - Assigns parsing jobs to raw input file
  #########################################################################
  def prRawInp(self, inpPath):
    inpRaw = []
    # Open input parameter file
    with open(inpPath, 'r') as f:
        # Split input parameter file by delimiter '+' to lists
        for key,group in it.groupby(f,lambda line: line.startswith('+')):
            if not key:
                inpRaw.append([x.strip().split(" ") for x in group if "#" not in x and len(x) > 0])
    # Iterate over blocks of input parameters in parsed raw input
    # Need to extract the following blocks:
    #  1. SLP's and Offset generation and/or read-in
    #  2. Plot
    #  3. Name
    #  4. (Optional) Decay - Monoexponential decays
    for b in inpRaw:
      # Parse spinlock powers and offsets to be used in the simulation
      if "sloff" in b[0][0].lower():
        self.prSLOff(b)
      # Parse plotting variables
      elif "plot" in b[0][0].lower():
        self.prPlotInp(b)
      # Parse input parameters for BM simulation
      elif "params" in b[0][0].lower():
        self.prParInp(b)
        self.checkFitPars()
      # Parse monoexponential decays, if they exist
      elif "decay" in b[0][0].lower():
        self.prDecay(b)

  #########################################################################
  # prDecay - Parse SL duration values for simulating monoexponential decays
  #  Input:
  #   - Decay pars input block from parsed raw input file (list of lists)
  #     Read-in decay file is just a newline separated text file of decays in sec
  #  Result:
  #   - Assigns decay times and errors to self values
  #########################################################################
  def prDecay(self, pdeb):
    # Loop over monoexponential decay block
    for i in pdeb:
      # Check for decay vdlist
      if i[0].lower() == "read":
        # If read flag is defined as a value as non-false
        if len(i) >= 2:
          readPath = os.path.join(self.curDir, i[1])
          # Check to make sure decay text file, if not exit program.
          if not os.path.isfile(readPath):
            bme.HandleErrors(True, "\nVdlist path is defined but does not exist.\n %s\n" % readPath)
          else:
            # Read text to numpy array
            dec = np.genfromtxt(readPath, dtype=float)
            # Strip nan values
            self.vdlist = dec[~np.isnan(dec)]
      # Get error percentage for noise corruption of decay
      elif i[0].lower() == "error" and len(i) == 2:
        try:
          self.decerr = float(i[1])
        except ValueError:
          bme.HandleErrors(True, "\nNo/bad error percentage defined for decay sim\n")
      # Get error MC num for noise corruption of decay
      elif i[0].lower() == "mcnum" and len(i) == 2:
        try:
          self.decmc = int(i[1])
        except ValueError:
          bme.HandleErrors(True, "\nNo/bad MC num defined for error corruption of decay sim\n")
      # Generate vdlist from lower/upper bounds
      elif i[0].lower() == "vdlist":
        if len(i) == 4:
          # tdecp = self.checkNums(i[1:4])
          minv, maxv, numv = self.checkNums(i[1:4])
          if minv > maxv: minv, maxv = maxv, minv
          # Generate/add to vdlist
          tvd = np.linspace(minv, maxv, numv)
          self.vdlist = tvd

  #########################################################################
  # prParInp - Parse BM parameters input block from raw input and parses it
  #            Maps values (from input csv or text) to dict of BM pars
  #  Input:
  #   - BM pars input block from parsed raw input file (list of lists)
  #  Result:
  #   - Assigns values to all the BM simulation parameters
  #     If defined, a BM fit CSV file is read in in lieu of explicitly
  #     defined variables in the input txt
  #########################################################################
  def prParInp(self, parb):
    readFlag = False
    # Loop over bm input parameter block
    for i in parb:
      # Check for BM fit csv
      if i[0].lower() == "read":
        readFlag = True
        # If read flag is defined as a value as non-false
        if len(i) >= 2 and i[1].lower() != "false":
          readPath = os.path.join(self.curDir, i[1])
          # Check to make sure BM fit csv exists, if not exit program.
          if not os.path.isfile(readPath):
            bme.HandleErrors(True, "\nBM fit path is defined but does not exist.\n %s\n" % readPath)
          else:
            # Read csv file to pandas dataframe
            bf = pd.read_csv(readPath, sep=',')
            # Reassign col headers to lowercase
            bf.columns = [x.lower() for x in bf.columns]
            # Check through input file and find values that
            #  correspond to self.fitpars from the bm fit pandas df
            for v in set(self.fitpars.keys()) & set(bf.columns):
              self.fitpars[v] = bf[v][0]

      elif i[0].lower() in self.fitpars.keys() and len(i) == 2:
        v = i[0].lower()
        # Check to make sure parameter is a value
        #  Assign if it is, except alignmag
        if v != "alignmag":
          try:
            self.fitpars[v] = float(i[1])
          except ValueError:
            bme.HandleErrors(True, "\nBM fit parameter is not a value.\n %s\n" % i[1])
        else:
          if i[1].lower() not in ["auto", "gs", "avg"]:
            self.fitpars[v] = "auto"
          else:
            self.fitpars[v] = i[1].lower()

  #########################################################################
  # checkFitPars - Checks to make sure BM fit pars are sufficient for sims
  #########################################################################
  def checkFitPars(self):
    if self.fitpars['pb'] is None and self.fitpars['pc'] is None:
      bme.HandleErrors(True, "\npB and pC have not been defined.\n")
    if self.fitpars['kexab'] is None and self.fitpars['kexac'] is None:
      bme.HandleErrors(True, "\nkexAB and kexAC have not been defined.\n")
    if (self.fitpars['r1'] is None or self.fitpars['r1b'] is None
        or self.fitpars['r1c'] is None):
      bme.HandleErrors(True, "\nR1, R1b, or R1c has not been defined.\n")
    if (self.fitpars['r2'] is None or self.fitpars['r2b'] is None
        or self.fitpars['r2c'] is None):
      bme.HandleErrors(True, "\nR2, R2b, or R2c has not been defined.\n") 
    if self.fitpars['lf'] is None:
      bme.HandleErrors(True, "\nLarmor frequency has not been defined.\n")

  #########################################################################
  # prPlotInp - Parse plot input block from raw input and parses it
  #           Maps values to local plotting parameters for 
  #           axes limits and font sizes
  #  Input:
  #   - Plot input block from parsed raw input file (list of lists)
  #  Result:
  #   - Assigns values to all the variable plotting parameters
  #########################################################################
  def prPlotInp(self, plob):
    for i in plob:
      if i[0].lower() != "plot" and len(i) == 3:
        # var name
        v = i[0].lower()
        # Check for numerical values if not line type or symbol
        if v != "line" and v != "symbol":
          if i[1].lower() != "none":
            try:
              tv = float(i[1])
              self.pltvar[v][0] = tv
            except ValueError:
              bme.HandleErrors(True, "\nNon-numeric value in plotting specs.\n")
          if i[2].lower() != "none":
            try:
              tv = float(i[2])
              self.pltvar[v][1] = tv
            except ValueError:
              bme.HandleErrors(True, "\nNon-numeric value in plotting specs.\n")
        else:
          # Make sure line/symbol size is numerical
          try:
            symsize = float(i[2])
          except ValueError:
            bme.HandleErrors(True, "\nLine or Symbol size non-numeric\n")
          self.pltvar[v] = [i[1], symsize]
      # Assign plotting type
      elif i[0].lower() == "plot" and len(i) == 2:
        self.pltvar[i[0].lower()] = i[1]

  #########################################################################
  # checkNums - Takes in an N-length list and checks that the values are
  #             not non-numerical
  #  Input:
  #   - List of values
  #  Result:
  #   - Returns a list of floats, if possible. Else, stops program
  #########################################################################
  def checkNums(self, numArr):
    # Check that all values in the array are numbers
    try:
      for i in numArr:
        float(i)
    except ValueError:
      bme.HandleErrors(True, "\nNot enough parameters defined for params\n")

    return np.asarray(numArr).astype(float)

  #########################################################################
  # prSLOff - Parse SL Offset block from raw input and parses it
  #           Generates numpy array of SLPs and Offsets for on-res and
  #           off-res
  #  Input:
  #   - SL/Offset block from parsed raw input file (list of lists)
  #  Result:
  #   - Reads and/or generates SLPs/offsets to be assigned to 
  #     self.slon - onres numpy array
  #     self.sloff - offres numpy array
  #########################################################################
  def prSLOff(self, slob):
    readPath = None
    # Iterate over sloffset block and extract
    # - Read value (i.e. read in .csv with SLP offsets pre-defined)
    #    If null, then generate with following ranges
    # - 'on' onres values: low, upper, N-pts
    # - 'off' offres values: SLP, low, upper, N-points
    for i in slob:
      # Check for read flag to read in SLP-offset values from a CSV
      #  Here col0 = offsets (Hz) and col1 = SLP (Hz)
      if i[0].lower() == "read":
        # If read flag is defined as a value as non-false
        if len(i) >= 2 and i[1].lower() != "false":
          readPath = os.path.join(self.curDir, i[1])
          # Check to make sure SLPOffs csv exists, if not just ignore.
          if not os.path.isfile(readPath):
            pass
            # bme.HandleErrors(True, "\nSLP/Offset path is defined but does not exist.\n %s\n" % readPath)
          else:
            # Read csv to numpy array
            rawsloff = np.genfromtxt(readPath, dtype=float, delimiter=',')
            # Strip nan values
            rawsloff = rawsloff[~np.isnan(rawsloff).any(axis=1)]
            # Split to on-res vs offres
            self.sloff = rawsloff[rawsloff[:,0] != 0.]
            self.slon = rawsloff[rawsloff[:,0] == 0.]
      # Generate on-res SLPs
      elif i[0].lower() == "on" and len(i) >= 4:
        # Check that lower, upper, and N are numbers
        try:
          low, hi = float(i[1]), float(i[2])
          # Swap low/high if low is > high
          if low > hi: low, hi = hi, low
          # Check number parameters
          numv = int(i[3])
        except ValueError:
          bme.HandleErrors(True, "\nBad on-res SLP generation parameters\n %s" % " ".join(i))
        # Generate array of these values with 0 set to offset
        ton = np.array([[0., x] for x in np.linspace(low, hi, numv)])
        # append to existing array if it already exists
        if self.slon is not None:
          self.slon = np.append(self.slon, ton, axis=0)
        # else assign onres array to this array
        else:
          self.slon = ton
      elif i[0].lower() == "on" and len(i) < 4:
        bme.HandleErrors(True, "\nNot enough parameters defined for on-res SLP generation\n")
      # Generate off-res SLPs
      elif i[0].lower() == "off" and len(i) >= 5:
        # Check that lower, upper, and N are numbers
        try:
          # Assign slp
          slp = float(i[1])
          # Assign lower/upper offset limits
          low, hi = float(i[2]), float(i[3])
          # Swap low/high if low is > high
          if low > hi: low, hi = hi, low
          # Check number parameters
          numv = int(i[4])
        except ValueError:
          bme.HandleErrors(True, "\nBad off-res generation parameters\n %s" % " ".join(i))
        # Generate array of these values with slp set to SLP
        toff = np.array([[x, slp] for x in np.linspace(low, hi, numv)])
        # append to existing array if it already exists
        if self.sloff is not None:
          self.sloff = np.append(self.sloff, toff, axis=0)
        # else assign onres array to this array
        else:
          self.sloff = toff
      # Handle bad number of sloff generation parameters
      elif i[0].lower() == "off" and len(i) < 5:
        bme.HandleErrors(True, "\nNot enough parameters defined for off-res SLP generation\n")
      # Get error percentage for corruption of R1rho values
      elif i[0].lower() == "error":
        if len(i) == 2:
          try:
            self.rhoerr = float(i[1])
          except ValueError:
            bme.HandleErrors(True, "\nError percentage does not exist\n")
      # Get error MCnum for corruption of R1rho values
      elif i[0].lower() == "mcnum":
        if len(i) == 2:
          try:
            self.rhomc = int(i[1])
          except ValueError:
            bme.HandleErrors(True, "\nError corruption MC number does not exist\n")
    # Combine both on and off-res
    if self.slon is None:
      self.slonoff = self.sloff
    elif self.sloff is None:
      self.slonoff = self.slon
    else:
      self.slonoff = np.append(self.slon, self.sloff, axis=0)

