args = {
    input: path string or list of paths string to frame_cap: maximum number of frames to process
    quality: percentage of frames to process (0 - 1)
    color_weight: colour analysis weighting relative to focus (-1 for raw values) 
    focus_weight: focus analysis weighting relative to focus (-1 for raw values) 
    farm: Weather to do the processing on the farm or locally on the api server
    priority: The farm priority
    farm_threads: the number of threads to use on the farm
    db_address: list of the mongo client address, database, and collection to store frame data
    cue_address: list of the cue api submitter address and version
    submission_threads: the number of threads to use if running localy
}