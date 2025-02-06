import * as React from 'react';
import { useState } from 'react';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress'
import { LightTooltip } from './tooltip'
import { formatAMPM } from './utils.js'

// dummy data for before the table is loaded
const dummyData = [
  [1,[1],1,{jobName: "Crop Job", filenames:['test.jpg']},'01/01/1990'],
  [2,[2],1,{jobName: "Crop Job", filenames:['test.jpg']},'01/01/1990'],
  [3,[3],1,{jobName: "Crop Job", filenames:['test.jpg']},'01/01/1990']
];

// converts date returned from psql to a cleaner string
function timeColumn(job) {
  var datetime = job[4]
  // hacky fix to correct the timezone coming from psql
  if (datetime.slice(-3) === 'GMT') {
    datetime = datetime.slice(0, -3) + 'EST'
  }
  const date = new Date(datetime)
  return date.toLocaleDateString() + " " + formatAMPM(date)
}

// converts job status from an int to a readable string
// returns a download link if the job is complete (status=2)
function statusColumn(job) {
  const id = job[0]
  const status = job[2]
  if (status == 0) {
    return 'Sent'
  } else if (status == 1) {
    return 'In Progress'
  } else { // status == 2
    return (
      <a href={"/api/download/"+id}>Complete</a>
    )
  }
}

// populates the tooltip with the filenames associated with the job
function toolTipText(job) {
  return job[3]['filenames'].join("\n")
}

export default function BasicTable() {
  const [rows, setRows] = useState(dummyData)
  const [isLoaded, setIsLoaded] = useState(false)

  // fetches jobs and updates rows
  function updateJobs() {
    fetch('/api/jobs', { method: 'GET' })
      .then(data => data.json())
      .then(json => {
        if (json.jobs.length) {
          setRows(json.jobs)
          if(!isLoaded) {
            setIsLoaded(true)
          }
        }
      })
  }
  
  // initializes the table
  React.useEffect(() => updateJobs(), [])

  // pings for new jobs once a second
  React.useEffect(() => {
    const interval = setInterval(updateJobs, 1000)
    // clears the Interval on unmount
    return () => {
      clearInterval(interval)
    }
  }, [])

  return (
    <div className={isLoaded ? 'maskLoaded' : 'mask'}>
      {!isLoaded && <CircularProgress size="65px" sx={{position: "absolute", top: "43%", left: "43%"}} />}
      <TableContainer sx={{backgroundColor: 'rgb(30,30,30)' }} component={Paper}>
        <Table sx={{ minWidth: 450 }} aria-label="simple table">
          <TableHead>
            <TableRow>
              <TableCell sx={{color: "white", fontWeight: "bold"}}>Name</TableCell>
              <TableCell sx={{color: "white", fontWeight: "bold"}} align="right">Files</TableCell>
              <TableCell sx={{color: "white", fontWeight: "bold"}} align="right">Time</TableCell>
              <TableCell sx={{color: "white", fontWeight: "bold"}} align="right">Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow
                key={""+row[0]}
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                <TableCell sx={{color: "white"}} component="th" scope="row">{row[3]['jobName']}</TableCell>
                <TableCell sx={{color: "white"}} align="right"><LightTooltip placement="right" title={<div style={{ whiteSpace: 'pre-line' }}>{toolTipText(row)}</div>}><div>{row[1].length}</div></LightTooltip></TableCell>
                <TableCell sx={{color: "white"}} align="right">{timeColumn(row)}</TableCell>
                <TableCell sx={{color: "white"}} align="right">{statusColumn(row)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}