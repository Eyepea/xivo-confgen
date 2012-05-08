import unittest
import StringIO
from mock import Mock, patch, ANY
from xivo_confgen.generators.agents_conf import AgentsConf


class TestAgents(unittest.TestCase):

    def assertConfigEqual(self, configExpected, configResult):
        self.assertEqual(configExpected.replace(' ', ''), configResult.replace(' ', ''))

    def setUp(self):
        self._output = StringIO.StringIO()


    def tearDown(self):
        pass

    generate_general = Mock()

    @patch.object(AgentsConf, '_generate_general')
    @patch.object(AgentsConf, '_generate_agents')
    def testGenerate(self, generate_general, generate_agents):

        agents_conf = AgentsConf([], [])

        agents_conf.generate(self._output)

        generate_general.assert_called_with(self._output)
        generate_agents.assert_called_with(self._output)

    def test_general_section(self):

        agent_general_db = [{'category': u'general',
                        'var_name': u'multiplelogin',
                        'var_val': u'yes'},
                            ]
        expected = """\
                    [general]
                    multiplelogin = yes
                    
                   """

        agents_conf = AgentsConf(agent_general_db, [])

        agents_conf._generate_general(self._output)

        self.assertConfigEqual(expected, self._output.getvalue())

    def test_agents_section(self):

        agent_db = [{'firstname':u'John', 'lastname':u'Wayne', 'number':u'3456', 'passwd': u'0022',
                     'autologoff':u'0', 'ackcall':u'no', 'acceptdtmf':u'#', 'enddtmf':u'*', 'wrapuptime':u'30000', 'musiconhold':u'default'},
                    {'firstname':u'Alfred', 'lastname':u'Bourne', 'number':u'7766', 'passwd': u'',
                     'autologoff':u'0', 'ackcall':u'no', 'acceptdtmf':u'#', 'enddtmf':u'*', 'wrapuptime':u'50000', 'musiconhold':u'classic'}, ]

        expected = """\
                    [agents]
                    
                    autologoff = 0
                    ackcall = no
                    acceptdtmf = #
                    enddtmf = *
                    wrapuptime = 30000
                    musiconhold = default
                    agent => 3456,0022,John Wayne
                    
                    autologoff = 0
                    ackcall = no
                    acceptdtmf = #
                    enddtmf = *
                    wrapuptime = 50000
                    musiconhold = classic
                    agent => 7766,,Alfred Bourne
                    
                   """
        agents_conf = AgentsConf([], agent_db)

        agents_conf._generate_agents(self._output)

        self.assertConfigEqual(expected, self._output.getvalue())

