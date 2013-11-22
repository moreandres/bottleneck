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
import math

TAG = {}

class Logger:
    """Enable logging."""

    def __init__(self, name):
        """Store all logs in file, show only errors in console."""

        cwd = os.path.abspath('.')
        program = os.path.basename(cwd)
    
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

        self.logger = logging.getLogger(name)
        self.logger.timestamp = timestamp
        self.logger.logdir = '{0}/.bt/{1}/{2}'.format(os.path.expanduser("~"),
                                                      program,
                                                      self.logger.timestamp)

        if not os.path.exists(self.logger.logdir):
            os.makedirs(self.logger.logdir)

        self.logger.setLevel(logging.DEBUG)

        fileh = logging.FileHandler(self.logger.logdir + '/full.log')
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
        self.logger.debug('Logging to {0}'.format(self.logger.logdir))
        return self.logger

LOGGER = Logger('bt')
LOG = LOGGER.get()
LOGDIR = LOGGER.logger.logdir

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
    """TBD: to be refactored."""
    cwd = os.path.abspath('.')
    program = os.path.basename(cwd)

# TODO: check if baseline results are valid
# TODO: choose size to fit in 1 minute

    TAG['timestamp'] = LOG.timestamp

    TAG['log'] = LOG.logdir
    TAG['host'] = socket.getfqdn()
    TAG['distro'] = ', '.join(platform.linux_distribution())
    TAG['platform'] = platform.platform()

    try:
        hardware = pickle.load(open("hardware.cache", "rb"))
        LOG.debug('Loading hardware.cache')
    except IOError:
        LOG.debug('Dumping hardware.cache')
        grep = 'grep -E "memory|processor|bridge|network|storage"'
        command = 'lshw -short -sanitize | cut -b25- | ' + grep
        hardware = subprocess.check_output(command, shell = True)
        pickle.dump(hardware, open("hardware.cache", "wb"))

    pickle.dump(hardware, open(LOGDIR + "/hardware.log", "wb"))

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

#
    pidstat = '& pidstat -s -r -d -u -h -p $! 1 | sed "s| \+|,|g" | grep ^, | cut -b2-'
    command = run.format(cores, last, program) + pidstat
    output = subprocess.check_output(command, shell = True)

    pickle.dump(output, open(LOGDIR + "/resources.log", "wb"))

    lines = output.splitlines()
    header = 'Time,PID,%usr,%system,%guest,%CPU,CPU,minflt/s,majflt/s,VSZ,RSS,%MEM,StkSize,StkRef,kB_rd/s,kB_wr/s,kB_ccwr/s,Command'
    fields = header.split(',')

    data = {}
    for i in range(0, len(fields)):
        field = fields[i]
        if field in ['%CPU', '%MEM']:

            # TODO: add disk read/writes

            data[field] = []
            for line in lines:
                data[field].append(line.split(',')[i])

            matplotlib.pyplot.plot(data[field])
            matplotlib.pyplot.xlabel('{0} usage rate'.format(field))
            matplotlib.pyplot.grid(True)  
            matplotlib.pyplot.ylabel('percentage of available resources')
            matplotlib.pyplot.title('resource usage')
            matplotlib.pyplot.savefig('{0}.pdf'.format(field, bbox_inches=0).replace('%',''))
            matplotlib.pyplot.clf()

    TAG['resources'] = output
    LOG.debug("Resource usage plotting completed")

