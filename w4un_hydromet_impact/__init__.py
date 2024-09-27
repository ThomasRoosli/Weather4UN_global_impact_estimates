""" Initializations """
import logging
import os


from w4un_hydromet_impact.config.service_settings import ServiceSettings

CONFIG = ServiceSettings()

# Log the deployment environment we are in
logger = logging.getLogger(__name__)
logger.info('Configured site is %s', CONFIG.site)


# disable TQDM progress bar logs (used by CLIMADA) because we are a background application
os.environ['TQDM_DISABLE'] = 'true'
