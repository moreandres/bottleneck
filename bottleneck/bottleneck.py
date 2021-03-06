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

try:
    import cPickle as pickle
except:
    import pickle

import platform
import pprint
import re
import scipy.stats
import socket
import subprocess
import time

class Singleton(type):
    """Singleton metaclass."""
    _instances = {}
    def __call__(cls, *args, **kwargs):
        """Return singleton if already there, otherwise create it."""
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Tags:
    """Tags to be replaced at the report."""
    __metaclass__ = Singleton
    def __init__(self):
        """Tags are empty."""
        self.tags = {}

class Log:
    """Enable logging."""
    __metaclass__ = Singleton
    def __init__(self):
        """Store all logs in file, show also in console."""

# TODO: cli option to select log level in console

        # logs are hidden in ~/.bt/PROGRAM/TIMESTAMP
        cwd = os.path.abspath('.')
        program = os.path.basename(cwd)
    
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

        self.logger = logging.getLogger('bottleneck')
        self.timestamp = timestamp
        self.logdir = '{0}/.bt/{1}/{2}'.format(os.path.expanduser("~"),
                                               program,
                                               self.timestamp)

        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)

        self.logger.setLevel(logging.DEBUG)

        fileh = logging.FileHandler(self.logdir + '/full.log')
        fileh.setLevel(logging.DEBUG)
        consoleh = logging.StreamHandler()
        consoleh.setLevel(logging.DEBUG)
        fmt = '%(asctime)s: %(levelname)s: %(message)s'
        formatter = logging.Formatter(fmt, datefmt="%Y%m%d-%H%M%S")

        fileh.setFormatter(formatter)
        consoleh.setFormatter(formatter)

        self.logger.addHandler(fileh)
        self.logger.addHandler(consoleh)

        self.logger.debug('Logging to {0}'.format(self.logdir))

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def close(self):
        """Close logging."""

        return self
        
    def get(self):
        """Get logger instance."""
        return self.logger

# TODO: fix logging in unit tests

class Config:
    __metaclass__ = Singleton
    """ Parse configuration."""

    def __init__(self):

        """Empty configuration."""
        self.config = None
        self.parser = None
        self.args = None

    def load(self):
        """Load arguments and configuration from file."""
        description = 'Generate performance report for OpenMP programs.'
        epilog = 'Check github readme for more details.'
        self.parser = argparse.ArgumentParser(description=description,
                                              epilog=epilog,
                                              version='0.0.1')

        # TODO: use action to verify that configuration file exists

        self.parser.add_argument('--config', '-c',
                                 help='path to configuration',
                                 default= os.path.abspath('.') + '/bt.cfg')
        self.parser.add_argument('--debug', '-d',
                                 action='store_true',
                                 help='enable verbose logging')

        self.args = self.parser.parse_args()
        self.config = ConfigParser.ConfigParser()
        path = os.path.abspath(self.args.config)

        if not os.path.exists(path):
            print 'Configuration file not found.'
            raise SystemExit

        # TODO: use $CWD/bt.cfg, create it from ~/.bt/bt.cfg if not there

        self.config.read(path)
        return self

    def get(self, key, section='default'):
        """Get configuration attribute."""
        value = self.config.get(section, key)
        Log().debug('Getting {0} from config: {1}'.format(key, value))
        return value

    def items(self, section='default'):
        """Get tags as a dictionary."""
        Log().debug('Getting all items from config')
        try:
            items = dict(zip(self.config.items(section)[0::2],
                             self.config.items(section)[1::2]))
        except ConfigParser.NoSectionError:
            Log().error('No configuration found')
            items = {}
        return items

