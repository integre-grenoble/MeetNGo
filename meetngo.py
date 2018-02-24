import csv


def generate(filename, model, **kwargs):
    with open(model) as i, open(filename, 'w') as o:
        o.write(i.read().format(**kwargs))


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
                if ans.casefold() == 'n'.casefold():
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
        self.languages = set(row[7].split(';'))
        self.country = row[8].strip()
        self.city = row[9].strip()
        self.university = row[10].strip()

    def look_like(self, other):
        return (self.email.casefold() == other.email.casefold()
                or (self.email.casefold() == other.email.casefold()
                    and self.email.casefold() == other.email.casefold()))

    def __str__(self):
        return ' - {name} {surname}, {email}, have studied in {country}, \
speak {languages}.'.format_map(self.__dict__)


class Mentee:

    def __init__(self, row):
        self.surname = row[1].strip()
        self.name = row[2].strip()
        self.email = row[3].strip()
        self.languages = set(row[7].split(';'))
        self.country = row[8].strip()
        self.city = row[9].strip()
        self.university = row[10].strip()

    def look_like(self, other):
        return (self.email.casefold() == other.email.casefold()
                or (self.email.casefold() == other.email.casefold()
                    and self.email.casefold() == other.email.casefold()))

    def __str__(self):
        return ' - {name} {surname}, {email}, want to go to {country}, \
speak {languages}.'.format_map(self.__dict__)


if __name__ == '__main__':
    mentors = Group(Mentor)
    mentors.load("../Meet'N'Go 2018 - Questionnaire Parrain_Marraine.csv")

    mentees = Group(Mentee)
    mentees.load("../Meet'N'Go 2018 - Questionnaire Filleul.csv")

    print('Mentors:')
    for mentor in mentors:
        print(mentor)
    print('Mentees:')
    for mentee in mentees:
        print(mentee)
