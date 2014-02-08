#! /usr/bin/env python

"""
Bottleneck - Performance report generator.
"""

import ConfigParser
import argparse
import datetime
import logging
import math
import matplotlib.pyplot
import multiprocessing
import numpy
import os
import pickle
import platform
import pprint
import re
import scipy.stats
import socket
import subprocess
import time

# Tokens to be replaced at the report are kept here."""
TAG = {}

class Logger:
    """Enable logging."""

    def __init__(self, name):
        """Store all logs in file, show also in console."""

# TODO: cli option to select log level in console

        # logs are hidden in ~/.bt/PROGRAM/TIMESTAMP
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
        path = os.path.abspath(self.args.config)
        LOG.debug('Loading config from {0}'.format(path))
        self.config.read(path)
        return self

    def get(self, key, section='default'):
        """Get configuration attribute."""
        value = self.config.get(section, key)
        LOG.debug('Getting {0} from config: {1}'.format(key, value))
        return value

CFG = None # ConfigurationParser().load()

class Section:
    def __init__(self, name, tags = {}, cache = 0):
        """Store section name and context tags."""
        self.name = name
        self.tags = tags
        self.cache = cache
        LOG.debug('Creating section named {0}'.format(self.name))
    def run(self, command):
        """Run command keeping logs and caching output."""
        cache = self.name + ".cache"
        output = None

        if os.path.exists(cache) and time.time() - os.path.getmtime(cache) <= self.cache:
            try:
                output = pickle.load(open(cache, "rb"))
                LOG.debug('Loading ' + cache)
            except IOError:
                LOG.debug('Dumping ' + cache)
                output = subprocess.check_output(command, shell = True).strip()
                pickle.dump(output, open(cache, "wb"))
        else:
            LOG.debug('Running ' + cache)
            output = subprocess.check_output(command, shell = True).strip()

        with open(LOGDIR + '/' + self.name + '.log', 'w') as log:
            log.write(output)

        self.output = output

        return self

    def gather(self):
        """Populate section contents."""
        LOG.debug('Empty gather in section named {0}'.format(self.name))
        return self
    def get(self):
        """Return tags."""
        LOG.debug('Returning tags from section named {0}'.format(self.name))
        return self.tags
    def show(self):
        """Show section name and tags in console."""
        LOG.debug('Showing section named {0}'.format(self.name))
        for key, value in sorted(self.tags.iteritems()):
            LOG.debug('Tag {0} is {1}'.format(key, value))
        return self

class HardwareSection(Section):
    def __init__(self):
        """Create hardware section."""
        LOG.debug('Creating hardware section')
        Section.__init__(self, 'hardware', cache=86400)
    def gather(self):
        """Gather hardware information."""

        # WARNING: you should run this program as super-user.
        # H/W path    Device      Class      Description
        # ==============================================
        #                         system     Computer
        # /0                      bus        Motherboard
        # /0/0                    memory     994MiB System memory
        # /0/1                    processor  Intel(R) Core(TM) i5-3320M CPU @ 2.60GHz
        # /0/100                  bridge     440FX - 82441FX PMC [Natoma]
        # /0/100/1                bridge     82371SB PIIX3 ISA [Natoma/Triton II]
        # /0/100/1.1              storage    82371AB/EB/MB PIIX4 IDE
        # /0/100/2                display    VirtualBox Graphics Adapter
        # /0/100/3    eth0        network    82540EM Gigabit Ethernet Controller
        # /0/100/4                generic    VirtualBox Guest Service
        # /0/100/6                bus        KeyLargo/Intrepid USB
        # /0/100/7                bridge     82371AB/EB/MB PIIX4 ACPI
        # /0/100/d                storage    82801HM/HEM (ICH8M/ICH8M-E) SATA Controller
        # /0/2        scsi1       storage
        # /0/2/0.0.0  /dev/cdrom  disk       DVD reader
        # WARNING: output may be incomplete or inaccurate, you should run this program as super-user.

        ls = 'lshw -short -sanitize | cut -b25- | '
        grep = 'grep -E "memory|processor|bridge|network|storage"'
        self.tags['hardware'] = self.run(ls + grep).output

        return self

class ProgramSection(Section):
    def __init__(self):
        """Create program section."""
        LOG.debug('Creating program section')
        Section.__init__(self, 'program')
    def gather(self):
        """Gather program information."""
        self.tags['timestamp'] = LOG.timestamp
        self.tags['log'] = LOG.logdir
        self.tags['host'] = socket.getfqdn()
        self.tags['distro'] = ', '.join(platform.linux_distribution())
        self.tags['platform'] = platform.platform()
        self.tags['cwd'] = os.path.abspath('.')
        self.tags['program'] = os.path.basename(self.tags['cwd'])

        return self

class SoftwareSection(Section):
    def __init__(self):
        """Create program section."""
        LOG.debug('Creating program section')
        Section.__init__(self, 'software')        
    def gather(self):

        # gcc (Ubuntu/Linaro 4.7.3-1ubuntu1) 4.7.3
        # Copyright (C) 2012 Free Software Foundation, Inc.

        compiler = 'gcc --version'
        self.tags['compiler'] = re.split('\n', self.run(compiler).output)[0]

        # GNU C Library (Ubuntu EGLIBC 2.17-0ubuntu5.1) stable release version 2.17, by Roland McGrath et al.
        # Copyright (C) 2012 Free Software Foundation, Inc.

        libc = '/lib/x86_64-linux-gnu/libc.so.6'
        self.tags['libc'] = re.split('\n', self.run(libc).output)[0]

        return self

