from pathlib import Path
from typing import List
import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from immuneML.data_model.dataset.Dataset import Dataset
from immuneML.hyperparameter_optimization.HPSetting import HPSetting
from immuneML.ml_methods.MLMethod import MLMethod
from immuneML.reports.ReportOutput import ReportOutput
from immuneML.reports.ReportResult import ReportResult
from immuneML.reports.ml_reports.MLReport import MLReport
from immuneML.util.PathBuilder import PathBuilder


class ConfounderAnalysis(MLReport):
    """
    A report that plots the distributions of the false positives and the false negatives made by a given ML method in a barplot.
    These metrics are ploted separately with respect to each of the metadata features specified by the user.

    Arguments:

        metadata_labels (list): A list of the metadata features to use as a basis for the calculations
    """

    @classmethod
    def build_object(cls, **kwargs):
        metadata_labels = kwargs["metadata_labels"]

        if not isinstance(metadata_labels, list):
            raise TypeError("metadata_labels is not a list")

        if not all(isinstance(i, str) for i in metadata_labels):
            raise TypeError("Some elements in metadata_labels are not of type str")

        return ConfounderAnalysis(metadata_labels=metadata_labels)

    def __init__(self, metadata_labels: List[str], train_dataset: Dataset = None, test_dataset: Dataset = None,
                 method: MLMethod = None,
                 result_path: Path = None, name: str = None, hp_setting: HPSetting = None, label=None):
        super().__init__(train_dataset, test_dataset, method, result_path, name, hp_setting, label)

        self.metadata_labels = metadata_labels

    def _generate(self) -> ReportResult:
        PathBuilder.build(self.result_path)
        paths = []

        # make predictions
        predictions = self.method.predict(self.test_dataset.encoded_data, self.label)[self.label]  # label = disease

        true_labels = self.test_dataset.get_metadata(self.metadata_labels + [self.label])

        plot = make_subplots(rows=len(self.metadata_labels), cols=2)
        for label_index, meta_label in enumerate(self.metadata_labels):
            for metric_index, metric in enumerate(["FP", "FN"]):
                output_name = metric + "_" + meta_label

                plotting_data = self._metrics(metric=metric, label=self.label, meta_label=meta_label,
                                              predictions=predictions, true_labels=true_labels)

                plot.add_trace(go.Bar(x=plotting_data[meta_label], y=plotting_data[metric]), row=label_index + 1,
                               col=metric_index + 1)

                plot.update_xaxes(title_text=f"{meta_label}", row=label_index + 1,
                                  col=metric_index + 1)

                plot.update_yaxes(title_text=f"{metric}", row=label_index + 1,
                                  col=metric_index + 1)

        plot.update_traces(marker_color=px.colors.sequential.Teal[3], showlegend=False)
        filename = self.result_path / f"{output_name}.html"
        plot.write_html(str(filename))
        report_output_fig = ReportOutput(filename)
        paths.append(report_output_fig)

        return ReportResult(name=self.name, output_figures=paths)

    @staticmethod
    def _metrics(metric, label, meta_label, predictions, true_labels):
        # indices of samples at which misclassification occured
        if metric == "FP":
            metric_inds = np.nonzero(np.greater(predictions, true_labels[label]))[0].tolist()
        else:
            metric_inds = np.nonzero(np.less(predictions, true_labels[label]))[0].tolist()

        # indices of misclassification with respect to the metadata label
        label_inds = np.array(true_labels[meta_label])[metric_inds]

        # number of misclassifications at Val_1 = TRUE of the metadata label
        metric_val = np.count_nonzero(label_inds)

        plotting_data = pd.DataFrame(
            {f"{metric}": [len(label_inds) - metric_val, metric_val], f"{meta_label}": [False, True]})

        return plotting_data
