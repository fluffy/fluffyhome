# Copyright (c) 2010, Cullen Jennings. All rights reserved.

# Create your views here.
from django.http import HttpResponse
import urllib2
import csv


def view1(request,feed,stream):
    # feed,stream are user input - need to validate to stop cross site scripting
    feed = int(feed) 
    stream = int(stream)
    url = "http://www.pachube.com/feeds/%d/datastreams/%d/archive.csv"%(feed,stream)
    print "New URL is: %s"%url

    request = urllib2.Request( url )
    file = urllib2.urlopen( request )
    
    csvReader = csv.reader( file )

    html = "<html><body> <p>This is view1:</p>"

    for row in csvReader:
        html += "<p>  %s  %s</p>"%(row[0],row[1])

    html += "</body></html>"

    return HttpResponse(html)


def json(request,feed,stream):
    # feed,stream are user input - need to validate to stop cross site scripting
    feed = int(feed) 
    stream = int(stream)
    url = "http://www.pachube.com/feeds/%d/datastreams/%d/archive.csv"%(feed,stream)
    print "New URL is: %s"%url

    request = urllib2.Request( url )
    file = urllib2.urlopen( request )
    
    csvReader = csv.reader( file )

    html = ""
    #html = "<html><body><pre>"
    
    html += "google.visualization.Query.setResponse({version:'0.6',"
    # reqId:'0',status:'ok',sig:'6099996038638149313',
    html += "status:'ok', \n"
    html += "reqId:'0', \n"

    html += "table:{ cols:[ {id:'Time',label:'TimE',type:'datetime'}, {id:'Value',label:'ValuE',type:'number'}], \n"

    html += "  rows:[ \n"
    for row in csvReader:
        try:
            year = int( row[0][0:0+4] )
            month = int( row[0][5:5+2] )
            day = int( row[0][8:8+2] )
            hour = int( row[0][11:11+2] )
            minute = int( row[0][14:14+2] )
            second = int( row[0][17:17+2] )
        
            value = float( row[1] )
            html += "   {c:[  {v:'Date(%d,%d,%d,%d,%d,%d)'},{v:'%f'}  ]}, \n"%(year,month,day,hour,minute,second,value)
        except:
            print "Some error parsing inputs: %s %s"%(row[0], row[1])

    html += "  ] } \n" #close rows, then thable
    html += "} );\n" #close whole object 

    #html += "</pre></body></html>"

    #response = HttpResponse("text/plain")
    response = HttpResponse()
    #response['Content-Disposition'] = 'attachment; filename=somefilename.csv'

    response.write( html );

    return response 


def view3(request,feed,stream):
    html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <title>
      Table View
    </title>
    <script type="text/javascript" src="http://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load('visualization', '1', {packages: ['table']});
    </script>
    <script type="text/javascript">
    var visualization;

    function drawVisualization() {
      // To see the data that this visualization uses, browse to
      // http://spreadsheets.google.com/ccc?key=pCQbetd-CptGXxxQIG7VFIQ  
      var query = new google.visualization.Query(
"""

    # feed,stream are user input - need to validate to stop cross site scripting
    feed = int(feed) 
    stream = int(stream)

    host = request.META["HTTP_HOST"]

    url = "http://%s/pachube/%d/%d/json/"%(host,feed,stream)
    print "New data URL is: %s"%url

    html += " '%s' "%url

    html += """ 
    );
     
      // Send the query with a callback function.
      query.send(handleQueryResponse);
    }
    
    function handleQueryResponse(response) {
      if (response.isError()) {
        alert('Error in query: ' + response.getMessage() + ' ' + response.getDetailedMessage());
        return;
      }
    
      var data = response.getDataTable();
      visualization = new google.visualization.Table(document.getElementById('visualization'));
      visualization.draw(data, null);
    }

    google.setOnLoadCallback(drawVisualization);
    </script>
  </head>
  <body style="font-family: Arial;border: 0 none;">
    <div id="visualization" style="height: 400px; width: 400px;"></div>
  </body>
</html>
    """
    return HttpResponse(html)



def view4(request,feed,stream):
    html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
    <title>
      Table View
    </title>
    <script type="text/javascript" src="http://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load('visualization', '1', {packages: ['annotatedtimeline']});
    </script>
    <script type="text/javascript">
    var visualization;

    function drawVisualization() {
      // To see the data that this visualization uses, browse to
      // http://spreadsheets.google.com/ccc?key=pCQbetd-CptGXxxQIG7VFIQ  
      var query = new google.visualization.Query(
"""

    # feed,stream are user input - need to validate to stop cross site scripting
    feed = int(feed) 
    stream = int(stream)

    host = request.META["HTTP_HOST"]

    url = "http://%s/pachube/%d/%d/json/"%(host,feed,stream)
    print "New data URL is: %s"%url

    html += " '%s' "%url

    html += """ 
    );
     
      // Send the query with a callback function.
      query.send(handleQueryResponse);
    }
    
    function handleQueryResponse(response) {
      if (response.isError()) {
        alert('Error in query: ' + response.getMessage() + ' ' + response.getDetailedMessage());
        return;
      }
    
      var data = response.getDataTable();
      visualization = new google.visualization.AnnotatedTimeLine(document.getElementById('visualization'));
      visualization.draw(data, null);
    }

    google.setOnLoadCallback(drawVisualization);
    </script>
  </head>
  <body style="font-family: Arial;border: 0 none;">
    <div id="visualization" style="height: 400px; width: 400px;"></div>
  </body>
</html>
    """

   
    return HttpResponse(html)
