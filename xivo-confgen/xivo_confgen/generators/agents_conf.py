from xivo_confgen.generators.util import format_ast_option
class AgentsConf(object):

    def __init__(self, general, agents):
        self._general = general
        self._agents = agents


    def generate(self, output):
        self._generate_general(output)
        self._generate_agents(output)

    def _generate_general(self, output):
        print >> output, u'[general]'
        for item in self._general:
            print >> output, format_ast_option(item['var_name'], item['var_val'])
        print >> output

    def _generate_agents(self, output):
        agent_options = ['autologoff', 'ackcall', 'acceptdtmf', 'enddtmf', 'wrapuptime', 'musiconhold']
        print >> output, u'[agents]'
        print >> output
        for agent in self._agents:
            for option in agent_options:
                print >> output, format_ast_option(option, agent[option])
            print >> output, self._format_agent_line(agent)
            print >> output

    def _format_agent_line(self, agent):
        return u'agent => %s,%s,%s %s' % (agent['number'], agent['passwd'], agent['firstname'], agent['lastname'])

    @classmethod
    def new_from_backend(cls, backend):
        general = backend.agent.all(commented=False, category='general')
        agents = backend.agentfeatures.all(commented=False)
        return cls(general, agents)



