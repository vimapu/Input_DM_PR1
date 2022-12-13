import pandas

from common import *
import logging
import os
import requests
import time

## logging config
logging.basicConfig(filename = './log/download_actors.log', encoding = 'utf-8', level = logging.DEBUG)

## urls
API_KEY = os.getenv('API_KEY')
ACTOR_URL = 'https://api.themoviedb.org/3/person/%d'
OUTPUT_FILE = './output/actors.csv'

## fieldnames
ID_FIELD = 'id'
NAME_FIELD = 'name'
GENDER_FIELD = 'gender'
BIRTHDAY_FIELD = 'birthday'
POPULARITY_FIELD = 'popularity'
PLACE_OF_BIRTH_FIELD = 'place_of_birth'

## download actor by id and returns json
def download_actor_by_id(id = None):
    if id is None:
        raise Exception('Actor ID must have value!')
    logging.debug('Downloading info for actor with ID %s' % id)
    ## time.sleep(200/1000)
    response = requests.get(ACTOR_URL % id, {'api_key': API_KEY, 'language': 'en-US'})
    if response.status_code != 200:
        logging.warning('Could not find actor with id %s', id)
        return None
    return response.json()

## extract the fields into the dictionary that will be used for the csv row fields
def build_actor_file_row_dict(actor = None):
    actor_dict = {}
    if actor is None:
        logging.warning('Actor object came empty')
        return actor_dict
    actor_dict[ID_FIELD] = actor[ID_FIELD]
    actor_dict[NAME_FIELD] = actor[NAME_FIELD]
    actor_dict[GENDER_FIELD] = actor[GENDER_FIELD]
    actor_dict[BIRTHDAY_FIELD] = actor[BIRTHDAY_FIELD]
    actor_dict[POPULARITY_FIELD] = actor[POPULARITY_FIELD]
    actor_dict[PLACE_OF_BIRTH_FIELD] = actor[PLACE_OF_BIRTH_FIELD]
    return actor_dict

def obtain_already_parsed_actors():
    actors = []
    if os.path.exists(OUTPUT_FILE):
        actors_df = pandas.read_csv(OUTPUT_FILE)
        ids = actors_df[ID_FIELD]
        if ids is not None and len(ids) >= 0:
            actors.extend(pandas.unique(ids))
    return actors

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    logging.info('Starting to download actors.')
    actor_ids = obtain_already_parsed_actors()
    fieldnames = [ID_FIELD, NAME_FIELD, GENDER_FIELD, BIRTHDAY_FIELD, POPULARITY_FIELD, PLACE_OF_BIRTH_FIELD]
    new_write = not os.path.exists(OUTPUT_FILE)
    with open('./output/actors.csv', 'a', newline = '', encoding = 'utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        if new_write:
            writer.writeheader()
        # iterate over the credits dataset
        with open('./input/tmdb_5000_credits.csv', newline = '') as csvfile:
            for row in csv.DictReader(csvfile):
                # iterate over the actor ids per movie credits
                for id in parse_actor_ids(row['cast']):
                    if id not in actor_ids:
                        actor_ids.append(id)
                        # retrieve the actor from TMDB API
                        actor = download_actor_by_id(id = id)
                        # build and write new actor row
                        try:
                            actor_dict = build_actor_file_row_dict(actor = actor)
                            if not actor_dict or ID_FIELD not in actor_dict:
                                actor_dict = {}
                                actor_dict[ID_FIELD] = id
                            writer.writerow(actor_dict)
                        except:
                            logging.warning('Actor with id %d could not be downloaded for movie with id %s.', id,
                                            row['movie_id'])

    logging.info('Finished downloading actors.')