#

    TAG['count'] = count
    TAG['build'] = build
    TAG['run'] = run
    TAG['first'] = first
    TAG['last'] = last
    TAG['increment'] = increment
    TAG['cores'] = cores

    test = ' && '.join([ build.format('-O3'),
                        run.format(cores, first, program) ])
    output = subprocess.check_output(test, shell = True)
    LOG.debug("Sanity test successful")

    pickle.dump(output, open(LOGDIR + "/sanity.log", "wb"))

    try:
        output = pickle.load(open("benchmark.cache", "rb"))
        LOG.debug('Loading benchmark.cache')
    except IOError:
        LOG.debug('Dumping benchmark.cache')
        benchmark = 'mpirun `which hpcc` && cat hpccoutf.txt'
        output = subprocess.check_output(benchmark, shell = True)
        pickle.dump(output, open("benchmark.cache", "wb"))

    pickle.dump(output, open(LOGDIR + "/benchmarks.log", "wb"))

    metrics = [ ('success', r'Success=(\d+.*)', None),
                ('hpl', r'HPL_Tflops=(\d+.*)', 'TFlops'),
                ('dgemm', r'StarDGEMM_Gflops=(\d+.*)', 'GFlops'),
                ('ptrans', r'PTRANS_GBs=(\d+.*)', 'GBs'),
                ('random', r'StarRandomAccess_GUPs=(\d+.*)', 'GUPs'),
                ('stream', r'StarSTREAM_Triad=(\d+.*)', 'MBs'),
                ('fft', r'StarFFT_Gflops=(\d+.*)', 'GFlops'), ]

    for metric in metrics:
        try:
            match = re.search(metric[1], output).group(1)
        except AttributeError:
            match = 'Unknown'
        TAG['hpcc-{0}'.format(metric[0])] = '{0} {1}'.format(match, metric[2])

    LOG.debug("System baseline completed")

    outputs = []
    times = []
    for i in range(0, int(count)):
        start = time.time()
        output = subprocess.check_output(run.format(cores, first, program), shell = True)
        end = time.time()
        elapsed = end - start
        times.append(elapsed)
        outputs.append(output)
        LOG.debug("Control {0} took {1:.2f} seconds".format(i, elapsed))
    array = numpy.array(times)
    deviation = "Deviation: gmean {0:.2f} std {1:.2f}"
    LOG.debug(deviation.format(scipy.stats.gmean(array), numpy.std(array)))

    TAG['geomean'] = "%.5f" % scipy.stats.gmean(array)
    TAG['stddev'] = "%.5f" % numpy.std(array)

    TAG['max'] = "%.5f" % numpy.max(array)
    TAG['min'] = "%.5f" % numpy.min(array)

    pickle.dump(outputs, open(LOGDIR + "/workload.log", "wb"))

    # min/max

    buckets, bins, patches = matplotlib.pyplot.hist(times,
                                                    bins=math.ceil(math.sqrt(int(count))),
                                                    normed=True)
    matplotlib.pyplot.plot(bins, 
                           scipy.stats.norm.pdf(bins,
                                                loc = numpy.mean(array),
                                                scale = array.std()),
                           'r--')
    matplotlib.pyplot.xlabel('time in seconds')
    matplotlib.pyplot.ylabel('ocurrences in units')
    matplotlib.pyplot.title('histogram')
    matplotlib.pyplot.grid(True)  
    matplotlib.pyplot.savefig('hist.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted histogram")

# TODO: detect/report outliers

# TODO: historical comparison

    data = {}
    outputs = []
    for size in range(int(first), int(last) + 1, int(increment)):
        start = time.time()
        output = subprocess.check_output(run.format(cores, size, program), shell = True)
        end = time.time()
        outputs.append(output)
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
    matplotlib.pyplot.grid(True)  

# TODO: add problem size as labels in X axis

    matplotlib.pyplot.ylabel('time in seconds')
    matplotlib.pyplot.title('data size scaling')
    matplotlib.pyplot.savefig('data.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted problem scaling")

    pickle.dump(outputs, open(LOGDIR + "/size.log", "wb"))

    outputs = []
    procs = []
    for core in range(1, int(cores) + 1):
        start = time.time()
        output = subprocess.check_output(run.format(core, last, program), shell = True)
        end = time.time()
        outputs.append(output)
        elapsed = end - start
        procs.append(elapsed)
        LOG.debug("Threads at {0} took {1:.2f} seconds".format(core, elapsed))
    array = numpy.array(procs)

    matplotlib.pyplot.plot(procs, label="actual")
    matplotlib.pyplot.grid(True)  

    ideal = [ procs[0] ]
    for proc in range(1, len(procs)):
        ideal.append(procs[proc]/proc+1)

    matplotlib.pyplot.plot(ideal, label="ideal")

    matplotlib.pyplot.xlabel('cores in units')
    matplotlib.pyplot.xticks(range(0, int(cores)),
                             range(1, int(cores) + 1))
    matplotlib.pyplot.ylabel('time in seconds')
    matplotlib.pyplot.title('thread count scaling')
    matplotlib.pyplot.savefig('procs.pdf', bbox_inches=0)
    matplotlib.pyplot.grid(True)  
    matplotlib.pyplot.clf()
    LOG.debug("Plotted thread scaling")

    pickle.dump(outputs, open(LOGDIR + "/threads.log", "wb"))

    # TODO: if procs[1] is less than half procs[0] then supralinear then formula does not work

    parallel = 2 * (procs[0] - procs[1]) / procs[0]
    serial = (procs[0] - 2 * (procs[0] - procs[1])) / procs[0]
    TAG['serial'] = "%.5f" % serial
    TAG['parallel'] = "%.5f" % parallel

    TAG['amdalah'] = "%.5f" % ( 1 / (serial + (1/1024) * (1 - serial)) )
    TAG['gustafson'] = "%.5f" % ( 1024 - (serial * (1024 - 1)) )

    LOG.debug("Computed scaling laws")

    outputs = []
    opts = []
    for opt in range(0, 4):
        start = time.time()
        command = ' && '.join([ build.format('-O{0}'.format(opt)),
                               run.format(cores, first, program) ])
        output = subprocess.check_output(command, shell = True)
        end = time.time()
        outputs.append(output)
        elapsed = end - start
        opts.append(elapsed)
        optimizations = "Optimizations at {0} took {1:.2f} seconds"
        LOG.debug(optimizations.format(opt, elapsed))
    array = numpy.array(opts)

    matplotlib.pyplot.plot(opts)
    matplotlib.pyplot.savefig('opts.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    LOG.debug("Plotted optimizations")

    pickle.dump(outputs, open(LOGDIR + "/opts.log", "wb"))

# TODO: make all interesting commands to log into timestamp folder

    command = build.format('"-O3 -ftree-vectorizer-verbose=7" 2>&1')
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
    output = subprocess.check_output(command, shell = True)
    cattest = 'cat /tmp/test | grep -v "0.00"'
    output = subprocess.check_output(cattest, shell = True)
    TAG['annotation'] = output
    LOG.debug("Source annotation completed")

    template = open('/home/amore/tmp/bottleneck/bt/bt.tex', 'r').read()
    for key, value in sorted(TAG.iteritems()):
        LOG.debug("Replacing macro {0} with {1}".format(key, value))
        template = template.replace('@@' + key.upper() + '@@',
                                    value.replace('%', '?'))
    open(program + '.tex', 'w').write(template)

    latex = 'pdflatex {0}.tex && pdflatex {0}.tex && pdflatex {0}.tex'
    command = latex.format(program)
    subprocess.call(command, shell = True)

if __name__ == "__main__":
    main()
