import numpy as np
from .RiskCohort import RiskCohort
from .RiskCluster import RiskCluster
from .Visualization import _SplitSymbols
from .Visualization import _WrapSymbols
from .Visualization import RankedBox
from .Visualization import PairScatter
from .Visualization import KMPlots
from .WriteGCT import WriteGCT
from .WriteRNK import WriteRNK


def FeatureAnalysis(Model, Normalized, Raw, Symbols, Survival, Censored,
                    NBox=10, NScatter=10, NKM=10, NCluster=100, Tau=0.05,
                    Path=None):
    """
    Generate visualizations of risk profiles. Backpropagation is used to

    Parameters:
    -----------
    Model : class
    Model generated by finetuning.

    Normalized : array_like
    Numpy array containing normalized feature values used in training /
    finetuning. These are used to examine associations between feature values
    and cluster assignments. Features are in columns and samples are in rows.

    Raw : array_like
    Numpy array containing raw, unnormalized feature values. These are used to
    examine associations between feature values and cluster assignments.
    Features are in columns and samples are in rows.

    Symbols : array_like
    List containing strings describing features. See Notes below for
    restrictions on symbol names.

    Survival : array_like
    Array containing death or last followup values.

    Censored : array_like
    Array containing vital status at last followup. 1 (alive) or 0 (deceased).

    NPlot : scalar
    Number of features to include when generating boxplot.
    Features are scored by absolute mean gradient and the highest N magnitude
    features will be used to generate the plot. Default value = 10.

    NCluster : scalar
    Number of features to include when generating cluster analysis.
    Features are scored by absolute mean gradient and the highest N magnitude
    features will be used to generate the plot. Default value = 100.

    Tau : scalar
    Threshold for statistical significance when examining cluster associations.

    Path : string
    Path to store .pdf versions of plots generated.
    """

    # wrap long symbols and remove leading and trailing whitespace
    Corrected, Types = _SplitSymbols(Symbols)
    Wrapped = _WrapSymbols(Corrected)

    # generate risk derivative profiles for cohort
    print "Generting risk gradient profiles..."
    Gradients = RiskCohort(Model, Normalized)
    
    # normalize risk derivative profiles
    Gradients = Gradients / np.outer(np.linalg.norm(Gradients, axis=1),
                                     np.ones((1, Gradients.shape[1])))

    # re-order symbols, raw features, gradients by mean gradient value, trim
    Means = np.asarray(np.mean(Gradients, axis=0))
    Order = np.argsort(-np.abs(Means))
    cSymbols = [Wrapped[i] for i in Order]
    cTypes = [Types[i] for i in Order]
    cRaw = Raw[:, Order]
    cGradients = Gradients[:, Order]

    # generate ranked box plot series
    print "Generating risk gradient boxplot..."
    RBFig = RankedBox(cGradients[:, 0:NBox],
                      [cSymbols[i] for i in np.arange(NBox)],
                      [cTypes[i] for i in np.arange(NBox)],
                      XLabel='Model Features', YLabel='Risk Gradient')

    # generate paired scatter plot for gradients
    print "Generating paired scatter gradient plots..."
    PSGradFig = PairScatter(cGradients[:, 0:NScatter],
                            [cSymbols[i] for i in np.arange(NScatter)],
                            [cTypes[i] for i in np.arange(NScatter)])

    # generate paired scatter plot for features
    print "Generating paired scatter feature plots..."
    PSFeatFig = PairScatter(cRaw[:, 0:NScatter],
                            [cSymbols[i] for i in np.arange(NScatter)],
                            [cTypes[i] for i in np.arange(NScatter)])

    # generate cluster plot
    print "Generating cluster analysis..."
    CFig, Labels = RiskCluster(cGradients[:, 0:NCluster], cRaw[:, 0:NCluster],
                               [cSymbols[i] for i in np.arange(NCluster)],
                               [cTypes[i] for i in np.arange(NCluster)],
                               Tau)

    # generate Kaplan-Meier plots for individual features
    print "Generating Kaplan-Meier plots..."
    KMFigs = KMPlots(cGradients[:, 0:NKM], cRaw[:, 0:NKM],
                     [cSymbols[i] for i in np.arange(NKM)],
                     [cTypes[i] for i in np.arange(NKM)],
                     Survival, Censored)

    # save figures
    print "Saving figures and outputs..."
    if Path is not None:

        # save standard figures
        RBFig.savefig(Path + 'RankedBox.pdf')
        PSGradFig.savefig(Path + 'PairedScatter.Gradient.pdf')
        PSFeatFig.savefig(Path + 'PairedScatter.Feature.pdf')
        CFig.savefig(Path + 'Heatmap.pdf')
        for i, Figure in enumerate(KMFigs):
            Figure.savefig(Path + 'KM.' + Symbols[Order[i]].strip() + '.pdf')

        # save tables
        WriteRNK(Corrected, Means, Path + 'Gradients.rnk')
        WriteGCT(Corrected, None, Gradients, Path + 'Gradients.gct')
