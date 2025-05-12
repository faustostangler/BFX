from beatforge.config import MIN_BPM, STEP, MAX_BPM

def get_intervals():
    edges = list(range(MIN_BPM, MAX_BPM + STEP, STEP))
    return [(edges[i], edges[i+1]) for i in range(len(edges)-1)]
