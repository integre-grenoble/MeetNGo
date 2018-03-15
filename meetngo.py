#!/usr/bin/env python3
import configparser
import csv
import os
import pathlib
import pickle
import shutil
import unicodedata
from datetime import datetime


# sorry for the global variable... at least it make sense for a config
config = configparser.ConfigParser(
    converters={'datetime': lambda s: datetime.strptime(s, '%Y-%m-%d')}
)
config.read('config.ini')


def compat(s):
    """Return the string in lowercase and without accents."""
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
                   if unicodedata.category(c) != 'Mn')\
             .casefold().strip().replace(' ', '')


def find_file(name, folder='.'):
    """Find a file that contain `name` in its filename."""
    files = list(pathlib.Path(folder).glob('*{}*'.format(name)))

    if len(files) == 1:
        return files[0]
    elif len(files) < 1:
        input('No file match "{}".'.format(name))
        exit()

    print('There are {} files that match "{}":'.format(len(files), name))
    print('\n'.join(['  {}) {}'.format(i+1, f) for i, f in enumerate(files)]))
    try:
        ans = int(input('\nEnter a selection (default=1): ')) - 1
    except (ValueError):
        ans = 0
    print()
    return files[ans] if 0 <= ans and ans < len(files) else files[0]


class Group(set):

    def __init__(self, person_class, *args):
        self.person_class = person_class
        super().__init__(*args)

    def append(self, person):
        """Add a person to the group, ask user if already into."""
        exist = False
        for other in self:
            if not exist and person.look_like(other):
                print('\n{}\n{}'.format(other, person))
                ans = input('Are these people the same person ? [Y/n] ')
                if compat(ans) == compat('n'):
                    print('Answer taken into account. Those are two different \
person.')
                else:
                    print('Copy removed!')
                    exist = True
        if not exist:
            self.add(person)

    def load(self, filename, ignore_before=datetime.min):
        """Load a csv file into the group."""
        date_format = '%Y/%m/%d %I:%M:%S %p %Z'
        with open(filename) as f:
            reader = csv.reader(f)
            for _ in range(config['CSV files'].getint('unread row', 1)):
                next(reader)  # discard first lines
            for row in reader:
                if datetime.strptime(row[0], date_format) > ignore_before:
                    self.append(self.person_class(row))

    def restore(self, dir_path):
        """Unpickle objects into the group."""
        for path in pathlib.Path(dir_path).glob('*.pickle'):
            with path.open('rb') as f:
                self.append(pickle.load(f))


class Mentor:

    def __init__(self, row):
        """Initialize a mentor from a csv row."""
        self.surname = row[1].strip()
        self.name = row[2].strip()
        self.email = row[3].strip()
        self.lang = set(row[7].split(';'))
        self.country = row[8].strip()
        self.city = row[9].strip()
        self.university = row[10].strip()
        self.present_the_23 = True if row[16] == 'Oui / Yes' else False
        self.helping_the_23 = True if row[17] == 'Oui / Yes' else False

        self.mentees = []

    @property
    def languages(self):
        return ', '.join(self.lang)

    def look_like(self, other):
        """Return `True` if `other` might be the same person."""
        return (compat(self.email) == compat(other.email)
                or (compat(self.name) == compat(other.name)
                    and compat(self.surname) == compat(other.surname)))

    def generate_email(self):
        """Generate emails form a predefined template."""
        emails = ''
        template_path = config['Templates']['folder'] + '/'
        template_path += config['Templates']['mentors']
        with open(template_path) as tmpl:
                template = tmpl.read()
        for mentee in self.mentees:
            emails += template.format(recipient=self, mentee=mentee)
        return emails

    def save(self):
        """Pickle mentor information for later use."""
        path = pathlib.Path(config['Data']['top folder'])
        path = path / config['Data']['mentors folder']
        if not path.exists():
            path.mkdir(parents=True)
        path = path / '{}.{}.pickle'.format(compat(self.name),
                                            compat(self.surname))
        with path.open('wb') as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    def __str__(self):
        return ' - {name} {surname}, {email}, have studied in {country}, \
speak {lang}.'.format_map(self.__dict__)


