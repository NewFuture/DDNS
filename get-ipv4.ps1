# Replace Ehternet_UCAS with the <InterfaceAlias> of your target interface.
# 				  ↓
(Get-NetIPAddress -InterfaceAlias Ethernet_UCAS -AddressFamily IPv4).IPAddress
