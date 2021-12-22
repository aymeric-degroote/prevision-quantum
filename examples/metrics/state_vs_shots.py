import pennylane as qml
import numpy as np

if __name__ == "__main__":

    circuit_bool = True
    num_q = 1
    n_sample = 2

    for shots in [10, 100, 1000]:
        print("\nnb shots =", shots)
        dev = qml.device("default.qubit", wires=num_q, shots=shots)


        @qml.qnode(dev)
        def circuit(variables):

            qml.StronglyEntanglingLayers(variables, wires=range(num_q))
            return qml.expval(qml.PauliZ(0))

        np.random.seed(12)
        for _ in range(n_sample):
            var = np.random.random((1, num_q, 3))
            print("var", var)

            if circuit_bool:
                circuit(var)

        npr = np.random.RandomState(12)
        for _ in range(n_sample):
            var_npr = npr.random((1, num_q, 3))
            print("var_npr", var_npr)

            if circuit_bool:
                circuit(var_npr)
