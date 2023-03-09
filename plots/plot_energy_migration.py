import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u
from astropy.coordinates.angle_utilities import angular_separation
from ctapipe.io import TableLoader
from sklearn.metrics import roc_auc_score, roc_curve
from astropy.table import vstack


gammaness = "RandomForestClassifier_prediction"
reco_energy = "RandomForestRegressor_energy"


fov_offset_max = 2.5 * u.deg

opts = dict(load_dl2=True, load_simulated=True, load_dl1_parameters=False)

gamma_path = "./build/gamma_test.dl2.h5"
proton_path = "./build/proton_test.dl2.h5"

particle_ids = {"Gammas": 0, "Proton": 101}


def load_data():
    with TableLoader(gamma_path, **opts) as gamma_loader:
        gammas = gamma_loader.read_subarray_events()

    with TableLoader(proton_path, **opts) as proton_loader:
        protons = proton_loader.read_subarray_events()

    events = vstack([gammas, protons])
    del gammas
    del protons

    events['true_source_fov_offset'] = angular_separation(
        events["true_az"].quantity, events["true_alt"].quantity,
        0 * u.deg, 70 * u.deg,
    )

    events = events[events["true_source_fov_offset"].quantity < fov_offset_max]

    return events


def plot_energy_migration(events):
    mask = np.isfinite(events[reco_energy])

    fpr, tpr, threshold = roc_curve(
        events['true_shower_primary_id'][mask],
        # sklearn computes confusion matrix for each possible cut
        # much faster if rounded to 3 digits to reduce number of unique values
        np.round(events['RandomForestClassifier_prediction'][mask], 3),
        pos_label=0,
    )

    roc_auc = np.trapz(x=fpr, y=tpr)

    fig, ax = plt.subplots(layout="constrained")

    n_bins = 101
    energy_bins = np.geomspace(10 * u.GeV, 100 * u.TeV, n_bins + 1)
    *_, plot = ax.hist2d(
        events["true_energy"][mask].quantity.to_value(u.GeV),
        events[reco_energy][mask].quantity.to_value(u.GeV),
        bins=[
            energy_bins.to_value(u.GeV),
            energy_bins.to_value(u.GeV),
        ]
    )
    plot.set_rasterized(True)
    fig.colorbar(plot, ax=ax, label="Number of Events")

    ax.set(
        aspect=1,
        xlabel=r"$E \mathrel{/} \unit{\GeV}$",
        ylabel=r"$\hat{E} \mathrel{/} \unit{\GeV}$",
        xscale='log',
        yscale='log',
    )

    fig.savefig("build/plots/energy_migration.pdf", bbox_inches="tight")



def main():
    events = load_data()
    plot_energy_migration(events)



if __name__ == "__main__":
    main()
