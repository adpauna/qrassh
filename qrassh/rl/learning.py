import numpy as np
import random
import csv
from nn import neural_net, LossHistory
import os.path
import timeit
import os
import pickle
import plotting


TUNING = False  # If False, just use arbitrary, pre-selected params.
# params example, not used. Please check qrassh/rl/rl_state.py
sequence_length = 10
nn_param = [128, 128]
params = {
    "batchSize": 64,
    "buffer": 5000,
    "nn": nn_param,
    "sequence_length": 10, # The number of commands that make of a state
    "number_of_actions": 5,
    "cmd2number_reward": "cmd2number_reward.p",
    "GAMMA" :  0.9  # Forgetting.
}



#get_command and do_action are not implemented
def train_qlearner(load=None, save=None):
    rl_agent = q_learner(params)
    print_cmd2reward(rl_agent.cmd2number_reward)
    if load is not None:
        rl_agent.load_model(load)
    while True:
        cmd = get_command()
        rl_agent.train(cmd)
        action = rl_agent.choose_action(isTrained=False)
        do_action(action)
    if save is not None:
        rl_agent.save_model(save)

def get_command():
    return ""

def print_cmd2reward(cmd2number_reward):
    for cmd in cmd2number_reward:
        print(cmd,"has reward",cmd2number_reward[cmd][1],"and the number",cmd2number_reward[cmd][0])

# Takes the command as text and returns the command as a number along with the reward
# The dummy atribute specifies that dummy could will be executed, not the real code
def get_command_reward(cmd2number, cmd2reward, dummy=True):
    if dummy:
        # Generate a random command
        cmd_num = random.randint(1, 57)
        # 56 is the "exit" command
        if cmd_num == 56:
            # resetez starea
            state = np.zeros(params["sequence_length"])
            state_index = 0
            state[0] = cmd_num

        # Find out what the reward is for the given command
        reward = cmd2reward[cmd_num]
    else:
        cmd = get_command_as_str()
        # Check if the command is known
        if cmd in cmd2number:
            cmd_num = cmd2number[cmd]
            reward = cmd2reward[cmd_num]
        else:
            cmd_num = cmd2number["unknown"]
            reward = cmd2reward["unknown"]
    return cmd_num, reward


# The dummy atribute specifies that dummy could will be executed, not the real code
def do_action(action, dummy=True):
    if not dummy:
        execute_response(action2text[action])




# Dummy function for training
def train_net_test(params):
    cmd2reward, cmd2number = get_cmd2reward()
    rl_agent = q_learner(params)
    state = np.zeros(params["sequence_length"])
    state_index = 0

    # Generate a random command
    cmd = random.randint(0, 58)

    # The state is a sequence of the last params["sequence_length"] commands given
    # Here the first command is inputed into the state
    state[state_index] = cmd
    state_index = state_index + 1
    for i in range(10000):
        action = rl_agent.choose_action(state)
        do_action(action)
        # Generate the next command along with the reward
        cmd, reward = get_command_reward(cmd2number, cmd2reward)

        if state_index == params["sequence_length"]:
            # The oldest command is erased and the newest is introduced
            np.roll(state, 1)
            state[params["sequence_length"] - 1] = cmd
        else:
            # The next command is added to the state
            state[state_index] = cmd
            state_index = state_index + 1
        rl_agent.update_replay(reward, state)

        # 56 is the "exit" command
        if cmd == 56:
            # The state is reset
            state = np.zeros(params["sequence_length"])
            state_index = 0

    rl_agent.log_results()


