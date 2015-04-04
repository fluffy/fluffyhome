import httplib, urllib
# This can be used a pything trigger script in Indigo to post to fluentd.org agent to send to cloud  

conn = httplib.HTTPConnection("localhost", port=30080, timeout=2)
data = '{ "heat": 1 }'

params = urllib.urlencode( {'json': data} )
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

conn.request("POST", "/td.testdb.junk2" , body= params , headers= headers)
response = conn.getresponse()
rdata = response.read()
conn.close()

if ( response.status == 200 ):
   indigo.server.log("Sent " + data + " to td agent" )
else: 
   indigo.server.log("Error talk to TD agent: " + str(response.status) + " " + rdata )

