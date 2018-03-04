import os
import random
import time

import pygeoip

from irassh.actions import dao
from irassh.rl import rl_state
from irassh.rl.learning import q_learner

# generate RL state
sequence_length = 10
nn_param = [128, 128]
params = {
    "batchSize": 64,
    "buffer": 5000,
    "nn": nn_param,
    "sequence_length": 10,  # The number of commands that make of a state
    "number_of_actions": 5,
    "cmd2number_reward": "irassh/rl/cmd2number_reward.p",
    "GAMMA": 0.9  # Forgetting.
}
rl_agent = q_learner(params)

class Action(object):
    def __init__(self, write):
        self.is_allowed = True
        self.write = write

    def process(self):
        """
        """

    def isPassed(self):
        return self.is_allowed

    def setPassed(self, passed):
        self.passed = passed

    def write(self, text):
        self.write(text)


class BlockedAction(Action):
    def __init__(self, write):
        super(BlockedAction, self).__init__(write)

        self.setPassed(False)

    def process(self):
        self.write("Blocked command!\n")

    def getActionName(self):
        return "Blocked"

    def getColor(self):
        return "31"


class DelayAction(Action):
    def process(self):
        time.sleep(3)
        self.setPassed(True)
        print("delay ...\n")

    def getActionName(self):
        return "Delay"

    def getColor(self):
        return "34"


class AllowAction(Action):
    def process(self):
        self.setPassed(True)

    def getActionName(self):
        return "Allow"

    def getColor(self):
        return "32"


class InsultAction(Action):
    def __init__(self, clientIp, write):
        super(InsultAction, self).__init__(write)

        self.clientIp = clientIp
        self.setPassed(False)

    def process(self):
        location = self.getCountryCode()
        print("Insult Message! IP= %s/location=%s\n" % (self.clientIp, location))
        self.write(dao.getIRasshDao().getInsultMsg(location.lower()) + "\n")

    def getCountryCode(self):
        path, file = os.path.split(__file__)
        file_name = os.path.join(path, "geo_ip.dat")
        print("Load geo_ip.dat from " + file_name)
        geo_ip = pygeoip.GeoIP(file_name)
        return geo_ip.country_code_by_addr(self.clientIp)

    def getActionName(self):
        return "Insult"

    def getColor(self):
        return "38"


class FakeAction(Action):
    def __init__(self, command, write):
        super(FakeAction, self).__init__(write)

        self.command = command
        self.setPassed(False)

    def process(self):
        fake_output = dao.getIRasshDao().getFakeOutput(self.command)
        if fake_output is not None:
            self.write(fake_output + "\n")

    def getActionName(self):
        return "Fake"

    def getColor(self):
        return "33"


class ActionGenerator(object):
    def generate(self):
        '''
        :return: action
        '''


class RandomActionGenerator(ActionGenerator):
    def generate(self):
        return random.randrange(0, 4)


class RlActionGenerator(ActionGenerator):
    def generate(self):
        print ("get action by q-learning", rl_state.current_command)
        rl_agent.train(rl_state.current_command)
        return rl_agent.choose_action()


class ActionFactory(object):

    def __init__(self, write, listener, generator):
        self.write = write
        self.listener = listener
        self.generator = generator
        pass

    def getAction(self, cmd, clientIp):
        action = self.generator.generate()
        print("Receive action: ", action)
        self.listener.handle(action)
        if action == 0:
            return AllowAction(self.write)
        elif action == 1:
            return DelayAction(self.write)
        elif action == 2:
            return FakeAction(cmd, self.write)
        elif action == 3:
            return InsultAction(clientIp, self.write)
        elif action == 4:
            return BlockedAction(self.write)


class ActionValidator(object):
    def __init__(self, factory):
        self.factory = factory
        pass

    def validate(self, cmd, clientIp):
        self.action = self.factory.getAction(cmd, clientIp)
        self.action.process()
        return self.action.isPassed()

    def getActionName(self):
        return self.action.getActionName()

    def getActionColor(self):
        return self.action.getColor()


class ActionPersister(object):
    def save(self, actionState, cmd):
        if "initial_cmd" in actionState.keys():
            print("Save next_cmd: " + cmd)
            actionState["next_cmd"] = cmd
            dao.getIRasshDao().saveCase(actionState)

        print("Save initial_cmd: " + cmd)
        actionState["initial_cmd"] = cmd


class ActionListener(object):
    def __init__(self, store):
        self.store = store
        pass

    def handle(self, action):
        self.store["action"] = action
