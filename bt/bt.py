#! /usr/bin/env python

"""
Bottleneck - Performance report generator.
"""

import ConfigParser
import argparse
import logging
import os
import subprocess
import numpy
import scipy.stats
import time
import multiprocessing
import matplotlib.pyplot
import re
import datetime
import socket
import platform

from pylint import epylint as lint

class Logger:
    """Enable logging."""

    def __init__(self, name):
        """Store all logs in file, show only errors in console."""

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        fileh = logging.FileHandler(name + '.log')
        fileh.setLevel(logging.DEBUG)
        consoleh = logging.StreamHandler()
        consoleh.setLevel(logging.DEBUG)
        fmt = '%(asctime)s: %(levelname)s: %(message)s'
        formatter = logging.Formatter(fmt, datefmt="%Y%m%d-%H%M%S")
        fileh.setFormatter(formatter)
        consoleh.setFormatter(formatter)
        self.logger.addHandler(fileh)
        self.logger.addHandler(consoleh)

    def close(self):
        """Close logging."""

        return self
        
    def get(self):
        """Get logger instance."""

        return self.logger

LOG = Logger('bt').get()

class ConfigurationParser:
    """ Parse configuration."""

    def __init__(self):
        """Empty configuration."""
        self.config = None
        self.parser = None
        self.args = None
        LOG.debug('Starting configuration parser')

    def load(self):
        """Load arguments and configuration from file."""
        description = 'Generate performance report for OpenMP programs.'
        epilog = 'Check github readme for more details.'
        self.parser = argparse.ArgumentParser(description=description,
                                              epilog=epilog,
                                              version='0.0.1')
        self.parser.add_argument('--config', '-c',
                                 help='path to configuration',
                                 default='/home/amore/bt/bt.cfg')
        LOG.debug('Parsing arguments')
        self.args = self.parser.parse_args()
        self.config = ConfigParser.ConfigParser()
        LOG.debug('Loading configuration from {0}'.format(self.args.config))
        self.config.read(self.args.config)
        return self

    def get(self, key, section='default'):
        """Get configuration attribute."""
        value = self.config.get(section, key)
        LOG.debug('Getting {0} from config: {1}'.format(key, value))
        return value

CFG = ConfigurationParser().load()

class Test:
    """Test."""
    def __init__(self):
        """Do nothing."""
        pass

    def test_matrix(self):
        """Analyze matrix multiplication kernel."""
        directory = 'matrix'
        command = 'cd {0}; ../{1}'.format(directory, 'bt.py')
        subprocess.check_call(command, shell = True)

    def test_heat2d(self):
        """Analyze heat 2D simulation kernel."""
        directory = 'heat2d'
        command = 'cd {0}; ../{1}'.format(directory, 'bt.py')
        retcode = subprocess.call(command, shell = True)
        assert retcode == 0

    def test_mandel(self):
        """Analyze mandelbrot set kernel."""
        directory = 'mandel'
        command = 'cd {0}; ../{1}'.format(directory, 'bt.py')
        retcode = subprocess.call(command, shell = True)
        assert retcode == 0
    
    def test_pylint(self):
        """ Check source code using pylint. """

        (stdout, stderr) = lint.py_run(__file__, True)
        output = stdout.readlines()
        error = stderr.readlines()
        assert len(output) == 0, output
        assert len(error) == 0, error

