package main

// from https://github.com/Ahmad-Magdy/CSV-To-JSON-Converter

import (
	"bytes"
	"encoding/csv"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/araddon/dateparse"
)

func main() {
	// argsWithProg := os.Args
	argsWithoutProg := os.Args[1:]

	if len(argsWithoutProg) == 0 {
		fmt.Println("Usage: csv2ins datafile.csv")
		os.Exit(1)
	}
	path := flag.String("path", argsWithoutProg[0], "Path of the file")
	// path := argsWithoutProg[0]
	flag.Parse()
	fileBytes, fileNPath := ReadCSV2(path)
	SaveFile(fileBytes, fileNPath)
	fmt.Println(strings.Repeat("=", 10), "Done", strings.Repeat("=", 10))
}

// ReadCSV to read the content of CSV File
func ReadCSV2(path *string) (string, string) {
	csvFile, err := os.Open(*path)

	if err != nil {
		log.Fatal("The file is not found || wrong root")
	}
	defer csvFile.Close()

	reader := csv.NewReader(csvFile)
	content, _ := reader.ReadAll()

	if len(content) < 1 {
		log.Fatal("Something wrong, the file maybe empty or length of the lines are not the same")
	}

	headersArr := make([]string, 0)
	for _, headE := range content[0] {
		headersArr = append(headersArr, headE)
	}

	//Remove the header row
	content = content[1:]

	var buffer bytes.Buffer
	// var ct string
	fileNm := filepath.Base(*path)
	fmt.Println("Filename from path : %s from %s", *path, fileNm)
	justFileNm := strings.Replace(fileNm, ".csv", "", -1)
	buffer.WriteString("CREATE TABLE ")
	buffer.WriteString(justFileNm)

	var firstField bool
	firstField = true
	for _, d := range content {
		buffer.WriteString("(")
		for j, y := range d {
			if firstField {
				buffer.WriteString(`"` + headersArr[j] + `" `)
				firstField = false
			} else {
				buffer.WriteString(`, "` + headersArr[j] + `" `)
			}
			fmt.Println("Reading line : ", y)

			_, fErr := strconv.ParseFloat(y, 64)
			_, bErr := strconv.ParseBool(y)
			_, iErr := strconv.ParseInt(y, 0, 32)
			_, dtUsShortYearErr := time.Parse("MM-dd-YY", y)
			_, dtUsLongYearErr := time.Parse("MM-dd-YYYY", y)
			_, dtISOErr := time.Parse("YYYY-MM-DD", y)
			_, dtParseErr := dateparse.ParseAny(y)

			fmt.Println("date parse error : ", dtParseErr)
			if fErr == nil {
				buffer.WriteString(" double")
			} else if bErr == nil {
				buffer.WriteString(" bool")
			} else if iErr == nil {
				buffer.WriteString(" int")
			} else if dtUsShortYearErr == nil {
				buffer.WriteString(" date")
			} else if dtUsLongYearErr == nil {
				buffer.WriteString(" date")
			} else if dtISOErr == nil {
				buffer.WriteString(" date")
			} else if dtParseErr == nil {
				buffer.WriteString(" date")
			} else {
				buffer.WriteString(" varchar(0)")
			}
		}
		break
	}

	buffer.WriteString(`);`)
	newFileName := filepath.Base(*path)
	newFileName = newFileName[0:len(newFileName)-len(filepath.Ext(newFileName))] + "out" + ".sql"
	r := filepath.Dir(*path)
	return buffer.String(), filepath.Join(r, newFileName)
}

func checkError(message string, err error) {
	if err != nil {
		log.Fatal(message, err)
	}
}

// SaveFile Will Save the file, magic right?
func SaveFile(myFileContents string, path string) {

	// csv =
	// writer := csv.NewWriter(&buf)
	// writer.Flush()

	file, err := os.Create(path)
	checkError("Cannot create file", err)
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// for _, value := range myFileContents {
	// 	err := writer.Write(value)
	// 	checkError("Cannot write to file", err)
	// }
	fmt.Println(myFileContents)
	fileBytes := []byte(myFileContents)
	if err := ioutil.WriteFile(path, fileBytes, os.FileMode(0644)); err != nil {
		panic(err)
	}
}
