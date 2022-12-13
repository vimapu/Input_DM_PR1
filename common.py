import csv
import json

# opens the credit dataset and returns an iterator per line.
def get_file_row_generator(file: str = None, newline = ''):
    with open(file, newline = newline) as csvfile:
        return csv.DictReader(csvfile)

# parses an actors for movie represented as in the credits dataset
def parse_actor_ids(actors_cell = None):
    for actor in json.loads(actors_cell):
        yield actor['id']

# parses an actor
def parse_actor(actors_cell = None):
    for actor in json.loads(actors_cell):
        yield actor
