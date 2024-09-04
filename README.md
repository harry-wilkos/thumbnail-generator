<h1 align="center">ETC Thumbnail Generator</h1>
<div align="center">
A http api that finds the most visually interesting frame of a given image sequence or video. Includes options to run on the ETC farm and return a job id untill finished.
</div>

## Args:
### Input: strings or list of strings
File paths to analyse
#### frame_cap: Int
The maximum number of frames to process. -1 to remove cap
#### quality: Float
Percentage of frames to process (0 - 1)
#### color_weight: Float
colour analysis weighting relative to focus. -1 for raw values
#### focus_weight: Float
Frame analysis weighting relative to color. -1 for raw values
#### farm: Bool
Weather to run the analusis on the farm or locally on the api
#### priority: Int
The priority assigned to the job on the farm
#### db_address: List
A list made up of a Mongo client address, database name, and collection name to store frama data in
#### cue_address: List
A list made up of the ETC cue api submitter address and version
#### submission_threads: Int
THe number of threads to use if running locally
