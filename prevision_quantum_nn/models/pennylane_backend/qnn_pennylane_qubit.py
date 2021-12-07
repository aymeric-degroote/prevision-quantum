""" Qubit module"""

import tensorflow as tf
import pennylane as qml
import pennylane.numpy as np
import math

from prevision_quantum_nn.models.pennylane_backend.pennylane_ansatz import \
    AnsatzBuilder
from prevision_quantum_nn.models.pennylane_backend.qnn_pennylane \
        import PennylaneNeuralNetwork


class PennylaneQubitNeuralNetwork(PennylaneNeuralNetwork):
    """Class PennylaneQubitNeuralNetwork.

    Implements a neural network on a discrete qubit architecture

    Attributes:
        dev (qml.device):device to be used to train the model
    """
    def __init__(self, params):
        """Constructor.

        Args:
            params (dictionnary):parameters of the model
        """
        super().__init__(params)
        self.architecture_type = "discrete"
        self.encoding = self.params.get("encoding", "angle")
        self.backend = self.params.get("backend", "default.qubit.tf")
        self.layer_name = self.params.get("layer_name",
                                          "StronglyEntanglingLayers")

        self.check_encoding()

    def build_model(self):
        """ builds the device and the qnode"""
        self.ansatz_builder = AnsatzBuilder(self.num_q,
                                            self.num_layers,
                                            self.layer_name)
        self.ansatz_builder.build()

        def neural_network(var, features=None):
            """Neural_network, decorated by a pennylane qnode.

            Args:
                var (list):list of weights of the model
                features (array or tf.Tensor):observations to be passed
                    through the neural network

            Returns:
                list:predictions of the model
            """

            # encode data
            self.encode_data(features)

            # layers
            self.layers(var)

            return self.output_layer()

        self.ansatz = neural_network

    def build(self, weights_file=None):
        """ builds the backend and the device """
        super().build(weights_file=weights_file)
        # build backend
        if self.interface == "autograd":
            self.backend = "default.qubit.autograd"
        elif self.interface == "tf":
            self.backend = "default.qubit.tf"
        # build device
        self.dev = qml.device(self.backend, wires=self.num_q)

        self.neural_network = qml.QNode(self.ansatz,
                                        self.dev,
                                        interface=self.interface)

    def check_encoding(self):
        """Checks encoding consistency.

        Raises:
            ValueError if invalid encoding for qubit calculation
        """
        valid_encoding = ["angle", "amplitude", "mottonen", "no_encoding"]
        if self.encoding not in valid_encoding:
            raise ValueError("Invalid encoding for qubit neural network. "
                             f"Valid encoding are: {', '.join(valid_encoding)}")

    def initialize_weights(self, weights_file=None):
        """Initializes weights.

        Args:
            weights_file (str):option, if None, the weights will be initialized
                randomly if not None, weights will be loaded from file
        """
        if weights_file is not None:
            self.load_weights(weights_file)
        else:
            low, high = self.ansatz_builder.variables_range
            var_shape = self.ansatz_builder.variables_shape

            var_init = np.random.uniform(low=low, high=high, size=var_shape)

            if self.interface == "tf":
                var_init = tf.Variable(var_init)
            self.var = var_init

    def encode_data(self, features):
        """Encodes data according to encoding method."""

        wires = range(self.num_q)

        # amplitude encoding mode
        if self.encoding == "amplitude":
            qml.templates.embeddings.AmplitudeEmbedding(features,
                                                        wires=wires,
                                                        normalize=True)
        # angle encoding mode
        elif self.encoding == "angle":
            qml.templates.embeddings.AngleEmbedding(features,
                                                    wires=wires)
        elif self.encoding == "mottonen":
            norm = np.sum(np.abs(features) ** 2)
            features = features / math.sqrt(norm)
            qml.templates.state_preparations.MottonenStatePreparation(
                features, wires=wires)
        elif self.encoding == "no_encoding":
            pass

    def layers(self, variables):
        """Layers of the model.

        Depending on layer_type, the layers will either be
        custom or template

        Args:
            variables (list):weights of the model
        """

        # todo: remove this condition, it is similar to StronglyEntanglingLayers
        if self.num_q == 1:
            for var in variables:
                for k in range(self.num_q):
                    qml.Rot(var[0], var[1], var[2], wires=k)

        # custom layer
        if self.layer_type == "custom":
            # todo: implement custom layers
            pass
        # template layer
        elif self.layer_type == "template":
            self.ansatz_builder.ansatz(variables)
        else:
            raise ValueError(f"Unrecognized layer_type: {self.layer_type}")

    def output_layer(self):
        """Output layer.

        Returns:
            list: quantum observables
        """
        expectations = None
        if self.type_problem == "classification" or \
                self.type_problem == "regression":
            expectations = qml.expval(qml.PauliZ(0))
        elif self.type_problem == "multiclassification" or \
                self.type_problem == "reinforcement_learning":
            expectations = [qml.expval(qml.PauliZ(i))
                            for i in range(self.num_categories)]
        elif self.type_problem == "descriptor_computation":
            expectations = qml.state()
        return expectations
