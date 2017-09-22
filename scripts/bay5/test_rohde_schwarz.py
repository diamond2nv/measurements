
import logging
from measurements.instruments import RS_SMBV100A as rf
reload(rf)

rf_source = rf.RS_SMBV100A(address = '192.168.1.57', log_level = logging.WARNING)


