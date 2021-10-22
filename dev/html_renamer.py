import os
import re
import sys
import getopt
import html2text
import logging
import difflib
from itertools import zip_longest

logging.basicConfig()


def color(text, which):
    # other type of coloring here (backgrounds only?) https://stackoverflow.com/a/21786287/3577695
    if which == 'test':     # print all colors, and exit function
        for i in range(1, 100):
            print('\\033[' + str(i) + 'm', '\033[' + str(i) + 'm' + 'xxxxx' + '\033[0m')
        return

    options = {
        'red'        : '\033[31m',
        'green'      : '\033[32m',
        'yellow'     : '\033[93m',
        'blue'       : '\033[34m',
        'purple'     : '\033[95m',
        'cyan'       : '\033[96m',
        'darkcyan'   : '\033[36m',
        'bold'       : '\033[1m',
        'underline'  : '\033[4m',
        'END'        : '\033[0m',
    }

    return options[which] + text + options['END']

def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

def color_print(c, *args):
    print(*[color(arg, c) for arg in args])


def print_diffs(name, new_name):
    """
    Prints file names, with differences colored
    :param name:
    :param new_name:
    :return:
    """
    d = difflib.Differ()
    result = list(d.compare([name], [new_name]))

    # for line in result:
    #     print(line)

    changes = [[name, ''], [new_name, '']]
    curr = -1
    for line in result:
        if curr == -1:
            curr += 1
            changes[curr][0] = line     # save string
        elif curr > -1:
            if line[0] in ['+', '-', ' ']:
                curr += 1
                changes[curr][0] = line     # save string
            else:
                changes[curr][1] = line          # save changes

    for i, change in enumerate(changes):
        ret = []
        for c, dif in zip_longest(change[0][2:], change[1][2:]):
            if c is None:
                c = ''
            if dif == '+' or [dif, i] == ['^', 1]:
                c = color(c, 'green')
            elif dif == '-' or [dif, i] == ['^', 0]:
                c = color(c, 'red')
            ret.append(c)
        print(''.join(ret))
    print()


