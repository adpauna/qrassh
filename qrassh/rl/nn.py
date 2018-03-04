"""
The design of this comes from here:
http://outlace.com/Reinforcement-Learning-Part-3/
"""

from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.embeddings import Embedding
from keras.optimizers import RMSprop,Adam
from keras.layers import Bidirectional
from keras.layers.recurrent import LSTM
from keras.callbacks import Callback

class LossHistory(Callback):
    def on_train_begin(self, logs={}):
        self.losses = []

    def on_batch_end(self, batch, logs={}):
        self.losses.append(logs.get('loss'))


def neural_net(input_length,number_of_actions, params, load=''):
    model = Sequential()

    # First layer.
    model.add(Embedding(100, 32, input_length=input_length))
    if input_length==1:
        model.add(Dense(params[0], init='lecun_uniform'))
        model.add(Activation('relu'))
    else:
        model.add(Bidirectional(LSTM(params[0])))
    model.add(Dropout(0.2))

    # Second layer.
    model.add(Dense(params[1], init='lecun_uniform'))
    model.add(Activation('relu'))
    model.add(Dropout(0.2))

    # Output layer.
    model.add(Dense(number_of_actions, init='lecun_uniform'))
    model.add(Activation('linear'))

    optimizer = Adam()
    model.compile(loss='mse', optimizer=optimizer)

    if load:
        model.load_weights(load)

    return model