class Section:
    """Report section."""
    def __init__(self, name):
        """Store section name, config and tags."""
        self.name = name
        self.tags = Tags().tags
        self.config = Config()
        self.counter = {}
        self.output = None
        self.log = Log()
        self.log.debug('Creating section named {0}'.format(self.name))
    def command(self, cmd):
        """Run command keeping logs and caching output."""

        # keep count to cache multiple executions of the same command
        try:
            self.counter[cmd] += 1
        except:
            self.counter[cmd] = 0

        temp = '{0}.{1}.cache'.format(self.name, self.counter[cmd])
        output = None

        try:
            output = pickle.load(open(temp, "rb"))
            self.log.debug('Loading ' + temp)
        except IOError:
            self.log.debug('Dumping ' + temp)
            output = subprocess.check_output(cmd, shell = True).strip()
            pickle.dump(output, open(temp, "wb"))

        with open(self.log.logdir + '/' + self.name + '.log', 'w') as log:
            log.write(output)

        self.output = output

        return self

    def gather(self):
        """Populate section contents."""
        self.log.debug('Empty gather in section named {0}'.format(self.name))
        return self
    def get(self):
        """Return tags."""
        self.log.debug('Returning tags from section named {0}'.format(self.name))
        return self.tags
    def show(self):
        """Show section name and tags in console."""
        self.log.debug('Showing section named {0}'.format(self.name))
        for key, value in sorted(self.tags.iteritems()):
            self.log.debug('Tag {0} is {1}'.format(key, value))
        return self

class HardwareSection(Section):
    """Gather hardware information."""
    def __init__(self):
        """Create hardware section."""
        Section.__init__(self, 'hardware')
    def gather(self):
        """Gather hardware information."""

        listing = 'lshw -short -sanitize | cut -b25- | '
        grep = 'grep -E "memory|processor|bridge|network|storage"'
        self.tags['hardware'] = self.command(listing + grep).output

        return self

class ProgramSection(Section):
    """Gather program information."""
    def __init__(self):
        """Create program section."""
        Section.__init__(self, 'program')
        self.log = Log()
    def gather(self):
        """Gather program information."""
        self.tags['timestamp'] = self.log.timestamp
        self.tags['log'] = self.log.logdir
        self.tags['host'] = socket.getfqdn()
        self.tags['distro'] = ', '.join(platform.linux_distribution())
        self.tags['platform'] = platform.platform()
        self.tags['cwd'] = os.path.abspath('.')
        self.tags['program'] = os.path.basename(self.tags['cwd'])

        return self

class SoftwareSection(Section):
    """Gather software information."""
    def __init__(self):
        """Create program section."""
        Section.__init__(self, 'software')        
    def gather(self):
        """Get compiler and C library version."""

        compiler = 'gcc --version'
        self.tags['compiler'] = re.split('\n', self.command(compiler).output)[0]

        libc = '/lib/x86_64-linux-gnu/libc.so.6'
        self.tags['libc'] = re.split('\n', self.command(libc).output)[0]

        return self

class SanitySection(Section):
    """Gather sanity information."""
    def __init__(self):
        """Create sanity section."""
        Section.__init__(self, 'sanity')
        self.dir = 'cd {0}'.format(self.tags['dir'])
        self.build = self.tags['build'].format('-O3')
        self.run = self.tags['run']
        self.cores = self.tags['cores']
        self.first = self.tags['first']
        self.program = self.tags['program']
    def gather(self):
        """Build and run the program using a small input size."""
        test = ' && '.join([ self.dir,
                             self.build,
                             self.run.format(self.cores,
                                             self.first,
                                             self.program),
                             'cd -'])
        self.command(test)
        return self

class BenchmarkSection(Section):
    """Gather benchmark information."""
    def __init__(self):
        """Create benchmark section."""
        Section.__init__(self, 'benchmark')
    def gather(self):
        """Run HPCC and gather metrics."""
        # TBD: make this a tag
        cores = str(multiprocessing.cpu_count())
        mpirun = 'mpirun -np {0} `which hpcc` && cat hpccoutf.txt'
        output = self.command(mpirun.format(cores)).output

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
        self.tags['hpcc-{0}'.format(metric[0])] = '{0} {1}'.format(match,
                                                                   metric[2])

        self.log.debug("System baseline completed")

        return self