# Dummy function for play
def playing_test(params):
    cmd2reward, cmd2number = get_cmd2reward()
    rl_agent = q_learner(params)
    state = np.zeros(params["sequence_length"])
    state_index = 0

    # Generate a random command
    cmd = random.randint(0, 58)

    # The state is a sequence of the last params["sequence_length"] commands given
    # Here the first command is inputed into the state
    state[state_index] = cmd
    state_index = state_index + 1
    while True:
        # Genereate rl decision without logging for training
        action = rl_agent.nn_choose_action(state)
        do_action(action)
        # Generate a random command
        cmd = random.randint(1, 57)
        # 56 is the "exit" command

        # Look up reward for action
        reward = cmd2reward[cmd]

        if state_index == params["sequence_length"]:
            # The oldest command is erased and the newest is introduced
            np.roll(state, 1)
            state[params["sequence_length"] - 1] = cmd
        else:
            # The next command is added to the state
            state[state_index] = cmd
            state_index = state_index + 1

        # 56 is the "exit" command
        if cmd == 56:
        # The state is reset
            state = np.zeros(params["sequence_length"])
        state_index = 0


class q_learner:
    def __init__(self, params, load_replay_file=None, save_replay_file_prefix="replay",
                 save_model_file_prefix="saved-models/", save_every=500, end_value=-500):
        # This where the input values are saved so they can be used in other functions whithin the class

        # sequence_length specifies the number of commands that form a state
        self.sequence_length = params['sequence_length']
        # number_of_actions specifies the number of possible actions
        self.number_of_actions = params["number_of_actions"]
        # The neural network is build here
        self.model = neural_net(self.sequence_length, self.number_of_actions, params["nn"])
        # The name that will be used when saving the neural network model
        self.filename = params_to_filename(params)
        # Specifes the number of states to be inputed in replay before saving
        self.save_every = save_every
        # A prefix to the name of the replay file when saved
        self.save_replay_file_prefix = save_replay_file_prefix
        self.save_model_file_prefix = save_model_file_prefix
        # The value check for at the end of the "game"
        self.end_value = end_value
        # Forgetting value
        self.GAMMA  = params["GAMMA"]

        self.observe = 1000  # Number of frames to observe before training.
        self.epsilon = 1  # Chance to choose random action
        self.train_frames = 10000  # Number of frames to play.
        self.batchSize = params['batchSize']
        self.buffer = params['buffer']


        if isinstance(params["cmd2number_reward"], str):
            #if string load from file
            self.cmd2number_reward = pickle.load(open(params["cmd2number_reward"],"rb"))
        else:
            # if dictionary
            self.cmd2number_reward = params["cmd2number_reward"]

        self.state = np.zeros(params["sequence_length"])
        self.state_index = 0

        # Just stuff used below.
        self.max_hacker_cmds = 0
        self.hacker_cmds = 0
        self.t = 0
        self.data_collect = []
        if load_replay_file is None:
            self.replay = []  # stores tuples of (S, A, R, S').
        else:
            self.replay = pickle.load(open(load_replay_file, "rb"))

        self.loss_log = []

        # Let's time it.
        self.start_time = timeit.default_timer()
        self.state = np.zeros(10)
        self.lastAction = 0

    def save_model(self,filename):
        self.model.save_weights(filename,overwrite=True)

    def load_model(self, filename):
        self.model = neural_net(self.sequence_length, self.number_of_actions, params["nn"], filename)

    def train(self, cmd):
        # Check if the command is known
        if cmd in self.cmd2number_reward:
            cmd_num, reward = self.cmd2number_reward[cmd]
        else:
            cmd_num, reward = self.cmd2number_reward["unknown"]


        if self.state_index >= 1:
            if self.state_index == self.sequence_length:
                # The oldest command is erased and the newest is introduced
                np.roll(self.state, 1)
                self.state[self.sequence_length - 1] = cmd_num
            else:
                # The next command is added to the state
                self.state[self.state_index] = cmd_num
                self.state_index = self.state_index + 1

            self.update_replay(reward, self.state)
            # 56 is the "exit" command
            if cmd_num == 56:
                # The state is reset
                self.state = np.zeros(params["sequence_length"])
                self.state_index = 0
        else:
            # The state is a sequence of the last params["sequence_length"] commands given
            # Here the first command is inputed into the state
            self.state[self.state_index] = cmd_num
            self.state_index = self.state_index + 1



    def choose_action(self, isTrained = False):
        if isTrained:
            return self.choose_action_after_training(self.state)
        else:
            return self.choose_action_and_train(self.state)

    def choose_action_and_train(self, state):
        if len(state.shape) == 1:
            state = np.expand_dims(state, axis=0)
        self.t += 1
        self.hacker_cmds += 1

        # Choose an action.
        if random.random() < self.epsilon or self.t < self.observe:
            action = np.random.randint(0, self.number_of_actions)  # random
        else:
            # Get Q values for each action.
            qval = self.model.predict(state, batch_size=1)
            action = (np.argmax(qval))  # best
        self.lastAction = action
        return action

    def choose_action_after_training(self, state):
        if len(state.shape) == 1:
            state = np.expand_dims(state, axis=0)
        qval = self.model.predict(state, batch_size=1)
        action = (np.argmax(qval))
        return action

    def update_replay(self, reward, new_state, action=None):
        if action is None:
            action = self.lastAction

        # Experience replay storage.
        self.replay.append((np.copy(self.state), action, reward, np.copy(new_state)))

        # If we're done observing, start training.
        if self.t > self.observe:
            # If we've stored enough in our buffer, pop the oldest.
            if len(self.replay) > self.buffer:
                self.replay.pop(0)

            # Randomly sample our experience replay memory
            minibatch = random.sample(self.replay, self.batchSize)

            # Get training values.
            X_train, y_train = process_minibatch2(minibatch, self.model, self.sequence_length, self.end_value, self.GAMMA)

            # Train the model on this batch.
            history = LossHistory()
            self.model.fit(
                X_train, y_train, batch_size=self.batchSize,
                nb_epoch=1, verbose=0, callbacks=[history]
            )
            self.loss_log.append(history.losses)

            if self.t % self.save_every == 0:
                if len(self.data_collect) > 50:
                    # Save the results to a file so we can graph it later.
                    learn_f = 'results/command-frames/learn_data-' + self.filename + '.csv'
                    with open(learn_f, 'w', newline='') as data_dump:
                        wr = csv.writer(data_dump)
                        wr.writerows(self.data_collect)
                    plotting.plot_file(learn_f, 'learn')

                if len(self.loss_log) > 500:
                    loss_f = 'results/command-frames/loss_data-' + self.filename + '.csv'
                    with open(loss_f, 'w', newline='') as lf:
                        wr = csv.writer(lf)
                        for loss_item in self.loss_log:
                            wr.writerow(loss_item)

                    plotting.plot_file(loss_f, 'loss')


        # Update the starting state with S'.
        self.state = new_state

        # Decrement epsilon over time.
        if self.epsilon > 0.1 and self.t > self.observe:
            self.epsilon -= (1.0 / self.train_frames)

        # We died, so update stuff.
        if reward == -500:
            # Log the car's distance at this T.
            print([self.t, self.hacker_cmds])
            self.data_collect.append([self.t, self.hacker_cmds])

            # Update max.
            if self.hacker_cmds > self.max_hacker_cmds:
                self.max_hacker_cmds = self.hacker_cmds

            # Time it.
            tot_time = timeit.default_timer() - self.start_time
            fps = self.hacker_cmds / tot_time

            # Output some stuff so we can watch.
            print("Max: %d at %d\tepsilon %f\t(%d)\t%f fps" %
                  (self.max_hacker_cmds, self.t, self.epsilon, self.hacker_cmds, fps))

            # Reset.
            self.hacker_cmds = 0
            start_time = timeit.default_timer()

        # Save the model every 25,000 frames.
        if self.t % self.save_every == 0:
            pickle._dump(self.replay, open(self.save_replay_file_prefix + "-" + str(self.t), "wb"))
            model_save_filename = self.save_model_file_prefix + self.filename + '-' + str(self.t) + '.h5'
            self.model.save_weights(model_save_filename,
                                    overwrite=True)
            print("Saving model %s - %d" % (self.filename, self.t))


    def log_results(self):
        # Log results after we're done all frames.
        log_results(self.filename, self.data_collect, self.loss_log)


