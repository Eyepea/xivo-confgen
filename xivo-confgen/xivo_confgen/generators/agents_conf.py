from xivo_confgen.generators.util import format_ast_option
class AgentsConf(object):

    def __init__(self, general, agent_global_params, agents):
        self._general = general
        self._agent_global_params = agent_global_params
        self._agents = agents


    def generate(self, output):
        self._generate_general(output)
        self._generate_agent_global_params(output)
        self._generate_agents(output)

    def _generate_general(self, output):
        print >> output, u'[general]'
        for item in self._general:
            print >> output, format_ast_option(item['option_name'], item['option_value'])
        print >> output

    def _generate_agent_global_params(self, output):
        print >> output, u'[agents]'
        for item in self._agent_global_params:
            print >> output, format_ast_option(item['option_name'], item['option_value'])
        print >> output

    def _generate_agents(self, output):
        agent_options = ['autologoff', 'ackcall', 'acceptdtmf', 'enddtmf', 'wrapuptime', 'musiconhold']
        for agent in self._agents:
            for option in agent_options:
                print >> output, format_ast_option(option, agent[option])
            print >> output, self._format_agent_line(agent)
            print >> output

    def _format_agent_line(self, agent):
        return u'agent => %s,%s,%s %s' % (agent['number'], agent['passwd'], agent['firstname'], agent['lastname'])

    @classmethod
    def new_from_backend(cls, backend):
        general = backend.agentglobalparams.all(category='general')
        agent_global_params = backend.agentglobalparams.all(category='agents')
        agents = backend.agentfeatures.all(commented=False)
        return cls(general, agent_global_params, agents)



