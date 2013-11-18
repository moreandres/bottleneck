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
import pickle

TAG = {}

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

        cwd = os.path.abspath('.')
        program = os.path.basename(cwd)
    
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        self.logger.timestamp = timestamp
        self.logger.logdir = '~/.bt/{0}-{1}'.format(program,
                                                    self.logger.timestamp)
        if not os.path.exists(self.logger.logdir):
            os.makedirs(self.logger.logdir)

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
                                 default='/home/amore/tmp/bottleneck/bt/bt.cfg')
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

# TODO: check design

def main():
    """The full Monty."""
    cwd = os.path.abspath('.')
    program = os.path.basename(cwd)

# program

# system

# baseline

# TODO: check if baseline results are valid

# workload

# TODO: fix histogram
# TODO: choose size to fit in 1 minute

# scalability

# profile

# bottlenecks

# vectorization

# counters

    TAG['timestamp'] = LOG.timestamp

    TAG['log'] = LOG.logdir
    TAG['host'] = socket.getfqdn()
    TAG['distro'] = ', '.join(platform.linux_distribution())
    TAG['platform'] = platform.platform()

    try:
        hardware = pickle.load(open("hardware.cache", "rb"))
    except IOError:
        grep = 'grep -E "memory|processor|bridge|network|storage"'
        command = 'lshw -short -sanitize | cut -b25- | ' + grep
        hardware = subprocess.check_output(command, shell = True)
        pickle.dump(hardware, open("hardware.cache", "wb"))

    TAG['hardware'] = hardware

    command = 'gcc --version | head -n1'
    TAG['compiler'] = subprocess.check_output(command, shell = True).strip()

    command = '/lib/x86_64-linux-gnu/libc.so.6 | head -n1'
    TAG['libc'] = subprocess.check_output(command, shell = True).strip()

    TAG['cwd'] = cwd
    TAG['program'] = program

    count = CFG.get('count')
    build = CFG.get('build')
    run = CFG.get('run')
    first, last, increment = CFG.get('range', program).split(',')

    TAG['range'] = str(range(int(first), int(last), int(increment)))

    cores = str(multiprocessing.cpu_count())

    TAG['count'] = count
    TAG['build'] = build
    TAG['run'] = run
    TAG['first'] = first
    TAG['last'] = last
    TAG['increment'] = increment
    TAG['cores'] = cores

    test = ' && '.join([ build.format('-O3'),
                        run.format(cores, first, program) ])
    subprocess.check_call(test, shell = True)
    LOG.debug("Sanity test returned status 0")

    try:
        output = pickle.load(open("benchmark.cache", "rb"))
    except IOError:
        benchmark = 'mpirun `which hpcc` && cat hpccoutf.txt'
        output = subprocess.check_output(benchmark, shell = True)
        pickle.dump(output, open("benchmark.cache", "wb"))

    metrics = [ ('success', r'Success=(\d+.*)', None),
                ('hpl', r'HPL_Tflops=(\d+.*)', 'TFlops'),
                ('dgemm', r'StarDGEMM_Gflops=(\d+.*)', 'GFlops'),
                ('ptrans', r'PTRANS_GBs=(\d+.*)', 'GBss'),
                ('random', r'StarRandomAccess_GUPs=(\d+.*)', 'GUPss'),
                ('stream', r'StarSTREAM_Triad=(\d+.*)', 'MBs'),
                ('fft', r'StarFFT_Gflops=(\d+.*)', 'GFlops'), ]

    for metric in metrics:
        match = re.search(metric[1], output).group(1)
        TAG['hpcc-{0}'.format(metric[0])] = '{0} {1}'.format(match, metric[2])

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
    deviation = "Deviation: gmean {0:.2f} std {1:.2f}"
    LOG.debug(deviation.format(scipy.stats.gmean(array), numpy.std(array)))

    TAG['geomean'] = "%.5f" % scipy.stats.gmean(array)
    TAG['stddev'] = "%.5f" % numpy.std(array)

    TAG['max'] = "%.5f" % numpy.max(array)
    TAG['min'] = "%.5f" % numpy.min(array)

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

    data = {}
    for size in range(int(first), int(last) + 1, int(increment)):
        start = time.time()
        subprocess.call(run.format(cores, size, program), shell = True)
        end = time.time()
        elapsed = end - start
        data[size] = elapsed
        LOG.debug("Problem at {0} took {1:.2f} seconds".format(size, elapsed))
    array = numpy.array(data.values())

