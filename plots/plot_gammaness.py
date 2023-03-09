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

particle_ids = {"Protons": 101, "Gammas": 0}


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


def plot_gammaness(events):
    fig, ax = plt.subplots(layout="constrained")

    hist_opts = dict(bins=101, range=[0, 1], histtype='step')

    key = "gammaness"
    for label, particle_id in particle_ids.items():
        mask = events["true_shower_primary_id"] == particle_id
        plt.hist(events[gammaness][mask], **hist_opts, label=label)

    ax.set_xlabel(key)
    ax.legend(ncol=2, loc='upper center')

    fig.savefig("build/plots/gammaness.pdf")


def plot_gammaness_energy(events):
    n_bins = 4
    reco_energy_bins = np.geomspace(10 * u.GeV, 100 * u.TeV, n_bins + 1)

    fig, axs = plt.subplots(
        2, 2,
        sharex=True,
        layout="constrained"
    )
    axs = axs.ravel()

    hist_opts = dict(bins=51, range=[0, 1], histtype='step')

    key = "gammaness"

    for label, particle_id in particle_ids.items():
        
        grouped = events.group_by(np.digitize(events[reco_energy], reco_energy_bins))
        
        for idx, group in zip(grouped.groups.keys, grouped.groups):
            # skip under / overflow
            if idx == 0 or idx == (n_bins + 1):
                continue
            
            idx -= 1
            ax = axs[idx]
            
            mask = group["true_shower_primary_id"] == particle_id
            ax.hist(group[gammaness][mask], **hist_opts, label=label)

            e_min = reco_energy_bins[idx]
            e_max = reco_energy_bins[idx + 1]
            if e_min < 1 * u.TeV:
                e_min = e_min.to(u.GeV)
            if e_max < 1 * u.TeV:
                e_max = e_max.to(u.GeV)

            label = r'{:.0f} $\leq \hat{{E}} < $ {:.0f}'.format(
                e_min, e_max
            )
            ax.set_title(label)
                
    axs[-2].set_xlabel('gammaness')
    axs[-1].set_xlabel('gammaness')
    fig.savefig("build/plots/gammaness_energy.pdf")



def main():
    events = load_data()
    plot_gammaness(events)
    plot_gammaness_energy(events)



if __name__ == "__main__":
    main()