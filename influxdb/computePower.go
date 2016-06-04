package main

import (
	"encoding/json"
	"os"
	"time"
    "fmt"
    "github.com/influxdata/influxdb/client/v2"
)

const (
    databaseName = "fh2"
)

func main() {

	if len(os.Args[1:]) != 1 {
		fmt.Println("Must pass influxdb server URL on command line")
		os.Exit(1)
	}
	
	databaseUrl := os.Args[1]
	
	// Make client
	c, err := client.NewHTTPClient(client.HTTPConfig{
		Addr: databaseUrl,
	})
	if err != nil {
		fmt.Println("Error creating InfluxDB Client: ", err.Error())
	}
	defer c.Close()

	q := client.NewQuery("SELECT v FROM senml WHERE u = 'J' AND time > now() - 30m GROUP BY n",
		databaseName, "ns")
	if response, err := c.Query(q); err == nil && response.Error() == nil {
		
		fmt.Println( "num results = " , len( response.Results ) )
		//fmt.Println( response.Results[0] )
		fmt.Println( "num series = " , len( response.Results[0].Series ) )

		batch, err := client.NewBatchPoints(client.BatchPointsConfig{
			Database:  databaseName,
			Precision: "ns",
		})
		if err != nil {
			fmt.Println("problem allocating batch points: ", err.Error() )	
		}
		
		for j, series := range response.Results[0].Series {

			//fmt.Println( series )

			fmt.Println( "DOING " , series.Tags["n"] )
			
			var pt int64 = 0
			var pv float64 = 0.0 
			
			for i, point := range series.Values {
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
						fmt.Println( j, i, "watts", dv / dt  )

						tags := map[string]string{
							"u": "W",
							"n": series.Tags["n"],
						}
						
						fields := map[string]interface{}{
							"v": dv / dt ,
						}

						timeRec := time.Unix( t / 1000000000, t%1000000000)
						
						pt, err := client.NewPoint(
							"synth",
							tags,
							fields,
							timeRec,
						)
						if err != nil {
							println("Error:", err.Error())
							continue
						}
						batch.AddPoint(pt)
						
					}
				}

				pt = t
				pv = v
			}
		}

		err = c.Write(batch)
		if err != nil {
			fmt.Println("Error writing power points to influxdb: ", err.Error())
		}

	}
}
