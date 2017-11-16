import logging

from gcm import GCM

from config import Config
from device import Device
from user import User

class gcm(object):
    @staticmethod
    def send(data, reg_ids=[], dev_ids=[], user_ids=[]):
        logging.getLogger().debug('data=' + str(data));
        logging.getLogger().debug('reg_ids (' + str(len(reg_ids)) + ')=' + str(reg_ids))
        logging.getLogger().debug('dev_ids (' + str(len(dev_ids)) + ')=' + str(dev_ids))
        logging.getLogger().debug('user_ids (' + str(len(user_ids)) + ')=' + str(user_ids))

        # Add user_ids.
        user_keys = []
        for user_id in user_ids:
            user_keys.extend(Device.query(Device.user_id == user_id, ancestor=Device.ROOT_KEY).fetch(keys_only=True))
        logging.getLogger().debug('user_keys (' + str(len(user_keys)) + ')=' + str(user_keys))

        dev_ids.extend([user_key.get().dev_id for user_key in user_keys])
        logging.getLogger().debug('dev_ids (' + str(len(dev_ids)) + ')=' + str(dev_ids))

        # Add dev_ids.
        device_keys = []
        for dev_id in dev_ids:
            device_keys.extend(Device.query(Device.dev_id == dev_id, ancestor=Device.ROOT_KEY).fetch(keys_only=True))
        logging.getLogger().debug('device_keys (' + str(len(device_keys)) + ')=' + str(device_keys))

        reg_ids.extend([device_key.get().reg_id for device_key in device_keys])
        logging.getLogger().debug('reg_ids (' + str(len(reg_ids)) + ')=' + str(reg_ids))

        if not reg_ids:
            logging.getLogger().error('no reg_ids')
            return

        # Get API key.
        config = Config.get_master_db()
        if not config or not config.gcm_api_key:
            logging.getLogger().error('no GCM API key')
            return

        # Send message.
        try:
            gcm = GCM(config.gcm_api_key)
            response = gcm.json_request(
                registration_ids=reg_ids, data=data,
                collapse_key='uptoyou', delay_while_idle=True, time_to_live=3600
            )
        except Exception as e:
                logging.getLogger().error('exception=' + str(e))
                return

        # Handling errors
        if 'errors' in response:
            for error, reg_ids in response['errors'].items():
                logging.getLogger().error('error ' + error)
                # Check for errors and act accordingly
                if error is 'NotRegistered':
                    # Remove reg_ids from database
                    for reg_id in reg_ids:
                        logging.getLogger().debug('remove ' + reg_id)

        if 'canonical' in response:
            for reg_id, canonical_id in response['canonical'].items():
                # Replace reg_id with canonical_id in your database
                logging.getLogger().debug('replace ' + reg_id + ' with ' + canonical_id)