class Mentee:

    def __init__(self, row):
        """Initialize a mentee from a csv row."""
        self.surname = row[1].strip()
        self.name = row[2].strip()
        self.email = row[3].strip()
        self.lang = set(row[7].split(';'))
        self.country = row[8].strip()
        self.city = row[9].strip()
        self.university = row[10].strip()
        self.present_the_23 = True if row[16] == 'Oui / Yes' else False

        self.mentor = None

    @property
    def languages(self):
        return ', '.join(self.lang)

    def look_like(self, other):
        """Return `True` if `other` might be the same person."""
        return (compat(self.email) == compat(other.email)
                or (compat(self.name) == compat(other.name)
                    and compat(self.surname) == compat(other.surname)))

    def find_mentor(self, mentors_group):
        """Find the most suitable mentors among `mentors_group`."""
        # only keep mentor that have been the the desired country
        mentors = [m for m in mentors_group
                   if compat(self.country) == compat(m.country)]
        if len(mentors) > 0:
            # if some mentors remain, try to limit to the desired city
            by_city = [m for m in mentors
                       if compat(self.city) == compat(m.city)]
            if len(by_city) > 0:
                # if some mentors remain, try to limit to the desired univ
                mentors = by_city
                by_univ = [m for m in mentors
                           if compat(self.university) == compat(m.university)]
                if len(by_univ) > 0:
                    mentors = by_univ
            # among the remaining mentors, choose the one with less mentees
            mentors.sort(key=lambda mentor: len(mentor.mentees))
            self.mentor = mentors[0]
            # don't forget to add self to its mentor's mentees
            self.mentor.mentees.append(self)

    def generate_email(self):
        """Generate email form predefined templates."""
        template_path = config['Templates']['folder'] + '/'
        if self.mentor is None:
            template_path += config['Templates']['alone mentees']
            with open(template_path) as tmpl:
                email = tmpl.read().format(recipient=self)
        else:
            template_path += config['Templates']['mentees']
            with open(template_path) as tmpl:
                email = tmpl.read().format(recipient=self, mentor=self.mentor)
        return email

    def save(self):
        """Pickle mentee information for later use."""
        path = pathlib.Path(config['Data']['top folder'])
        path = path / config['Data']['mentees folder']
        if not path.exists():
            path.mkdir(parents=True)
        path = path / '{}.{}.pickle'.format(compat(self.name),
                                            compat(self.surname))
        with path.open('wb') as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    def __str__(self):
        return ' - {name} {surname}, {email}, want to go to {country}, speak \
{lang}.'.format_map(self.__dict__)


if __name__ == '__main__':
    os.system('')  # enable ANSI escape code on Windows *facepalm*

    # nice ascii art
    print('''\x1B[1;34m\
 __  __           _   _ _   _ _  ____
|  \\/  | ___  ___| |_( ) \\ | ( )/ ___| ___
| |\\/| |/ _ \\/ _ \\ __|/|  \\| |/| |  _ / _ \\
| |  | |  __/  __/ |_  | |\\  | | |_| | (_) |
|_|  |_|\\___|\\___|\\__| |_| \\_|  \\____|\\___/\x1B[m\n''')

    # if 'last run' is in the config, the user might want to ignore
    # results prior to that date
    last_run = config['CSV files'].getdatetime('last run', datetime.min)
    if last_run > datetime.min:
        ans = input('Do you want to ignore csv data from before {}? [Y/n] '\
                    .format(last_run.date()))
        if compat(ans) == compat('n'):
            last_run == datetime.min.date()

    # create a mentor group and fill it with old data (if the user agree)
    mentors = Group(Mentor)
    path = pathlib.Path(config['Data']['top folder'])
    path = path / config['Data']['mentors folder']
    if path.exists():
        ans = input('Previous mentors data are available, do you want to \
use them? [Y/n] ')
        if compat(ans) != compat('n'):
            mentors.restore(path)
    # add new mentors from csv
    mentors_file = find_file(config['CSV files']['mentors file'],
                             config['CSV files']['folder'])
    print('"{}" will be used for new mentors data.'.format(mentors_file))
    mentors.load(mentors_file, last_run)

    # create a mentee group and fill it with old data (if the user agree)
    mentees = Group(Mentee)
    path = pathlib.Path(config['Data']['top folder'])
    path = path / config['Data']['mentees folder']
    if path.exists():
        ans = input('\nPrevious mentees data are available, do you want to \
use them? [Y/n] ')
        if compat(ans) != compat('n'):
            mentors.restore(path)
    # add new mentees from csv
    mentees_file = find_file(config['CSV files']['mentees file'],
                             config['CSV files']['folder'])
    print('"{}" will be used for new mentees data.'.format(mentees_file))
    mentees.load(mentees_file, last_run)

    # try to find a mentor for each mentee
    for mentee in mentees:
        mentee.find_mentor(mentors)

    # generate all the emails, and write them in a file
    with open(config['Emails']['generated emails file'], 'w') as email:
        need_alone_message = True

        for mentee in mentees:  # generate mentees emails
            email.write(mentee.generate_email())

            if mentee.mentor is None:  # warn the user if some mentee
                if need_alone_message:
                    # print this message only once
                    need_alone_message = False
                    print("\nThese students don't have a mentor:")
                print(mentee)

        for mentor in mentors:  # generate mentors emails
            email.write(mentor.generate_email())

    # if some mentees are alone
    if not need_alone_message:
        # ask the user to save them
        ans = input('\nDo you want to save them for next time? [Y/n] ')
        if compat(ans) != compat('n'):
            # if old data are present, remove them first
            path = pathlib.Path(config['Data']['top folder'])
            path = path / config['Data']['mentees folder']
            if path.exists():
                shutil.rmtree(path)
            # save only mentees that doesn't have a mentor
            for mentee in mentees:
                if mentee.mentor is None:
                    mentee.save()

    # also ask the user to save mentors
    ans = input('\nDo you want to save mentors data for next time? [Y/n] ')
    if compat(ans) != compat('n'):
        for mentor in mentors:
            mentor.save()

    # save today's date for the next time
    with open('config.ini', 'w') as f:
        config['CSV files']['last run'] = datetime.today().date().isoformat()
        config.write(f)

    print()  # final new line, IMHO it look better with it
