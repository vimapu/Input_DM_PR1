import logging
import pandas
from common import *
from datetime import datetime
import numpy
import json
import sys

# logging config
logging.basicConfig(filename = './log/integration_script.log', encoding = 'utf-8', level = logging.DEBUG)

## files
MOVIES_FILE = './input/tmdb_5000_movies.csv'

GENRE_SUFFIX = '_genre'

## fieldnames
# new
MOVIE_AGE = 'movie_age'
HAS_TAGLINE = 'has_tagline'
# new - popularity
MAX_ACTOR_POPULARITY = 'max_actor_popularity'
MIN_ACTOR_POPULARITY = 'min_actor_popularity'
AVG_ACTOR_POPULARITY = 'avg_actor_popularity'
ADDED_ACTOR_POPULARITY = 'added_actor_popularity'
# new - number of actors
ACTORS_COUNT = 'actors_count'
FEMALE_ACTORS_COUNT = 'female_actors_count'
MALE_ACTORS_COUNT = 'male_actors_count'
AVG_ACTOR_AGE = 'avg_actor_age'
MAX_ACTOR_AGE = 'max_actor_age'
MIN_ACTOR_AGE = 'min_actor_age'
# original fields
MOVIE_ID_FIELD = 'id'
MOVIE_GENRES_FIELD = 'genres'
MOVIE_TAGLINE_FIELD = 'tagline'
RELEASE_DATE_FIELD = 'release_date'
ACTOR_ID_FIELD = 'id'
ACTOR_GENDER_FIELD = 'gender'
ACTOR_BIRTHDAY_FIELD = 'birthday'
ACTOR_POPULARITY_FIELD = 'popularity'

def get_movies_length():
    movies_df = pandas.read_csv(MOVIES_FILE)
    return movies_df[MOVIE_ID_FIELD].size

