import unittest
from xivo_confgen.frontends.asterisk.extensionsconf import ExtensionsConf


class Test(unittest.TestCase):


    def setUp(self):
        self.extensionsconf = ExtensionsConf(None,'context.conf')


    def tearDown(self):
        pass

    def test_generate_dialplan_from_template(self):
        template = ["%%EXTEN%%,%%PRIORITY%%,Set('XIVO_BASE_CONTEXT': ${CONTEXT})"]
        exten = {'exten':'*98', 'priority':1}
        result = self.extensionsconf.gen_dialplan_from_template(template, exten)

        self.assertEqual(result, "exten = *98,1,Set('XIVO_BASE_CONTEXT': ${CONTEXT})\n")



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()