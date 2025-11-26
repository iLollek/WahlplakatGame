from DatabaseService import DatabaseService

env = DatabaseService.get_sillyorm_environment(use_postgres=True)

wahlspruch = DatabaseService.get_random_wahlspruch(env)

print(wahlspruch)