# This command creates a new PopIt instance based on the Person,
# Position and Organisation models in Pombola.

from __future__ import absolute_import
import json
from optparse import make_option
from os.path import exists, isdir, join
import six.moves.urllib.parse

from pombola.core.popolo import get_popolo_data

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = 'OUTPUT-DIRECTORY POMBOLA-URL'
    help = 'Export all people, organisations and memberships to Popolo JSON and mongoexport format'

    option_list = BaseCommand.option_list + (
            make_option(
                "--pombola",
                dest="pombola",
                action="store_true",
                help="Make a single file with inline memberships"
            ),
    )

    def handle(self, *args, **options):

        if len(args) != 2:
            raise CommandError("You must provide a filename prefix and the Pombola instance URL")

        output_directory, pombola_url = args
        if not (exists(output_directory) and isdir(output_directory)):
            message = "'{0}' was not a directory"
            raise CommandError(message.format(output_directory))
        parsed_url = six.moves.urllib.parse.urlparse(pombola_url)
        if not parsed_url.netloc:
            message = "The Pombola URL must begin http:// or https://"
            raise CommandError(message)

        primary_id_scheme = '.'.join(reversed(parsed_url.netloc.split('.')))

        if options['pombola']:
            for inline_memberships, leafname in (
                    (True, 'pombola.json'),
                    (False, 'pombola-no-inline-memberships.json'),
            ):
                popolo_data = get_popolo_data(
                    primary_id_scheme,
                    pombola_url,
                    inline_memberships=inline_memberships
                )
                output_filename = join(output_directory, leafname)
                with open(output_filename, 'w') as f:
                    json.dump(popolo_data, f, indent=4, sort_keys=True)
        else:
            popolo_data = get_popolo_data(
                primary_id_scheme,
                pombola_url,
                inline_memberships=False
            )
            for collection, data in popolo_data.items():
                for mongoexport_format in (True, False):
                    if mongoexport_format:
                        output_basename = 'mongo-' + collection + '.dump'
                    else:
                        output_basename = collection + ".json"
                    output_filename = join(output_directory, output_basename)
                    with open(output_filename, 'w') as f:
                        if mongoexport_format:
                            for item in data:
                                item['_id'] = item['id']
                                json.dump(item, f, sort_keys=True)
                                f.write("\n")
                        else:
                            json.dump(data, f, indent=4, sort_keys=True)
