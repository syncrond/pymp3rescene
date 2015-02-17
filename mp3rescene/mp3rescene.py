#!/usr/bin/env python
# encoding: utf-8

"""
This tool recovers the music scene releases from broken tags and renamings.

"""
from __future__ import print_function
from __future__ import absolute_import
from optparse import OptionParser
from urllib import pathname2url
from collections import OrderedDict
import sys
import os
import re
import fnmatch
from colorama import Fore, init

import rescene
from resample.srs import main as srsmain
from resample.main import get_file_type, sample_class_factory

from utils.srrdb import *
#from utils.srr import SRR
#from utils.srs import SRS

SUCCESS = Fore.GREEN + "  [SUCCESS] " + Fore.RESET
FAIL = Fore.RED + "  [FAIL] " + Fore.RESET
missing_files = []

def fix_tags(srr_file, rls_name, input_dir, output_dir, always_yes=False):
    if not srr_file.endswith(".srr"):
        raise AttributeError("The first parameter must be an SRR file.")
    if not os.path.isdir(input_dir):
        raise AttributeError("The input location must be a directory.")
    output_dir = os.path.join(output_dir, rls_name)
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir)
        except:
            pass
        if not os.path.isdir(output_dir):
            raise AttributeError("Could not create output location.")

    stored_files = rescene.info(srr_file)['stored_files']

    # extract files
    srs_files = []
    for sfile in stored_files.keys():
        if sfile.endswith(".srs"):
            srs_files.append(sfile)
        else:
            print("Extracting %s" % sfile)
            rescene.extract_files(srr_file, output_dir, False, sfile)

    for srs in srs_files:
        print("Extracting %s" % srs)
        rescene.extract_files(srr_file, output_dir, False, srs)

    # fix music files that can be found
    successes = 0
    failures = 0
    for srs in srs_files:
        srsf = os.path.join(output_dir, os.path.basename(srs))
        srs_info = get_srs_info(srsf)
        original_name = srs_info.sample_name
        print("Fixing %s" % original_name)
        # TODO: will fail on *nix when capitals differ
        musicf = os.path.join(input_dir, original_name)
        if not os.path.isfile(musicf):
            filenr = re.search("(\d{2,3})[-_]", original_name)
            filenr = filenr.group(1)
            regex = "*" + filenr + "*.mp3"
            musicf = find(regex, input_dir)
            if not musicf is None and len(musicf) > 0:
                musicf = musicf[0]
            else:
                failures +=1
                continue


        srs_parameters = [srsf, musicf, "-o", output_dir, "-k"]
        if always_yes:
            srs_parameters.append("-y")
        try:
            srsmain(srs_parameters, no_exit=True)
            successes += 1
        except ValueError: # pexit() only throws ValueError
            failures += 1

        os.remove(srsf)

    print("\n\n%d/%d files succeeded. %d failures." %
        (successes, failures + successes, failures))
    return failures == 0

def get_srs_info(srs_file):
    # TODO: get_file_type can be unknown
    sample = sample_class_factory(get_file_type(srs_file))
    srs_data, _tracks = sample.load_srs(srs_file)
    return srs_data

def get_directories(root_dir):
    dir_list = []
    for dirName, subdirList, fileList in os.walk(root_dir):
        #print('Found directory: %s' % dirName)
        if dirName != root_dir:
            dir_list.append(dirName)
    return dir_list

def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root,
                    name))
                return result

def search_srrdb(rlsnames = [], names = []):
    print("\t - Searching srrdb.com for matching release")
    try:
        if len(rlsnames):
            results = search_by_release(rlsnames)
        elif len(names):
            results = search_by_name(names)

    except Exception as e:
        print("%s -> %s" % (FAIL, e))
        return False

    if not results:
        print("%s -> %s" % (FAIL, "No matching results"))
        return False
    else:
        print("%s" % SUCCESS)

    if len(results) > 1:
        # need to work out which rls to use
        print("\t\t %s More than one release found matching release name %s" % (FAIL, results))
        return False

    release = results[0]
    print("\t\t - Matched release: %s" % release['release'])

    return release