class WorkloadSection(Section):
    """Gather workload information."""
    def __init__(self):
        """Create workload section."""
        Section.__init__(self, 'workload')

        self.count = self.tags['count']
        self.run = self.tags['run']
        self.cores = self.tags['cores']
        self.first = self.tags['first']
        self.program = self.tags['program']
        self.dir = self.tags['dir']
        
    def gather(self):
        """Run program multiple times, check geomean and deviation."""

        # TODO: compile before running

        outputs = []
        times = []
        for i in range(0, int(self.count)):
            start = time.time()
            cmd = ' && '.join([ 'cd {0}'.format(self.dir),
                                self.run.format(self.cores,
                                                self.first,
                                                self.program),
                                'cd -' ])

            output = self.command(cmd)

            end = time.time()
            elapsed = end - start
            times.append(elapsed)
            outputs.append(output)
            self.log.debug("Control {0} took {1:.2f} seconds".format(i, elapsed))

        array = numpy.array(times)
        deviation = "Deviation: gmean {0:.2f} std {1:.2f}"
        self.log.debug(deviation.format(scipy.stats.gmean(array), numpy.std(array)))

        self.tags['geomean'] = "%.5f" % scipy.stats.gmean(array)
        self.tags['stddev'] = "%.5f" % numpy.std(array)

        self.tags['max'] = "%.5f" % numpy.max(array)
        self.tags['min'] = "%.5f" % numpy.min(array)

        number = math.ceil(math.sqrt(int(self.tags['count'])))

        buckets, bins, patches = matplotlib.pyplot.hist(times,
                                                        bins=number,
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
        Log().debug("Plotted histogram")

        return self

# TODO: detect/report outliers

class ScalingSection(Section):
    """Gather scaling information."""
    def __init__(self):
        """."""
        # TODO: first, last, increment should be read from self.tags
        Section.__init__(self, 'scaling')

        self.tags = Tags().tags
        self.first = self.tags['first']
        self.last = self.tags['last']
        self.increment = self.tags['increment']
        self.run = self.tags['run']
        self.cores = self.tags['cores']
        self.size = self.tags['size']
        self.program = self.tags['program']
        self.dir = self.tags['dir']
        self.cflags = self.tags['cflags']
        self.clean = self.tags['clean']
        self.build = self.tags['build']

    def gather(self):
        """Run program."""

        cleanup = 'cd {0}; {1}; {2}'.format(self.dir,
                                            self.clean,
                                            self.build.format(self.cflags))
        subprocess.check_output(cleanup, shell = True)

        data = {}
        outputs = []

        for size in range(int(self.first),
                          int(self.last) + 1,
                          int(self.increment)):
            start = time.time()
            output = self.command(' && '.join([ 'cd {0}'.format(self.dir), self.run.format(self.cores, self.size, self.program), 'cd -' ]))
            end = time.time()
            outputs.append(output)
            elapsed = end - start
            data[size] = elapsed
            self.log.debug("Problem at {0} took {1:.2f} seconds".format(self.size, elapsed))
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
        self.log.debug("Plotted problem scaling")
        
        return self
        

class ProfileSection(Section):
    """Gather performance profile information."""
    def __init__(self):
        """Create profile section."""
        Section.__init__(self, 'profile')
    def gather(self):
        """Run gprof and gather results."""
        return self

class ResourcesSection(Section):
    """Gather system resources information."""
    def __init__(self):
        """Create resources section."""
        Section.__init__(self, 'resources')
    def gather(self):
        """Run program under pidstat."""
        return self

class VectorizationSection(Section):
    """Gather vectorization information."""
    def __init__(self):
        """Create vectorization section."""
        Section.__init__(self, 'vectorization')
    def gather(self):
        """Run oprofile."""
        return self

class CountersSection(Section):
    """Gather hardware counters information."""
    def __init__(self):
        """Create hardware counters section."""
        Section.__init__(self, 'counters')
    def gather(self):
        """Run program and gather counter statistics."""
        return self

class ConfigSection(Section):
    """Gather configuration information."""
    def __init__(self):
        """Create configuration section."""
        Section.__init__(self, 'config')
    def gather(self):
        """Load configuration and update tags."""
        return self

def main():
    """Gather information into tags, replace on a .tex file and compile."""

    Config().load()

    cfg = Config()
    log = Log()
    tags = Tags().tags

# TODO: check why config file cannot be loaded
    tags.update(Config().items())

    tags.update(HardwareSection(tags).gather().show().get())

# TODO: check if baseline results are valid
# TODO: choose size to fit in 1 minute
# TODO: cli option to not do any smart thing like choosing problem size

    tags.update(ProgramSection(tags).gather().show().get())
    tags.update(SoftwareSection(tags).gather().show().get())

# TODO: program should be read from a tag

    count = CFG.get('count')
    build = CFG.get('build')
    run = CFG.get('run')
    first, last, increment = CFG.get('range', program).split(',')

    tags['range'] = str(range(int(first), int(last), int(increment)))

    cores = str(multiprocessing.cpu_count())

# TODO: get/log human readable output, then process using Python

    pidstat = '& pidstat -s -r -d -u -h -p $! 1 | sed "s| \+|,|g" | grep ^, | cut -b2-'
    command = run.format(cores, last, program) + pidstat
    output = subprocess.check_output(command, shell = True)

    with open(self.logger.logdir + '/resources.log', 'w') as log:
        log.write(output)

    lines = output.splitlines()

# TODO: this should be parsed from output's header, not hardcoded

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
            name = '{0}.pdf'.format(field, bbox_inches=0).replace('%','')
            matplotlib.pyplot.savefig(name)
            matplotlib.pyplot.clf()

    tags['resources'] = output
    logging.getLogger('bottleneck').debug("Resource usage plotting completed")

    tags.update(BenchmarkSection().gather().show().get())
    tags.update(WorkloadSection().gather().show.get())
    tags.update(ScalingSection().gather.show.get())

# TODO: historical comparison

    outputs = []
    procs = []
    for core in range(1, int(cores) + 1):
        start = time.time()
        output = subprocess.check_output(run.format(core, last, program),
                                         shell = True)
        end = time.time()
        outputs.append(output)
        elapsed = end - start
        procs.append(elapsed)
        log.debug("Threads at {0} took {1:.2f} seconds".format(core, elapsed))
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
    log.debug("Plotted thread scaling")

    with open(self.logger.logdir + '/threads.log', 'w') as log:
        log.write("\n".join(outputs))

    # TODO: procs[1] less than half procs[0] then supralinear then FAIL

    parallel = 2 * (procs[0] - procs[1]) / procs[0]
    serial = (procs[0] - 2 * (procs[0] - procs[1])) / procs[0]
    tags['serial'] = "%.5f" % serial
    tags['parallel'] = "%.5f" % parallel

    tags['amdalah'] = "%.5f" % ( 1 / (serial + (1/1024) * (1 - serial)) )
    tags['gustafson'] = "%.5f" % ( 1024 - (serial * (1024 - 1)) )

    log.debug("Computed scaling laws")

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
        log.debug(optimizations.format(opt, elapsed))
    array = numpy.array(opts)

    matplotlib.pyplot.plot(opts)
    matplotlib.pyplot.savefig('opts.pdf', bbox_inches=0)
    matplotlib.pyplot.clf()
    log.debug("Plotted optimizations")

    with open(self.logger.logdir + '/opts.log', 'w') as log:
        log.write("\n".join(outputs))

    command = build.format('"-O3 -ftree-vectorizer-verbose=7" 2>&1')
    output = subprocess.check_output(command, shell = True)
    tags['vectorizer'] = output
    log.debug("Vectorization report completed")

    gprofgrep = 'gprof -l -b {0} | grep [a-zA-Z0-9]'
    command = ' && '.join([ build.format('"-O3 -g -pg"'),
                            run.format(cores, first, program),
                            gprofgrep.format(program) ])
    output = subprocess.check_output(command, shell = True)

    with open(self.logger.logdir + '/vectorization.log', 'w') as log:
        log.write(output)

    tags['profile'] = output
    log.debug("Profiling report completed")
    
    environment = run.format(cores, first, program).split('./')[0]
    record = 'perf record ./{0}'.format(program)
    annotate = 'perf annotate > /tmp/test'
    command = ' && '.join([ build.format('"-O3 -g"'),
                           environment + record,
                           annotate ])
    output = subprocess.check_output(command, shell = True)
    cattest = 'cat /tmp/test | grep -v "^\s*:\s*$" | grep -v "0.00"'
    output = subprocess.check_output(cattest, shell = True)

    with open(self.logger.logdir + '/annotation.log', 'w') as log:
        log.write(output)

    tags['annotation'] = output
    log.debug("Source annotation completed")

    counters = 'N={0} perf stat -r 3 ./{1}'.format(last, program)
    output = subprocess.check_output(command, shell = True)
    TAG['counters'] = output

    with open(self.logger.logdir + '/counters.log', 'w') as log:
        log.write(output)

    log.debug("Hardware counters gathering completed")

    template = open('/home/amore/tmp/bottleneck/bt/bt.tex', 'r').read()
    for key, value in sorted(TAG.iteritems()):
        log.debug("Replacing macro {0} with {1}".format(key, value))
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