# In cmd2type.p a dictionary with the commands as keys and their types as values is saved in the pickle format
def get_cmd2reward(filename="cmd2type.p"):
    cmd2type = pickle.load(open(filename, "rb"))
    cmd2number_reward = dict()
    for cmd in cmd2type:
        if cmd2type[cmd][1] == 'general':
            cmd2number_reward[cmd] = (len(cmd2number_reward) + 1, 0)
        else:
            cmd2number_reward[cmd] = (len(cmd2number_reward) + 1, 500)
    cmd2number_reward["exit"] = (len(cmd2number_reward) + 1, -500)
    cmd2number_reward["unknown"] =(len(cmd2number_reward) + 1, 0)
    pickle.dump(cmd2number_reward,open("cmd2number_reward.p","wb"))
    return cmd2number_reward


def log_results(filename, data_collect, loss_log):
    # Save the results to a file so we can graph it later.
    with open('results/sonar-frames/learn_data-' + filename + '.csv', 'w') as data_dump:
        wr = csv.writer(data_dump)
        wr.writerows(data_collect)

    with open('results/sonar-frames/loss_data-' + filename + '.csv', 'w') as lf:
        wr = csv.writer(lf)
        for loss_item in loss_log:
            wr.writerow(loss_item)


def process_minibatch2(minibatch, model, sequence_length, end_value, GAMMA=0.9):
    # by Microos, improve this batch processing function
    #   and gain 50~60x faster speed (tested on GTX 1080)
    #   significantly increase the training FPS

    # instead of feeding data to the model one by one,
    #   feed the whole batch is much more efficient

    mb_len = len(minibatch)

    old_states = np.zeros(shape=(mb_len, sequence_length))
    actions = np.zeros(shape=(mb_len,))
    rewards = np.zeros(shape=(mb_len,))
    new_states = np.zeros(shape=(mb_len, sequence_length))

    for i, m in enumerate(minibatch):
        old_state_m, action_m, reward_m, new_state_m = m
        old_states[i, :] = old_state_m[...]
        actions[i] = action_m
        rewards[i] = reward_m
        new_states[i, :] = new_state_m[...]

    old_qvals = model.predict(old_states, batch_size=mb_len)
    new_qvals = model.predict(new_states, batch_size=mb_len)

    maxQs = np.max(new_qvals, axis=1)
    y = old_qvals
    abs_end_value = abs(end_value)
    non_term_inds = np.where(abs(rewards) != abs_end_value)[0]
    term_inds = np.where(abs(rewards) == abs_end_value)[0]

    y[non_term_inds, actions[non_term_inds].astype(int)] = rewards[non_term_inds] + (GAMMA * maxQs[non_term_inds])
    y[term_inds, actions[term_inds].astype(int)] = rewards[term_inds]

    X_train = old_states
    y_train = y
    return X_train, y_train