def get_name_from_00_file(filename):
    base = os.path.basename(filename)
    name = os.path.splitext(base)[0]
    if '000-' in name:
        name = name[4:]
    elif '000_' in name:
        name = name[4:]
    elif '00-' in name:
        name = name[3:]
    elif '00_' in name:
        name = name[3:]
    return name

def get_release_name(dir):
    possible_rls_names = []
    sfv = find('*.sfv', dir)
    if not sfv is None and len(sfv) > 0:
        name = get_name_from_00_file(sfv[0])
        possible_rls_names.append(name)
        intname = name + "int"
        possible_rls_names.append(intname)
        intname = name + "-int"
        possible_rls_names.append(intname)
    nfo = find('*.nfo', dir)
    if not nfo is None and len(nfo) > 0:
        name = get_name_from_00_file(nfo[0])
        possible_rls_names.append(name)
        intname = name + "int"
        possible_rls_names.append(intname)
        intname = name + "-int"
        possible_rls_names.append(intname)
    m3u = find('*.m3u', dir)
    if not m3u is None and len(m3u) > 0:
        name = get_name_from_00_file(m3u[0])
        possible_rls_names.append(name)
        intname = name + "int"
        possible_rls_names.append(intname)
        intname = name + "-int"
        possible_rls_names.append(intname)
    directory_name = os.path.basename(os.path.normpath(dir))
    possible_rls_names.append(pathname2url(directory_name))
    possible_rls_names = list(OrderedDict.fromkeys(possible_rls_names))

    # find release by release name
    rls = search_srrdb(possible_rls_names)
    if not rls:
        if len(possible_rls_names) > 0:
            names = re.split('[^a-zA-Z0-9]+', possible_rls_names[0])
            rls = search_srrdb([], names)
    if not rls:
        names = re.split('[^a-zA-Z0-9]+', directory_name)
        rls = search_srrdb([], names)

    return rls

def process_dirs(dirs, output_dir):
    for dir in dirs:
        rls = get_release_name(dir)
        if not rls:
            missing_files.append(dir)
            continue

        print("\t - Downloading SRR from srrdb.com")
        # download srr
        try:
            srr_path = download_srr(rls['release'])
        except Exception as e:
            print("%s -> %s" % (FAIL, e))
            missing_files.append(dir)
        else:
            print("%s" % srr_path)
            if not fix_tags(srr_path, rls['release'], dir, output_dir):
                missing_files.append(dir)


def main(argv=None):
    parser = OptionParser(
    usage=("Usage: %prog -i input_dir -o output_dir\n"
    "This tool fixes the tags of music files.\n"
    "Example usage: %prog --input /home/johndoe/broken --output /home/johndoe/scene"),
    #version="%prog " + mp3rescene.__version__) # --help, --version
    version="%prog ") # --help, --version

    parser.add_option("-i", "--input", dest="input_dir", metavar="DIR",
                    default=".", help="Specifies input directory. "
                    "The default input path is the current directory.")
    parser.add_option("-o", "--output", dest="output_dir", metavar="DIR",
                    default=".", help="Specifies output directory. "
                    "The default output path is the current directory.")
    parser.add_option("-y", "--always-yes", dest="always_yes", default=False,
                    action="store_true",
                    help="assume Yes for all prompts")

    if argv is None:
        argv = sys.argv[1:]

    # no arguments given
    if not len(argv):
       # show application usage
       parser.print_help()
       return 0

    (options, args) = parser.parse_args(args=argv)
    dirs = get_directories(options.input_dir)

    process_dirs(dirs, options.output_dir)
    if len(missing_files) > 0:
        print("could not recover:")
        print(*missing_files, sep='\n')

if __name__ == "__main__":
    sys.exit(main())