class Renamer():

    def __init__(self):
        self.dryrun = False
        self.verbose = False
        self.directory = '.'
        self.extension = 'html'
        self.depth = -1
        self.problematic = []
        self.used_names = {}
        self.logger = logging.getLogger('Renamer')

    def sanitize(self, string):
        # Extended list of reserved chars for file names and the chosen replacements
        #   : (colon)                   ->      @ (at)
        #   < (less than)               ->      $ (dollar sing)
        #   > (greater than)            ->      + (plus)
        #   " (double quote)            ->      = (equal)
        #   / (forward slash)           ->      % (percentage)
        #   \ (backslash)               ->      & (ampersand)
        #   | (vertical bar or pipe)    ->      # (hash)
        #   ? (question mark)           ->      ! (exclamation mark)
        #   * (asterisk)                ->      ~ (tilde)

        string = string.replace(':', '@')
        string = string.replace('<', '$')
        string = string.replace('>', '+')
        string = string.replace('\"', '=')
        string = string.replace('/', '%')
        string = string.replace('\\', '&')
        string = string.replace('|', '#')
        string = string.replace('?', '!')
        string = string.replace('*', '~')

        return string

    def generate_name(self, in_file):

        self.logger.debug(('generate_name: ', in_file))

        # This will rarely separate any file since rtf's have non printable format chars
        if os.stat(in_file).st_size > 0:
            with open(in_file, 'r') as file:
                text = file.read()
            
            read = html2text.html2text(text).strip()

            if len(read) == 0:
                print('WARNING!! ', in_file, ' is empty, check by hand.')
                self.problematic.append(in_file)
            else:

                # prepare the new name of the file
                page_number = ''
                i = 0
                                    
                match0 = re.search(':\\s?([0-9]+(?:-[0-9]+){0,3})\\s?[\'‘’"`]{0,3}\\)', read)
                match1 = re.search('[p|P]\\.\\s?([0-9]+(?:-[0-9]+)?)', read)
                match2 = re.search(r'\(\d{4}(?:-[0-9]{4})?\D*?(?:\*){0,2}\D*?:\D*?(?:\*){0,2}\D*?([0-9]+(?:-[0-9]+){0,3})\D*?\)', read)

                if not any((match0, match1, match2)):
                    self.problematic.append(in_file)
                    self.logger.debug(('matches', match0, match1, match2))
                else:
                    # filter the non matching regexs and
                    # use the match that begins earliest
                    match = min(filter(None, [match0, match1, match2]), key=lambda x: x.start())
                    page_number = match[1]

                page_number = self.sanitize(page_number)

                new_name = os.path.join(os.path.dirname(in_file), 
                                        os.path.basename(os.path.dirname(in_file)) + ' p' + page_number)

                name_end = '.' + self.extension

                # prevents double points between the file names and the extension
                # the path has already been normalized so this will not change the file path
                new_name = new_name.replace('..', '.')

                # if the name was already used append a number at the end to prevent overwriting
                i = 1
                appendix = ''

                while (new_name + appendix + name_end) in self.used_names:
                    appendix = ' #' + str(i)
                    i += 1

                # a feasible name was found 
                # record the new name and the file to be renamed
                self.used_names[new_name + appendix + name_end] = in_file
                self.logger.debug(new_name)
                
    def get_params(self):

        try:
            opts, args = getopt.getopt(sys.argv[1:],
                                       "hd:e:lp:v", 
                                       ['help', 'path=', 'extension=', 'dryrun', 'depth=', 'verbose'])
        except getopt.GetoptError as err:
            # print help information and exit:
            print(err)  # will print something like "option -a not recognized"
            sys.exit(2)
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                print('file_namer: will read the reanme the files with the first line of text')
                print('Currently supported formats: txt rtf html')
                print('Parameters:')
                print('\th, --help: prints this message')
                print('\tp, --path: the directory containing the files, default is ./')
                print('\te, --extension: the extension if the files to be renamed, default is html')
                print('\td, --depth: how many subdirectories to traverse on the renaming, -1 for full depth')
                print('\tl, --dryrun: see what changes would be made, no file names will be changed')
                print('\tv, --verbose: see what changes would be made, file names will be changed if possible')
                sys.exit()

            elif opt in ("-p", "--path"):
                self.directory = os.path.normpath(arg)
                self.logger.debug(self.directory)
            elif opt in ("-l", "--dryrun"):
                self.dryrun = True
            elif opt in ("-v", "--verbose"):
                self.verbose = True
            elif opt in ("-d", "--depth"):
                self.depth = int(arg)
            elif opt in ("-e", "--extension"):
                self.extension = arg
                self.logger.debug(arg)
                if self.extension[0] == '.':
                    # remove leading point
                    self.extension = self.extension[1:]

        print('Renaming all the ' + self.extension + ' the directory: ' + self.directory)
        print('Failsafe: ' + ('Engaged' if self.dryrun else 'Disengaged, file names will be rewritten'))

    def rename_all(self):

        def find_files(path, live, level=0):
            for base in os.listdir(path):
                full_path = os.path.join(path, base)

                # avoid hidden files and directories
                if not base.startswith('.'):
                    # if its a file, rename it
                    if os.path.isfile(full_path):
                        self.logger.debug(('file:', base))

                        if base.endswith(self.extension):

                            self.generate_name(full_path)

                            if self.verbose:
                                print('Reading:', base)

                    # if is a directory, traverse it
                    elif os.path.isdir(full_path) and (level < self.depth or self.depth == -1):
                        self.logger.debug((level, full_path))
                        find_files(full_path, live, level + 1)
                    else:
                        self.logger.debug((level, base))

        find_files(self.directory, False)

        if self.dryrun or self.verbose:
            for new, curr in self.used_names.items():
                print_diffs(curr, new)
                # if curr != new:
                #     print(curr, ' ->\n', new)
                # else:
                #     print(curr, 'stays the same')

        if self.problematic:
            print('Problematic Files:')
            for pro in natural_sort(self.problematic):
                print(pro)
        else:
            print('No problematic files detected')
            # if no probleamtic files are detected execute the renaming
            if not self.dryrun:
                print('Procedding to rename')
                for new, curr in self.used_names.items():
                    os.rename(curr, new)


if __name__ == '__main__':
    rnmr = Renamer()
    rnmr.logger.setLevel(logging.WARN)
    rnmr.get_params()
    rnmr.rename_all()
