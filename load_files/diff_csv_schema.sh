#!/usr/bin/env bash

# ==================================================================================================================================
# 
# Copyright (c) 2019 ThoughtSpot
# 
# ----------------------------------------------------------------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
# files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#  BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
#  OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ----------------------------------------------------------------------------------------------------------------------------------
# Last Modified: Thursday September 12th 2019 9:09:26 am
# ==================================================================================================================================
declare -r EXIT_OK=0
declare -r EXIT_ERRORS=1
declare -r INPUT_FILE_DETAILS="/tmp/input_file_details.csv"
declare -r TABLE_DETAILS="/tmp/table_details.csv"

#--[function usage()]-----------------------------------------------------------------------------------------
#
#  Shows the usage instructions of this script
#-------------------------------------------------------------------------------------------------------------
function usage() {
  exit_code=$1
  error_msg=$2 

  echo ""
  if [ "${error_msg}" != "" ]; then
    echo "${error_msg}"
    echo ""
  fi
  
  echo "usage: ${0} [-i|--input] INPUT_FILE |[-t|--table] TABLE_NAME"
  echo
  echo "  where "
  echo "  -i|--input INPUT_FILE is the name of input file to compare to the table."
  echo "  -t|--table TABLE_NAME is the name of the table in the database (including database name and schema name)."
  echo ""
  exit ${exit_code}
}

#--[function get_input_file_details()]------------------------------------------------------------------------
#
#  Gets the details of the csv file and export it to csv format and only keep column name and data type
#-------------------------------------------------------------------------------------------------------------
function get_input_file_details() {
  input_file=$1
  max_lines=$2

  # Remove the target file if it exists
  rm -f "${INPUT_FILE_DETAILS}"

  # Get the details via csvstat and cut out the column name and type
  head -${max_lines} "${input_file}" | csvstat --csv 2>/dev/null | csvcut -c column_name,type > "${INPUT_FILE_DETAILS}" 2>/dev/null
}

#--[function get_table_details()]-----------------------------------------------------------------------------
#
#  Gets the details of the table and extract column name and data type and write it to a csv file
#-------------------------------------------------------------------------------------------------------------
function get_table_details() {
  table_name=$1

  # Remove the target file if it exists
  rm -f "${TABLE_DETAILS}"

  # Execute a show table command in TQL and extract the column names and data types
  echo "show table ${table_name};" | tql 2>/dev/null | awk '
    BEGIN {
      FS="|"
      print "column_name,type"
    } 
    {
      if ($5=="datetime") {
        $3=$5
      }
      gsub(/[ \t]+$/, "", $1)
      gsub(/[ \t]+$/, "", $3)
      print $1","$3
    }' > "${TABLE_DETAILS}" 

}

#--[function compare()]---------------------------------------------------------------------------------------
#
#  Compare the file details to the table details by outer joining them and highlight potential issues
#  or items to review
#-------------------------------------------------------------------------------------------------------------
function compare() {
  input_file=$1
  table_name=$2

  echo
  echo Comparison results
  echo
  # Outer join the two output files on column name
  csvjoin --outer -c column_name "${INPUT_FILE_DETAILS}" "${TABLE_DETAILS}" 2>/dev/null | 
    awk -v input_file="${input_file}" -v table_name="${table_name}" -v h1="`printf '=%.0s' $(seq 1 ${#input_file})`" -v h2="`printf '=%.0s' $(seq 1 ${#table_name})`"   '
      BEGIN {
        # Set delimited to comma
        FS=","
        # Write the table header
        print h1",==========,"h2",==========,=========="
        print input_file",,"table_name",,status"
        print h1",==========,"h2",==========,=========="
      } 
      {
        # For all data lines:
        if(NR>1) {
          $5="REVIEW"
          # If the source type is identified as text we will accept a target type of varchar or date time
          if ($2=="Text") {
            if ($4=="varchar" || $4="date_time") {
              $5="OK"
            }
          }
          # If the source type is identified as numeric, we will accept doubles, floats, ints and bigints
          if ($2=="Number") {
            if ($4=="double" || $4=="float" || $4=="int32" || $4=="int64") {
              $5="OK"
            }
          }
          # Check if columns are missing on either end
          if ($1=="") {
            $1="<missing>"
            $2=""
            $5="ISSUE"
          }
          if ($3=="") {
            $3="<missing>"
            $4=""
            $5="ISSUE"
          }
          # Write out the (adjusted) elements
          print $1","$2","$3","$4","$5
        }
      }
      END {
        # Close the table
        print h1",==========,"h2",==========,=========="
      }
      ' | column -s ',' -t -o '|'
  echo

  # Remove temporary files
  rm -f "${TABLE_DETAILS}"
  rm -f "${INPUT_FILE_DETAILS}"

}

#--------------------------------------------------------------------------------------------------------------
# Parse the arguments
#--------------------------------------------------------------------------------------------------------------
error_msg=
max_lines=-1
while [[ $# > 0 ]]; do
  case "$1" in
    -i|--input)     input_file=$2
                    if [[ ! -f "${input_file}" ]]; then
                      usage $EXIT_ERRORS "Input file ${input_file} does not exist. Aborting"
                    fi
                    shift 2
                    ;;
    -t|--table)     table_name=$2
                    shift 2
                    ;;
    -l|--lines)     max_lines=$2
                    shift 2
                    ;;
    *)              # unknown flag/switch
                    error_msg="Error: Unknown flag/switch: $1"
                    usage ${EXIT_ERRORS} "${error_msg}"
                    shift
                    ;;
  esac
done

echo
echo "Comparing input file ${input_file} to tablename ${table_name}"

if [[ ${max_lines} == -1 ]]; then
  max_lines=`wc -l "${input_file}" | awk '{ print $1 }'`
  echo "Parsing full input file (${max_lines} lines)"
else 
  echo "Parsing just ${max_lines} of the input file"
fi

# Requires csv toolkit (csvstat, csvcut, csvjoin) to be installed
type csvstat >/dev/null 2>&1 || { 
  echo >&2 "This script requires csvstat from the csv toolkit but it's not installed.  Aborting."; 
  exit ${EXIT_ERRORS}; 
}
type csvcut >/dev/null 2>&1 || { 
  echo >&2 "This script requires csvcut from the csv toolkit but it's not installed.  Aborting."; 
  exit ${EXIT_ERRORS}; 
}
type csvjoin >/dev/null 2>&1 || { 
  echo >&2 "This script requires csvjoin from the csv toolkit but it's not installed.  Aborting."; 
  exit ${EXIT_ERRORS}; 
}

# Gather details on the input file
get_input_file_details "${input_file}" ${max_lines}

# Gather inputs on the target table
get_table_details "${table_name}"

# Compare the two and output results table
compare "${input_file}" "${table_name}"