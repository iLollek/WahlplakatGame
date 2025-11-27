from DatabaseService import DatabaseService
from NetworkService import NetworkService

env = DatabaseService.get_sillyorm_environment(use_postgres=False)

NetService = NetworkService()
NetService.start()