class SanitySection(Section):
    def __init__(self):
        LOG.debug('Creating sanity section')
        Section.__init__(self, 'sanity')
    def gather(self):
        test = ' && '.join([ self.tags['build'].format('-O3'),
                             self.tags['run'].format(self.tags['cores'],
                                        self.tags['first'],
                                        self.tags['program']) ])
        self.run(test)
        return self

class BenchmarkSection(Section):
    def __init__(self):
        LOG.debug('Creating benchmark section')
        Section.__init__(self, 'benchmark')
    def gather(self):
        self.run('ls')
        return self

class WorkloadSection(Section):
    def __init__(self):
        LOG.debug('Creating workload section')
        Section.__init__(self, 'workload')
    def gather(self):
        pass

class ScalabilitySection(Section):
    def __init__(self):
        LOG.debug('Creating scalability section')
        Section.__init__(self, 'scalability')
    def gather(self):
        pass

class ProfileSection(Section):
    def __init__(self):
        LOG.debug('Creating profile section')
        Section.__init__(self, 'profile')
    def gather(self):
        pass

class ResourcesSection(Section):
    def __init__(self):
        LOG.debug('Creating resources section')
        Section.__init__(self, 'resources')
    def gather(self):
        pass

class VectorizationSection(Section):
    def __init__(self):
        pass
    def gather(self):
        pass

class CountersSection(Section):
    def __init__(self):
        LOG.debug('Creating counters section')
        Section.__init__(self, 'counters')
    def gather(self):
        pass

def main():

    CFG = ConfigurationParser().load()

    HardwareSection().gather().show().get()

# TODO: check if baseline results are valid
# TODO: choose size to fit in 1 minute
# TODO: cli option to not do any smart thing like choosing problem size

    ProgramSection().gather().show().get()
    SoftwareSection().gather().show().get()

    count = CFG.get('count')
    build = CFG.get('build')
    run = CFG.get('run')
    first, last, increment = CFG.get('range', program).split(',')

    TAG['range'] = str(range(int(first), int(last), int(increment)))

    cores = str(multiprocessing.cpu_count())


# TODO: get/log human readable output, then process using Python

    pidstat = '& pidstat -s -r -d -u -h -p $! 1 | sed "s| \+|,|g" | grep ^, | cut -b2-'
    command = run.format(cores, last, program) + pidstat
    output = subprocess.check_output(command, shell = True)

    with open(LOGDIR + '/resources.log', 'w') as log:
        log.write(output)

    lines = output.splitlines()

# TODO: this should be parsed from output's header

    header = 'Time,PID,%usr,%system,%guest,%CPU,CPU,minflt/s,majflt/s,VSZ,RSS,%MEM,StkSize,StkRef,kB_rd/s,kB_wr/s,kB_ccwr/s,Command'
    fields = header.split(',')

    data = {}
    for i in range(0, len(fields)):
        field = fields[i]
        if field in ['%CPU', '%MEM']:

            # TODO: add disk read/writes plots

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

#

    try:
        output = pickle.load(open("benchmark.cache", "rb"))
        LOG.debug('Loading benchmark.cache')
    except IOError:
        LOG.debug('Dumping benchmark.cache')
        benchmark = 'mpirun `which hpcc` && cat hpccoutf.txt'
        output = subprocess.check_output(benchmark, shell = True)
        pickle.dump(output, open("benchmark.cache", "wb"))

    with open(LOGDIR + '/benchmarks.log', 'w') as log:
        log.write(output)

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

# TODO: append? instead of sending list

    with open(LOGDIR + '/workload.log', 'w') as log:
        log.write("\n".join(outputs))

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

    with open(LOGDIR + '/size.log', 'w') as log:
        log.write("\n".join(outputs))

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

    with open(LOGDIR + '/threads.log', 'w') as log:
        log.write("\n".join(outputs))

    # TODO: procs[1] less than half procs[0] then supralinear then FAIL

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

    with open(LOGDIR + '/opts.log', 'w') as log:
        log.write("\n".join(outputs))

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

    with open(LOGDIR + '/vectorization.log', 'w') as log:
        log.write(output)

    TAG['profile'] = output
    LOG.debug("Profiling report completed")
    
    environment = run.format(cores, first, program).split('./')[0]
    record = 'perf record ./{0}'.format(program)
    annotate = 'perf annotate > /tmp/test'
    command = ' && '.join([ build.format('"-O3 -g"'),
                           environment + record,
                           annotate ])
    output = subprocess.check_output(command, shell = True)
    cattest = 'cat /tmp/test | grep -v "^\s*:\s*$" | grep -v "0.00"'
    output = subprocess.check_output(cattest, shell = True)

    with open(LOGDIR + '/annotation.log', 'w') as log:
        log.write(output)

    TAG['annotation'] = output
    LOG.debug("Source annotation completed")

    counters = 'N={0} perf stat -r 3 ./{1}'.format(last, program)
    output = subprocess.check_output(command, shell = True)
    TAG['counters'] = output

    with open(LOGDIR + '/counters.log', 'w') as log:
        log.write(output)

    LOG.debug("Hardware counters gathering completed")

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

# _ROOT = os.path.abspath(os.path.dirname(__file__))
# def get_data(path):
# return os.path.join(_ROOT, 'data', path)
