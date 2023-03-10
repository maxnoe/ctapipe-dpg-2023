import matplotlib.pyplot as plt
import astropy.units as u
import numpy as np

from common import load_data, particle_ids, reco_energy, gammaness


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
    plot_gammaness_energy(events)


if __name__ == "__main__":
    main()
