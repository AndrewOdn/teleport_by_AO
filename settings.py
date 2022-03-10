# -*- coding: utf-8 -*-
# telegram
USER_NAME = 'Channellistener'
API_ID = '13834047'
API_HASH = 'ae18a6c3dfd09897f42a38c5036ac1af'

# parser
EXTRA_WORDS = [
    'silver', 'bronze', 'black',
    'blue', 'pink'
]
EXTRA_WORDS = [s.lower() for s in EXTRA_WORDS]

# debug
DEBUG = False

# handler
# recommendation for developer: use chat int id's
HANDLED_CHATS = [-1001517694982]

# etc
DATE_WITH_TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
DATE_FORMAT = '%Y-%m-%d'
