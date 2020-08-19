import datetime

from source.data_model.dataset.Dataset import Dataset
from source.hyperparameter_optimization.HPSetting import HPSetting
from source.hyperparameter_optimization.core.HPSelection import HPSelection
from source.hyperparameter_optimization.core.HPUtil import HPUtil
from source.hyperparameter_optimization.states.HPAssessmentState import HPAssessmentState
from source.hyperparameter_optimization.states.HPOptimizationState import HPOptimizationState
from source.ml_methods.MLMethod import MLMethod
from source.reports.ReportUtil import ReportUtil
from source.util.PathBuilder import PathBuilder
from source.workflows.instructions.MLProcess import MLProcess


class HPAssessment:

    @staticmethod
    def run_assessment(state: HPOptimizationState) -> HPOptimizationState:

        state = HPAssessment._create_root_path(state)
        train_val_datasets, test_datasets = HPUtil.split_data(state.dataset, state.assessment, state.path)

        for index in range(len(train_val_datasets)):
            state = HPAssessment.run_assessment_split(state, train_val_datasets[index], test_datasets[index], index)

        state.hp_report_results = HPUtil.run_hyperparameter_reports(state, f"{state.path}hyperparameter_reports/")
        state.data_report_results = ReportUtil.run_data_reports(state.dataset, list(state.data_reports.values()), f"{state.path}data_reports/",
                                                                state.context)

        return state

    @staticmethod
    def _create_root_path(state: HPOptimizationState) -> HPOptimizationState:
        state.path = f"{state.path}{state.name}/"
        return state

    @staticmethod
    def run_assessment_split(state, train_val_dataset, test_dataset, split_index: int):
        """run inner CV loop (selection) and retrain on the full train_val_dataset after optimal model is chosen"""

        print(f'{datetime.datetime.now()}: Hyperparameter optimization: running outer CV loop: started assessment split {split_index+1}.\n')

        current_path = HPAssessment.create_assessment_path(state, split_index)

        assessment_state = HPAssessmentState(split_index, train_val_dataset, test_dataset, current_path, state.label_configuration)
        state.assessment_states.append(assessment_state)

        state = HPSelection.run_selection(state, train_val_dataset, current_path, split_index)

        state = HPAssessment.run_assessment_split_per_label(state, split_index)

        print(f'{datetime.datetime.now()}: Hyperparameter optimization: running outer CV loop: finished assessment split {split_index+1}.\n')

        return state

    @staticmethod
    def run_assessment_split_per_label(state: HPOptimizationState, split_index: int):
        """iterate through labels and hp_settings and retrain all models"""
        for label in state.label_configuration.get_labels_by_name():

            path = f"{state.assessment_states[split_index].path}"

            for index, hp_setting in enumerate(state.hp_settings):

                if hp_setting != state.assessment_states[split_index].label_states[label].optimal_hp_setting:
                    setting_path = f"{path}{label}_{hp_setting}/"
                else:
                    setting_path = f"{path}{label}_{hp_setting}_optimal/"

                train_val_dataset = state.assessment_states[split_index].train_val_dataset
                test_dataset = state.assessment_states[split_index].test_dataset
                state = HPAssessment.reeval_on_assessment_split(state, train_val_dataset, test_dataset, hp_setting, setting_path, label, split_index)

        return state

    @staticmethod
    def reeval_on_assessment_split(state, train_val_dataset: Dataset, test_dataset: Dataset, hp_setting: HPSetting, path: str, label: str,
                                   split_index: int) -> MLMethod:
        """retrain model for specific label, assessment split and hp_setting"""

        assessment_item = MLProcess(train_dataset=train_val_dataset, test_dataset=test_dataset, label=label, metrics=state.metrics,
                                    optimization_metric=state.optimization_metric, path=path, hp_setting=hp_setting, report_context=state.context,
                                    ml_reports=state.assessment.reports.model_reports.values(), number_of_processes=state.batch_size,
                                    encoding_reports=state.assessment.reports.encoding_reports.values(), label_config=state.label_configuration)\
            .run(split_index)

        state.assessment_states[split_index].label_states[label].assessment_items[hp_setting] = assessment_item

        return state

    @staticmethod
    def create_assessment_path(state, split_index):
        current_path = f"{state.path}split_{split_index+1}/"
        PathBuilder.build(current_path)
        return current_path