def process_minibatch(minibatch, model, number_of_actions, end_value, GAMMA=0.9):
    """This does the heavy lifting, aka, the training. It's super jacked."""
    global global_sequence_length
    X_train = []
    y_train = []
    # Loop through our batch and create arrays for X and y
    # so that we can fit our model at every step.
    for memory in minibatch:
        # Get stored values.
        old_state_m, action_m, reward_m, new_state_m = memory
        # Get prediction on old state.
        old_qval = model.predict(old_state_m, batch_size=1)
        # Get prediction on new state.
        newQ = model.predict(new_state_m, batch_size=1)
        # Get our predicted best move.
        maxQ = np.max(newQ)
        y = np.zeros((1, number_of_actions))
        y[:] = old_qval[:]
        # Check for terminal state.
        if reward_m != end_value:  # non-terminal state
            update = (reward_m + (GAMMA * maxQ))
        else:  # terminal state
            update = reward_m
        # Update the value for the action we took.
        y[0][action_m] = update
        X_train.append(old_state_m.reshape(sequence_length, ))
        y_train.append(y.reshape(number_of_actions, ))

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    return X_train, y_train


# Generates a name for saving
def params_to_filename(params):
    return str(params['nn'][0]) + '-' + str(params['nn'][1]) + '-' + \
           str(params['batchSize']) + '-' + str(params['buffer'])


if __name__ == "__main__":
    train_qlearner()
