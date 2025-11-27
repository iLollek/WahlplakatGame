
from NetworkClient import NetworkClient

NetClient = NetworkClient()
NetClient.connect()

NetClient.register_account("iLollek", "MySecurePassword")
reply = NetClient.login("iLollek", "MySecurePassword")
print(reply)