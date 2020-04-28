from source.environment.EnvironmentSettings import EnvironmentSettings
from source.presentation.TemplateParser import TemplateParser
from source.presentation.html.Util import Util
from source.simulation.SimulationState import SimulationState
from source.util.StringHelper import StringHelper


class SimulationHTMLBuilder:
    """
    A class that will make a HTML file(s) out of SimulationState object to show what analysis took place in
    the SimulationInstruction.
    """

    CSS_PATH = f"{EnvironmentSettings.html_templates_path}css/custom.css"

    @staticmethod
    def build(state: SimulationState) -> str:
        """
        Function that builds the HTML files based on the Simulation state.
        Arguments:
            state:
        Returns:
             path to the main HTML file (which is located under state.result_path)
        """
        html_map = SimulationHTMLBuilder.make_html_map(state)
        result_file = f"{state.result_path}Simulation.html"

        TemplateParser.parse(template_path=f"{EnvironmentSettings.html_templates_path}Simulation.html",
                             template_map=html_map, result_path=result_file)

        return result_file

    @staticmethod
    def make_html_map(state: SimulationState) -> dict:

        html_map = {
            "css_style": Util.get_css_content(SimulationHTMLBuilder.CSS_PATH),
            "name": state.name,
            "dataset_name": state.dataset.name if state.dataset.name is not None else state.dataset.identifier,
            "dataset_type": " ".join(StringHelper.camel_case_to_words(type(state.dataset).__name__)),
            "example_count": state.dataset.get_example_count(),
            "implantings": [Util.to_dict_recursive(implanting) for implanting in state.simulation.implantings]
        }

        return html_map