def main():

    cwd = os.path.abspath('.')
    program = os.path.basename(cwd)

    timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    logdir = '~/.bt/{0}-{1}'.format(program, timestamp)
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    macros = {}

    macros['timestamp'] = timestamp
    macros['log'] = logdir

    macros['host'] = socket.getfqdn()

    macros['distro'] = ', '.join(platform.linux_distribution())
    macros['platform'] = platform.platform()
    command = 'lshw -short -sanitize | cut -b25-'
    macros['hardware'] = subprocess.check_output(command, shell = True)

    command = 'gcc --version | head -n1'
    macros['compiler'] = subprocess.check_output(command, shell = True).strip()

    command = '/lib/x86_64-linux-gnu/libc.so.6 | head -n1'
    macros['libc'] = subprocess.check_output(command, shell = True).strip()

    macros['cwd'] = cwd
    macros['program'] = program

    count = CFG.get('count')
    build = CFG.get('build')
    run = CFG.get('run')
    first, last, increment = CFG.get('range', program).split(',')

    macros['range'] = str(range(int(first), int(last), int(increment)))

    cores = str(multiprocessing.cpu_count())

    macros['count'] = count
    macros['build'] = build
    macros['run'] = run
    macros['first'] = first
    macros['last'] = last
    macros['increment'] = increment
    macros['cores'] = cores

    test = ' && '.join([ build.format('-O3'),
                        run.format(cores, first, program) ])
    subprocess.check_call(test, shell = True)
    LOG.debug("Sanity test returned status 0")

    benchmark = 'mpirun `which hpcc` && cat hpccoutf.txt'
    # output = subprocess.check_output(benchmark, shell = True)
    # metrics = [ ('success', r'Success=(\d+.*)', None),
    #             ('hpl', r'HPL_Tflops=(\d+.*)', 'TFlops'),
    #             ('dgemm', r'StarDGEMM_Gflops=(\d+.*)', 'GFlops'),
    #             ('ptrans', r'PTRANS_GBs=(\d+.*)', 'GBss'),
    #             ('random', r'StarRandomAccess_GUPs=(\d+.*)', 'GUPss'),
    #             ('stream', r'StarSTREAM_Triad=(\d+.*)', 'MBs'),
    #             ('fft', r'StarFFT_Gflops=(\d+.*)', 'GFlops'), ]

    # for metric in metrics:
    #     match = re.search(metric[1], output).group(1)
    #     macros['hpcc-{0}'.format(metric[0])] = '{0} {1}'.format(match,
    #                                                             metric[2])

    LOG.debug("System baseline completed.")

    times = []
    for i in range(0, int(count)):
        start = time.time()
        subprocess.call(run.format(cores, first, program), shell = True)
        end = time.time()
        elapsed = end - start
        times.append(elapsed)
        LOG.debug("Control {0} took {1:.2f} seconds".format(i, elapsed))
    array = numpy.array(times)
    LOG.debug("Deviation: gmean {0:.2f} std {1:.2f}".format(scipy.stats.gmean(array),
                                                            numpy.std(array)))

    macros['geomean'] = str(scipy.stats.gmean(array))
    macros['stddev'] = str(numpy.std(array))

    # min/max

    buckets, bins, patches = matplotlib.pyplot.hist(times,
                                                    bins=16,
                                                    normed=True)
    matplotlib.pyplot.plot(bins, 
                           scipy.stats.norm.pdf(bins,
                                                loc = numpy.mean(array),
                                                scale = array.std()),
                           'r--')
    matplotlib.pyplot.xlabel('time in seconds')
    matplotlib.pyplot.ylabel('ocurrences in units')
    matplotlib.pyplot.title('histogram')
    matplotlib.pyplot.savefig('hist.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted histogram")

    data = []
    for n in range(int(first), int(last) + 1, int(increment)):
        start = time.time()
        subprocess.call(run.format(cores, n, program), shell = True)
        end = time.time()
        elapsed = end - start
        data.append(elapsed)
        LOG.debug("Problem at {0} took {1:.2f} seconds".format(n, elapsed))
    array = numpy.array(data)

    matplotlib.pyplot.plot(data)
    matplotlib.pyplot.xlabel('problem size in bytes')
    matplotlib.pyplot.ylabel('time in seconds')
    matplotlib.pyplot.title('data size scaling')
    matplotlib.pyplot.savefig('data.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted problem scaling")

    procs = []
    for c in range(1, int(cores) + 1):
        start = time.time()
        subprocess.call(run.format(c, first, program), shell = True)
        end = time.time()
        elapsed = end - start
        procs.append(elapsed)
        LOG.debug("Threads at {0} took {1:.2f} seconds".format(c, elapsed))
    array = numpy.array(procs)

    matplotlib.pyplot.plot(procs)
    matplotlib.pyplot.xlabel('cores in units')
    matplotlib.pyplot.ylabel('time in seconds')
    matplotlib.pyplot.title('thread count scaling')
    matplotlib.pyplot.savefig('procs.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted thread scaling")

    opts = []
    for o in range(0, 4):
        start = time.time()
        command = ' && '.join([ build.format('-O{0}'.format(o)),
                               run.format(cores, first, program) ])
        subprocess.call(command, shell = True)
        end = time.time()
        elapsed = end - start
        opts.append(elapsed)
        LOG.debug("Optimizations at {0} took {1:.2f} seconds".format(o, elapsed))
    array = numpy.array(opts)

    matplotlib.pyplot.plot(opts)
    matplotlib.pyplot.savefig('opts.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted optimizations")

    command = build.format('"-O3 -ftree-vectorizer-verbose=7"')
    output = subprocess.check_output(command, shell = True)
    macros['vectorizer'] = output
    LOG.debug("Vectorization report completed")

    command = ' && '.join([ build.format('"-O3 -g -pg"'),
                           run.format(cores, first, program),
                           'gprof -l -b' ])
    output = subprocess.check_output(command, shell = True)
    macros['profile'] = output
    LOG.debug("Profiling report completed")
    
    environment = run.format(cores, first, program).split('./')[0]
    record = 'perf record ./{0}'.format(program)
    annotate = 'perf annotate > /tmp/test'
    command = ' && '.join([ build.format('"-O3 -g"'),
                           environment + record,
                           annotate ])
    subprocess.check_call(command, shell = True)
    output = subprocess.check_output('cat /tmp/test', shell = True)
    macros['annotation'] = output
    LOG.debug("Source annotation completed")

    command = run.format(cores, first, program) + '& pidstat -r -d -u -h -p $! 1'
    output = subprocess.check_output(command, shell = True)
    macros['resources'] = output
    LOG.debug("Resource usage tracking completed")

    template = open('/home/amore/bt/bt.tex', 'r').read()
    for k, v in macros.iteritems():
        LOG.debug("Replacing macro {0} with {1}".format(k,v))
        template = template.replace('@@' + k.upper() + '@@', v.replace('%',
                                                                       '?'))
    open(program + '.tex', 'w').write(template)

    command = 'pdflatex {0}.tex; pdflatex {0}.tex'.format(program)
    subprocess.call(command, shell = True)

if __name__ == "__main__":
    main()
