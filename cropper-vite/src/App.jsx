import { useState } from 'react'
import './App.css'

import Stack from '@mui/material/Stack'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import BasicTable from './table'

function App() {
  const [files, setFiles] = useState([])
  const [jobName, setJobName] = useState("")

  const fileHandler = (e) => {
    if (e.target.files) {
      setFiles(e.target.files)
    }
  }

  const jobNameHandler = (e) => {
    setJobName(e.target.value)
  }

  function upload() {
    if (!files.length) {
      return false;
    }
    var formData = new FormData()
    for (var i = 0; i < files.length; i++) {
      formData.append('file', files[i])
    }
    formData.append('jobName', jobName)
    fetch('/api/create_job', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(json => json)
      .catch(error => console.error(error))
    return false;
  }

  return (
    <>
      <Stack spacing={1}>
        <input onChange={fileHandler} type="file" name="file[]" multiple></input>
        <TextField onChange={jobNameHandler} slotProps={{ inputLabel: { className: 'jobLabelColor' }, input: { className: 'jobNameColor'}}} id="standard-basic" label="Job Name" variant="standard" />
        <Button onClick={upload} variant="contained">submit</Button>
        <BasicTable></BasicTable>
      </Stack>
    </>
  )
}

export default App
