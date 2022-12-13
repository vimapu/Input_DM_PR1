import logging
from common import *

## logging config
logging.basicConfig(filename = './log/credits_flattening_script.log', encoding = 'utf-8', level = logging.DEBUG)

## fieldnames
MOVIE_ID_FIELD = 'movie_id'
ACTOR_ID_FIELD = 'actor_id'
CAST_FIELD = 'cast'

## Build the flattened credit row dictionary
def build_credit_row_dict(movie_id = None, actor = None):
    if movie_id is None or actor is None:
        raise Exception('Movie ID and actor must have a value.')
    actor_id = actor['id']
    logging.debug('Building row for combination actor %d and movie %s' % (actor_id, movie_id))
    credit_dict = {}
    credit_dict[MOVIE_ID_FIELD] = movie_id
    credit_dict[ACTOR_ID_FIELD] = actor_id
    return credit_dict

## Press the green button in the gutter to run the script.
if __name__ == '__main__':
    logging.info('Starting credit file flattening.')
    fieldnames = [MOVIE_ID_FIELD, ACTOR_ID_FIELD]
    with open('./output/credit.csv', 'w', newline = '') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        writer.writeheader()
        # iterate over the credits dataset
        with open('./input/tmdb_5000_credits.csv', newline = '') as csvfile:
            for row in csv.DictReader(csvfile):
                movie_id = row[MOVIE_ID_FIELD]
                logging.debug('Flattening credit for movie with id %s' % movie_id)
                # iterate over the actors
                for actor in parse_actor(row[CAST_FIELD]):
                    # create the row dictionary and write it to the file
                    credit_dict = build_credit_row_dict(movie_id = movie_id, actor = actor)
                    writer.writerow(credit_dict)
    logging.info('Finished flattening credits file.')
