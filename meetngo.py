#!/usr/bin/env python3
import csv
import os
import pickle
import shutil
import unicodedata
from pathlib import Path


def compat(s):
    """Return the string in lowercase and without accents."""
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
                   if unicodedata.category(c) != 'Mn')\
             .casefold().strip().replace(' ', '')


def find_file(name, folder='.'):
    """Find a file that contain `name` in its filename."""
    files = list(Path(folder).glob('*{}*'.format(name)))

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

    def load(self, filename):
        """Load a csv file into the group."""
        with open(filename) as f:
            reader = csv.reader(f)
            next(reader)  # discard the first line
            for row in reader:
                self.append(self.person_class(row))

    def restore(self, dir_path):
        """Load pickeled object into the group."""
        for path in Path(dir_path).glob('*.pickle'):
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
        with open('templates/mail_parrain_marraine.txt') as tmpl:
                template = tmpl.read()
        for mentee in self.mentees:
            emails += template.format(recipient=self, mentee=mentee)
        return emails

    def save(self):
        """Pickle mentor information for later use."""
        path = Path('data') / 'mentors'
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
        if self.mentor is None:
            with open('templates/mail_filleul_sans_parrain.txt') as tmpl:
                email = tmpl.read().format(recipient=self)
        else:
            with open('templates/mail_filleul.txt') as tmpl:
                email = tmpl.read().format(recipient=self, mentor=self.mentor)
        return email

    def save(self):
        """Pickle mentee information for later use."""
        path = Path('data') / 'mentees'
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

    # create a mentor group and fill it with old data (if the user agree)
    mentors = Group(Mentor)
    path = Path('data') / 'mentors'
    if path.exists():
        ans = input('Previous mentors data are available, do you want to \
use them? [y/N] ')
        if compat(ans) == compat('y'):
            mentors.restore(path)
    # add new mentors from csv
    mentors_file = find_file('Questionnaire Parrain-Marraine')
    print('"{}" will be used for new mentors data.'.format(mentors_file))
    mentors.load(mentors_file)

    # create a mentor group and fill it with old data (if the user agree)
    mentees = Group(Mentee)
    path = Path('data') / 'mentees'
    if path.exists():
        ans = input('\nPrevious mentees data are available, do you want to \
use them? [y/N] ')
        if compat(ans) == compat('y'):
            mentors.restore(path)
    # add new mentors from csv
    mentees_file = find_file('Questionnaire Filleul')
    print('"{}" will be used for new mentees data.'.format(mentees_file))
    mentees.load(mentees_file)

    # try to find a mentor for each mentee
    for mentee in mentees:
        mentee.find_mentor(mentors)

    # generate all the emails, and write them in a file
    with open('email.txt', 'w') as email:
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
            path = Path('data') / 'mentees'
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

    print()  # final new line, IMHO it look better with it
