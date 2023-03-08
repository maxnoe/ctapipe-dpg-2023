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


def plot_roc(events):
    mask = np.isfinite(events[gammaness])

    fpr, tpr, threshold = roc_curve(
        events['true_shower_primary_id'][mask],
        # sklearn computes confusion matrix for each possible cut
        # much faster if rounded to 3 digits to reduce number of unique values
        np.round(events['RandomForestClassifier_prediction'][mask], 3),
        pos_label=0,
    )

    roc_auc = np.trapz(x=fpr, y=tpr)

    fig, ax = plt.subplots(layout="constrained")

    plot = ax.scatter(
        fpr, tpr,
        c=threshold,
        cmap='inferno',
        vmin=0,
        vmax=1,
        s=5,
    )

    fig.colorbar(plot, ax=ax, label="gammaness threshold")

    n_bins = 4
    reco_energy_bins = np.geomspace(10 * u.GeV, 100 * u.TeV, n_bins + 1)
    grouped = events[mask].group_by(np.digitize(events[mask][reco_energy], reco_energy_bins))
    
    for idx, group in zip(grouped.groups.keys, grouped.groups):
        # skip under / overflow
        ax.legend()
        if idx == 0 or idx == (n_bins + 1):
            continue

        idx -= 1

        fpr, tpr, threshold = roc_curve(
            group['true_shower_primary_id'],
            # sklearn computes confusion matrix for each possible cut
            # much faster if rounded to 3 digits to reduce number of unique values
            np.round(group['RandomForestClassifier_prediction'], 3),
            pos_label=0,
        )

        e_min = reco_energy_bins[idx]
        e_max = reco_energy_bins[idx + 1]
        if e_min < 1 * u.TeV:
            e_min = e_min.to(u.GeV)
        if e_max < 1 * u.TeV:
            e_max = e_max.to(u.GeV)

        label = r'{:.0f} $\leq \hat{{E}} < $ {:.0f}'.format(
            e_min, e_max
        )
        ax.plot(fpr, tpr, label=label, color=str(0.3 + (idx + 1) * 0.7 / n_bins))

    ax.legend(loc='lower right')
    ax.set(
        title=f'ROC AUC: {roc_auc:.3f}',
        aspect=1,
        xlim=(-0.01, 1.01),
        ylim=(-0.01, 1.01),
        xlabel="False Positive Rate",
        ylabel="True Positive Rate",
    )

    fig.savefig("build/plots/roc.pdf")



def main():
    events = load_data()
    plot_roc(events)
    plt.show()



if __name__ == "__main__":
    main()
