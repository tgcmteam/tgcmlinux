import tgcm

if tgcm.country_support != "uk" :
	from SessionInfo import SessionInfo
else:
	from SessionInfoUK import SessionInfo 	