# TODO: kill execution if time takes more than a limit

    xvalues = data.keys()
    xvalues.sort()

    matplotlib.pyplot.plot(data.values())
    matplotlib.pyplot.xlabel('problem size in bytes')
    matplotlib.pyplot.xticks(range(0, len(data.values())), xvalues)

# TODO: add problem size as labels in X axis

    matplotlib.pyplot.ylabel('time in seconds')
    matplotlib.pyplot.title('data size scaling')
    matplotlib.pyplot.savefig('data.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted problem scaling")

    procs = []
    for core in range(1, int(cores) + 1):
        start = time.time()
        subprocess.call(run.format(core, first, program), shell = True)
        end = time.time()
        elapsed = end - start
        procs.append(elapsed)
        LOG.debug("Threads at {0} took {1:.2f} seconds".format(core, elapsed))
    array = numpy.array(procs)

    matplotlib.pyplot.plot(procs)

    ideal = [ procs[0] ]
    for proc in range(1, len(procs)):
        ideal.append(procs[proc]/proc+1)

    matplotlib.pyplot.plot(ideal)

    matplotlib.pyplot.xlabel('cores in units')
    matplotlib.pyplot.xticks(range(0, int(cores)),
                             range(1, int(cores) + 1))
    matplotlib.pyplot.ylabel('time in seconds')
    matplotlib.pyplot.title('thread count scaling')
    matplotlib.pyplot.savefig('procs.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted thread scaling")
    
    serial = (2 * procs[0] - procs[1])
    parallel = (1 - 2 * procs[0] - procs[1])
    TAG['serial'] = "%.5f" % serial
    TAG['parallel'] = "%.5f" % parallel

    TAG['amdalah'] = "%.5f" % ( 1 / (serial + (1/1024) * (1 - serial)) )
    TAG['gustafson'] = "%.5f" % ( 1024 - (serial * (1024 - 1)) )

    opts = []
    for opt in range(0, 4):
        start = time.time()
        command = ' && '.join([ build.format('-O{0}'.format(opt)),
                               run.format(cores, first, program) ])
        subprocess.call(command, shell = True)
        end = time.time()
        elapsed = end - start
        opts.append(elapsed)
        optimizations = "Optimizations at {0} took {1:.2f} seconds"
        LOG.debug(optimizations.format(opt, elapsed))
    array = numpy.array(opts)

    matplotlib.pyplot.plot(opts)
    matplotlib.pyplot.savefig('opts.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted optimizations")

    command = build.format('"-O3 -ftree-vectorizer-verbose=7"')
    output = subprocess.check_output(command, shell = True)
    TAG['vectorizer'] = output
    LOG.debug("Vectorization report completed")

    gprofgrep = 'gprof -l -b {0} | grep [a-zA-Z0-9]'
    command = ' && '.join([ build.format('"-O3 -g -pg"'),
                            run.format(cores, first, program),
                            gprofgrep.format(program) ])
    output = subprocess.check_output(command, shell = True)
    TAG['profile'] = output
    LOG.debug("Profiling report completed")
    
    environment = run.format(cores, first, program).split('./')[0]
    record = 'perf record ./{0}'.format(program)
    annotate = 'perf annotate > /tmp/test'
    command = ' && '.join([ build.format('"-O3 -g"'),
                           environment + record,
                           annotate ])
    subprocess.check_call(command, shell = True)
    cattest = 'cat /tmp/test | grep -v "0.00"'
    output = subprocess.check_output(cattest, shell = True)
    TAG['annotation'] = output
    LOG.debug("Source annotation completed")

    pidstat = '& pidstat -r -d -u -h -p $! 1 | cut -b1-39,49-82,98-131'
    command = run.format(cores, first, program) + pidstat
    output = subprocess.check_output(command, shell = True)
    TAG['resources'] = output
    LOG.debug("Resource usage tracking completed")

    template = open('/home/amore/tmp/bottleneck/bt/bt.tex', 'r').read()
    for key, value in TAG.iteritems():
        LOG.debug("Replacing macro {0} with {1}".format(key, value))
        template = template.replace('@@' + key.upper() + '@@',
                                    value.replace('%', '?'))
    open(program + '.tex', 'w').write(template)

    latex = 'pdflatex {0}.tex && pdflatex {0}.tex && pdflatex {0}.tex'
    command = latex.format(program)
    subprocess.call(command, shell = True)

if __name__ == "__main__":
    main()