def print_progress(current: int, total: int):
    increment = total / 20
    sys.stdout.write(
        "\r[" + "=" * round((current // increment)) + " " * round(((total - current) // increment)) + "]" + str(
            (current / total) * 100) + "%")
    sys.stdout.flush()

## calculates the age difference
def calculate_age_years(date_str: str):
    if date_str is None or not date_str:
        logging.warning("A date string must be passed.")
        return "N/A"
    else:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.today()
        year_diff = today.year - date.year
        if date.month - today.month < 0 and date.day - today.day < 0:
            year_diff -= 1
        return year_diff

## parses the genres from the genres field
def parse_genres(genre_field: str):
    genre_names = []
    genre_list = json.loads(genre_field)
    for genre in genre_list:
        genre_name = genre['name']
        genre_names.append(genre_name.lower())
    return genre_names

## finds the list of unique genres
def find_genres(genre_column = None):
    if genre_column is None:
        raise Exception('genre_column param must not be null.')
    genres_list = []
    for genre_str in genre_column.iteritems():
        parsed_genres = parse_genres(genre_field = genre_str[1])
        for genre in parsed_genres:
            genre_lc = genre.lower()
            if (genre_lc + GENRE_SUFFIX) not in genres_list:
                genres_list.append(genre_lc + GENRE_SUFFIX)
    return genres_list

class NewFieldsBuffer:
    def __init__(self):
        self.popularities = []
        self.birthdays = []
        self.genders = []
        return

    def add_actor(self, actor_row = None):
        if actor_row is None:
            raise Exception("Actor must have a value.")
        self.popularities.append(actor_row[ACTOR_POPULARITY_FIELD])
        self.birthdays.append(actor_row[ACTOR_BIRTHDAY_FIELD])
        self.genders.append(actor_row[ACTOR_GENDER_FIELD])

    def calculate_ages(self, movie_release_date_str = None):
        ages = []
        if movie_release_date_str is None or not movie_release_date_str:
            logging.warning("A release date must be passed.")
        else:
            movie_release_date = datetime.strptime(movie_release_date_str, '%Y-%m-%d')
            for birthday_str in self.birthdays:
                if type(birthday_str) == str and birthday_str:
                    try:
                        birthday = datetime.strptime(birthday_str, '%Y-%m-%d')
                        year_diff = movie_release_date.year - birthday.year
                        if movie_release_date.month - birthday.month < 0 and movie_release_date.day - birthday.day < 0:
                            year_diff -= 1
                        ages.append(year_diff)
                    except:
                        logging.debug('Found problematic birthday %s', birthday_str)
        return ages

    def count_genders(self):
        males, females = 0, 0
        for gender in self.genders:
            if gender == 2:
                males += 1
            elif gender == 1:
                females += 1
        return males, females

    ## adds the genre binary features
    def add_genres(self, features_dict = None, genres_list = None, genres_string_field: list = None):
        if features_dict is None or genres_string_field is None or genres_list is None:
            raise Exception('The features dict, genres string and genres must not be null')
        for genre_field in genres_list:
            features_dict[genre_field] = 0
        parsed_genres = parse_genres(genre_field = genres_string_field)
        genre_field_names = [g + GENRE_SUFFIX for g in parsed_genres]
        for genre_field_name in genre_field_names:
            features_dict[genre_field_name] = 1
        return features_dict

    ## adds a has tagline binary field.
    def add_has_tagline(self, features_dict = None, tagline_field = None):
        if tagline_field is None or not tagline_field or tagline_field == '':
            features_dict[HAS_TAGLINE] = 0
        else:
            features_dict[HAS_TAGLINE] = 1
        return features_dict

    def get_features_dict(self, release_date_str = None, genres = None, genre_field_str = None, tagline_str = None):
        if release_date_str is None or genres is None or genre_field_str is None:
            raise Exception("Release date, genres and genre field must have values")
        new_features_dict = {}
        new_features_dict[MOVIE_AGE] = calculate_age_years(date_str = release_date_str)
        new_features_dict[AVG_ACTOR_POPULARITY] = 0 if len(self.popularities) == 0 else numpy.nanmean(self.popularities)
        new_features_dict[MIN_ACTOR_POPULARITY] = 0 if len(self.popularities) == 0 else numpy.nanmin(self.popularities)
        new_features_dict[MAX_ACTOR_POPULARITY] = 0 if len(self.popularities) == 0 else numpy.nanmax(self.popularities)
        new_features_dict[ADDED_ACTOR_POPULARITY] = 0 if len(self.popularities) == 0 else numpy.nansum(
            self.popularities)
        males, females = self.count_genders()
        new_features_dict[FEMALE_ACTORS_COUNT] = females
        new_features_dict[MALE_ACTORS_COUNT] = males
        new_features_dict[ACTORS_COUNT] = len(self.popularities)
        ages = self.calculate_ages(movie_release_date_str = release_date_str)
        avg_age = 0
        max_age = 0
        min_age = 0
        if len(ages) > 0:
            max_age = numpy.max(ages)
            avg_age = numpy.average(ages)
            min_age = numpy.min(ages)
        new_features_dict[MAX_ACTOR_AGE] = max_age
        new_features_dict[AVG_ACTOR_AGE] = avg_age
        new_features_dict[MIN_ACTOR_AGE] = min_age
        new_features_dict = self.add_genres(features_dict = new_features_dict, genres_list = genres,
                                            genres_string_field = genre_field_str)
        new_features_dict = self.add_has_tagline(features_dict = new_features_dict, tagline_field = tagline_str)
        return new_features_dict

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    logging.info('Starting datasets integration.')
    credit_df = pandas.read_csv('./output/credit.csv')
    actors_df = pandas.read_csv('./output/actors.csv')
    movies_length = get_movies_length()
    genres = find_genres(pandas.Series(pandas.read_csv('./input/tmdb_5000_movies.csv')['genres']))
    movies_count = 0
    with open('./input/tmdb_5000_movies.csv', encoding = 'utf-8', newline = '') as moviescsv:
        reader = csv.DictReader(moviescsv)
        fieldnames = []
        fieldnames.extend(reader.fieldnames)
        fieldnames.extend(
            [MAX_ACTOR_POPULARITY, MIN_ACTOR_POPULARITY, AVG_ACTOR_POPULARITY, ADDED_ACTOR_POPULARITY, ACTORS_COUNT,
             FEMALE_ACTORS_COUNT, MALE_ACTORS_COUNT, AVG_ACTOR_AGE, MAX_ACTOR_AGE, MIN_ACTOR_AGE, MOVIE_AGE, HAS_TAGLINE])
        fieldnames.extend(genres)
        with open('./output/movies.csv', 'w', encoding = 'utf-8', newline = '') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
            writer.writeheader()
            # iterate over the movies
            for movie in reader:
                logging.info('Processed %.2f percent. Processing movie %d out of %d' % (
                    movies_count / movies_length, movies_count + 1, movies_length))
                print_progress(current = movies_count, total = movies_length)
                movies_count += 1
                ## for each movie, obtain the actors in the credit and the actors dataset
                movie_id = movie[MOVIE_ID_FIELD]
                actor_ids = credit_df[credit_df['movie_id'] == int(movie_id)].iloc[:, 1].tolist()
                buffer = NewFieldsBuffer()
                # iterate over the actors to calculate the new fields and add them to the new csv file
                for actor_id in actor_ids:
                    # add single actor fields to buffer
                    buffer.add_actor(actor_row = actors_df[actors_df[ACTOR_ID_FIELD] == actor_id].iloc[0])
                # obtain buffer calculated fields and merge into a row dictionary
                new_csv_row = movie | buffer.get_features_dict(release_date_str = movie[RELEASE_DATE_FIELD],
                                                               genres = genres,
                                                               genre_field_str = movie[MOVIE_GENRES_FIELD],
                                                               tagline_str = movie[MOVIE_TAGLINE_FIELD])
                writer.writerow(new_csv_row)
    logging.INFO('\rFinished integrating datasets.')
