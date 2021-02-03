#
# Copyright 2018 Analytics Zoo Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import sys
import numpy as np
from optparse import OptionParser

import tensorflow.keras.backend as K
from tensorflow.keras import Sequential
from tensorflow.keras.layers import *
from tensorflow.keras.optimizers import SGD

from zoo.orca.data import XShards
from zoo.orca.learn.tf.estimator import Estimator
from zoo.orca import init_orca_context, stop_orca_context


def mean_absolute_error(y_true, y_pred):
    result = K.mean(K.abs(y_true - y_pred), axis=1)
    return result


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--cluster_mode', type=str, default="local",
                      help='The mode for the Spark cluster. local or yarn.')
    parser.add_option("--nb_epoch", dest="nb_epoch", default="500")
    (options, args) = parser.parse_args(sys.argv)

    cluster_mode = options.cluster_mode
    if cluster_mode == "local":
        sc = init_orca_context()
    elif cluster_mode == "yarn":
        sc = init_orca_context(cluster_mode="yarn-client", num_nodes=2)
    else:
        print("init_orca_context failed. cluster_mode should be either 'local' or 'yarn' but got "
              + cluster_mode)

    data_len = 1000
    X_ = np.random.uniform(0, 1, (1000, 2))
    Y_ = ((2 * X_).sum(1) + 0.4).reshape([data_len, 1])
    train_dataset = XShards.partition({'x': X_, 'y': Y_})
    model = Sequential()
    model.add(Dense(1, input_shape=(2,)))
    model.compile(optimizer=SGD(learning_rate=1e-2),
                  loss=mean_absolute_error,
                  metrics=None)

    est = Estimator.from_keras(keras_model=model)
    est.fit(data=train_dataset,
            batch_size=32,
            epochs=int(options.nb_epoch),
            validation_data=None
            )

    model = est.get_model()
    w = model.get_weights()
    print(w)
    pred = model.predict(X_)
    print(pred)
    print("finished...")
    stop_orca_context()
