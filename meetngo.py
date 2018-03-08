#!/usr/bin/env python3
import csv
from pathlib import Path
import pickle
import sys
import unicodedata


def compat(s):
    """Return the string in lowercase and without accents."""
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
                     if c == ' ' or unicodedata.category(c) != 'Mn')\
             .casefold().strip()


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
                    print('Answer taken into account. Those are two \
different person.\n')
                else:
                    print('Copy removed!\n')
                    exist = True
        if not exist:
            self.add(person)

    def load(self, filename):
        with open(filename) as f:
            reader = csv.reader(f)
            next(reader)  # discard the first line
            for row in reader:
                self.append(self.person_class(row))

    def restore(self, dir_path):
        pass


class Mentor:

    def __init__(self, row):
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
        return (compat(self.email) == compat(other.email)
                or (compat(self.name) == compat(other.name)
                    and compat(self.surname) == compat(other.surname)))

    def generate_email(self):
        emails = ''
        with open('templates/mail_parrain_marraine.txt') as tmpl:
                template = tmpl.read()
        for mentee in self.mentees:
            emails += template.format(recipient=self, mentee=mentee)
        return emails

    def save(self):
        path = Path('data') / 'mentors'
        if not path.exists():
            print('created')
            path.mkdir(parents=True)
        path = path / '{}.{}.pickle'.format(compat(self.name),
                                            compat(self.surname))
        with path.open('wb') as f:
            pickle.dump(self, f)

    def __str__(self):
        return ' - {name} {surname}, {email}, have studied in {country}\
, speak {lang}.'.format_map(self.__dict__)


class Mentee:

    def __init__(self, row):
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
        return (compat(self.email) == compat(other.email)
                or (compat(self.name) == compat(other.name)
                    and compat(self.surname) == compat(other.surname)))

    def find_mentor(self, mentors_group):
        mentors = [m for m in mentors_group
                   if compat(self.country) == compat(m.country)]
        if len(mentors) > 0:
            by_city = [m for m in mentors
                       if compat(self.city) == compat(m.city)]
            if len(by_city) > 0:
                mentors = by_city
                by_univ = [m for m in mentors
                           if compat(self.university) == compat(m.university)]
                if len(by_univ) > 0:
                    mentors = by_univ
            self.mentor = mentors.sort(key=lambda x: len(x.mentees))[0]

    def generate_email(self):
        if self.mentor is None:
            with open('templates/mail_filleul_sans_parrain.txt') as tmpl:
                email = tmpl.read().format(recipient=self)
        else:
            with open('templates/mail_filleul.txt') as tmpl:
                email = tmpl.read().format(recipient=self, mentor=self.mentor)
        return email

    def __str__(self):
        return ' - {name} {surname}, {email}, want to go to {country}, \
speak {lang}.'.format_map(self.__dict__)


if __name__ == '__main__':

    print(r''' __  __           _   _ _   _ _  ____
|  \/  | ___  ___| |_( ) \ | ( )/ ___| ___
| |\/| |/ _ \/ _ \ __|/|  \| |/| |  _ / _ \
| |  | |  __/  __/ |_  | |\  | | |_| | (_) |
|_|  |_|\___|\___|\__| |_| \_|  \____|\___/
                                            ''')

    mentors = Group(Mentor)
    mentors.load(input('Path to "Questionnaire Parrain-Marraine": '))

    mentees = Group(Mentee)
    mentees.load(input('Path to "Questionnaire Filleul": '))

    for mentee in mentees:
        mentee.find_mentor(mentors)

    with open('email.txt', 'w') as email:

        need_alone_message = True

        for mentee in mentees:
            email.write(mentee.generate_email())

            if mentee.mentror is None:
                if need_alone_message:
                    need_alone_message = False
                    print("These students don't have a mentor:")
                print(mentee)

    input('\nDone.')
