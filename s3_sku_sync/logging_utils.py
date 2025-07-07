import logging
import sys
import json

class JsonLineFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'time': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'msg': record.getMessage(),
            'name': record.name,
        }
        return json.dumps(log_record)

def setup_logging(level: str = 'INFO'):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLineFormatter())
    logging.basicConfig(level=level, handlers=[handler])
