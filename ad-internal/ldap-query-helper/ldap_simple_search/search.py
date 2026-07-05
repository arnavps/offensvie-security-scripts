import logging
import ldap

logger = logging.getLogger(__name__)

class LDAPSearch(object):
    _conn = None

    def __init__(self,
                 uri,
                 bind_dn,
                 password):

        ldap.set_option(ldap.OPT_REFERRALS, 0)
        self.uri = uri
        self.bind_dn = bind_dn
        self.password = password

    def __del__(self):
        self._unbind()

    def conn(self):
        if self._conn is None:
            self._conn = self._bind()
        return self._conn

    def _bind(self):
        l = ldap.initialize(self.uri)
        l.protocol_version = ldap.VERSION3
        try:
            l.simple_bind_s(self.bind_dn, self.password)
        except ldap.INVALID_CREDENTIALS:
            logger.error('Your username or password is incorrect.')
            raise
        except ldap.LDAPError as e:
            if type(e.message) == dict and 'desc' in e.message:
                logger.error(e.message['desc'])
            if type(e.message) == dict and 'desc' in e.message:
                logger.error(e)
            else:
                logger.error(e)
            raise
        return l

    def _unbind(self):
        if self._conn is not None:
            self.conn().unbind_s()
            self._conn = None

    def search(self, base_dn, searchFilter, searchAttribute=None, callback=None):
        try:
            ldap_result_id = self.conn().search(
                                        base_dn,
                                        ldap.SCOPE_SUBTREE,
                                        searchFilter,
                                        searchAttribute)
            result_set = []
            while 1:
                result_type, result_data = self.conn().result(ldap_result_id, 0)
                if (result_data == []):
                    break
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set += self._handleResults(result_data, callback)
            self._unbind()
            return result_set
        except ldap.LDAPError as e:
            self._unbind()
            logger.error(e)

    def _handleResults(self, data, callback):
        results = []

        for dn, record in data:
            if dn is not None:
                if callback is not None:
                    results = callback(dn, record)
                else:
                    results.append((dn, record))

        return results
