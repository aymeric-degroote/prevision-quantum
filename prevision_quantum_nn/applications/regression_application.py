""" regression application module
    provides with the class for regression applications
"""

from prevision_quantum_nn.applications.application import Application
from prevision_quantum_nn.preprocessing.preprocess import Preprocessor
from prevision_quantum_nn.postprocessing.postprocess import Postprocessor
from prevision_quantum_nn.utils.get_model import get_model


class RegressionApplication(Application):
    """Regression Application.

    Attributes:
        model: (QuantumNeuralNetwork):model to be trained to
            solve the application
        preprocessor (Preprocessor):preprocessor to be used to
            solve the application
        postprocessor (Postprocessor):postprocessor to be used to
            solve the application
    """

    def __init__(self,
                 prefix="qnn",
                 preprocessing_params=None,
                 model_params=None,
                 postprocessing_params=None):
        """ constructor """
        super().__init__(prefix)

        # default params
        default_preprocessing_params = {"force_dimension_reduction": True}
        default_model_params = {
            "type_problem": "regression",
            "interface": "autograd"
        }
        default_postprocessing_params = dict()

        # combine preprocessing params
        if preprocessing_params:
            preprocessing_params = {
                **default_preprocessing_params,
                **preprocessing_params
            }
        else:
            preprocessing_params = default_preprocessing_params

        # combine preprocessing params
        if model_params:
            model_params = {
                **default_model_params,
                **model_params
            }
        else:
            model_params = default_model_params

        # combine postprocessing params
        if postprocessing_params:
            postprocessing_params = {
                **default_postprocessing_params,
                **postprocessing_params
            }
        else:
            postprocessing_params = default_postprocessing_params

        # init attributes
        self.preprocessor = Preprocessor(preprocessing_params)
        self.model = get_model(model_params)
        self.postprocessor = Postprocessor(postprocessing_params)

    def build(self):
        """ build the application according to dataset characteristics
        """
        # build model
        self.model.build()
        self.preprocessor.build_for_model(self.model.architecture_type,
                                          self.model.encoding,
                                          self.model.num_q,
                                          self.model.type_problem)

        self.logger.info("successfully built")
        self.log_params()

    def solve(self, dataset):
        """Solves the problem given a certain dataset.

        Args:
            dataset (DataSet):dataset to be solved with this application
        """
        self.dataset = dataset

        # build application
        self.build()

        # retrieve dataset as numpy array
        train_features, train_labels, \
            val_features, val_labels = self.dataset.to_numpy()

        # preprocess data
        train_features = self.preprocessor.fit_transform(train_features,
                                                         train_labels)

        # set validation data for plotter before preprocessing x_val
        # but after fit_transform
        self.postprocessor.build(preprocessor=self.preprocessor)
        if hasattr(self.postprocessor, "plotter") and \
                self.postprocessor.plotter:
            self.postprocessor.plotter.set_validation_data(val_features,
                                                           val_labels)

        if val_features is not None:
            val_features = self.preprocessor.transform(val_features)

        # save params and preprocessor before fit
        self.save_params()
        self.save_preprocessor()

        # fit model
        self.model.fit(train_features,
                       train_labels,
                       val_features=val_features,
                       val_labels=val_labels,
                       plotter_callback=self.postprocessor.callback)
