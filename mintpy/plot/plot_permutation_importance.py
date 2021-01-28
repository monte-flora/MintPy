import numpy as np

from .base_plotting import PlotStructure


class PlotImportance(PlotStructure):
    def is_bootstrapped(self, original_score):
        """Check if the permutation importance results are bootstrapped"""
        try:
            len(original_score)
        except:
            bootstrapped = False
        else:
            bootstrapped = True

        if bootstrapped:
            original_score_mean = np.mean(original_score)
        else:
            original_score_mean = original_score

        return bootstrapped, original_score_mean

    def plot_variable_importance(
        self,
        data,
        metrics_used,
        multipass=True,
        display_feature_names={},
        feature_colors=None,
        num_vars_to_plot=10,
        model_output="raw",
        model_names=None,
        **kwargs,
    ):

        """Plots any variable importance method for a particular estimator

        Args:
            data : xarray.Dataset or list of xarray.Dataset
                Permutation importance dataset for one or more metrics

            multipass : boolean
                if True, plots the multipass results
            display_feature_names : dict
                A dict mapping feature names to readable, "pretty" feature names
            feature_colors : dict
                A dict mapping features to various colors. Helpful for color coding groups of features
            num_vars_to_plot : int
                Number of top variables to plot (defalut is None and will use number of multipass results)
            xaxis_label : str
                Metric used to compute the predictor importance, which will display as the X-axis label.
        """
        hspace = kwargs.get("hspace", 0.5)
        wspace = kwargs.get("wspace", 0.2)
        xticks = kwargs.get("xticks", None)
        title = kwargs.get("title", "")
        ylabels = kwargs.get("ylabels", "")
        xlabels = kwargs.get("xlabels", "")
        n_columns = kwargs.get("n_columns", 3)

        perm_method = "multipass" if multipass else "singlepass"

        if not isinstance(data, list):
            data = [data]

        if len(data) != len(metrics_used):
            raise ValueError(
                """
                             The number of metrics used (the different metrics used to compute 
                             permutation importance) must match the number of dataset given!
                             """
            )

        if len(model_names) == 1:
            # Only one model, but one or more metrics
            only_one_model = True
            xlabels = metrics_used
            n_columns = min(len(xlabels), 3)
            n_panels = len(xlabels)
            xlabels = metrics_used
        else:
            # More than one model, and one or more metrics
            only_one_model = False
            n_columns = min(len(model_names), 3)
            if len(metrics_used) == 1:
                xlabels = metrics_used
            else:
                ylabels = metrics_used

            n_panels = n_columns * len(metrics_used)

        # get the number of panels which will be the number of ML models in dictionary
        # n_keys = [list(importance_dict.keys()) for importance_dict in data]
        # n_panels = len([item for sublist in n_keys for item in sublist])

        if model_output == "probability" and xticks is None:
            # Most probability-based scores are between 0-1 (AUC, BSS, NAUPDC,etc.)
            xticks = [0, 0.2, 0.4, 0.6, 0.8, 1.0]

        if n_panels == 1:
            figsize = (3, 2.5)
        elif n_panels == 2:
            figsize = (6, 2.5)
        elif n_panels == 3:
            figsize = kwargs.get("figsize", (6, 2.5))
        else:
            figsize = kwargs.get("figsize", (8, 5))
            hspace = 0.2

        # create subplots, one for each feature
        fig, axes = self.create_subplots(
            n_panels=n_panels,
            n_columns=n_columns,
            hspace=hspace,
            wspace=wspace,
            figsize=figsize,
        )

        if n_panels == 1:
            axes = [axes]

        # List of data for different metrics
        for g, results in enumerate(data):
            # loop over each model creating one panel per model
            for k, model_name in enumerate(model_names):
                if len(data) == 1:
                    ax = axes[k]
                else:
                    ax = axes[g, k]

                if g == 0:
                    ax.set_title(
                        model_name, fontsize=self.FONT_SIZES["small"], alpha=0.8
                    )

                if only_one_model:
                    ax.set_xlabel(xlabels[g])

                sorted_var_names = list(
                    results[f"{perm_method}_rankings__{model_name}"].values
                )
                sorted_var_names = sorted_var_names[
                    : min(num_vars_to_plot, len(sorted_var_names))
                ]

                if num_vars_to_plot is None:
                    num_vars_to_plot == len(sorted_var_names)

                scores = [
                    results[f"{perm_method}_scores__{model_name}"].values[i, :]
                    for i in range(len(sorted_var_names))
                ]

                # Get the original score (no permutations)
                original_score = results[f"original_score__{model_name}"].values

                # Get the original score (no permutations)
                # Check if the permutation importance is bootstrapped
                bootstrapped, original_score_mean = self.is_bootstrapped(original_score)

                # Get the colors for the plot
                colors_to_plot = [
                    self.variable_to_color(var, feature_colors)
                    for var in [
                        "No Permutations",
                    ]
                    + sorted_var_names
                ]
                # Get the predictor names
                variable_names_to_plot = [
                    fr"$ {var}$" 
                    for var in self.convert_vars_to_readable(
                        [
                            "No Permutations",
                        ]
                        + sorted_var_names,
                        display_feature_names,
                    )
                ]

                if bootstrapped:
                    scores_to_plot = np.array(
                        [
                            original_score_mean,
                        ]
                        + [np.mean(score) for score in scores]
                    )
                    ci = np.array(
                        [
                            np.abs(np.mean(score) - np.percentile(score, [2.5, 97.5]))
                            for score in np.r_[
                                [
                                    original_score,
                                ],
                                scores,
                            ]
                        ]
                    ).transpose()
                else:
                    scores_to_plot = np.array(
                        [
                            original_score_mean,
                        ]
                        + scores
                    )
                    ci = np.array(
                        [
                            [0, 0]
                            for score in np.r_[
                                [
                                    original_score,
                                ],
                                scores,
                            ]
                        ]
                    ).transpose()

                # Despine
                self.despine_plt(ax)

                if bootstrapped:
                    ax.barh(
                        np.arange(len(scores_to_plot)),
                        scores_to_plot,
                        linewidth=1,
                        alpha=0.8,
                        color=colors_to_plot,
                        xerr=ci,
                        capsize=2.5,
                        ecolor="grey",
                        error_kw=dict(alpha=0.4),
                        zorder=2,
                    )
                else:
                    ax.barh(
                        np.arange(len(scores_to_plot)),
                        scores_to_plot,
                        alpha=0.8,
                        linewidth=1,
                        color=colors_to_plot,
                        zorder=2,
                    )

                if num_vars_to_plot > 10:
                    size = self.FONT_SIZES["teensie"] - 1
                else:
                    size = self.FONT_SIZES["teensie"]

                # Put the variable names _into_ the plot
                if model_output == "probability":
                    x_pos = 0
                    ha = "left"
                else:
                    x_pos = 0.05
                    ha = "right"

                # Put the variable names _into_ the plot
                for i in range(len(variable_names_to_plot)):
                    ax.text(
                        x_pos,
                        i,
                        variable_names_to_plot[i],
                        va="center",
                        ha=ha,
                        size=size,
                        alpha=0.8,
                    )

                if model_output == "probability":
                    # Add vertical line
                    ax.axvline(
                        original_score_mean,
                        linestyle="dashed",
                        color="grey",
                        linewidth=0.7,
                        alpha=0.7,
                    )
                    ax.text(
                        original_score_mean,
                        len(variable_names_to_plot) / 2,
                        "Original Score",
                        va="center",
                        ha="left",
                        size=self.FONT_SIZES["teensie"],
                        rotation=270,
                        alpha=0.7,
                    )

                ax.tick_params(axis="both", which="both", length=0)
                ax.set_yticks([])
                if xticks is not None:
                    ax.set_xticks(xticks)

                upper_limit = min(1.05 * np.amax(scores_to_plot), 1.0)
                if model_output == "probability":
                    upper_limit = min(1.05 * np.amax(scores_to_plot), 1.0)
                    ax.set_xlim([0, upper_limit])
                else:
                    upper_limit = 1.05 * np.amax(scores_to_plot)
                    ax.set_xlim([upper_limit, 0])

                # make the horizontal plot go with the highest value at the top
                ax.invert_yaxis()
                vals = ax.get_xticks()
                for tick in vals:
                    ax.axvline(
                        x=tick, linestyle="dashed", alpha=0.4, color="#eeeeee", zorder=1
                    )

                if k == 0:
                    pad = -0.15
                    ax.annotate(
                        "higher ranking",
                        xy=(pad, 0.8),
                        xytext=(pad, 0.5),
                        arrowprops=dict(arrowstyle="->", color="xkcd:blue grey"),
                        xycoords=ax.transAxes,
                        rotation=90,
                        size=6,
                        ha="center",
                        va="center",
                        color="xkcd:blue grey",
                        alpha=0.65,
                    )

                    ax.annotate(
                        "lower ranking",
                        xy=(pad + 0.05, 0.2),
                        xytext=(pad + 0.05, 0.5),
                        arrowprops=dict(arrowstyle="->", color="xkcd:blue grey"),
                        xycoords=ax.transAxes,
                        rotation=90,
                        size=6,
                        ha="center",
                        va="center",
                        color="xkcd:blue grey",
                        alpha=0.65,
                    )

        if len(xlabels) == 1 and not only_one_model:
            self.set_major_axis_labels(
                fig,
                xlabel=xlabels[0].replace("_", "").upper(),
                ylabel_left="",
                labelpad=5,
                fontsize=self.FONT_SIZES["tiny"],
            )

        self.set_row_labels(ylabels, axes)

        if model_output == "probability":
            pos = (0.9, 0.09)
        else:
            pos = (0.05, 0.95)
        self.add_alphabet_label(n_panels, axes, pos=pos)

    # You can fill this in by using a dictionary with {var_name: legible_name}
    def convert_vars_to_readable(self, variables_list, VARIABLE_NAMES_DICT):
        """Substitutes out variable names for human-readable ones
        :param variables_list: a list of variable names
        :returns: a copy of the list with human-readable names
        """
        human_readable_list = list()
        for var in variables_list:
            if var in VARIABLE_NAMES_DICT:
                human_readable_list.append(VARIABLE_NAMES_DICT[var])
            else:
                human_readable_list.append(var)
        return human_readable_list

    # This could easily be expanded with a dictionary
    def variable_to_color(self, var, VARIABLES_COLOR_DICT):
        """
        Returns the color for each variable.
        """
        if var == "No Permutations":
            return "xkcd:pastel red"
        else:
            if VARIABLES_COLOR_DICT is None:
                return "xkcd:powder blue"
            elif not isinstance(VARIABLES_COLOR_DICT, dict) and isinstance(
                VARIABLES_COLOR_DICT, str
            ):
                return VARIABLES_COLOR_DICT
            else:
                return VARIABLES_COLOR_DICT[var]
