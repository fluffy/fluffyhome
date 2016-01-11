package main

import (
    "fmt"
	"encoding/json"
    "github.com/influxdb/influxdb/client/v2"
)

const (
    databaseName = "fh2"
	databaseUrl =  "http://10.1.3.254:8086"
)

func main() {

	// Make client
	c, err := client.NewHTTPClient(client.HTTPConfig{
		Addr: databaseUrl,
	})
	if err != nil {
		fmt.Println("Error creating InfluxDB Client: ", err.Error())
	}
	defer c.Close()
	
	q := client.NewQuery("SELECT v FROM senml WHERE n = 'ECM1240-42340-ch1' AND time > now() - 2m",
		databaseName, "ns")
	if response, err := c.Query(q); err == nil && response.Error() == nil {

		var pt int64 = 0
		var pv float64 = 0.0 
		
		for i, point := range response.Results[0].Series[0].Values {
			var t int64 
			var v float64
			
			switch  x := point[0].(type) {
			case json.Number:
				t, err = x.Int64()
				if err != nil {
					fmt.Println("problem converting time to int ")
				}
			}

			switch x := point[1].(type) {
			case json.Number:
				v, err = x.Float64()
				if err != nil {
					fmt.Println("problem converting value to float ")
				}
			}
			
			//fmt.Println( "raw val=", i, t ,v )
		
			if ( i > 0 ) {
				dt := float64( t - pt ) / 1e9 
				dv := v - pv
				//fmt.Println( "delta", dt , dv )
				if (dt > 0.0) && ( dv >= 0.0 ) {
					fmt.Println( "watts", dv / dt  )
				}
			}

			pt = t
			pv = v
		}
		
	}
}
