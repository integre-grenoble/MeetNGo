import csv
import unicodedata


def compat(s):
    """Return the string in lowercase and without accents."""
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
                   if unicodedata.category(c) != 'Mn').casefold().strip()


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
                    print('Answer taken into account. Those are to different person.\n')
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

    @property
    def languages(self):
        return ', '.join(self.lang)

    def look_like(self, other):
        return (compat(self.email) == compat(other.email)
                or (compat(self.name) == compat(other.name)
                    and compat(self.surname) == compat(other.surname)))

    def generate_email(self):
        with open('templates/mail_Filleul.txt') as template:
            email = template.read()
        #email = email.format(recipient=self, partner=self.partner)
        email = email.format(recipient=self)
        with open('generated_emails/{}.txt'.format(self.email), 'w') as f:
            f.write(email)

    def __str__(self):
        return ' - {name} {surname}, {email}, have studied in {country}, \
speak {lang}.'.format_map(self.__dict__)


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
        self.helping_the_23 = True if row[17] == 'Oui / Yes' else False

    @property
    def languages(self):
        return ', '.join(self.lang)

    def look_like(self, other):
        return (compat(self.email) == compat(other.email)
                or (compat(self.name) == compat(other.name)
                    and compat(self.surname) == compat(other.surname)))

    def generate_email(self):
        with open('templates/mail_Filleul.txt') as template:
            email = template.read()
        #email = email.format(recipient=self, partner=self.partner)
        email = email.format(recipient=self)
        with open('generated_emails/{}.txt'.format(self.email), 'w') as f:
            f.write(email)

    def __str__(self):
        return ' - {name} {surname}, {email}, want to go to {country}, \
speak {lang}.'.format_map(self.__dict__)


if __name__ == '__main__':
    mentors = Group(Mentor)
    mentors.load("../Meet'N'Go 2018 - Questionnaire Parrain_Marraine.csv")

    mentees = Group(Mentee)
    mentees.load("../Meet'N'Go 2018 - Questionnaire Filleul.csv")

    print('Mentors:')
    for mentor in mentors:
        print(mentor)
        mentor.generate_email()
    print('Mentees:')
    for mentee in mentees:
        print(mentee)
        mentee.generate_email()
