import unittest
from xivo_confgen.frontends.asterisk.extensionsconf import ExtensionsConf
from StringIO import StringIO
from mock import Mock


class TestExtensionsConf(unittest.TestCase):


    def assertConfigEqual(self, configExpected, configResult):
        self.assertEqual(configExpected.replace(' ', ''), configResult.replace(' ', ''))

    def setUp(self):
        self.extensionsconf = ExtensionsConf(None, 'context.conf')

    def tearDown(self):
        pass

    def test_generate_dialplan_from_template(self):
        output = StringIO()
        template = ["%%EXTEN%%,%%PRIORITY%%,Set('XIVO_BASE_CONTEXT': ${CONTEXT})"]
        exten = {'exten':'*98', 'priority':1}
        self.extensionsconf.gen_dialplan_from_template(template, exten, output)

        self.assertEqual(output.getvalue(), "exten = *98,1,Set('XIVO_BASE_CONTEXT': ${CONTEXT})\n\n")


    def test_generate_voice_menus(self):
        output = StringIO()
        voicemenus = [{'name': u'menu1',
                       },
                      {'name': u'menu2',
                       }
                      ]
        
        self.extensionsconf.backend = Mock()
        self.extensionsconf.backend.extensions.all.return_value = \
            [{'exten':u'2300','app':u'GoSub','priority':1,'appdata':u'    endcall,s,1(hangup)'}]
        self.extensionsconf.generate_voice_menus(voicemenus, output)
        
        
        self.assertConfigEqual("""\
                                        [voicemenu-menu1]
                                        exten=2300,1,GoSub(endcall,s,1(hangup))
                                        
                                        [voicemenu-menu2]
                                        exten=2300,1,GoSub(endcall,s,1(hangup))
                                        
                                        """, output.getvalue())

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
