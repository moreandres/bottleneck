import random
import unittest
import bottleneck.bottleneck as bt
import subprocess
import os

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
        """Test how TestSection initialize."""
        bt.Tags().tags = {}
        assert bt.Section('name'), 'could not init Section without tags'
        bt.Tags().tags = { 'key0': 'value0', 'key1': 'value1'}
        assert bt.Section('name'), 'could not init Section with tags'
        
    def test_gather(self):
        bt.Tags().tags = {}
        assert bt.Section('name').gather(), 'could not gather Section'

    def test_get(self):
        bt.Tags().tags = { 'key0': 'value0', 'key1': 'value1'}
        assert bt.Section('name').get()['key0'] == 'value0', 'could not get Section tags'

    def test_show(self):
        bt.Tags().tags = { 'key0': 'value0', 'key1': 'value1'}
        assert bt.Section('name').show(), 'could not show Section'

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
        assert bt.SoftwareSection(), 'could not init SoftwareSection'
    def test_gather(self):
        assert bt.SoftwareSection().gather(), 'could not gather SoftwareSection'
    def test_get(self):
        assert bt.SoftwareSection().gather().get()['compiler'], 'could not get SoftwareSection'

class TestSanitySection(unittest.TestCase):
    def test_init(self):
        bt.Tags().tags = {
            'first': '512',
            'last': '1024',
            'increment': '64',
            'run': 'OMP_NUM_THREADS={0} N={1} ./{2}',
            'cores': '2',
            'size': '512',
            'program': 'matrix',
            'dir': 'tests/examples',
            'clean': 'make clean',
            'build': 'CFLAGS="{0}" make',
            'cflags': '-Wall -Wextra',
            }
        
        section = bt.SanitySection()
        assert section, 'could not init SanitySection'
        assert section.gather(), 'could not gather SanitySection'
        assert section.get(), 'could not get SanitySection'

class TestBenchmarkSection(unittest.TestCase):
    def test_init(self):
        assert bt.BenchmarkSection(), 'could not init BenchmarkSection'
    def test_gather(self):
        assert bt.BenchmarkSection().gather(), 'could not gather BenchmarkSection'
    def test_get(self):
        assert bt.BenchmarkSection().gather().get(), 'could not get BenchmarkSection'

class TestWorkloadSection(unittest.TestCase):
    def test_section(self):
        bt.Tags().tags = {
            'first': '512',
            'last': '512',
            'increment': '64',
            'run': 'OMP_NUM_THREADS={0} N={1} ./{2}',
            'cores': '2',
            'size': '512',
            'count': '32',
            'program': 'matrix',
            'dir': 'tests/examples',
            'clean': 'make clean',
            'build': 'CFLAGS="{0}" make',
            'cflags': '-Wall -Wextra',
            }
        section = bt.WorkloadSection()
        assert section, 'could not init WorkloadSection'
        assert section.gather(), 'could not init WorkloadSection'
        assert section.get(), 'could not get WorkloadSection'

class TestScalingSection(unittest.TestCase):        
    def test_section(self):
        bt.Tags().tags = {
            'first': '512',
            'last': '1024',
            'increment': '64',
            'run': 'OMP_NUM_THREADS={0} N={1} ./{2}',
            'cores': '2',
            'size': '512',
            'program': 'matrix',
            'dir': 'tests/examples',
            'clean': 'make clean',
            'build': 'CFLAGS="{0}" make',
            'cflags': '-Wall -Wextra',
            }
        section = bt.ScalingSection()
        assert section, 'could not init ScalingSection'
        assert section.gather(), 'could not gather ScalingSection'
        assert section.get(), 'could not get ScalingSection'

class TestProfileSection(unittest.TestCase):
    def test_init(self):
        assert bt.ProfileSection(), 'could not init ProfileSection'
    def test_gather(self):
        assert bt.ProfileSection().gather(), 'could not gather ProfileSection'
    def test_get(self):
        assert bt.ProfileSection().gather().get(), 'could not get ProfileSection'

class TestResourcesSection(unittest.TestCase):
    def test_init(self):
        assert bt.ResourcesSection(), 'could not init ResourcesSection'
    def test_gather(self):
        assert bt.ResourcesSection().gather(), 'could not gather ResourcesSection'
    def test_get(self):
        assert bt.ResourcesSection().gather().get(), 'could not get ResourcesSection'

class TestVectorizationSection(unittest.TestCase):
    def test_init(self):
        assert bt.VectorizationSection(), 'could not init VectorizationSection'
    def test_gather(self):
        assert bt.VectorizationSection().gather(), 'could not gather VectorizationSection'
    def test_get(self):
        assert bt.VectorizationSection().gather().get(), 'could not get VectorizationSection'

class TestCountersSection(unittest.TestCase):
    def test_init(self):
        assert bt.CountersSection(), 'could not init CountersSection'
    def test_gather(self):
        assert bt.CountersSection().gather(), 'could not gather CountersSection'
    def test_get(self):
        assert bt.CountersSection().gather().get(), 'could not get CountersSection'

class TestScript(unittest.TestCase):
    def test_install(self):
        assert subprocess.check_output('sudo python setup.py install', shell=True)
    def test_help(self):
        assert subprocess.check_output('sudo python setup.py install; bt --help', shell=True)
    def test_version(self):
        assert subprocess.check_output('sudo python setup.py install; bt --version', shell=True)

if __name__ == '__main__':
    unittest.main()
