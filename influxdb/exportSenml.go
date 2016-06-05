package main

/*
exports senml data from influxdb to JSON file creating one file per day

Dump with something like
./exportSenml http://10.1.3.254:8086

Can load back into influxdb with something like
./senmlCat -ijsonl -topic senml -linp -post "http://10.1.3.254:8086/write?db=junk3" dump2016-06-02-2000.jsonl


*/

// TODO deal with sum and update time
// TODO deal with non float values vs,vb,vd

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/cisco/senml"
	"github.com/influxdata/influxdb/client/v2"
	"io/ioutil"
	"math"
	"os"
	"runtime/pprof"
	"strconv"
	"time"
)

const (
	databaseName = "fh2"
)

func main() {
	var startDate string
	var databaseUrl string
	var numDays int
	var numHours int

	flag.IntVar(&numHours, "step", 1, "number of hours in each dump")
	flag.IntVar(&numDays, "days", 2, "number of days to dump")
	flag.StringVar(&startDate, "from", "", "date to start dump from ex: 2016-07-08")
	flag.StringVar(&databaseUrl, "db", "", "URL to indexdb datgabase ex: http://10.1.3.254:8086)")
	flag.Parse()

	if false {
		f, err := os.Create("exportSenml.prof")
		if err != nil {
			fmt.Println("error opening profile file", err)
			os.Exit(1)
		}
		pprof.StartCPUProfile(f)
		defer pprof.StopCPUProfile()
	}

	if len(startDate) > 0 {
		fmt.Println("Start date is", startDate)
		t, err := time.Parse("2006-01-02", startDate)
		if err != nil {
			fmt.Println("Could not parse time", startDate, err)
			os.Exit(1)
		}
		d := time.Since(t)
		numDays = int(math.Floor(d.Hours() / 24.0))
	}
	if numDays < 0 {
		fmt.Println("Can not dump data in the fture", numDays, "days")
		os.Exit(1)
	}

	if len(databaseUrl) <= 0 {
		fmt.Println("Must pass influxdb server URL on command line (example http://10.1.3.254:8086)")
		os.Exit(1)
	}

	step := time.Duration(time.Hour) * time.Duration(numHours)

	fmt.Println("Dumping", numDays, "days")

	for day := -numDays; day <= 0; day++ {
		for h := time.Duration(0); h < time.Duration(24*time.Hour); h = h + step {

			start := time.Now().Truncate(24*time.Hour).AddDate(0, 0, day).Add(h)
			end := start.Add(step)

			fmt.Println("Dumping ", start.Format("2006-01-02-1504"), "  (day of year=", start.YearDay(), ")")

			dumpRange(databaseUrl, start, end, "senml", "dump_"+start.Format("2006-01-02-1504")+"_senml"+".jsonl")
			dumpRange(databaseUrl, start, end, "synth", "dump_"+start.Format("2006-01-02-1504")+"_synth"+".jsonl")
		}
	}
}

func dumpRange(databaseUrl string, start time.Time, end time.Time, series string, fileName string) error {

	// Make client
	c, err := client.NewHTTPClient(client.HTTPConfig{
		Addr: databaseUrl,
	})
	if err != nil {
		fmt.Println("Error creating InfluxDB Client: ", err.Error())
	}
	defer c.Close()

	sql := "SELECT time,n,v,u FROM " + series + " WHERE time >= " + strconv.FormatInt(start.UnixNano(), 10) + " AND time < " + strconv.FormatInt(end.UnixNano(), 10)
	//fmt.Println("sql=", sql)
	q := client.NewQuery(sql, databaseName, "ns")
	response, err := c.Query(q)
	if err != nil {
		fmt.Println("Error with querry: ", err.Error())
	}
	if err == nil && response.Error() != nil {
		fmt.Println("Error with querry response ", response.Error())
	}

	var s senml.SenML

	if err == nil && response.Error() == nil {

		//fmt.Println( "num results = " , len( response.Results ) )
		//fmt.Println( response.Results[0] )
		//fmt.Println( "num series = " , len( response.Results[0].Series ) )

		for _, series := range response.Results[0].Series {

			//fmt.Println( series )

			//fmt.Println( "DOING " , series.Tags["n"] )

			for _, point := range series.Values {
				var t float64
				var n string
				var v float64
				var u string

				//fmt.Println( "point = " ,point)

				switch x := point[0].(type) {
				case json.Number:
					ti, err := x.Int64()
					if err != nil {
						fmt.Println("problem converting time to int ")
					}
					t = float64(ti) / 1000000000.0
				default:
					fmt.Println("unknown  type for t ", x)
				}

				switch x := point[1].(type) {
				case string:
					n = string(x)
				default:
					fmt.Println("unknown  type for n ", x)
				}

				switch x := point[2].(type) {
				case json.Number:
					v, err = x.Float64()
					if err != nil {
						fmt.Println("problem converting value to float ")
					}
				default:
					fmt.Println("unknown  type for v ", x)
				}

				switch x := point[3].(type) {
				case string:
					u = string(x)
				default:
					fmt.Println("unknown  type for u ", x)
				}

				//fmt.Println( "raw val=", t,n,v,u )

				r := senml.SenMLRecord{Time: t, Name: n, Value: &v, Unit: u}

				s.Records = append(s.Records, r)

			}
		}

	}

	options := senml.OutputOptions{Topic: "senml"}

	//format := senml.CSV
	format := senml.JSONLINE

	dataOut, err := senml.Encode(s, format, options)
	if err != nil {
		fmt.Println("Error encoding senml", err)
	}

	//fmt.Println("Encode got: " + string(dataOut))

	err = ioutil.WriteFile(fileName, dataOut, 0644)
	if err != nil {
		fmt.Println("Problem writing file", err)
		panic(err)
	}

	return nil
}
