from DatabaseService import DatabaseService

env = DatabaseService.get_sillyorm_environment(use_postgres=False)

wahlspruch = DatabaseService.get_random_wahlspruch(env)

parteien = DatabaseService.get_alle_parteien(env)
print(parteien)