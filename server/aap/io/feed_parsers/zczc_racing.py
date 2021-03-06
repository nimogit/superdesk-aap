#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license*.

from .zczc import ZCZCFeedParser
from superdesk.metadata.item import CONTENT_TYPE, FORMAT, FORMATS
from superdesk.io import register_feeding_service_error
from superdesk.errors import AlreadyExistsError
from superdesk.io import register_feed_parser
from aap.errors import AAPParserError
from superdesk.io.iptc import subject_codes
from superdesk.logging import logger
import superdesk
from apps.publish.content.common import ITEM_PUBLISH


class ZCZCRacingParser(ZCZCFeedParser):
    NAME = 'Racing_zczc'

    def set_item_defaults(self, item, provider):
        super().set_item_defaults(item, provider)
        item[FORMAT] = FORMATS.PRESERVED

    def post_process_item(self, item, provider):
        try:
            # Pagemasters sourced content is Greyhound or Trot related, maybe AFL otherwise financial
            # It is from the Racing system
            item[self.ITEM_ANPA_CATEGORY] = [{'qcode': 'r'}]
            item[self.ITEM_SUBJECT] = [{'qcode': '15030001', 'name': subject_codes['15030001']}]
            lines = item['body_html'].split('\n')
            if lines[2] and lines[2].find(':SPORT -') != -1:
                item[self.ITEM_HEADLINE] = lines[2][9:]
                if lines[1] and lines[1].find(':POTTED :') != -1:
                    item[self.ITEM_SLUGLINE] = lines[1][9:]
            elif lines[1] and lines[1].find('RACING : ') != -1:
                item[self.ITEM_HEADLINE] = lines[1][8:]
                item[self.ITEM_SLUGLINE] = lines[1][8:]
            elif lines[0] and lines[0].find('YY FORM') != -1:
                item[self.ITEM_HEADLINE] = lines[1]
                item[self.ITEM_SLUGLINE] = lines[1]
            elif lines[1] and lines[1].find(':POTTED :') != -1:
                item[self.ITEM_HEADLINE] = lines[1][9:]
                item[self.ITEM_SLUGLINE] = lines[1][9:]
            else:
                for line_num in range(3, min(len(lines), 6)):
                    if lines[line_num] != '':
                        item[self.ITEM_HEADLINE] = lines[line_num].strip()
                        item[self.ITEM_SLUGLINE] = lines[line_num].strip()
                        break
            # Truncate the slugline and headline to the lengths defined on the validators if required if required
            lookup = {'act': ITEM_PUBLISH, 'type': CONTENT_TYPE.TEXT}
            validators = superdesk.get_resource_service('validators').get(req=None, lookup=lookup)
            if validators.count():
                max_slugline_len = validators[0]['schema']['slugline']['maxlength']
                max_headline_len = validators[0]['schema']['headline']['maxlength']
                if self.ITEM_SLUGLINE in item and len(item[self.ITEM_SLUGLINE]) > max_slugline_len:
                    # the overflow of the slugline is dumped in the take key
                    item[self.ITEM_TAKE_KEY] = item.get(self.ITEM_SLUGLINE)[max_slugline_len:]
                    item[self.ITEM_SLUGLINE] = item[self.ITEM_SLUGLINE][:max_slugline_len]
                if self.ITEM_HEADLINE in item:
                    item[self.ITEM_HEADLINE] = item[self.ITEM_HEADLINE][:max_headline_len] \
                        if len(item[self.ITEM_HEADLINE]) > max_headline_len else item[self.ITEM_HEADLINE]

            return item

        except Exception as ex:
            logger.exception(ex)


try:
    register_feed_parser(ZCZCRacingParser.NAME, ZCZCRacingParser())
except AlreadyExistsError as ex:
    pass
register_feeding_service_error('file', AAPParserError.ZCZCParserError().get_error_description())
