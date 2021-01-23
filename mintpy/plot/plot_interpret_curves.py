from ..common.utils import to_list, is_list
from .base_plotting import PlotStructure
from math import log10
import numpy as np


class PlotInterpretCurves(PlotStructure):
    """
    InterpretCurves handles plotting the ALE and PDP curves and the corresponding
    background histogram for the various features.

    Inherits the Plot class which handles making plots pretty
    """

    line_colors = [
        "xkcd:fire engine red",
        "xkcd:water blue",
        "xkcd:very dark purple",
        "xkcd:medium green",
        "xkcd:burnt sienna",
    ]

    def plot_1d_curve(
        self,
        method,
        data,
        features,
        model_names,
        display_feature_names={},
        display_units={},
        to_probability=False,
        line_colors=None,
        **kwargs,
    ):
        """
        Generic function for 1-D ALE and PD plots.

        Args:
        --------------
            data : dict of data
            features : list of strs
                List of the features to be plotted.
            model_names : list of strs
                List of models to be plotted
            display_feature_names : dict or list
            display_units : dict or list
            unnormalize : callable
                Function used to unnormalize data for the
                background histogram plot

            **Optional keyword args:


        """
        if line_colors is None:
            line_colors = self.line_colors

        if not is_list(model_names):
            model_names = to_list(model_names)

        self.display_feature_names = display_feature_names
        self.display_units = display_units
        hspace = kwargs.get("hspace", 0.5)
        wspace = kwargs.get("wspace", 0.5)
        facecolor = kwargs.get("facecolor", "gray")
        left_yaxis_label = kwargs.get("left_yaxis_label")
        unnormalize = kwargs.get("unnormalize", None)
        ice_curves = kwargs.get("ice_curves", None)

        # get the number of panels which will be length of feature dictionary
        n_panels = len(features)

        majoraxis_fontsize = self.FONT_SIZES["teensie"]

        if n_panels == 1:
            kwargs["figsize"] = (3, 2.5)
        elif n_panels == 2:
            kwargs["figsize"] = (6, 2.5)
        elif n_panels == 3:
            kwargs["figsize"] = (10, 5)
            hspace = 0.6
        else:
            kwargs["figsize"] = kwargs.get("figsize", (8, 5))
            majoraxis_fontsize = self.FONT_SIZES["small"]

        # create subplots, one for each feature
        fig, axes = self.create_subplots(n_panels=n_panels, **kwargs)

        ax_iterator = self.axes_to_iterator(n_panels, axes)

        # loop over each feature and add relevant plotting stuff
        for lineplt_ax, feature in zip(ax_iterator, features):

            # Pull the x-values and histogram from the first model.
            # if isinstance(model_names, list):
            #    choosen_model = model_names[0]
            # else:
            #    choosen_model=model_names
            xdata = data[f"{feature}__bin_values"].values
            hist_data = data[f"{feature}"].values

            # xdata = data[feature][choosen_model]["xdata1"]
            # hist_data = data[feature][choosen_model]["xdata1_hist"]
            if unnormalize is not None:
                hist_data = unnormalize.inverse_transform(hist_data, feature)
                xdata = unnormalize.inverse_transform(xdata, feature)

            # add histogram
            hist_ax = self.make_twin_ax(lineplt_ax)
            twin_yaxis_label = self.add_histogram_axis(
                hist_ax, hist_data, min_value=xdata[0], max_value=xdata[-1]
            )

            for i, model_name in enumerate(model_names):
                if ice_curves:
                    ice_data = ice_curves[f"{feature}__{model_name}__ice"].values
                    ice_xdata = ice_curves[f"{features}__bin_values"].values
                    if to_probability:
                        ice_data *= 100
                    if unnormalize is not None:
                        ice_xdata = unnormalize.inverse_transform(ice_xdata, feature)
                    for ind_curve in ice_data:
                        lineplt_ax.plot(
                            ice_xdata, ind_curve, color="k", alpha=0.85, linewidth=0.25
                        )

                # ydata = data[feature][model_name]["values"]
                ydata = data[f"{feature}__{model_name}__{method}"].values

                if to_probability:
                    ydata *= 100.0

                # depending on number of bootstrap examples, do CI plot or just mean
                if ydata.shape[0] > 1:
                    self.confidence_interval_plot(
                        lineplt_ax,
                        xdata,
                        ydata,
                        color=self.line_colors[i],
                        facecolor=self.line_colors[i],
                        label=model_name,
                    )
                else:
                    self.line_plot(
                        lineplt_ax,
                        xdata,
                        ydata[0, :],
                        color=line_colors[i],
                        label=model_name.replace("Classifier", ""),
                    )

            self.set_n_ticks(lineplt_ax)
            self.set_minor_ticks(lineplt_ax)
            self.set_axis_label(lineplt_ax, xaxis_label="".join(feature))
            lineplt_ax.axhline(
                y=0.0, color="k", alpha=0.8, linewidth=0.8, linestyle="dashed"
            )
            lineplt_ax.set_yticks(
                self.calculate_ticks(ax=lineplt_ax, nticks=5, center=True)
            )

        # kwargs['fontsize'] = majoraxis_fontsize
        major_ax = self.set_major_axis_labels(
            fig,
            xlabel=None,
            ylabel_left=left_yaxis_label,
            ylabel_right=twin_yaxis_label,
            **kwargs,
        )
        self.set_legend(n_panels, fig, lineplt_ax, major_ax)
        self.add_alphabet_label(n_panels, axes)

        return fig, axes

    def add_histogram_axis(
        self, ax, data, bins=15, min_value=None, max_value=None, density=False, **kwargs
    ):
        """
        Adds a background histogram of data for a given feature.
        """

        color = kwargs.get("color", "lightblue")
        edgecolor = kwargs.get("color", "white")

        # if min_value is not None and max_value is not None:
        #    data = np.clip(data, a_min=min_value, a_max=max_value)

        cnt, bins, patches = ax.hist(
            data,
            bins=bins,
            alpha=0.3,
            color=color,
            density=density,
            edgecolor=edgecolor,
            zorder=1,
        )

        if density:
            return "Relative Frequency"
        else:
            ax.set_yscale("log")
            ymax = round(10 * len(data))
            n_ticks = round(log10(ymax))
            ax.set_ylim([0, ymax])
            ax.set_yticks([10 ** i for i in range(n_ticks + 1)])
            return "Frequency"

    def line_plot(self, ax, xdata, ydata, label, **kwargs):
        """
        Plots a curve of data
        """

        linewidth = kwargs.get("linewidth", 1.25)
        linestyle = kwargs.get("linestyle", "-")

        if "color" not in kwargs:
            kwargs["color"] = "xkcd:darkish blue"

        ax.plot(
            xdata,
            ydata,
            linewidth=linewidth,
            linestyle=linestyle,
            label=label,
            alpha=0.8,
            **kwargs,
            zorder=2,
        )

    def confidence_interval_plot(self, ax, xdata, ydata, label, **kwargs):
        """
        Plot a line plot with an optional confidence interval polygon
        """

        facecolor = kwargs.get("facecolor", "r")
        color = kwargs.get("color", "blue")

        # get mean curve
        mean_ydata = np.mean(ydata, axis=0)

        # plot mean curve
        self.line_plot(ax, xdata, mean_ydata, color=color, label=label)

        # get confidence interval bounds
        lower_bound, upper_bound = np.percentile(ydata, [2.5, 97.5], axis=0)

        # fill between CI bounds
        ax.fill_between(xdata, lower_bound, upper_bound, facecolor=facecolor, alpha=0.4)

    def make_twin_ax(self, ax):
        """
        Create a twin axis on an existing axis with a shared x-axis
        """
        # align the twinx axis
        twin_ax = ax.twinx()

        # Turn twin_ax grid off.
        twin_ax.grid(False)

        # Set ax's patch invisible
        ax.patch.set_visible(False)
        # Set axtwin's patch visible and colorize it in grey
        twin_ax.patch.set_visible(True)

        # move ax in front
        ax.set_zorder(twin_ax.get_zorder() + 1)

        return twin_ax

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
            else:
                return VARIABLES_COLOR_DICT[var]
