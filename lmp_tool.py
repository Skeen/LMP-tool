import json
import struct

import click
from more_itertools import chunked, flatten


def determine_version(lmp_bytes):
    return lmp_bytes[0]


def extract_header(lmp_bytes):
    shared_prefix = [
        'game_version',
        'skill_level',
        'episode',
        'map',
    ]
    post_102 = [
        'multiplayer_mode',
        'flag_respawn',
        'flag_fast',
        'flag_nomonsters',
        'player_pov',
    ]
    shared_postfix = [
        'player1_present',
        'player2_present',
        'player3_present',
        'player4_present'
    ]
    old_header = shared_prefix + shared_postfix
    new_header = shared_prefix + post_102 + shared_postfix

    game_version = determine_version(lmp_bytes)

    header_labels = new_header
    # Different header before version 1.2
    if game_version <= 102:
        header_labels = old_header

    num_bytes_header = len(header_labels)
    header = dict(zip(header_labels, lmp_bytes))
    remaining_bytes = lmp_bytes[num_bytes_header:]

    return header, remaining_bytes

tic_format = 'bbbB'

def to_dict(lmp_bytes):
    if lmp_bytes[-1] != 0x80:
        print("Missing 0x80 at the end of lump!")
    lmp_bytes = lmp_bytes[:-1]
    header, tic_bytes = extract_header(lmp_bytes)
    if len(tic_bytes) % 4 != 0:
        print("Movement bytes are invalid (not mod 4)!")

    tic_struct = struct.Struct(tic_format)
    tic_header = ["movement", "strafing", "turning", "action"]

    def parse_tic(tic_bytes):
        formatted_bytes = tic_struct.unpack(bytes(tic_bytes))
        #return dict(zip(tic_header, formatted_bytes))
        return list(formatted_bytes)

    tics = map(parse_tic, chunked(tic_bytes, 4))
    return {
        'header': header,
        'tics': list(tics)
    }


def to_lmp(dic):
    def to_bytes(tic):
        # return tic_struct.pack(*tic.values())
        return tic_struct.pack(*tic)

    header_bytes = bytes(dic['header'].values())
    tic_struct = struct.Struct(tic_format)
    tic_bytes = bytes(flatten(map(to_bytes, dic['tics'])))
    return header_bytes + tic_bytes + bytes([0x80])


@click.group()
def cli():
    pass


@cli.command()
@click.argument('input_file', type=click.File('rb'))
@click.argument('output_file', type=click.File('w'))
def lmp_to_json(input_file, output_file):
    lmp_bytes = input_file.read()
    json.dump(to_dict(lmp_bytes), output_file)


@cli.command()
@click.argument('input_file', type=click.File('r'))
@click.argument('output_file', type=click.File('wb'))
def json_to_lmp(input_file, output_file):
    dic = json.load(input_file)
    output_file.write(to_lmp(dic))


if __name__ == '__main__':
    cli()
