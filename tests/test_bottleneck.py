import random
import unittest
import bottleneck.bottleneck as bt

class TestLogger(unittest.TestCase):
    def test_init(self):
        pass
    def test_close(self):
        pass
    def test_get(self):
        pass

class TestConfigurationParser(unittest.TestCase):
    def test_init(self):
        pass
    def test_load(self):
        pass
    def test_get(self):
        pass

class TestSection(unittest.TestCase):
    def test_init(self):
        assert bt.Section('name', {}), 'could not init Section without tags'
        assert bt.Section('name', { 'key0': 'value0', 'key1': 'value1'}), 'could not init Section with tags'
        
    def test_gather(self):
        assert bt.Section('name',  {}).gather(), 'could not gather Section'

    def test_get(self):
        assert bt.Section('name', { 'key0': 'value0', 'key1': 'value1'}).get()['key0'] == 'value0', 'could not get Section tags'

    def test_show(self):
        assert bt.Section('name', { 'key0': 'value0', 'key1': 'value1'}).show(), 'could not show Section'

class TestHardwareSection(unittest.TestCase):
    def test_init(self):
        assert bt.HardwareSection(), 'could not init HardwareSection'
    def test_gather(self):
        assert bt.HardwareSection().gather(), 'could not gather HardwareSection'
    def test_get(self):
        assert bt.HardwareSection().gather().get()['hardware'], 'could not get HardwareSection'

class TestProgramSection(unittest.TestCase):
    def test_init(self):
        assert bt.ProgramSection(), 'could not init ProgramSection'
    def test_gather(self):
        assert bt.ProgramSection().gather(), 'could not gather ProgramSection'
    def test_get(self):
        assert bt.ProgramSection().gather().get()['timestamp'], 'could not get ProgramSection'

class TestSoftwareSection(unittest.TestCase):
    def test_init(self):
        pass
    def test_gather(self):
        pass
    def test_get(self):
        pass

class TestBenchmarkSection(unittest.TestCase):
    def test_init(self):
        pass
    def test_gather(self):
        pass
    def test_get(self):
        pass

class TestWorkloadSection(unittest.TestCase):
    def test_init(self):
        pass
    def test_gather(self):
        pass
    def test_get(self):
        pass

class TestScalabilitySection(unittest.TestCase):
    def test_init(self):
        pass
    def test_gather(self):
        pass
    def test_get(self):
        pass

class TestProfileSection(unittest.TestCase):
    def test_init(self):
        pass
    def test_gather(self):
        pass
    def test_get(self):
        pass

class TestResourcesSection(unittest.TestCase):
    def test_init(self):
        pass
    def test_gather(self):
        pass
    def test_get(self):
        pass

class TestVectorizationSection(unittest.TestCase):
    def test_init(self):
        pass
    def test_gather(self):
        pass
    def test_get(self):
        pass

class TestCountersSection(unittest.TestCase):
    def test_init(self):
        pass
    def test_gather(self):
        pass
    def test_get(self):
        pass

class TestReport(unittest.TestCase):
    def test_init(self):
        pass

if __name__ == '__main__':
    unittest.main()
