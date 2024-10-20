<h1 align="center">ETC Thumbnail Generator</h1>

###

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white&style=for-the-badge" height="40" alt="python logo"  />
  <img width="12" />
  <img src="https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white&style=for-the-badge" height="40" alt="mongodb logo"  />
  <img width="12" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&style=for-the-badge" height="40" alt="fastapi logo"  />
</div>

###

<br clear="both">

<h4 align="center">A http api that finds the most visually interesting frame of a given image sequence or video. Includes options to run on the ETC farm and return a job id untill finished.</h4>

###

<h3 align="left">Options:</h3>

###

<h5 align="left">Input - String or List</h5>

###

<p align="left">File paths to analyse</p>

###

<h5 align="left">Frame Cap - Integer</h5>

###

<p align="left">The maximum number of frames to process<br>Negative to remove cap</p>

###

<h5 align="left">Quality - Float</h5>

###

<p align="left">Percentage of frames to process<br>Range between 0 & 1</p>

###

<h5 align="left">Color Weight - Float</h5>

###

<p align="left">Color analysis weighting relative to focus<br>Negative for raw values</p>

###

<h5 align="left">Focus Weight - Float</h5>

###

<p align="left">In-focus weighting relative to color<br>Negative for raw values</p>

###

<h5 align="left">Farm - Boolean</h5>

###

<p align="left">Whether to run on the farm or the api host</p>

###

<h5 align="left">Priority - Integer</h5>

###

<p align="left">The priority of the job sent to the farm</p>

###

<h5 align="left">DB Address - List</h5>

###

<p align="left">A list made of a Mongo client address, database name & collection name to store frame data in</p>

###

<h5 align="left">Cue Address - List</h5>

###

<p align="left">A list made of the ETC cue api submitter & version</p>

###

<h5 align="left">Submission Threads - Integer</h5>

###

<p align="left">The number of threads to use if running on the api host</p>

###
