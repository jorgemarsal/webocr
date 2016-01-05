import schemaless
import torndb


class Db(object):
    def query(self, query):
        """Run a query.

        :param query: string, SQL query
        :return:
        """
        raise NotImplementedError

    def execute(self, query):
        """Run a query.

        :param query: string, SQL query
        :return:
        """
        raise NotImplementedError

    def put(self, obj):
        """Store object in DB"""
        raise NotImplementedError


class SchemalessDb(Db):
    def __init__(self, config):
        super(SchemalessDb, self).__init__()
        self.db = torndb.Connection(
            '{}:{}'.format(config['DB_HOSTNAME'],
                           config['DB_PORT']),
            config['DB_NAME'],
            user=config['DB_USER'],
            password=config['DB_PASSWORD'])
        self.datastore = schemaless.DataStore(
            mysql_shards=['{}:{}'.format(config['DB_HOSTNAME'],
                                         config['DB_PORT'])],
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            database=config['DB_NAME'])
        # declare which indexes are available
        self.url_index = \
            self.datastore.define_index('index_url', ['url'])
        self.service_id_index = \
            self.datastore.define_index('index_service_id', ['service_id'])

    def query(self, query):
        return self.db.query(query)

    def execute(self, query):
        return self.db.execute(query)

    def put(self, obj):
        return self.datastore.put(obj)
