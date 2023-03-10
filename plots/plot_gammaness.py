import matplotlib.pyplot as plt

from common import load_data, particle_ids, gammaness


def plot_gammaness(events):
    fig, ax = plt.subplots(layout="constrained")

    hist_opts = dict(bins=101, range=[0, 1], histtype='step')

    for label, particle_id in particle_ids.items():
        mask = events["true_shower_primary_id"] == particle_id
        plt.hist(events[gammaness][mask], **hist_opts, label=label)

    ax.set_xlabel("gammaness")
    ax.legend(ncol=2, loc='upper center')

    fig.savefig("build/plots/gammaness.pdf")


def main():
    events = load_data()
    plot_gammaness(events)



if __name__ == "__main__":
    main()
