import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u
from astropy.coordinates.angle_utilities import angular_separation
from ctapipe.io import TableLoader
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
    mask = np.isfinite(events[reco_energy]) & (events[gammaness] > 0.6)

    fig, ax = plt.subplots(layout="constrained")

    n_bins = 101
    energy_bins = np.geomspace(10 * u.GeV, 100 * u.TeV, n_bins + 1)
    *_, plot = ax.hist2d(
        events["true_energy"][mask].quantity.to_value(u.GeV),
        events[reco_energy][mask].quantity.to_value(u.GeV),
        bins=[
            energy_bins.to_value(u.GeV),
            energy_bins.to_value(u.GeV),
        ],
        vmax=700,
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

    fig.savefig("build/plots/energy_migration_gammaness.pdf", bbox_inches="tight")



def main():
    events = load_data()
    plot_energy_migration(events)



if __name__ == "__main__":
    main()
