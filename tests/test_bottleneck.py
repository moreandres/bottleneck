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
        assert bt.SoftwareSection(), 'could not init SoftwareSection'
    def test_gather(self):
        assert bt.SoftwareSection().gather(), 'could not gather SoftwareSection'
    def test_get(self):
        assert bt.SoftwareSection().gather().get()['compiler'], 'could not get SoftwareSection'

class TestSanitySection(unittest.TestCase):
    def test_init(self):
        assert bt.SanitySection(), 'could not init SanitySection'
    def test_gather(self):
        section = bt.SanitySection()
        section.tags.update({ 'build': 'CFLAGS={0} make', 'run': 'OMP_NUM_THREADS={0} N={1} ./{2}', 'cores' : '1', 'first': '1024'})
        assert section.gather(), 'could not gather SanitySection'
    def test_get(self):
        assert bt.SanitySection().gather().get(), 'could not get SanitySection'

class TestBenchmarkSection(unittest.TestCase):
    def test_init(self):
        assert bt.BenchmarkSection(), 'could not init BenchmarkSection'
    def test_gather(self):
        assert bt.BenchmarkSection().gather(), 'could not gather BenchmarkSection'
    def test_get(self):
        assert bt.BenchmarkSection().gather().get(), 'could not get BenchmarkSection'

class TestWorkloadSection(unittest.TestCase):
    def test_init(self):
        assert bt.WorkloadSection(), 'could not init WorkloadSection'
    def test_gather(self):
        assert bt.WorkloadSection().gather(), 'could not gather WorkloadSection'
    def test_get(self):
        assert bt.WorkloadSection().gather().get(), 'could not get WorkloadSection'

class TestScalabilitySection(unittest.TestCase):
    def test_init(self):
        assert bt.ScalabilitySection(), 'could not init ScalabilitySection'
    def test_gather(self):
        assert bt.ScalabilitySection().gather(), 'could not gather ScalabilitySection'
    def test_get(self):
        assert bt.ScalabilitySection().gather().get(), 'could not get ScalabilitySection'

class TestHistogramSection(unittest.TestCase):
    def test_init(self):
        assert bt.HistogramSection(), 'could not init HistogramSection'
    def test_gather(self):
        assert bt.HistogramSection().gather(), 'could not gather HistogramSection'
    def test_get(self):
        assert bt.HistogramSection().gather().get(), 'could not get HistogramSection'

class TestScalingSection(unittest.TestCase):
    def test_init(self):
        assert bt.ScalingSection(), 'could not init ScalingSection'
    def test_gather(self):
        assert bt.ScalingSection().gather(), 'could not gather ScalingSection'
    def test_get(self):
        assert bt.ScalingSection().gather().get(), 'could not get ScalingSection'

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

if __name__ == '__main__':
    unittest.main()
